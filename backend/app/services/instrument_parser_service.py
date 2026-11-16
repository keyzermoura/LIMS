"""Serviço de Parsers e Ingestão Direta de Instrumentos Analíticos (Fase 5 / Sprint 5.3).

Implementa:
1. Cálculo de hash imutável SHA-256 dos dados brutos (ALCOA+ / 21 CFR Part 11).
2. Parsers metrológicos para Balanças Analíticas (ASCII/RS-232), UV-Vis e Cromatografia (HPLC/GC).
3. Intertravamento operacional: bloqueia importação de equipamentos com calibração vencida.
4. Mapeamento direto e assistido dos resultados na execução do ensaio (Zero Transcrição Manual).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationDomainError
from app.models.enums import (
    AuditAction,
    AuditEntity,
    EquipmentCalibrationStatus,
    ExecutionStatus,
    InstrumentFileFormat,
    InstrumentImportStatus,
)
from app.models.equipment import LaboratoryEquipment
from app.models.instrument_data import InstrumentDataImport
from app.models.test_execution import TestExecution
from app.services import audit_service


def compute_sha256(content: bytes | str) -> str:
    """Calcula o resumo criptográfico SHA-256 dos dados brutos."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def parse_balanca_ascii(raw_text: str) -> dict[str, Any]:
    """Extrai leituras de peso de protocolos ASCII/RS-232 de balanças analíticas.
    
    Suporta saídas Mettler Toledo, Shimadzu, Sartorius e balanças genéricas:
    Exemplos:
    - N  +   12.4568 g
    - T  +    2.1002 g
    - G  +   14.5570 g
    - S S      12.4568 g
    - Net: 12.4568 g / Tare: 2.1002 g
    """
    net_weight: float | None = None
    gross_weight: float | None = None
    tare: float | None = None
    unit = "g"
    stable = True
    readings: list[dict[str, Any]] = []

    lines = raw_text.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Procura linhas com unidade de medida (g, mg, kg)
        unit_match = re.search(r"\b(mg|kg|g)\b", line_clean, re.IGNORECASE)
        current_unit = unit_match.group(1).lower() if unit_match else "g"

        # Regex para capturar números decimais com sinal opcional
        number_match = re.search(r"[-+]?\s*([0-9]+\.[0-9]+|[0-9]+)", line_clean)
        if not number_match:
            continue

        try:
            val_str = number_match.group(0).replace(" ", "")
            val = float(val_str)
        except ValueError:
            continue

        # Identificação de Peso Líquido (N / Net / Líquido)
        if re.search(r"^(N\b|Net|L[íi]quido)", line_clean, re.IGNORECASE):
            net_weight = val
            unit = current_unit
            readings.append({"type": "NET", "value": val, "unit": current_unit, "line": line_clean})
        # Identificação de Tara (T / Tare / Tara)
        elif re.search(r"^(T\b|Tare|Tara)", line_clean, re.IGNORECASE):
            tare = val
            readings.append({"type": "TARE", "value": val, "unit": current_unit, "line": line_clean})
        # Identificação de Peso Bruto (G / B / Gross / Bruto)
        elif re.search(r"^(G\b|B\b|Gross|Bruto)", line_clean, re.IGNORECASE):
            gross_weight = val
            readings.append({"type": "GROSS", "value": val, "unit": current_unit, "line": line_clean})
        # Leitura estável direta (Ex: S S 12.4568 g ou apenas valor numérico com unidade)
        else:
            if re.search(r"\bD\b", line_clean):  # Dynamic / Instável
                stable = False
            if net_weight is None:
                net_weight = val
                unit = current_unit
            readings.append({"type": "SAMPLE", "value": val, "unit": current_unit, "line": line_clean})

    if net_weight is None and readings:
        net_weight = readings[0]["value"]
        unit = readings[0]["unit"]

    if net_weight is None:
        raise ValidationDomainError("Não foi possível identificar nenhuma leitura de peso válida no arquivo.")

    return {
        "instrument_type": "BALANCA_ANALITICA",
        "net_weight": net_weight,
        "gross_weight": gross_weight,
        "tare": tare,
        "unit": unit,
        "is_stable": stable,
        "readings_count": len(readings),
        "readings": readings,
    }


