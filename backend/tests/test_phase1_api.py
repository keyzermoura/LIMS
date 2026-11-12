"""Testes de integração HTTP para a Fase 1 (M1.1): Solicitação, Recebimento e Custódia."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

from app.models.enums import (
    ConferenceStatus,
    CustodyEventType,
    CustodyObjectStatus,
    PresentationStatus,
    ReceiptDecisionEnum,
    ReceiptStatus,
    SolicitationStatus,
)


async def _login(client: AsyncClient, username: str, password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return str(res.json()["access_token"])


async def test_full_phase1_flow(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    custodiante_token = await _login(client, "custodiante", users["custodiante"]["password"])

    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}
    custodiante_auth = {"Authorization": f"Bearer {custodiante_token}"}

    # 1. Fiscal cadastra Solicitação com 2 itens
    sol_payload = {
        "requester_name": "Agência Nacional de Vigilância",
        "requester_email": "vigilancia@anvisa.gov.br",
        "requester_document": "00.000.000/0001-00",
        "requester_organization": "GGTPS / ANVISA",
        "purpose": "Ação de fiscalização pós-mercado de marca-passos",
        "request_type": "FISCALIZACAO",
        "priority": "ALTA",
        "items": [
            {
                "product_name": "Marca-passo Cardíaco Modelo Alfa",
                "category": "Dispositivo Médico Implantável",
                "manufacturer": "CardioTech Brasil Ltda",
                "model": "Alfa-200",
                "serial_number": "SN-ALFA-001",
                "lot_number": "LOT-2026-A",
                "declared_quantity": 2.0,
                "unit_of_measure": "UN",
                "notes": "Amostra lacrada",
            },
            {
                "product_name": "Eletrodo de Estimulação Cardíaca",
                "category": "Acessório",
                "manufacturer": "CardioTech Brasil Ltda",
                "model": "Eletro-Beta",
                "serial_number": "SN-ELE-002",
                "lot_number": "LOT-2026-B",
                "declared_quantity": 4.0,
                "unit_of_measure": "UN",
                "notes": "Acessório compatível",
            },
        ],
    }

    create_res = await client.post(
        "/api/v1/solicitations", json=sol_payload, headers=fiscal_auth
    )
    assert create_res.status_code == 201, create_res.text
    sol_data = create_res.json()
    sol_id = sol_data["id"]

    assert sol_data["solicitation_number"].startswith("SOL-2026-")
    assert sol_data["status"] == SolicitationStatus.RASCUNHO.value
    assert len(sol_data["items"]) == 2
    assert sol_data["has_receipt"] is False
    assert "X-Audit-Sequence" in create_res.headers

    # 2. Listar e consultar por ID
    list_res = await client.get("/api/v1/solicitations", headers=fiscal_auth)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    get_res = await client.get(f"/api/v1/solicitations/{sol_id}", headers=fiscal_auth)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == sol_id

    # 3. Atualizar em RASCUNHO
    update_res = await client.put(
        f"/api/v1/solicitations/{sol_id}",
        json={"priority": "URGENTE", "version": sol_data["version"]},
        headers=fiscal_auth,
    )
    assert update_res.status_code == 200
    assert update_res.json()["priority"] == "URGENTE"
    assert update_res.json()["version"] == 2

    # Conflito de concorrência com versão defasada
    conflict_res = await client.put(
        f"/api/v1/solicitations/{sol_id}",
        json={"priority": "NORMAL", "version": 1},
        headers=fiscal_auth,
    )
    assert conflict_res.status_code == 409

    # 4. Submeter a solicitação
    submit_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/submit",
        json={"version": 2, "notes": "Submissão formal aprovada"},
        headers=fiscal_auth,
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == SolicitationStatus.SUBMETIDA.value
    assert submit_res.json()["submitted_at"] is not None

    # Edição após submissão é bloqueada
    blocked_edit = await client.put(
        f"/api/v1/solicitations/{sol_id}",
        json={"priority": "BAIXA", "version": 3},
        headers=fiscal_auth,
    )
    assert blocked_edit.status_code == 422 or blocked_edit.status_code == 400

    # 5. Técnico registra a chegada física e formaliza o Recebimento
    rec_payload = {
        "arrival_location": "Doca 2 - Triagem e Custódia",
        "external_protocol": "PROT-ANVISA-2026-9999",
        "delivery_method": "Correios Sedex 10",
        "packaging_condition": "Íntegro com lacre oficial",
        "notes": "Pacote recebido sem avarias aparentes",
    }
    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json=rec_payload,
        headers=tecnico_auth,
    )
    assert rec_res.status_code == 201, rec_res.text
    rec_data = rec_res.json()
    receipt_id = rec_data["id"]

    assert rec_data["receipt_number"].startswith("REC-2026-")
    assert rec_data["status"] == ReceiptStatus.REGISTRADO.value
    assert len(rec_data["items"]) == 2

    # Verifica objetos de custódia gerados para cada item
    item1 = rec_data["items"][0]
    assert len(item1["custody_objects"]) == 1
    custody_obj1 = item1["custody_objects"][0]
    custody_obj1_id = custody_obj1["id"]
    assert custody_obj1["object_code"].startswith("OBJ-2026-")
    assert custody_obj1["status"] == CustodyObjectStatus.SOB_GUARDA.value

    item2 = rec_data["items"][1]
    custody_obj2 = item2["custody_objects"][0]
    custody_obj2_id = custody_obj2["id"]

    # Duplicidade de recebimento deve ser rejeitada
    dup_rec = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json=rec_payload,
        headers=tecnico_auth,
    )
    assert dup_rec.status_code == 409

    # Consulta recebimento pela solicitação
    rec_by_sol = await client.get(
        f"/api/v1/solicitations/{sol_id}/receipt", headers=tecnico_auth
    )
    assert rec_by_sol.status_code == 200
    assert rec_by_sol.json()["id"] == receipt_id

    # 6. Conferência individual do Item 1
    conf_res = await client.post(
        f"/api/v1/receipts/{receipt_id}/items/{item1['id']}/conference",
        json={
            "presentation_status": PresentationStatus.PRESENTED.value,
            "presented_quantity": 2.0,
            "conference_status": ConferenceStatus.CONFORME.value,
            "decision": ReceiptDecisionEnum.ACCEPTED.value,
            "notes": "Conferência quantitativa e física realizada com sucesso",
            "version": item1["version"],
        },
        headers=tecnico_auth,
    )
    assert conf_res.status_code == 200, conf_res.text
    assert conf_res.json()["conference_status"] == ConferenceStatus.CONFORME.value

    # Recebimento passou para EM_CONFERENCIA
    rec_check = await client.get(f"/api/v1/receipts/{receipt_id}", headers=tecnico_auth)
    assert rec_check.json()["status"] == ReceiptStatus.EM_CONFERENCIA.value

    # 7. Transferência de custódia do Objeto 1 para o Custodiante
    transfer_res = await client.post(
        f"/api/v1/custody/objects/{custody_obj1_id}/transfers",
        json={
            "to_custodian_id": users["custodiante"]["id"],
            "to_location": "Bancada de Ensaios Elétricos",
            "reason": "Transferência para preparação de ensaios prévios",
            "version": custody_obj1["version"],
        },
        headers=custodiante_auth,
    )
    assert transfer_res.status_code == 200, transfer_res.text
    assert transfer_res.json()["current_custodian_id"] == users["custodiante"]["id"]
    assert transfer_res.json()["current_location"] == "Bancada de Ensaios Elétricos"

    # Histórico de custódia do objeto 1 tem INGRESSO e TRANSFERENCIA
    history_res = await client.get(
        f"/api/v1/custody/objects/{custody_obj1_id}/history", headers=custodiante_auth
    )
    assert history_res.status_code == 200
    events = history_res.json()
    assert len(events) == 2
    assert events[0]["event_type"] == CustodyEventType.INGRESSO.value
    assert events[1]["event_type"] == CustodyEventType.TRANSFERENCIA.value

    # 8. Aceite técnico do Objeto 1 -> Gera atomicamente a DeviceSample!
    accept_res = await client.post(
        f"/api/v1/custody/objects/{custody_obj1_id}/acceptance",
        json={
            "decision": ReceiptDecisionEnum.ACCEPTED.value,
            "storage_location": "Almoxarifado Geral - Prateleira A1",
            "notes": "Aceite técnico aprovado com conformidade total",
            "version": transfer_res.json()["version"],
        },
        headers=tecnico_auth,
    )
    assert accept_res.status_code == 200, accept_res.text
    sample_data = accept_res.json()
    assert sample_data is not None
    assert sample_data["accession_number"].startswith("LIMS-2026-")
    assert sample_data["commercial_name"] == "Marca-passo Cardíaco Modelo Alfa"
    assert sample_data["current_location"] == "Almoxarifado Geral - Prateleira A1"

    # O objeto 1 agora está com status ACEITO
    obj1_final = await client.get(
        f"/api/v1/custody/objects/{custody_obj1_id}", headers=tecnico_auth
    )
    assert obj1_final.json()["status"] == CustodyObjectStatus.ACEITO.value
    assert obj1_final.json()["linked_device_sample_id"] == sample_data["id"]

    # 9. Recusa técnica do Objeto 2
    reject_res = await client.post(
        f"/api/v1/custody/objects/{custody_obj2_id}/acceptance",
        json={
            "decision": ReceiptDecisionEnum.REJECTED.value,
            "storage_location": "Área de Descarte/Devolução",
            "notes": "Eletrodos com isolamento rompido - não conforme",
            "version": custody_obj2["version"],
        },
        headers=tecnico_auth,
    )
    assert reject_res.status_code == 200
    assert reject_res.json() is None

    obj2_final = await client.get(
        f"/api/v1/custody/objects/{custody_obj2_id}", headers=tecnico_auth
    )
    assert obj2_final.json()["status"] == CustodyObjectStatus.RECUSADO.value
    assert obj2_final.json()["linked_device_sample_id"] is None
