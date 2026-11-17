"""Catálogo de Perfis Declarativos e Engine de Parsing de Instrumentos (H3.3).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §5.3 e ISO/IEC 17025 §7.11.
Substitui heurísticas soltas por especificações versionadas e determinísticas.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any

from app.core.errors import NotFoundError, ValidationDomainError
from app.services.astm_parser import parse_astm_e1394


@dataclass(frozen=True)
class InstrumentProfile:
    profile_id: str
    name: str
    version: int
    instrument_category: str  # CROMATOGRAFIA, ESPECTROFOTOMETRIA, BALANCA, ANALISADOR_CLINICO
    manufacturer: str
    model_regex: str
    delimiter: str = ","
    decimal_separator: str = "."
    columns: dict[str, str] = field(default_factory=dict)  # canonical_name -> file_column_name
    units: dict[str, str] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)  # min_rows, required_columns


INSTRUMENT_PROFILES: dict[str, InstrumentProfile] = {
    "agilent-chemstation-csv": InstrumentProfile(
        profile_id="agilent-chemstation-csv",
        name="Agilent ChemStation HPLC/GC Integration Report",
        version=3,
        instrument_category="CROMATOGRAFIA",
        manufacturer="Agilent",
        model_regex=r"^1100|^1200|^1260|^1290|^7890|^8890",
        delimiter=",",
        decimal_separator=".",
        columns={
            "retention_time": "RT",
            "area": "Area",
            "height": "Height",
            "area_percent": "% Area",
            "peak_name": "Name",
        },
        units={"retention_time": "min", "area": "mAU*s"},
        validation={"min_rows": 1, "required": ["RT", "Area"]},
    ),
    "shimadzu-labsolutions-csv": InstrumentProfile(
        profile_id="shimadzu-labsolutions-csv",
        name="Shimadzu LabSolutions Quantitative Report",
        version=2,
        instrument_category="CROMATOGRAFIA",
        manufacturer="Shimadzu",
        model_regex=r"^Prominence|^Nexera|^LC-|^GC-",
        delimiter=",",
        decimal_separator=".",
        columns={
            "retention_time": "R.Time",
            "area": "Area",
            "height": "Height",
            "area_percent": "Area%",
            "peak_name": "Name",
        },
        units={"retention_time": "min", "area": "uV*s"},
        validation={"min_rows": 1, "required": ["R.Time", "Area"]},
    ),
    "thermo-chromeleon-csv": InstrumentProfile(
        profile_id="thermo-chromeleon-csv",
        name="Thermo Scientific Chromeleon Chromatography Export",
        version=2,
        instrument_category="CROMATOGRAFIA",
        manufacturer="Thermo Scientific",
        model_regex=r"^Vanquish|^Ultimate|^Dionex|^TRACE",
        delimiter=";",
        decimal_separator=",",
        columns={
            "retention_time": "Ret.Time",
            "area": "Area",
            "height": "Height",
            "area_percent": "Rel.Area",
            "peak_name": "Peak Name",
        },
        units={"retention_time": "min", "area": "mAU*min"},
        validation={"min_rows": 1, "required": ["Ret.Time", "Area"]},
    ),
    "astm-e1394-analyzer": InstrumentProfile(
        profile_id="astm-e1394-analyzer",
        name="Generic ASTM E1381/E1394 Clinical Analyzer Protocol",
        version=1,
        instrument_category="ANALISADOR_CLINICO",
        manufacturer="Generic",
        model_regex=r".*",
        delimiter="|",
        decimal_separator=".",
        validation={"min_rows": 3, "required": ["R"]},
    ),
}


def get_profile(profile_id: str) -> InstrumentProfile:
    """Busca perfil pelo identificador estrito."""
    profile = INSTRUMENT_PROFILES.get(profile_id)
    if not profile:
        raise NotFoundError(f"Perfil de instrumento '{profile_id}' não encontrado.")
    return profile


def match_profile_for_equipment(
    manufacturer: str | None, model: str | None = None
) -> InstrumentProfile | None:
    """Identifica automaticamente o perfil adequado com base no fabricante e modelo cadastrado."""
    if not manufacturer:
        return None
    m_clean = manufacturer.strip().lower()
    for prof in INSTRUMENT_PROFILES.values():
        if prof.manufacturer.lower() in m_clean or m_clean in prof.manufacturer.lower():
            if not prof.model_regex or prof.model_regex == ".*":
                return prof
            if model and re.search(prof.model_regex, model.strip(), re.IGNORECASE):
                return prof
            # Se não especificou modelo ou bate fabricante, usa como fallback
            return prof
    return None


def parse_with_profile(profile: InstrumentProfile, raw_text: str) -> dict[str, Any]:
    """Processa o arquivo conforme as regras declarativas do perfil versionado."""
    if profile.profile_id == "astm-e1394-analyzer":
        parsed = parse_astm_e1394(raw_text)
        parsed["profile_id"] = profile.profile_id
        parsed["profile_version"] = profile.version
        return parsed

    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        raise ValidationDomainError("Arquivo do instrumento está vazio.")

    # 1. Encontra a linha de cabeçalho baseando-se nas colunas requeridas
    required_cols = profile.validation.get("required", [])
    header_idx: int | None = None
    header_cols: list[str] = []

    for idx, line in enumerate(lines[:30]):  # Procura cabeçalho nas primeiras 30 linhas
        parts = [c.strip().strip('"').strip("'") for c in line.split(profile.delimiter)]
        matched = sum(1 for req in required_cols if any(req.lower() == p.lower() for p in parts))
        if matched == len(required_cols):
            header_idx = idx
            header_cols = parts
            break

    if header_idx is None:
        raise ValidationDomainError(
            f"Cabeçalho com as colunas obrigatórias {required_cols} não encontrado no arquivo "
            f"conforme perfil '{profile.profile_id}' (v{profile.version})."
        )

    # 2. Mapeia índices das colunas canônicas
    col_map: dict[str, int] = {}
    for canonical, expected in profile.columns.items():
        for col_idx, actual in enumerate(header_cols):
            if actual.lower() == expected.lower():
                col_map[canonical] = col_idx
                break

    # Verifica se os requeridos foram mapeados
    for req in required_cols:
        canonical_key = next((k for k, v in profile.columns.items() if v.lower() == req.lower()), None)
        if canonical_key and canonical_key not in col_map:
            raise ValidationDomainError(
                f"Coluna obrigatória '{req}' do perfil '{profile.profile_id}' não pôde ser mapeada."
            )

    # 3. Lê e extrai dados
    data_lines = lines[header_idx + 1 :]
    reader = csv.reader(io.StringIO("\n".join(data_lines)), delimiter=profile.delimiter)

    peaks: list[dict[str, Any]] = []
    total_area = 0.0
    main_peak: dict[str, Any] | None = None
    max_area = -1.0

    def parse_float_val(r: list[str], col_name: str) -> float | None:
        c_idx = col_map.get(col_name)
        if c_idx is None or c_idx >= len(r):
            return None
        val_str = r[c_idx].strip().strip('"')
        if profile.decimal_separator == ",":
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            val_str = val_str.replace(",", "")
        try:
            return float(val_str)
        except ValueError:
            return None

    def parse_str_val(r: list[str], col_name: str) -> str | None:
        c_idx = col_map.get(col_name)
        if c_idx is None or c_idx >= len(r):
            return None
        return r[c_idx].strip().strip('"')

    for _row_idx, row in enumerate(reader):
        if not row or all(not c.strip() for c in row):
            continue

        rt = parse_float_val(row, "retention_time")
        area = parse_float_val(row, "area")

        if rt is None or area is None:
            continue

        height = parse_float_val(row, "height")
        area_pct = parse_float_val(row, "area_percent")
        peak_name = parse_str_val(row, "peak_name")

        peak_entry = {
            "peak_index": len(peaks) + 1,
            "name": peak_name or f"Peak {len(peaks) + 1}",
            "retention_time": rt,
            "area": area,
            "height": height,
            "area_percent": area_pct,
        }
        peaks.append(peak_entry)
        total_area += area

        if area > max_area:
            max_area = area
            main_peak = peak_entry

    min_rows = profile.validation.get("min_rows", 1)
    if len(peaks) < min_rows:
        raise ValidationDomainError(
            f"O arquivo forneceu {len(peaks)} linhas de dados, mínimo exigido pelo perfil é {min_rows}."
        )

    # Recalcula pureza percentual se não fornecida
    for p in peaks:
        if p["area_percent"] is None and total_area > 0:
            p["area_percent"] = round((p["area"] / total_area) * 100.0, 2)

    calculated_purity = round((max_area / total_area * 100.0), 2) if total_area > 0 else 0.0

    return {
        "profile_id": profile.profile_id,
        "profile_name": profile.name,
        "profile_version": profile.version,
        "instrument_category": profile.instrument_category,
        "peaks_count": len(peaks),
        "total_area": total_area,
        "main_peak": main_peak,
        "retention_time_main_peak": main_peak["retention_time"] if main_peak else None,
        "calculated_purity_percent": calculated_purity,
        "peaks": peaks,
        "units": profile.units,
    }