def parse_uv_vis_csv(raw_text: str) -> dict[str, Any]:
    """Processa dados de varredura ou fotometria de Espectrofotômetro UV-Vis.
    
    Espera formato tabular (CSV, TSV, ponto e vírgula):
    Wavelength, Absorbance
    200.0, 0.052
    210.0, 0.124
    ...
    """
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        raise ValidationDomainError("Arquivo UV-Vis está vazio.")

    # Detecção de delimitador
    sample = "\n".join(lines[:10])
    delimiter = ";" if ";" in sample and "," not in sample else ("," if "," in sample else "\t")

    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    spectrum: list[dict[str, float]] = []
    max_abs = -999999.0
    lambda_max: float | None = None

    for row in reader:
        if len(row) < 2:
            continue
        try:
            # Substitui vírgula decimal por ponto se aplicável
            c1 = row[0].strip().replace(",", ".")
            c2 = row[1].strip().replace(",", ".")
            wavelength = float(c1)
            absorbance = float(c2)

            spectrum.append({"wavelength": wavelength, "absorbance": absorbance})
            if absorbance > max_abs:
                max_abs = absorbance
                lambda_max = wavelength
        except ValueError:
            # Linha de cabeçalho ignorada
            continue

    if not spectrum:
        raise ValidationDomainError("Nenhum par (Comprimento de Onda, Absorbância) numérico foi encontrado.")

    return {
        "instrument_type": "ESPECTROFOTOMETRO_UV_VIS",
        "points_count": len(spectrum),
        "lambda_max": lambda_max,
        "max_absorbance": max_abs,
        "spectrum_summary": spectrum[:100],  # Amostra das primeiras 100 leituras
        "start_wavelength": spectrum[0]["wavelength"],
        "end_wavelength": spectrum[-1]["wavelength"],
    }


def parse_chromatography_csv(raw_text: str) -> dict[str, Any]:
    """Processa tabelas de integração de picos cromatográficos (HPLC / GC).
    
    Espera colunas como:
    Peak#, Retention Time, Area, Height, % Area
    1, 2.15, 120500, 15000, 1.2
    2, 4.82, 9850000, 840000, 98.8
    """
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        raise ValidationDomainError("Arquivo cromatográfico está vazio.")

    sample = "\n".join(lines[:10])
    delimiter = ";" if ";" in sample and "," not in sample else ("," if "," in sample else "\t")

    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    peaks: list[dict[str, Any]] = []
    total_area = 0.0
    main_peak: dict[str, Any] | None = None
    max_area = -1.0

    for _idx, row in enumerate(reader):
        if len(row) < 3:
            continue
        try:
            # Trata possíveis formatos: [Peak#, RT, Area, Height, %Area] ou [RT, Area, Height]
            nums = [float(col.strip().replace(",", ".")) for col in row if re.match(r"^-?[0-9]+(\.[0-9]+)?$", col.strip().replace(",", "."))]
            if len(nums) < 2:
                continue

            rt = nums[0] if len(nums) == 2 else nums[1]
            area = nums[1] if len(nums) == 2 else nums[2]
            height = nums[3] if len(nums) >= 4 else None
            area_pct = nums[4] if len(nums) >= 5 else None

            peak_entry = {
                "peak_index": len(peaks) + 1,
                "retention_time_min": rt,
                "area": area,
                "height": height,
                "area_percent": area_pct,
            }
            peaks.append(peak_entry)
            total_area += area

            if area > max_area:
                max_area = area
                main_peak = peak_entry
        except ValueError:
            continue

    if not peaks:
        raise ValidationDomainError("Nenhum pico cromatográfico válido foi identificado no arquivo.")

    purity = (max_area / total_area * 100.0) if total_area > 0 else 0.0

    return {
        "instrument_type": "CROMATOGRAFO_HPLC_GC",
        "peaks_count": len(peaks),
        "total_area": total_area,
        "main_peak": main_peak,
        "retention_time_main_peak": main_peak["retention_time_min"] if main_peak else None,
        "calculated_purity_percent": round(purity, 2),
        "peaks": peaks,
    }


