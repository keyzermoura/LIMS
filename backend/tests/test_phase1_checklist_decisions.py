"""Testes de integração para Checklist, Critérios e Revisão da Coordenação (M1.2 / D06, D10, D11-D12)."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

from app.models.enums import (
    ChecklistResult,
    ConferenceStatus,
    CoordinationReviewStatus,
    CriterionClass,
    ReceiptDecisionEnum,
)


async def _login(client: AsyncClient, username: str, password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return str(res.json()["access_token"])


async def _create_test_receipt(
    client: AsyncClient,
    fiscal_auth: dict[str, str],
    tecnico_auth: dict[str, str],
) -> dict[str, Any]:
    sol_payload = {
        "requester_name": "Fiscalização Hospitalar",
        "purpose": "Ação de conformidade em desfibriladores",
        "items": [
            {
                "product_name": "Desfibrilador Externo Automático",
                "declared_quantity": 1.0,
                "unit_of_measure": "UN",
                "manufacturer": "BioLife Tech",
                "serial_number": "DEA-9988",
                "lot_number": "LOT-2026-X",
            }
        ],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    assert sol_res.status_code == 201
    sol_id = sol_res.json()["id"]

    submit_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/submit",
        json={"version": 1, "notes": "Pronto para recebimento"},
        headers=fiscal_auth,
    )
    assert submit_res.status_code == 200

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Doca Principal", "packaging_condition": "Íntegro"},
        headers=tecnico_auth,
    )
    assert rec_res.status_code == 201
    return rec_res.json()


async def test_checklist_criteria_and_evaluation(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    # 1. Consulta templates de checklist disponíveis
    templates_res = await client.get("/api/v1/checklists/templates", headers=tecnico_auth)
    assert templates_res.status_code == 200
    templates = templates_res.json()
    assert len(templates) >= 1
    default_template = templates[0]
    assert default_template["code"] == "CKL-DISP-GERAL"
    assert len(default_template["criteria"]) >= 5

    crit_e01 = next(c for c in default_template["criteria"] if c["code"] == "E01")
    crit_s01 = next(c for c in default_template["criteria"] if c["code"] == "S01")
    crit_i01 = next(c for c in default_template["criteria"] if c["code"] == "I01")

    assert crit_e01["criterion_class"] == CriterionClass.ELIMINATORIO.value
    assert crit_s01["criterion_class"] == CriterionClass.SANEAVEL.value

    # 2. Cria recebimento para testar conferência
    rec = await _create_test_receipt(client, fiscal_auth, tecnico_auth)
    receipt_id = rec["id"]
    item_id = rec["items"][0]["id"]

    # 3. Validação: critério eliminatório não conforme sem justificativa é rejeitado
    bad_eval = await client.post(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/checklist",
        json={
            "answers": [
                {
                    "criterion_id": crit_e01["id"],
                    "result": ChecklistResult.NAO_CONFORME.value,
                    "justification": "",  # Vazia
                }
            ]
        },
        headers=tecnico_auth,
    )
    assert bad_eval.status_code in {400, 422}

    # 4. Avaliação com falha eliminatória gera status NAO_CONFORME
    eval_eliminatory = await client.post(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/checklist",
        json={
            "answers": [
                {
                    "criterion_id": crit_e01["id"],
                    "result": ChecklistResult.NAO_CONFORME.value,
                    "justification": "Lacre oficial violado na transportadora",
                },
                {
                    "criterion_id": crit_s01["id"],
                    "result": ChecklistResult.CONFORME.value,
                },
            ]
        },
        headers=tecnico_auth,
    )
    assert eval_eliminatory.status_code == 200
    assert eval_eliminatory.json()["conference_status"] == ConferenceStatus.NAO_CONFORME.value

    # 5. Avaliação com falha apenas saneável gera status COM_RESSALVA
    eval_remediable = await client.post(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/checklist",
        json={
            "answers": [
                {
                    "criterion_id": crit_e01["id"],
                    "result": ChecklistResult.CONFORME.value,
                },
                {
                    "criterion_id": crit_s01["id"],
                    "result": ChecklistResult.NAO_CONFORME.value,
                    "justification": "Divergência menor na contagem da embalagem secundária",
                },
                {
                    "criterion_id": crit_i01["id"],
                    "result": ChecklistResult.CONFORME.value,
                },
            ]
        },
        headers=tecnico_auth,
    )
    assert eval_remediable.status_code == 200
    assert eval_remediable.json()["conference_status"] == ConferenceStatus.COM_RESSALVA.value

    # 6. Avaliação 100% conforme gera status CONFORME
    eval_conforme = await client.post(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/checklist",
        json={
            "answers": [
                {
                    "criterion_id": crit_e01["id"],
                    "result": ChecklistResult.CONFORME.value,
                },
                {
                    "criterion_id": crit_s01["id"],
                    "result": ChecklistResult.CONFORME.value,
                },
                {
                    "criterion_id": crit_i01["id"],
                    "result": ChecklistResult.CONFORME.value,
                },
            ]
        },
        headers=tecnico_auth,
    )
    assert eval_conforme.status_code == 200
    assert eval_conforme.json()["conference_status"] == ConferenceStatus.CONFORME.value

    # 7. Consulta respostas gravadas
    answers_res = await client.get(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/checklist",
        headers=tecnico_auth,
    )
    assert answers_res.status_code == 200
    answers = answers_res.json()
    assert len(answers) == 3


async def test_decision_and_coordination_four_eyes(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    rec = await _create_test_receipt(client, fiscal_auth, tecnico_auth)
    receipt_id = rec["id"]
    item_id = rec["items"][0]["id"]

    # 1. Técnico registra decisão com PENDING (ressalva técnica)
    decision_res = await client.post(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/decisions",
        json={
            "decision": ReceiptDecisionEnum.PENDING.value,
            "justification": "Falta de manual em português; aguardando posicionamento da coordenação.",
        },
        headers=tecnico_auth,
    )
    assert decision_res.status_code == 200, decision_res.text
    decision_data = decision_res.json()
    assert decision_data["decision"] == ReceiptDecisionEnum.PENDING.value
    assert decision_data["requires_coordination_review"] is True
    assert decision_data["coordination_review"] is not None
    review_id = decision_data["coordination_review"]["id"]

    # 2. Lista revisões pendentes da coordenação
    pending_res = await client.get("/api/v1/coordination/reviews/pending", headers=fiscal_auth)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert any(r["id"] == review_id for r in pending_list)

    # 3. Segregação de funções (D10 / Four-Eyes Principle):
    # O técnico que decidiu NÃO pode deliberar a revisão da coordenação
    self_review = await client.post(
        f"/api/v1/coordination/reviews/{review_id}/action",
        json={
            "status": CoordinationReviewStatus.APROVADO.value,
            "review_notes": "Tentativa de auto-aprovação pelo próprio técnico",
        },
        headers=tecnico_auth,
    )
    assert self_review.status_code in {400, 403, 422}

    # 4. Outro usuário com perfil de coordenação (Fiscal) delibera e aprova
    fiscal_review = await client.post(
        f"/api/v1/coordination/reviews/{review_id}/action",
        json={
            "status": CoordinationReviewStatus.APROVADO.value,
            "review_notes": "Ressalva superada mediante apresentação de documentação complementar pelo fabricante.",
        },
        headers=fiscal_auth,
    )
    assert fiscal_review.status_code == 200, fiscal_review.text
    review_data = fiscal_review.json()
    assert review_data["status"] == CoordinationReviewStatus.APROVADO.value
    assert review_data["reviewed_by"] is not None
    assert review_data["reviewed_by"]["username"] == "fiscal"

    # 5. Consulta histórico de decisões do item
    decisions_list = await client.get(
        f"/api/v1/receipts/{receipt_id}/items/{item_id}/decisions",
        headers=tecnico_auth,
    )
    assert decisions_list.status_code == 200
    assert len(decisions_list.json()) >= 1
    assert decisions_list.json()[0]["coordination_review"]["status"] == CoordinationReviewStatus.APROVADO.value
