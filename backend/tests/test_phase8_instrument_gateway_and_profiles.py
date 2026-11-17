"""Testes automatizados do Horizonte 3 — Sprint 8.3: Gateway de Instrumentos e Perfis Declarativos (H3.3).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §5 e ISO/IEC 17025 §7.11.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ValidationDomainError
from app.models.enums import EquipmentCalibrationStatus
from app.models.equipment import LaboratoryEquipment
from app.services import instrument_profiles

API = "/api/v1"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "instruments"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_agilent_chemstation_profile_parsing() -> None:
    """Valida ingestão de cromatograma Agilent ChemStation real via perfil declarativo."""
    fixture_path = FIXTURES_DIR / "agilent-chemstation" / "chromatogram_01.csv"
    assert fixture_path.exists(), f"Fixture não encontrada: {fixture_path}"
    raw_content = fixture_path.read_text(encoding="utf-8")

    profile = instrument_profiles.get_profile("agilent-chemstation-csv")
    parsed = instrument_profiles.parse_with_profile(profile, raw_content)

    assert parsed["profile_id"] == "agilent-chemstation-csv"
    assert parsed["peaks_count"] == 3
    assert parsed["main_peak"]["name"] == "Atorvastatina Calcica"
    assert parsed["retention_time_main_peak"] == 4.831
    assert parsed["calculated_purity_percent"] == 98.15
    assert parsed["units"]["retention_time"] == "min"


def test_shimadzu_labsolutions_profile_parsing() -> None:
    """Valida ingestão de cromatograma Shimadzu LabSolutions real via perfil declarativo."""
    fixture_path = FIXTURES_DIR / "shimadzu-labsolutions" / "chromatogram_01.txt"
    assert fixture_path.exists()
    raw_content = fixture_path.read_text(encoding="utf-8")

    profile = instrument_profiles.get_profile("shimadzu-labsolutions-csv")
    parsed = instrument_profiles.parse_with_profile(profile, raw_content)

    assert parsed["profile_id"] == "shimadzu-labsolutions-csv"
    assert parsed["peaks_count"] == 2
    assert parsed["main_peak"]["name"] == "Principio Ativo"
    assert parsed["retention_time_main_peak"] == 5.21
    assert parsed["calculated_purity_percent"] == 97.95


def test_thermo_chromeleon_profile_parsing() -> None:
    """Valida ingestão de cromatograma Thermo Chromeleon (delimitador ';' e vírgula decimal)."""
    fixture_path = FIXTURES_DIR / "thermo-chromeleon" / "chromatogram_01.csv"
    assert fixture_path.exists()
    raw_content = fixture_path.read_text(encoding="utf-8")

    profile = instrument_profiles.get_profile("thermo-chromeleon-csv")
    parsed = instrument_profiles.parse_with_profile(profile, raw_content)

    assert parsed["profile_id"] == "thermo-chromeleon-csv"
    assert parsed["peaks_count"] == 2
    assert parsed["main_peak"]["name"] == "Valproato de Sodio"
    assert parsed["retention_time_main_peak"] == 6.45
    assert parsed["calculated_purity_percent"] == 98.45


def test_astm_e1394_analyzer_parsing() -> None:
    """Valida ingestão de mensagens clínicas no formato ASTM E1381/E1394."""
    fixture_path = FIXTURES_DIR / "astm-e1394" / "analyzer_01.astm"
    assert fixture_path.exists()
    raw_content = fixture_path.read_text(encoding="utf-8")

    profile = instrument_profiles.get_profile("astm-e1394-analyzer")
    parsed = instrument_profiles.parse_with_profile(profile, raw_content)

    assert parsed["profile_id"] == "astm-e1394-analyzer"
    assert parsed["results_count"] == 3
    results = {r["parameter"]: r for r in parsed["results"]}
    assert "GLUCOSE" in results
    assert results["GLUCOSE"]["value_numeric"] == 95.4
    assert results["GLUCOSE"]["units"] == "mg/dL"
    assert "CHOLESTEROL" in results
    assert results["CHOLESTEROL"]["value_numeric"] == 182.1
    assert "TRIGLYCERIDES" in results
    assert results["TRIGLYCERIDES"]["value_numeric"] == 140.0


def test_profile_validation_rejects_missing_required_columns() -> None:
    """Garante que ausência de colunas obrigatórias declaradas é sumariamente rejeitada."""
    invalid_csv = "RT,Height,Name\n1.2,500,Pico A\n"
    profile = instrument_profiles.get_profile("agilent-chemstation-csv")

    with pytest.raises(ValidationDomainError) as exc_info:
        instrument_profiles.parse_with_profile(profile, invalid_csv)
    assert "Cabeçalho com as colunas obrigatórias" in str(exc_info.value)


@pytest.mark.asyncio
async def test_instrument_upload_with_profile_id_api(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida upload direto na API especificando explicitamente o perfil declarativo."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    async with db_factory() as db:
        equip = LaboratoryEquipment(
            id=uuid4(),
            code=f"HPLC-AGI-{uuid4().hex[:4].upper()}",
            name="Agilent 1260 Infinity II",
            manufacturer="Agilent Technologies",
            model="1260 Infinity II",
            serial_number=f"DE-{uuid4().hex[:6]}",
            calibration_status=EquipmentCalibrationStatus.CALIBRADO,
            is_active=True,
        )
        db.add(equip)
        await db.commit()
        equip_id = str(equip.id)

    fixture_path = FIXTURES_DIR / "agilent-chemstation" / "chromatogram_01.csv"
    raw_content = fixture_path.read_text(encoding="utf-8")

    payload = {
        "equipment_id": equip_id,
        "file_name": "chromatogram_01.csv",
        "file_format": "CHROMATOGRAPHY_CSV",
        "raw_content": raw_content,
        "profile_id": "agilent-chemstation-csv",
    }
    res = await client.post(
        f"{API}/instrument-data/upload-raw", json=payload, headers=admin_headers
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["parsed_data"]["profile_id"] == "agilent-chemstation-csv"
    assert data["parsed_data"]["main_peak"]["name"] == "Atorvastatina Calcica"


@pytest.mark.asyncio
async def test_equipment_auto_match_profile_api(
    db_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida inferência automática de perfil a partir do fabricante/modelo do equipamento cadastrado."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    async with db_factory() as db:
        equip = LaboratoryEquipment(
            id=uuid4(),
            code=f"HPLC-SHIM-{uuid4().hex[:4].upper()}",
            name="Shimadzu Nexera LC-40",
            manufacturer="Shimadzu Corporation",
            model="Nexera LC-40",
            serial_number=f"SH-{uuid4().hex[:6]}",
            calibration_status=EquipmentCalibrationStatus.CALIBRADO,
            is_active=True,
        )
        db.add(equip)
        await db.commit()
        equip_id = str(equip.id)

    fixture_path = FIXTURES_DIR / "shimadzu-labsolutions" / "chromatogram_01.txt"
    raw_content = fixture_path.read_text(encoding="utf-8")

    # Envia sem especificar profile_id: o LIMS deve inferir shimadzu-labsolutions-csv
    payload = {
        "equipment_id": equip_id,
        "file_name": "chromatogram_01.txt",
        "file_format": "CHROMATOGRAPHY_CSV",
        "raw_content": raw_content,
    }
    res = await client.post(
        f"{API}/instrument-data/upload-raw", json=payload, headers=admin_headers
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["parsed_data"]["profile_id"] == "shimadzu-labsolutions-csv"
    assert data["parsed_data"]["main_peak"]["name"] == "Principio Ativo"


@pytest.mark.asyncio
async def test_list_instrument_profiles_endpoint(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    """Valida rota de catálogo de perfis suportados."""
    login_admin = await login(client, "admin", "Admin@Lims2026")
    admin_headers = auth(login_admin["access_token"])

    res = await client.get(f"{API}/instrument-data/profiles", headers=admin_headers)
    assert res.status_code == 200, res.text
    profiles = res.json()
    ids = [p["profile_id"] for p in profiles]
    assert "agilent-chemstation-csv" in ids
    assert "shimadzu-labsolutions-csv" in ids
    assert "thermo-chromeleon-csv" in ids
    assert "astm-e1394-analyzer" in ids