def parse_generic_json(raw_text: str) -> dict[str, Any]:
    """Processa dados de instrumentos que exportam JSON padronizado."""
    try:
        data = json.loads(raw_text)
        if not isinstance(data, dict):
            raise ValueError("JSON raiz deve ser um objeto.")
        return data
    except Exception as exc:
        raise ValidationDomainError(f"Arquivo JSON inválido: {exc}") from exc


def parse_instrument_data(
    file_format: InstrumentFileFormat, raw_text: str
) -> dict[str, Any]:
    """Despacha a análise para o parser específico de acordo com o formato."""
    if file_format == InstrumentFileFormat.BALANCA_ASCII:
        return parse_balanca_ascii(raw_text)
    elif file_format == InstrumentFileFormat.UV_VIS_CSV:
        return parse_uv_vis_csv(raw_text)
    elif file_format == InstrumentFileFormat.CHROMATOGRAPHY_CSV:
        return parse_chromatography_csv(raw_text)
    elif file_format == InstrumentFileFormat.GENERIC_JSON:
        return parse_generic_json(raw_text)
    raise ValidationDomainError(f"Formato {file_format} não suportado.")


# -----------------------------------------------------------------------------
# Operações de Banco de Dados e Ciclo de Vida ALCOA+
# -----------------------------------------------------------------------------


