"""Suíte de Testes da Fase 5: Conectores e Aquisição Direta de Instrumentos Analíticos (Sprint 5.3).

Valida:
1. Proteção de autenticação em todos os endpoints de aquisição de instrumentos.
2. Parser metrológico de Balança Analítica (ASCII/RS-232): tara, peso líquido, peso bruto e estabilidade.
3. Parser de Espectrofotometria UV-Vis: detecção de lambda max e absorbância máxima.
4. Parser de Cromatografia (HPLC/GC): tabela de picos, tempos de retenção e cálculo de pureza.
5. Cálculo imutável de hash criptográfico SHA-256 no ato da ingestão (ALCOA+).
6. Intertravamento metrológico: rejeição de aquisições de equipamentos com calibração vencida (ISO 17025 §6.4).
7. Mapeamento direto e assistido na execução de ensaio (TestExecution), eliminando transcrição manual.
8. Sumário de dados brutos e taxa de mapeamento.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.device_sample import DeviceSample
from app.models.enums import EquipmentCalibrationStatus
from app.models.equipment import LaboratoryEquipment
from app.models.lab_test import LabTest
from app.models.test_execution import TestExecution

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def create_helper_equipment(
    db_factory: async_sessionmaker[AsyncSession],
    *,
    code: str = "BAL-TEST-01",
    name: str = "Balança Analítica Mettler",
    calibration_status: EquipmentCalibrationStatus = EquipmentCalibrationStatus.CALIBRADO,
    calibration_due_date: datetime | None = None,
) -> LaboratoryEquipment:
    if calibration_due_date is None:
        calibration_due_date = datetime.now(UTC) + timedelta(days=90)

    async with db_factory() as session:
        eq = LaboratoryEquipment(
            id=uuid4(),
            code=code,
            name=name,
            equipment_type="Balança Analítica",
            manufacturer="Mettler Toledo",
            model="XSR205DU",
            serial_number=f"SN-{uuid4().hex[:8].upper()}",
            calibration_status=calibration_status,
            calibration_due_date=calibration_due_date,
        )
        session.add(eq)
        await session.commit()
        await session.refresh(eq)
        return eq


async def create_helper_execution(
    db_factory: async_sessionmaker[AsyncSession],
    user_id: str,
) -> tuple[LabTest, TestExecution]:
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    async with db_factory() as session:
        sample = DeviceSample(
            id=uuid4(),
            accession_number=f"ACC-{uuid4().hex[:8].upper()}",
            manufacturer="Fabricante Exemplo",
            commercial_name="Equipamento Médico Teste",
            serial_number=f"SN-{uuid4().hex[:8]}",
            received_by_id=user_uuid,
        )
        session.add(sample)
        await session.flush()

        test = LabTest(
            id=uuid4(),
            device_sample_id=sample.id,
            name="Ensaio Gravimétrico",
            unit="g",
        )
        session.add(test)
        await session.flush()

        execution = TestExecution(
            id=uuid4(),
            lab_test_id=test.id,
            execution_number=1,
            temperature_celsius=Decimal("22.5"),
            humidity_percent=Decimal("55.0"),
            pressure_hpa=Decimal("1013.2"),
            raw_data={},
        )
        session.add(execution)
        await session.commit()
        await session.refresh(test)
        await session.refresh(execution)
        return test, execution


@pytest.mark.asyncio
async def test_instrument_endpoints_require_authentication(client: AsyncClient) -> None:
    """Garante que endpoints de aquisição rejeitam acessos sem autenticação."""
    res_list = await client.get(f"{API}/instrument-data")
    assert res_list.status_code == 401

    res_sum = await client.get(f"{API}/instrument-data/summary")
    assert res_sum.status_code == 401

    res_upload = await client.post(
        f"{API}/instrument-data/upload-raw",
        json={
            "equipment_id": str(uuid4()),
            "file_name": "teste.txt",
            "file_format": "BALANCA_ASCII",
            "raw_content": "12.345 g",
        },
    )
    assert res_upload.status_code == 401


@pytest.mark.asyncio
async def test_balance_ascii_ingestion_and_sha256(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida ingestão de dados brutos de Balança Analítica, cálculo de hash SHA-256 e parsing."""
    tec_token = (await login(client, "tecnico", users["tecnico"]["password"]))["access_token"]

    eq = await create_helper_equipment(db_factory, code="BAL-01", name="Balança Mettler Semi-Micro")

    raw_balance_data = (
        "---- METTLER TOLEDO ----\n"
        "Date: 16-Nov-2026\n"
        "T   +    2.1005 g\n"
        "G   +   14.5573 g\n"
        "N   +   12.4568 g\n"
        "Status: S (Stable)\n"
    )

    payload = {
        "equipment_id": str(eq.id),
        "file_name": "pesagem_amostra_01.txt",
        "file_format": "BALANCA_ASCII",
        "raw_content": raw_balance_data,
    }

    res = await client.post(
        f"{API}/instrument-data/upload-raw",
        headers=auth(tec_token),
        json=payload,
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["equipment_id"] == str(eq.id)
    assert data["file_format"] == "BALANCA_ASCII"
    assert len(data["raw_file_hash_sha256"]) == 64
    assert data["status"] == "IMPORTED"

    parsed = data["parsed_data"]
    assert parsed["instrument_type"] == "BALANCA_ANALITICA"
    assert parsed["net_weight"] == 12.4568
    assert parsed["tare"] == 2.1005
    assert parsed["gross_weight"] == 14.5573
    assert parsed["unit"] == "g"
    assert parsed["is_stable"] is True


@pytest.mark.asyncio
async def test_uv_vis_and_hplc_parsers(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida ingestão de dados de Espectrofotometria UV-Vis e Cromatografia HPLC."""
    tec_token = (await login(client, "tecnico", users["tecnico"]["password"]))["access_token"]

    eq_uv = await create_helper_equipment(db_factory, code="UV-01", name="Espectrofotômetro UV-Vis")
    eq_hplc = await create_helper_equipment(
        db_factory, code="HPLC-01", name="Cromatógrafo Líquido HPLC"
    )

    # 1. Teste UV-Vis
    raw_uv = (
        "Wavelength,Absorbance\n240.0,0.125\n250.0,0.450\n260.0,1.854\n270.0,0.920\n280.0,0.210\n"
    )
    res_uv = await client.post(
        f"{API}/instrument-data/upload-raw",
        headers=auth(tec_token),
        json={
            "equipment_id": str(eq_uv.id),
            "file_name": "varredura_uv.csv",
            "file_format": "UV_VIS_CSV",
            "raw_content": raw_uv,
        },
    )
    assert res_uv.status_code == 201
    uv_data = res_uv.json()["parsed_data"]
    assert uv_data["lambda_max"] == 260.0
    assert uv_data["max_absorbance"] == 1.854
    assert uv_data["points_count"] == 5

    # 2. Teste HPLC
    raw_hplc = "Peak,RT,Area,Height,%Area\n1,1.85,15200,2100,1.2\n2,4.50,1250000,95000,98.8\n"
    res_hplc = await client.post(
        f"{API}/instrument-data/upload-raw",
        headers=auth(tec_token),
        json={
            "equipment_id": str(eq_hplc.id),
            "file_name": "cromatograma_hplc.csv",
            "file_format": "CHROMATOGRAPHY_CSV",
            "raw_content": raw_hplc,
        },
    )
    assert res_hplc.status_code == 201
    hplc_data = res_hplc.json()["parsed_data"]
    assert hplc_data["peaks_count"] == 2
    assert hplc_data["retention_time_main_peak"] == 4.50
    assert hplc_data["calculated_purity_percent"] == 98.8


@pytest.mark.asyncio
async def test_calibration_interlock_blocks_overdue_equipment(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Garante intertravamento metrológico: rejeição de aquisições de equipamentos com calibração vencida."""
    tec_token = (await login(client, "tecnico", users["tecnico"]["password"]))["access_token"]

    # Equipamento com calibração vencida
    overdue_eq = await create_helper_equipment(
        db_factory,
        code="BAL-VENCIDA",
        name="Balança Descalibrada",
        calibration_status=EquipmentCalibrationStatus.VENCIDO,
        calibration_due_date=datetime.now(UTC) - timedelta(days=10),
    )

    res = await client.post(
        f"{API}/instrument-data/upload-raw",
        headers=auth(tec_token),
        json={
            "equipment_id": str(overdue_eq.id),
            "file_name": "leitura_bloqueada.txt",
            "file_format": "BALANCA_ASCII",
            "raw_content": "N + 5.0000 g\n",
        },
    )
    # Deve ser rejeitado com 409 Conflict
    assert res.status_code == 409
    assert "calibração vencida" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_map_instrument_data_to_test_execution(
    client: AsyncClient,
    users: dict[str, Any],
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida o mapeamento direto de leituras importadas para a entidade TestExecution."""
    tec_token = (await login(client, "tecnico", users["tecnico"]["password"]))["access_token"]

    eq = await create_helper_equipment(db_factory, code="BAL-MAP-01")
    _, execution = await create_helper_execution(db_factory, users["admin"]["id"])

    # 1. Faz upload do dado de balança
    res_up = await client.post(
        f"{API}/instrument-data/upload-raw",
        headers=auth(tec_token),
        json={
            "equipment_id": str(eq.id),
            "file_name": "pesagem_final.txt",
            "file_format": "BALANCA_ASCII",
            "raw_content": "N + 15.3421 g\nT + 1.2000 g\n",
        },
    )
    assert res_up.status_code == 201
    import_id = res_up.json()["id"]

    # 2. Mapeia para a execução de ensaio
    res_map = await client.post(
        f"{API}/instrument-data/{import_id}/map-to-execution",
        headers=auth(tec_token),
        json={"execution_id": str(execution.id)},
    )
    assert res_map.status_code == 200, res_map.text
    mapped = res_map.json()
    assert mapped["status"] == "MAPPED"
    assert mapped["test_execution_id"] == str(execution.id)
    assert mapped["mapped_at"] is not None

    # 3. Consulta sumário
    res_sum = await client.get(
        f"{API}/instrument-data/summary",
        headers=auth(tec_token),
    )
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["total_imports"] >= 1
    assert summary["mapped_imports"] >= 1
