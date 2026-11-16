"""Suíte de Testes da Fase 4: Ciclo Completo de CAPA, RCA e Eficácia (Sprint 4.3).

Valida:
1. Abertura estruturada de CAPA com análise de causa raiz via 5 Porquês e Ishikawa (6Ms).
2. Gestão do ciclo de vida de itens de ação (Contenção, Corretiva, Preventiva) com prazos e evidências.
3. Avaliação formal de eficácia temporal (ISO/IEC 17025 §8.7.3) assinada digitalmente (21 CFR Part 11).
4. Abertura automática de CAPA derivada quando detectada ineficácia ou reincidência.
5. Disparo automático de CAPA quando orçamento de incerteza metrológica registra não conformidade.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

API = "/api/v1"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def signed(token: str, signature_token: str) -> dict[str, str]:
    return {**auth(token), "X-Signature-Token": signature_token}


async def login(client: AsyncClient, username: str, password: str) -> dict[str, Any]:
    res = await client.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def issue_signature(
    client: AsyncClient,
    access_token: str,
    password: str,
    *,
    entity_type: str,
    entity_id: str,
    action: str = "CREATE",
    meaning: str = "APROVACAO",
    reason: str = "Assinatura de garantia da qualidade Part 11.",
) -> str:
    res = await client.post(
        f"{API}/auth/sign",
        headers=auth(access_token),
        json={
            "password": password,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "meaning": meaning,
            "reason": reason,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["token"]


async def create_sample_and_test(
    client: AsyncClient, token_analista: str, pass_analista: str
) -> tuple[str, str]:
    sample_id = str(uuid4())
    sig_sample = await issue_signature(
        client,
        token_analista,
        pass_analista,
        entity_type="DeviceSample",
        entity_id=sample_id,
        action="CREATE",
        meaning="AUTORIA",
    )
    s_res = await client.post(
        f"{API}/samples",
        headers=signed(token_analista, sig_sample),
        json={
            "id": sample_id,
            "serial_number": f"CAPA-SN-{uuid4().hex[:6].upper()}",
            "lot_number": "CAPA-LOT-01",
            "device_model": "Medidor Metrológico Q3",
            "manufacturer": "TechLab",
            "commercial_name": "Medidor Metrológico Q3",
            "storage_location": "Bancada de Qualidade 03",
        },
    )
    assert s_res.status_code == 201, s_res.text

    test_id = str(uuid4())
    sig_test = await issue_signature(
        client,
        token_analista,
        pass_analista,
        entity_type="LabTest",
        entity_id=test_id,
        action="CREATE",
        meaning="AUTORIA",
    )
    t_res = await client.post(
        f"{API}/tests",
        headers=signed(token_analista, sig_test),
        json={
            "id": test_id,
            "device_sample_id": sample_id,
            "name": "Ensaio de Temperatura e Resistência Térmica",
            "test_type": "QUALIDADE_TERMICA",
            "unit": "°C",
            "lower_limit": 20.0,
            "upper_limit": 25.0,
        },
    )
    assert t_res.status_code == 201, t_res.text
    return sample_id, test_id


@pytest.mark.asyncio
async def test_capa_create_with_ishikawa_and_five_whys(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    admin_pass = users["admin"]["password"]
    tecnico_pass = users["tecnico"]["password"]

    admin_auth = await login(client, "admin", admin_pass)
    analyst_auth = await login(client, "tecnico", tecnico_pass)

    token_admin = admin_auth["access_token"]
    admin_id = admin_auth["user"]["id"]
    token_analista = analyst_auth["access_token"]
    analyst_id = analyst_auth["user"]["id"]

    sample_id, test_id = await create_sample_and_test(client, token_analista, tecnico_pass)

    capa_id = str(uuid4())
    future_due = date.fromordinal(date.today().toordinal() + 20).isoformat()
    future_eff = date.fromordinal(date.today().toordinal() + 50).isoformat()

    sig_token = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="CREATE",
        reason="Abertura formal de CAPA com RCA estruturada ISO 17025 §8.7.",
    )

    create_payload = {
        "id": capa_id,
        "device_sample_id": sample_id,
        "lab_test_id": test_id,
        "source_type": "AUDITORIA_INTERNA",
        "title": "Desvio Crítico na Estabilidade Térmica do Ensaio",
        "containment_action": "Segregação imediata do lote e bloqueio do equipamento térmico.",
        "root_cause": "Falha na vedação térmica da estufa devido ao desgaste do sensor de vedação.",
        "action_plan": "Substituição do anel de vedação, recalibração do sensor e treinamento operacional.",
        "owner_id": admin_id,
        "due_date": future_due,
        "target_effectiveness_date": future_eff,
        "ishikawa_causes": {
            "metodo": ["Procedimento analítico sem checklist de vedação prévia."],
            "maquina": ["Estufa com fadiga na vedação magnética."],
            "material": [],
            "mao_de_obra": ["Operador não executou inspeção tátil."],
            "meio_ambiente": ["Umidade ambiente alta durante o ensaio."],
            "medicao": ["Termopar com histerese."],
        },
        "five_whys": [
            {"why_number": 1, "question": "Por que a temperatura variou?", "answer": "Houve escape de ar quente."},
            {"why_number": 2, "question": "Por que o ar quente escapou?", "answer": "A porta não estava totalmente vedada."},
            {"why_number": 3, "question": "Por que não estava vedada?", "answer": "A borracha de vedação ressecou."},
            {"why_number": 4, "question": "Por que a borracha ressecou?", "answer": "Operou acima de 120°C por mais tempo do que o ciclo padrão."},
            {"why_number": 5, "question": "Por que operou acima da temperatura?", "answer": "Falta de trava de segurança no controle de rampa térmica."},
        ],
        "action_items": [
            {
                "title": "Substituição da borracha de vedação",
                "description": "Instalar kit de reposição original de silicone para alta temperatura.",
                "action_type": "CORRETIVA",
                "assigned_to_id": analyst_id,
                "due_date": future_due,
            }
        ],
    }

    res = await client.post(
        f"{API}/capas",
        headers=signed(token_admin, sig_token),
        json=create_payload,
    )
    assert res.status_code == 201, res.text
    data = res.json()["capa"]

    assert data["id"] == capa_id
    assert data["source_type"] == "AUDITORIA_INTERNA"
    assert data["containment_action"] == create_payload["containment_action"]
    assert len(data["ishikawa_causes"]["metodo"]) == 1
    assert len(data["five_whys"]) == 5
    assert len(data["action_items"]) == 1
    assert data["action_items"][0]["status"] == "PENDENTE"
    assert data["action_items"][0]["assigned_to"]["id"] == analyst_id
    assert data["effectiveness_status"] == "PENDENTE"


@pytest.mark.asyncio
async def test_capa_action_items_lifecycle(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    admin_pass = users["admin"]["password"]
    tecnico_pass = users["tecnico"]["password"]

    admin_auth = await login(client, "admin", admin_pass)
    analyst_auth = await login(client, "tecnico", tecnico_pass)

    token_admin = admin_auth["access_token"]
    admin_id = admin_auth["user"]["id"]
    token_analista = analyst_auth["access_token"]
    analyst_id = analyst_auth["user"]["id"]

    sample_id, test_id = await create_sample_and_test(client, token_analista, tecnico_pass)
    capa_id = str(uuid4())
    future_due = date.fromordinal(date.today().toordinal() + 15).isoformat()

    sig_token = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="CREATE",
    )
    await client.post(
        f"{API}/capas",
        headers=signed(token_admin, sig_token),
        json={
            "id": capa_id,
            "device_sample_id": sample_id,
            "lab_test_id": test_id,
            "source_type": "CONTROLE_QUALIDADE",
            "title": "Ajuste Operacional no Procedimento de Diluição",
            "root_cause": "Erro sistemático de pipetagem por volume inadequado.",
            "action_plan": "Treinamento prático e verificação gravimétrica das micropipetas.",
            "owner_id": admin_id,
            "due_date": future_due,
        },
    )

    # 1. Adicionar item de ação
    item_due = date.fromordinal(date.today().toordinal() + 10).isoformat()
    add_res = await client.post(
        f"{API}/capas/{capa_id}/items",
        headers=auth(token_admin),
        json={
            "title": "Verificação gravimétrica das micropipetas",
            "description": "Realizar 10 repetições de água deionizada em balança analítica calibrada.",
            "action_type": "CORRETIVA",
            "assigned_to_id": analyst_id,
            "due_date": item_due,
        },
    )
    assert add_res.status_code == 201, add_res.text
    item = add_res.json()
    item_id = item["id"]
    assert item["status"] == "PENDENTE"

    # 2. Atualizar para EM_ANDAMENTO
    patch1 = await client.patch(
        f"{API}/capas/{capa_id}/items/{item_id}",
        headers=auth(token_analista),
        json={"status": "EM_ANDAMENTO"},
    )
    assert patch1.status_code == 200, patch1.text
    assert patch1.json()["status"] == "EM_ANDAMENTO"

    # 3. Tentar concluir sem evidência (deve falhar com 400 ou 422)
    patch_fail = await client.patch(
        f"{API}/capas/{capa_id}/items/{item_id}",
        headers=auth(token_analista),
        json={"status": "CONCLUIDA"},
    )
    assert patch_fail.status_code in (400, 422), patch_fail.text

    # 4. Concluir com evidência
    patch_ok = await client.patch(
        f"{API}/capas/{capa_id}/items/{item_id}",
        headers=auth(token_analista),
        json={
            "status": "CONCLUIDA",
            "completion_evidence": "Verificação gravimétrica executada com desvio < 0.2% aprovado em certificado #9981.",
        },
    )
    assert patch_ok.status_code == 200, patch_ok.text
    assert patch_ok.json()["status"] == "CONCLUIDA"
    assert patch_ok.json()["completed_at"] is not None

    # 5. Tentar remover ação concluída (deve falhar)
    del_res = await client.delete(
        f"{API}/capas/{capa_id}/items/{item_id}",
        headers=auth(token_admin),
    )
    assert del_res.status_code in (400, 422), del_res.text


@pytest.mark.asyncio
async def test_capa_effectiveness_evaluation_workflow(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    admin_pass = users["admin"]["password"]
    admin_auth = await login(client, "admin", admin_pass)
    token_admin = admin_auth["access_token"]
    admin_id = admin_auth["user"]["id"]

    sample_id, test_id = await create_sample_and_test(client, token_admin, admin_pass)
    capa_id = str(uuid4())
    future_due = date.fromordinal(date.today().toordinal() + 10).isoformat()

    sig_token = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="CREATE",
    )
    await client.post(
        f"{API}/capas",
        headers=signed(token_admin, sig_token),
        json={
            "id": capa_id,
            "device_sample_id": sample_id,
            "lab_test_id": test_id,
            "source_type": "AUDITORIA_INTERNA",
            "title": "Calibração e Alinhamento Óptico",
            "root_cause": "Lentes com condensação após limpeza incorreta.",
            "action_plan": "Protocolo de limpeza aprovado e troca do agente dessecante.",
            "owner_id": admin_id,
            "due_date": future_due,
        },
    )

    # Adiciona ação
    add_res = await client.post(
        f"{API}/capas/{capa_id}/items",
        headers=auth(token_admin),
        json={
            "title": "Substituição do dessecante",
            "description": "Troca de sílica ativa e checagem de umidade relativa < 40%.",
            "action_type": "CONTENCAO",
            "assigned_to_id": admin_id,
            "due_date": future_due,
        },
    )
    item_id = add_res.json()["id"]

    # Tenta avaliar eficácia com ação pendente (deve ser rejeitado)
    eff_sig1 = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="UPDATE",
        meaning="VERIFICACAO",
    )
    eff_fail = await client.post(
        f"{API}/capas/{capa_id}/effectiveness",
        headers=signed(token_admin, eff_sig1),
        json={
            "effectiveness_status": "EFICAZ",
            "recurrence_detected": False,
            "justification": "Avaliação prévia antes da conclusão das ações.",
        },
    )
    assert eff_fail.status_code in (400, 422)

    # Conclui a ação
    await client.patch(
        f"{API}/capas/{capa_id}/items/{item_id}",
        headers=auth(token_admin),
        json={
            "status": "CONCLUIDA",
            "completion_evidence": "Sílica gel substituída e umidade estabilizada em 32%.",
        },
    )

    # Avalia eficácia com sucesso (EFICAZ)
    eff_sig2 = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="UPDATE",
        meaning="VERIFICACAO",
        reason="Verificação formal de eficácia após 30 dias de operação sem desvios.",
    )
    eff_ok = await client.post(
        f"{API}/capas/{capa_id}/effectiveness",
        headers=signed(token_admin, eff_sig2),
        json={
            "effectiveness_status": "EFICAZ",
            "recurrence_detected": False,
            "justification": "Durante 30 dias de monitoramento contínuo, não foi registrada qualquer condensação.",
        },
    )
    assert eff_ok.status_code == 200, eff_ok.text
    capa_concluida = eff_ok.json()
    assert capa_concluida["status"] == "CONCLUIDA"
    assert capa_concluida["effectiveness_status"] == "EFICAZ"
    assert capa_concluida["closed_at"] is not None


@pytest.mark.asyncio
async def test_capa_effectiveness_ineffective_opens_derived_capa(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    admin_pass = users["admin"]["password"]
    admin_auth = await login(client, "admin", admin_pass)
    token_admin = admin_auth["access_token"]
    admin_id = admin_auth["user"]["id"]

    sample_id, test_id = await create_sample_and_test(client, token_admin, admin_pass)
    capa_id = str(uuid4())
    future_due = date.fromordinal(date.today().toordinal() + 10).isoformat()

    sig_token = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="CREATE",
    )
    await client.post(
        f"{API}/capas",
        headers=signed(token_admin, sig_token),
        json={
            "id": capa_id,
            "device_sample_id": sample_id,
            "lab_test_id": test_id,
            "source_type": "ENSAIO_REPROVADO",
            "title": "Ajuste de Torque em Conector Metrológico",
            "root_cause": "Aperto manual insuficiente.",
            "action_plan": "Adquirir e usar torquímetro estalador regulado.",
            "owner_id": admin_id,
            "due_date": future_due,
        },
    )

    # Avalia eficácia com status INEFICAZ (detectou reincidência)
    eff_sig = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="CapaAction",
        entity_id=capa_id,
        action="UPDATE",
        meaning="VERIFICACAO",
        reason="Avaliação de eficácia revelou reincidência do desvio.",
    )
    eff_res = await client.post(
        f"{API}/capas/{capa_id}/effectiveness",
        headers=signed(token_admin, eff_sig),
        json={
            "effectiveness_status": "INEFICAZ",
            "recurrence_detected": True,
            "justification": "O desvio de aperto voltou a ocorrer no lote seguinte mesmo com uso do torquímetro.",
        },
    )
    assert eff_res.status_code == 200, eff_res.text
    data = eff_res.json()
    assert data["effectiveness_status"] == "INEFICAZ"
    assert data["recurrence_detected"] is True

    # Verifica se foi gerada automaticamente nova CAPA de reincidência
    list_res = await client.get(
        f"{API}/capas?sample_id={sample_id}",
        headers=auth(token_admin),
    )
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) >= 2
    derived = next(c for c in items if "Reincidência" in c["title"])
    assert derived["auto_opened"] is True
    assert derived["source_type"] == "AUDITORIA_INTERNA"


@pytest.mark.asyncio
async def test_uncertainty_non_conformity_auto_triggers_capa(
    client: AsyncClient,
    users: dict[str, dict[str, Any]],
) -> None:
    admin_pass = users["admin"]["password"]
    admin_auth = await login(client, "admin", admin_pass)
    token_admin = admin_auth["access_token"]

    sample_id, test_id = await create_sample_and_test(client, token_admin, admin_pass)

    # Cria orçamento de incerteza metrológica que resulta em NÃO CONFORME
    # Limites do ensaio: [20.0, 25.0]. Valor medido: 26.50 (fora da especificação superior)
    sig_budget = await issue_signature(
        client,
        token_admin,
        admin_pass,
        entity_type="LabTest",
        entity_id=test_id,
        action="UPDATE",
        meaning="RESPONSABILIDADE_TECNICA",
    )

    budget_res = await client.post(
        f"{API}/uncertainty/budgets",
        headers=signed(token_admin, sig_budget),
        json={
            "lab_test_id": test_id,
            "measured_value": 26.50,
            "unit": "°C",
            "repeatability_readings": [26.48, 26.52, 26.50, 26.49, 26.51],
            "decision_rule": "GUARD_BAND_CONSERVATIVE",
            "guard_band_multiplier": 1.0,
            "components": [
                {
                    "name": "Calibração do Termômetro Padrão",
                    "source_type": "TYPE_B",
                    "distribution": "NORMAL",
                    "half_width": 0.15,
                    "degrees_of_freedom": 50,
                }
            ],
            "notes": "Ensaio térmico com superação de tolerância.",
        },
    )
    assert budget_res.status_code == 201, budget_res.text
    budget_data = budget_res.json()
    assert budget_data["conformity_status"] == "NAO_CONFORME"

    # Confere que uma CAPA automática com source_type=INCERTEZA_METROLOGICA foi aberta
    capas_res = await client.get(
        f"{API}/capas?sample_id={sample_id}",
        headers=auth(token_admin),
    )
    assert capas_res.status_code == 200
    capas = capas_res.json()["items"]
    assert any(
        c["source_type"] == "INCERTEZA_METROLOGICA" and "Desvio Metrológico" in c["title"]
        for c in capas
    )
