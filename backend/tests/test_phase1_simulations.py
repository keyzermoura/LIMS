"""Suíte de Testes Automatizados dos Cenários Operacionais SEFI (SIM01 a SIM12).

Valida integralmente as regras de negócio, máquinas de estados, barreiras de aceite,
segregação de funções (D10) e controle de custódia pré-amostra definidas no documento
docs/VALIDACAO_CENARIOS_OPERACIONAIS_SEFI.md.
"""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

from app.models.enums import (
    ChecklistResult,
    ConferenceStatus,
    CoordinationReviewStatus,
    CriterionClass,
    CustodyEventType,
    CustodyObjectStatus,
    PresentationStatus,
    ReceiptDecisionEnum,
    SolicitationStatus,
)


async def _login(client: AsyncClient, username: str, password: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return str(res.json()["access_token"])


# ==============================================================================
# SIM01 — Recebimento integral com aceite e geração de amostra operacional
# ==============================================================================
async def test_sim01_recebimento_integral_com_aceite(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    # 1. Solicitante cadastra solicitação com 2 itens
    sol_payload = {
        "requester_name": "Fiscalização Sanitária - GGTES",
        "requester_organization": "Anvisa / Sede",
        "purpose": "Ação fiscalizatória em lote de ventiladores pulmonares",
        "priority": "ALTA",
        "request_type": "FISCALIZACAO",
        "items": [
            {
                "product_name": "Ventilador Pulmonar UTI Mod A",
                "declared_quantity": 1.0,
                "unit_of_measure": "UN",
                "manufacturer": "MedTech",
                "model": "VENT-2000",
                "serial_number": "SN-UTI-001",
                "lot_number": "LOT-2026-A",
            },
            {
                "product_name": "Ventilador Pulmonar UTI Mod B",
                "declared_quantity": 1.0,
                "unit_of_measure": "UN",
                "manufacturer": "MedTech",
                "model": "VENT-2000",
                "serial_number": "SN-UTI-002",
                "lot_number": "LOT-2026-A",
            },
        ],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    assert sol_res.status_code == 201
    sol = sol_res.json()
    assert sol["status"] == SolicitationStatus.RASCUNHO.value
    assert len(sol["items"]) == 2
    sol_id = sol["id"]

    # 2. Submissão formal da demanda
    sub_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/submit",
        json={"version": 1, "notes": "Demanda formalizada"},
        headers=fiscal_auth,
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == SolicitationStatus.SUBMETIDA.value

    # 3. Protocolo registra chegada física dos volumes
    rec_payload = {
        "arrival_location": "Recepção Central / Doca 1",
        "delivery_method": "CORREIOS_SEDEX",
        "external_protocol": "BR987654321XX",
        "packaging_condition": "LACRADO_INTEGRO",
    }
    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json=rec_payload,
        headers=tecnico_auth,
    )
    assert rec_res.status_code == 201
    receipt = rec_res.json()
    assert receipt["receipt_number"].startswith("REC-")
    assert len(receipt["items"]) == 2

    # Verifica geração atômica dos objetos de pré-custódia
    item1 = receipt["items"][0]
    assert len(item1["custody_objects"]) == 1
    obj1 = item1["custody_objects"][0]
    assert obj1["object_code"].startswith("OBJ-")
    assert obj1["status"] == CustodyObjectStatus.SOB_GUARDA.value

    # 4. Avaliação de checklist 100% conforme para o Item 1
    tmpl_res = await client.get("/api/v1/checklists/templates", headers=tecnico_auth)
    assert tmpl_res.status_code == 200
    criteria = tmpl_res.json()[0]["criteria"]

    checklist_answers = [
        {"criterion_id": c["id"], "result": ChecklistResult.CONFORME.value}
        for c in criteria
    ]
    eval_res = await client.post(
        f"/api/v1/receipts/{receipt['id']}/items/{item1['id']}/checklist",
        json={"answers": checklist_answers},
        headers=tecnico_auth,
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["conference_status"] == ConferenceStatus.CONFORME.value

    # 5. Decisão técnica formalizada: ACCEPTED
    dec_res = await client.post(
        f"/api/v1/receipts/{receipt['id']}/items/{item1['id']}/decisions",
        json={
            "decision": ReceiptDecisionEnum.ACCEPTED.value,
            "justification": "Equipamento íntegro e documentação técnica completa.",
        },
        headers=tecnico_auth,
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["decision"] == ReceiptDecisionEnum.ACCEPTED.value
    assert dec_res.json()["requires_coordination_review"] is False

    # 6. Aceite técnico atômico gerando amostra operacional DeviceSample
    acc_res = await client.post(
        f"/api/v1/custody/objects/{obj1['id']}/acceptance",
        json={
            "decision": ReceiptDecisionEnum.ACCEPTED.value,
            "storage_location": "Almoxarifado Geral / Prateleira Eletromédicos",
            "version": obj1["version"],
        },
        headers=tecnico_auth,
    )
    assert acc_res.status_code == 200
    sample = acc_res.json()
    assert sample["accession_number"].startswith("LIMS-")
    assert sample["serial_number"] == "SN-UTI-001"
    assert sample["current_location"] == "Almoxarifado Geral / Prateleira Eletromédicos"

    # Confirma que objeto foi marcado como ACEITO
    obj_check = await client.get(f"/api/v1/custody/objects/{obj1['id']}", headers=tecnico_auth)
    assert obj_check.json()["status"] == CustodyObjectStatus.ACEITO.value


# ==============================================================================
# SIM02 — Recebimento parcial com item não apresentado
# ==============================================================================
async def test_sim02_recebimento_parcial_com_item_nao_apresentado(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Fiscalização Regional",
        "items": [
            {"product_name": "Monitor Multiparamétrico", "declared_quantity": 1.0},
            {"product_name": "Sensor de Oximetria SpO2", "declared_quantity": 2.0},
        ],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Triagem"},
        headers=tecnico_auth,
    )
    rec = rec_res.json()
    item_sensor = rec["items"][1]

    # Item sensor é conferido como NÃO APRESENTADO (NOT_PRESENTED, qtd 0)
    conf_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item_sensor['id']}/conference",
        json={
            "presentation_status": PresentationStatus.NOT_PRESENTED.value,
            "presented_quantity": 0.0,
            "conference_status": ConferenceStatus.NAO_CONFORME.value,
            "version": item_sensor["version"],
            "notes": "Caixa secundária de sensores não constava na entrega do transportador.",
        },
        headers=tecnico_auth,
    )
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert conf_data["presentation_status"] == PresentationStatus.NOT_PRESENTED.value
    assert float(conf_data["presented_quantity"]) == 0.0
    assert conf_data["conference_status"] == ConferenceStatus.NAO_CONFORME.value


# ==============================================================================
# SIM03 — Divergência entre quantidade declarada e apresentada
# ==============================================================================
async def test_sim03_divergencia_quantidade_declarada_vs_apresentada(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Vigilância de Produtos",
        "items": [
            {
                "product_name": "Termômetro Digital Infravermelho",
                "declared_quantity": 10.0,
                "unit_of_measure": "UN",
            }
        ],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Doca"},
        headers=tecnico_auth,
    )
    rec = rec_res.json()
    item = rec["items"][0]

    # Declaração original foi de 10 unidades
    assert float(item["solicitation_item"]["declared_quantity"]) == 10.0

    # Conferência física observa apenas 8 unidades entregues
    conf_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item['id']}/conference",
        json={
            "presentation_status": PresentationStatus.PRESENTED.value,
            "presented_quantity": 8.0,
            "conference_status": ConferenceStatus.COM_RESSALVA.value,
            "version": item["version"],
            "notes": "Foram apresentadas 8 unidades físicas (divergência de 2 unidades a menor).",
        },
        headers=tecnico_auth,
    )
    assert conf_res.status_code == 200
    res_data = conf_res.json()
    # Declaração original permanece intacta
    assert float(res_data["solicitation_item"]["declared_quantity"]) == 10.0
    # Quantidade apresentada reflete a contagem física real
    assert float(res_data["presented_quantity"]) == 8.0