async def upload_instrument_data(
    db: AsyncSession,
    *,
    equipment_id: UUID,
    user_id: UUID,
    actor_username: str,
    file_name: str,
    raw_content: str,
    file_format: InstrumentFileFormat,
    test_execution_id: UUID | None = None,
) -> InstrumentDataImport:
    """Valida calibração, calcula hash imutável SHA-256, parseia e armazena os dados brutos."""
    # 1. Verifica equipamento e intertravamento de calibração (ISO 17025 §6.4)
    equipment = await db.get(LaboratoryEquipment, equipment_id)
    if not equipment:
        raise NotFoundError("Equipamento analítico não encontrado.")

    now = datetime.now(UTC)
    today = now.date()
    calib_date = equipment.calibration_due_date.date() if equipment.calibration_due_date else None

    if (
        equipment.calibration_status == EquipmentCalibrationStatus.VENCIDO
        or (calib_date and calib_date < today)
    ):
        raise ConflictError(
            f"Aquisição bloqueada: Equipamento {equipment.code} está com calibração vencida "
            f"({calib_date.strftime('%d/%m/%Y') if calib_date else 'Sem data'}). "
            f"Intertravamento metrológico ativo conforme ISO/IEC 17025:2017 §6.4."
        )

    # 2. Se informada execução, valida existência
    if test_execution_id:
        execution = await db.get(TestExecution, test_execution_id)
        if not execution:
            raise NotFoundError("Execução de ensaio não encontrada.")

    # 3. Cálculo de integridade criptográfica
    sha256_hash = compute_sha256(raw_content)

    # 4. Parsing das grandezas
    parsed_data = parse_instrument_data(file_format, raw_content)

    # 5. Persistência
    record = InstrumentDataImport(
        equipment_id=equipment_id,
        test_execution_id=test_execution_id,
        imported_by_id=user_id,
        file_name=file_name,
        file_format=file_format,
        raw_file_hash_sha256=sha256_hash,
        raw_content=raw_content,
        parsed_data=parsed_data,
        status=InstrumentImportStatus.IMPORTED,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # 6. Trilha de auditoria ALCOA+
    await audit_service.append(
        db,
        action=AuditAction.DATA_ACQUISITION,
        entity_type=AuditEntity.INSTRUMENT_DATA_IMPORT.value,
        entity_id=str(record.id),
        actor_username=actor_username,
        reason=f"Aquisição direta de dados brutos do equipamento {equipment.code} ({file_name}) com SHA-256 {sha256_hash[:16]}...",
        new_value={
            "equipment_code": equipment.code,
            "file_name": file_name,
            "file_format": file_format.value,
            "sha256": sha256_hash,
            "readings_summary": {k: v for k, v in parsed_data.items() if k != "spectrum_summary"},
        },
    )
    await db.commit()
    return record


async def list_instrument_imports(
    db: AsyncSession,
    *,
    equipment_id: UUID | None = None,
    test_execution_id: UUID | None = None,
    status: InstrumentImportStatus | None = None,
    limit: int = 50,
) -> list[InstrumentDataImport]:
    """Lista importações de instrumentos com filtros."""
    stmt = select(InstrumentDataImport)
    if equipment_id:
        stmt = stmt.where(InstrumentDataImport.equipment_id == equipment_id)
    if test_execution_id:
        stmt = stmt.where(InstrumentDataImport.test_execution_id == test_execution_id)
    if status:
        stmt = stmt.where(InstrumentDataImport.status == status)

    stmt = stmt.order_by(InstrumentDataImport.created_at.desc()).limit(limit)
    return list((await db.scalars(stmt)).all())


async def get_instrument_import(
    db: AsyncSession, import_id: UUID
) -> InstrumentDataImport:
    """Busca um registro de importação por UUID."""
    record = await db.get(InstrumentDataImport, import_id)
    if not record:
        raise NotFoundError("Registro de aquisição de instrumento não encontrado.")
    return record


async def map_import_to_execution(
    db: AsyncSession,
    *,
    import_id: UUID,
    execution_id: UUID,
    actor_username: str,
) -> InstrumentDataImport:
    """Mapeia os dados brutos de um instrumento diretamente nos resultados do TestExecution."""
    record = await get_instrument_import(db, import_id)
    execution = await db.get(TestExecution, execution_id)
    if not execution:
        raise NotFoundError("Execução de ensaio não encontrada.")

    if execution.status in (ExecutionStatus.CONCLUIDA, ExecutionStatus.CANCELADA):
        raise ConflictError(
            f"Não é possível mapear dados para execução em status {execution.status.value}."
        )

    # Injeta os dados brutos no raw_data e calcula result_value / result_text
    current_raw = dict(execution.raw_data or {})
    current_raw["instrument_acquisition"] = {
        "import_id": str(record.id),
        "equipment_code": record.equipment.code,
        "file_name": record.file_name,
        "file_format": record.file_format.value,
        "sha256": record.raw_file_hash_sha256,
        "data": record.parsed_data,
        "acquired_at": record.created_at.isoformat(),
    }

    # Se for balança analítica, atualiza campo de peso líquido diretamente se existir
    if record.file_format == InstrumentFileFormat.BALANCA_ASCII:
        weight = record.parsed_data.get("net_weight")
        if weight is not None:
            execution.result_value = Decimal(str(weight))
            execution.result_text = f"{weight} {record.parsed_data.get('unit', 'g')}"
    elif record.file_format == InstrumentFileFormat.UV_VIS_CSV:
        abs_max = record.parsed_data.get("max_absorbance")
        lambda_max = record.parsed_data.get("lambda_max")
        if abs_max is not None:
            execution.result_value = Decimal(str(abs_max))
            execution.result_text = f"Absorbância {abs_max} em {lambda_max} nm"
    elif record.file_format == InstrumentFileFormat.CHROMATOGRAPHY_CSV:
        purity = record.parsed_data.get("calculated_purity_percent")
        if purity is not None:
            execution.result_value = Decimal(str(purity))
            execution.result_text = f"Pureza cromatográfica {purity}% (RT: {record.parsed_data.get('retention_time_main_peak')} min)"

    execution.raw_data = current_raw

    # Atualiza o registro de importação
    record.test_execution_id = execution_id
    record.status = InstrumentImportStatus.MAPPED
    record.mapped_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(record)
    await db.refresh(execution)

    # Registra na trilha de auditoria
    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.TEST_EXECUTION.value,
        entity_id=str(execution.id),
        actor_username=actor_username,
        reason=f"Mapeamento automático de dados de instrumento {record.equipment.code} (SHA-256: {record.raw_file_hash_sha256[:16]}...) na execução {execution.id}.",
        new_value={
            "import_id": str(record.id),
            "execution_id": str(execution.id),
            "sha256": record.raw_file_hash_sha256,
        },
    )
    await db.commit()
    return record