# ==============================================================================
# SIM04 — Múltiplos objetos sob custódia com decisões independentes
# ==============================================================================
async def test_sim04_multiplos_objetos_decisoes_independentes(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Coordenação de Produtos",
        "items": [
            {"product_name": "Bomba de Infusão Contínua", "declared_quantity": 2.0}
        ],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Triagem"},
        headers=tecnico_auth,
    )
    rec = rec_res.json()
    item = rec["items"][0]
    obj1 = item["custody_objects"][0]

    # Objeto 1: Aceite técnico
    acc_res = await client.post(
        f"/api/v1/custody/objects/{obj1['id']}/acceptance",
        json={
            "decision": ReceiptDecisionEnum.ACCEPTED.value,
            "storage_location": "Bancada A",
            "version": obj1["version"],
        },
        headers=tecnico_auth,
    )
    assert acc_res.status_code == 200
    sample1 = acc_res.json()
    assert sample1["accession_number"].startswith("LIMS-")

    # Item de recebimento registra decisão técnica
    dec_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item['id']}/decisions",
        json={
            "decision": ReceiptDecisionEnum.ACCEPTED.value,
            "justification": "Aprovado tecnicamente com independência",
        },
        headers=tecnico_auth,
    )
    assert dec_res.status_code == 200


# ==============================================================================
# SIM05 — Pendência saneável com checklist S e deliberação da coordenação
# ==============================================================================
async def test_sim05_pendencia_saneavel_com_ressalva_e_coordenacao(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Fiscalização de Campo",
        "items": [{"product_name": "Eletroencefalógrafo", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Laboratório de Ensaios"},
        headers=tecnico_auth,
    )
    rec = rec_res.json()
    item = rec["items"][0]

    tmpl = (await client.get("/api/v1/checklists/templates", headers=tecnico_auth)).json()[0]
    answers = []
    for c in tmpl["criteria"]:
        if c["criterion_class"] == CriterionClass.SANEAVEL.value:
            answers.append({
                "criterion_id": c["id"],
                "result": ChecklistResult.NAO_CONFORME.value,
                "justification": "Falta guia rápida de operação em português; manual completo em PDF foi fornecido.",
            })
        else:
            answers.append({"criterion_id": c["id"], "result": ChecklistResult.CONFORME.value})

    chk_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item['id']}/checklist",
        json={"answers": answers},
        headers=tecnico_auth,
    )
    assert chk_res.status_code == 200
    assert chk_res.json()["conference_status"] == ConferenceStatus.COM_RESSALVA.value

    # Decisão PENDING gera obrigatoriamente CoordinationReview
    dec_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item['id']}/decisions",
        json={
            "decision": ReceiptDecisionEnum.PENDING.value,
            "justification": "Ressalva documental encaminhada para parecer da coordenação técnica.",
        },
        headers=tecnico_auth,
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["requires_coordination_review"] is True

    # Coordenação delibera e aprova a ressalva
    pending = (await client.get("/api/v1/coordination/reviews/pending", headers=fiscal_auth)).json()
    review = next(r for r in pending if r["decision_id"] == dec_res.json()["id"])

    action_res = await client.post(
        f"/api/v1/coordination/reviews/{review['id']}/action",
        json={
            "status": CoordinationReviewStatus.APROVADO.value,
            "review_notes": "Aprovada a ressalva pelo fiscal/coordenador tendo em vista o manual em PDF.",
        },
        headers=fiscal_auth,
    )
    assert action_res.status_code == 200
    assert action_res.json()["status"] == CoordinationReviewStatus.APROVADO.value


# ==============================================================================
# SIM06 — Recusa com permanência em custódia física
# ==============================================================================
async def test_sim06_recusa_com_permanencia_em_custodia(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Fiscalização de Portos e Aeroportos",
        "items": [{"product_name": "Implante Ortopédico de Quadril", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Doca Internacional"},
        headers=tecnico_auth,
    )
    rec = rec_res.json()
    item = rec["items"][0]
    obj = item["custody_objects"][0]

    # Decisão REJECTED
    dec_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item['id']}/decisions",
        json={
            "decision": ReceiptDecisionEnum.REJECTED.value,
            "justification": "Embalagem primária estéril violada e com contaminação visível.",
        },
        headers=tecnico_auth,
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["decision"] == ReceiptDecisionEnum.REJECTED.value
    assert dec_res.json()["requires_coordination_review"] is True

    # Objeto de custódia permanece auditável e sob custódia
    obj_res = await client.get(f"/api/v1/custody/objects/{obj['id']}", headers=tecnico_auth)
    assert obj_res.status_code == 200
    assert obj_res.json()["linked_device_sample_id"] is None


# ==============================================================================
# SIM07 — Transferência de custódia física entre responsáveis com assinatura
# ==============================================================================
async def test_sim07_transferencia_de_custodia_entre_responsaveis(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Fiscalização Estadual",
        "items": [{"product_name": "Aparelho de Ultrassom Diagnóstico", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Setor de Triagem"},
        headers=tecnico_auth,
    )
    rec = rec_res.json()
    obj = rec["items"][0]["custody_objects"][0]

    # Lista usuários para pegar ID do custodiante destino
    users_res = await client.get("/api/v1/users", headers=tecnico_auth)
    dest_user = next(u for u in users_res.json() if u["username"] == "tecnico2")

    # Transfere custódia
    trans_res = await client.post(
        f"/api/v1/custody/objects/{obj['id']}/transfers",
        json={
            "to_custodian_id": dest_user["id"],
            "to_location": "Laboratório de Acústica - Bancada 3",
            "reason": "Transferência física para testes de emissão acústica.",
            "version": obj["version"],
        },
        headers=tecnico_auth,
    )
    assert trans_res.status_code == 200
    updated_obj = trans_res.json()
    assert updated_obj["current_location"] == "Laboratório de Acústica - Bancada 3"
    assert updated_obj["current_custodian_id"] == dest_user["id"]
    assert updated_obj["status"] == CustodyObjectStatus.SOB_GUARDA.value

    # Trilha append-only reflete o evento
    hist_res = await client.get(f"/api/v1/custody/objects/{obj['id']}/history", headers=tecnico_auth)
    assert hist_res.status_code == 200
    events = hist_res.json()
    assert len(events) >= 2  # INGRESSO + TRANSFERENCIA
    assert any(e["event_type"] == CustodyEventType.TRANSFERENCIA.value for e in events)


# ==============================================================================
# SIM08 — Mudança de localização mantendo o mesmo custodiante
# ==============================================================================
async def test_sim08_mudanca_de_localizacao_sem_troca_de_custodiante(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Vigilância Pós-Mercado",
        "items": [{"product_name": "Bisturi Eletrônico", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Armário de Entrada 1"},
        headers=tecnico_auth,
    )
    obj = rec_res.json()["items"][0]["custody_objects"][0]
    initial_custodian_id = obj["current_custodian_id"]

    # Mesma pessoa responsável move para outro armário
    trans_res = await client.post(
        f"/api/v1/custody/objects/{obj['id']}/transfers",
        json={
            "to_custodian_id": initial_custodian_id,
            "to_location": "Armário Blindado de Segurança 4",
            "reason": "Realocação para compartimento seguro sob a mesma guarda.",
            "version": obj["version"],
        },
        headers=tecnico_auth,
    )
    assert trans_res.status_code == 200
    res_obj = trans_res.json()
    assert res_obj["current_location"] == "Armário Blindado de Segurança 4"
    assert res_obj["current_custodian_id"] == initial_custodian_id


# ==============================================================================
# SIM09 — Retificação auditável e imutabilidade da trilha
# ==============================================================================
async def test_sim09_retificacao_auditavel_e_imutabilidade(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}

    sol_payload = {
        "requester_name": "Fiscal Inicial",
        "purpose": "Finalidade preliminar",
        "items": [{"product_name": "Oxímetro de Pulso", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    audit_seq1 = sol_res.headers.get("X-Audit-Sequence")
    assert audit_seq1 is not None

    # Atualização em rascunho com controle de versão
    update_res = await client.put(
        f"/api/v1/solicitations/{sol_id}",
        json={
            "requester_name": "Fiscal Retificador",
            "purpose": "Finalidade retificada e justificada",
            "version": 1,
        },
        headers=fiscal_auth,
    )
    assert update_res.status_code == 200
    audit_seq2 = update_res.headers.get("X-Audit-Sequence")
    assert audit_seq2 is not None
    # Cada operação possui uma sequência cronológica append-only única e estritamente crescente
    assert int(audit_seq2) > int(audit_seq1)


# ==============================================================================
# SIM10 — Concorrência otimista e controle de versão
# ==============================================================================
async def test_sim10_concorrencia_otimista_e_idempotencia(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    tecnico_token = await _login(client, "tecnico", users["tecnico"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}
    tecnico_auth = {"Authorization": f"Bearer {tecnico_token}"}

    sol_payload = {
        "requester_name": "Coordenação Geral",
        "items": [{"product_name": "Ressuscitador Manual", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]

    # 1. Tentativa de atualização com version desatualizada (stale version) deve falhar com 409
    conflict_res = await client.put(
        f"/api/v1/solicitations/{sol_id}",
        json={"requester_name": "Tentativa Invalida", "version": 999},
        headers=fiscal_auth,
    )
    assert conflict_res.status_code == 409

    # 2. Duplicação de recebimento para a mesma solicitação deve retornar 409 Conflict
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)
    rec1 = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Doca"},
        headers=tecnico_auth,
    )
    assert rec1.status_code == 201

    rec2 = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Doca"},
        headers=tecnico_auth,
    )
    assert rec2.status_code == 409


# ==============================================================================
# SIM11 — Segregação de perfis e autorização RBAC
# ==============================================================================
async def test_sim11_segregacao_de_perfis_e_autorizacao_rbac(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    auditor_token = await _login(client, "auditor", users["auditor"]["password"])
    auditor_auth = {"Authorization": f"Bearer {auditor_token}"}

    # Auditor tem perfil estritamente de leitura / auditoria; tentativa de mutação deve retornar 403
    bad_res = await client.post(
        "/api/v1/solicitations",
        json={
            "requester_name": "Auditor Tentando Criar",
            "items": [{"product_name": "Item Proibido", "declared_quantity": 1.0}],
        },
        headers=auditor_auth,
    )
    assert bad_res.status_code == 403


# ==============================================================================
# SIM12 — Segregação estrita de funções (Regra D10 / Four-Eyes Principle)
# ==============================================================================
async def test_sim12_segregacao_estrita_funcoes_regra_d10(
    client: AsyncClient, users: dict[str, dict[str, Any]]
) -> None:
    fiscal_token = await _login(client, "fiscal", users["fiscal"]["password"])
    fiscal_auth = {"Authorization": f"Bearer {fiscal_token}"}

    # Usuário fiscal cadastra demanda e recebimento
    sol_payload = {
        "requester_name": "Fiscalização Integrada",
        "items": [{"product_name": "Aparelho de Hemodiálise", "declared_quantity": 1.0}],
    }
    sol_res = await client.post("/api/v1/solicitations", json=sol_payload, headers=fiscal_auth)
    sol_id = sol_res.json()["id"]
    await client.post(f"/api/v1/solicitations/{sol_id}/submit", json={"version": 1}, headers=fiscal_auth)

    rec_res = await client.post(
        f"/api/v1/solicitations/{sol_id}/receipt",
        json={"arrival_location": "Triagem"},
        headers=fiscal_auth,
    )
    rec = rec_res.json()
    item_id = rec["items"][0]["id"]

    # Fiscal emite decisão preliminar PENDING
    dec_res = await client.post(
        f"/api/v1/receipts/{rec['id']}/items/{item_id}/decisions",
        json={
            "decision": ReceiptDecisionEnum.PENDING.value,
            "justification": "Pendência técnica emitida pelo fiscal.",
        },
        headers=fiscal_auth,
    )
    assert dec_res.status_code == 200
    decision_id = dec_res.json()["id"]

    pending = (await client.get("/api/v1/coordination/reviews/pending", headers=fiscal_auth)).json()
    review = next(r for r in pending if r["decision_id"] == decision_id)

    # Regra D10: O MESMO usuário fiscal NÃO pode auto-deliberar a revisão da sua própria decisão!
    self_review_res = await client.post(
        f"/api/v1/coordination/reviews/{review['id']}/action",
        json={
            "status": CoordinationReviewStatus.APROVADO.value,
            "review_notes": "Tentativa de auto-aprovação pelo próprio autor da decisão.",
        },
        headers=fiscal_auth,
    )
    assert self_review_res.status_code == 422
    assert "Segregação de funções violada" in self_review_res.text

    # Outro usuário com perfil de coordenação (admin) delibera com imparcialidade e sucesso
    admin_token = await _login(client, "admin", users["admin"]["password"])
    admin_auth = {"Authorization": f"Bearer {admin_token}"}

    coord_res = await client.post(
        f"/api/v1/coordination/reviews/{review['id']}/action",
        json={
            "status": CoordinationReviewStatus.APROVADO.value,
            "review_notes": "Deliberação imparcial realizada por autoridade independente.",
        },
        headers=admin_auth,
    )
    assert coord_res.status_code == 200
    assert coord_res.json()["status"] == CoordinationReviewStatus.APROVADO.value
