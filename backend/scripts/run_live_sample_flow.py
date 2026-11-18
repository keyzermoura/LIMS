"""Script de Demonstração e Inserção de Amostra de Testes em Tempo Real no LIMS.

Executa o fluxo regulatório de ponta a ponta sobre o banco de desenvolvimento (lims-dev.db):
1. Garante schema e usuários demo (seed).
2. Autentica Fiscal e Técnico com emissão de tokens JWT.
3. Cadastra amostra de alta criticidade (Cateter de Balão PTCA) com assinatura 21 CFR Part 11.
4. Gera sub-alíquota com código de barras/DataMatrix (P4.2).
5. Cadastra insumo analítico padrão (CRM) com lote e validade (P3.1).
6. Planeja ensaio analítico (Pressão Nominal de Ruptura) com assinatura digital.
7. Executa ensaio de bancada com leituras ALCOA+ e consumo obrigatório de reagente rastreado.
8. Submete e homologa parecer colegiado da coordenação (4-Eyes Principle / ISO/IEC 17025).
9. Emite Laudo Pericial Oficial com hash SHA-256 e assinatura eletrônica.
10. Valida a autenticidade do laudo via endpoint público (QR Code).
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

# Garante path do backend
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.database import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import main as seed_main  # noqa: E402


async def run_flow() -> dict:
    print(f"[*] Conectando ao banco de dados: {settings.DATABASE_URL}")
    await init_db()
    
    # Garante usuários de demonstração
    print("[*] Verificando usuários demo...")
    try:
        await seed_main()
    except Exception as e:
        print(f"[*] Seed já aplicado ou ignorado ({e}). Continuando...")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        # 1. Login Fiscal e Técnico
        print("\n[Etapa 1] Autenticação de Usuários...")
        fiscal_login = await client.post(
            "/api/v1/auth/login",
            data={"username": "fiscal", "password": "Fiscal@Lims2026"},
        )
        assert fiscal_login.status_code == 200, fiscal_login.text
        fiscal_token = fiscal_login.json()["access_token"]

        tecnico_login = await client.post(
            "/api/v1/auth/login",
            data={"username": "tecnico", "password": "Tecnico@Lims2026"},
        )
        assert tecnico_login.status_code == 200, tecnico_login.text
        tecnico_token = tecnico_login.json()["access_token"]
        print("  -> Fiscal autenticado (Marina Prado - ANVISA-7781)")
        print("  -> Técnico autenticado (Rafael Nunes - CRF-3391)")

        def f_auth():
            return {"Authorization": f"Bearer {fiscal_token}"}

        def t_auth():
            return {"Authorization": f"Bearer {tecnico_token}"}

        async def sign(token: str, password: str, entity_type: str, entity_id: str, action: str, meaning: str, reason: str):
            res = await client.post(
                "/api/v1/auth/sign",
                headers={"Authorization": f"Bearer {token}"},
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

        # 2. Cadastro de Amostra com Assinatura Digital
        print("\n[Etapa 2] Entrada de Amostra de Dispositivo Médico (21 CFR Part 11)...")
        sample_id = str(uuid4())
        sig_sample = await sign(
            fiscal_token,
            "Fiscal@Lims2026",
            "DeviceSample",
            sample_id,
            "CREATE",
            "AUTORIA",
            "Apreensão fiscal e custódia regulatória de lote de dispositivos médicos.",
        )
        sample_payload = {
            "id": sample_id,
            "serial_number": f"SN-PTCA-{uuid4().hex[:6].upper()}",
            "lot_number": f"LOT-2026-{uuid4().hex[:4].upper()}",
            "manufacturer": "CardioVascular Tech Inc.",
            "commercial_name": "Cateter de Balão para Angioplastia Coronária PTCA",
            "model": "Apex-Glide RX 3.0x15mm",
            "registration_number": "80123450099",
            "description": "Dispositivo estéril para dilatação mecânica em angioplastia transluminal coronária.",
            "storage_location": "Almoxarifado Central - Armário de Quarentena Q-01",
        }
        res_sample = await client.post(
            "/api/v1/samples",
            headers={**f_auth(), "X-Signature-Token": sig_sample},
            json=sample_payload,
        )
        assert res_sample.status_code == 201, res_sample.text
        sample = res_sample.json()["sample"]
        acc_num = sample["accession_number"]
        print(f"  -> Amostra cadastrada: Accession={acc_num} | Serial={sample['serial_number']}")

        # 3. Fracionamento em Sub-Alíquota (P4.2)
        print("\n[Etapa 3] Fracionamento e Etiquetagem de Sub-Alíquota (P4.2)...")
        aliquot_code = f"ALQ-{acc_num}-01"
        res_aliq = await client.post(
            f"/api/v1/samples/{sample_id}/aliquots",
            headers=f_auth(),
            json={
                "aliquot_code": aliquot_code,
                "volume_or_mass": 1.0,
                "unit": "unidade",
                "storage_location": "Bancada Metrológica 02",
                "notes": "Alíquota destinada ao ensaio destrutivo de pressão nominal de ruptura.",
            },
        )
        assert res_aliq.status_code == 201, res_aliq.text
        aliquot = res_aliq.json()
        print(f"  -> Sub-Alíquota criada: {aliquot['aliquot_code']} (ID: {aliquot['id']})")

        # 4. Insumo e Lote de Padrão Analítico (P3.1 / ISO 17025)
        print("\n[Etapa 4] Cadastro de Padrão Primário Certificado (CRM) e Lote (P3.1)...")
        crm_code = f"CRM-SALINA-{uuid4().hex[:4].upper()}"
        res_reagent = await client.post(
            "/api/v1/reagents",
            headers=f_auth(),
            json={
                "code": crm_code,
                "name": "Solução Fisiológica Salina Padrão 0.9%",
                "reagent_type": "PRIMARY_STANDARD_CRM",
                "grade": "PA",
            },
        )
        assert res_reagent.status_code == 201, res_reagent.text
        crm_id = res_reagent.json()["id"]

        res_batch = await client.post(
            f"/api/v1/reagents/{crm_id}/batches",
            headers=f_auth(),
            json={
                "lot_number": f"LOT-CRM-{uuid4().hex[:4].upper()}",
                "manufacturer": "Merck KGaA",
                "initial_quantity": 500.0,
                "unit": "mL",
                "certificate_number": f"CERT-CRM-{uuid4().hex[:6].upper()}",
                "expiration_date": (date.today() + timedelta(days=365)).isoformat(),
            },
        )
        assert res_batch.status_code == 201, res_batch.text
        crm_batch = res_batch.json()
        print(f"  -> Padrão analítico registrado: {crm_code} | Lote={crm_batch['lot_number']} ({crm_batch['current_quantity']} mL disponíveis)")

        # 5. Planejamento do Ensaio
        print("\n[Etapa 5] Planejamento de Ensaio Analítico (LabTest)...")
        test_id = str(uuid4())
        sig_test = await sign(
            fiscal_token,
            "Fiscal@Lims2026",
            "LabTest",
            test_id,
            "CREATE",
            "AUTORIA",
            "Planejamento de ensaio metrológico de pressão de ruptura.",
        )
        test_payload = {
            "id": test_id,
            "device_sample_id": sample_id,
            "name": "Pressão Nominal de Ruptura (Rated Burst Pressure - RBP)",
            "method": "Ensaio Hidrostático Conforme Norma ISO 10555-4",
            "parameters": {"temperatura_banho": "37 °C", "taxa_pressurizacao": "1 atm/s"},
            "unit": "atm",
            "lower_limit": 14.0,
            "upper_limit": 25.0,
            "acceptance_criteria": "O balão deve suportar pressão mínima de 14.0 atm sem ruptura.",
        }
        res_test = await client.post(
            "/api/v1/tests",
            headers={**f_auth(), "X-Signature-Token": sig_test},
            json=test_payload,
        )
        assert res_test.status_code == 201, res_test.text
        test_obj = res_test.json()["test"]
        print(f"  -> Ensaio planejado: {test_obj['name']} (Status: {test_obj['status']})")

        # 6. Execução de Bancada ALCOA+ com Consumo de Reagente (P3.1)
        print("\n[Etapa 6] Execução de Bancada e Consumo de Reagente Rastreável (P3.1)...")
        res_exec = await client.post(
            f"/api/v1/tests/{test_id}/executions",
            headers=t_auth(),
            json={
                "temperature_celsius": 22.8,
                "humidity_percent": 52.0,
                "pressure_hpa": 1013.2,
                "notes": "Início do ensaio hidrostático na bancada metrológica.",
            },
        )
        assert res_exec.status_code == 201, res_exec.text
        execution = res_exec.json()
        exec_id = execution["id"]

        # Consumo do lote de CRM
        res_consume = await client.post(
            f"/api/v1/reagents/executions/{exec_id}/consume",
            headers=t_auth(),
            json={
                "batch_id": crm_batch["id"],
                "quantity_used": 50.0,
                "unit": "mL",
            },
        )
        assert res_consume.status_code == 201, res_consume.text
        print(f"  -> Consumo de reagente registrado com sucesso: 50.0 mL do lote {crm_batch['lot_number']}")

        # Leituras brutas ALCOA+
        await client.post(
            f"/api/v1/executions/{exec_id}/readings",
            headers=t_auth(),
            json={
                "raw_data": {
                    "patamares_atm": [4.0, 8.0, 12.0, 14.0, 16.0, 17.8],
                    "estabilizacao_seg": 30,
                    "ruptura": False,
                },
                "notes": "Pressurização progressiva a 37 °C.",
            },
        )

        # Conclusão da execução
        res_exec_complete = await client.post(
            f"/api/v1/executions/{exec_id}/complete",
            headers=t_auth(),
            json={
                "result_value": 17.8,
                "result_text": "Balão suportou até 17.8 atm sem ruptura ou estufamento.",
                "outcome": "APROVADO",
                "notes": "Critério de aceitação ISO 10555-4 plenamente atendido.",
            },
        )
        assert res_exec_complete.status_code == 200, res_exec_complete.text
        print("  -> Execução de bancada concluída: Resultado = 17.8 atm (APROVADO)")

        # Assinatura técnica do analista
        sig_analyst = await sign(
            tecnico_token,
            "Tecnico@Lims2026",
            "LabTest",
            test_id,
            "UPDATE",
            "RESPONSABILIDADE_TECNICA",
            "Emissão e formalização dos resultados analíticos obtidos em bancada.",
        )
        res_patch_test = await client.patch(
            f"/api/v1/tests/{test_id}/result",
            headers={**t_auth(), "X-Signature-Token": sig_analyst},
            json={
                "result_value": 17.8,
                "result_text": "Pressão máxima suportada de 17.8 atm sem ruptura.",
                "outcome": "APROVADO",
                "notes": "Ensaio analítico concluído com êxito.",
                "version": 1,
            },
        )
        assert res_patch_test.status_code == 200, res_patch_test.text
        print("  -> Laudo analítico assinado eletronicamente pelo Técnico.")

        # 7. Revisão por Pares Colegiada (4-Eyes Principle / ISO 17025)
        print("\n[Etapa 7] Revisão Técnica Colegiada e Aprovação por Pares (4-Eyes Principle)...")
        await client.post(
            f"/api/v1/reviews/tests/{test_id}/submit",
            headers=t_auth(),
            json={"notes": "Submissão para revisão colegiada da coordenação técnica."},
        )
        sig_review = await sign(
            fiscal_token,
            "Fiscal@Lims2026",
            "LabTest",
            test_id,
            "UPDATE",
            "APROVACAO",
            "Homologação colegiada independente dos dados brutos e cálculos metrológicos.",
        )
        res_review = await client.post(
            f"/api/v1/reviews/tests/{test_id}/decide",
            headers={**f_auth(), "X-Signature-Token": sig_review},
            json={
                "status": "APROVADO",
                "notes": "Dados de bancada e rastreabilidade metrológica integralmente verificados e aprovados.",
            },
        )
        assert res_review.status_code == 200, res_review.text
        print("  -> Parecer técnico homologado e aprovado pela Coordenação.")

        # 8. Emissão de Laudo Pericial Oficial (21 CFR Part 11)
        print("\n[Etapa 8] Emissão de Laudo Pericial Oficial Consolidado (21 CFR Part 11)...")
        sig_report = await sign(
            fiscal_token,
            "Fiscal@Lims2026",
            "DeviceSample",
            sample_id,
            "CLOSE",
            "RESPONSABILIDADE_TECNICA",
            "Emissão formal de Laudo Pericial Oficial Conclusivo de Fiscalização Sanitária.",
        )
        report_payload = {
            "device_sample_id": sample_id,
            "test_ids": [test_id],
            "title": "Laudo Pericial Oficial de Conformidade Mecânica e Estanqueidade",
            "conclusion": "APROVADO",
            "summary": "O lote de cateteres de balão atende plenamente aos critérios de pressão nominal de ruptura (RBP >= 14 atm) da norma ISO 10555-4.",
        }
        res_rep = await client.post(
            "/api/v1/reports/official",
            headers={**f_auth(), "X-Signature-Token": sig_report},
            json=report_payload,
        )
        assert res_rep.status_code == 200, res_rep.text
        report = res_rep.json()
        print(f"  -> Laudo Oficial Emitido: {report['report_number']}")
        print(f"  -> Hash SHA-256: {report['sha256_hash']}")
        print(f"  -> Token de Autenticidade (QR Code): {report['auth_token']}")

        # 9. Verificação Pública Anônima
        print("\n[Etapa 9] Consulta Pública de Autenticidade Regulatória (QR Code)...")
        res_verify = await client.get(f"/api/v1/reports/verify/{report['auth_token']}")
        assert res_verify.status_code == 200, res_verify.text
        verify_data = res_verify.json()
        print(f"  -> Autenticidade validada: is_valid = {verify_data['is_valid']}")
        print(f"  -> Dispositivo: {verify_data['sample_commercial_name']} | Número de Registro: {sample['registration_number']}")
        print(f"  -> Conclusão Final: {verify_data['conclusion']}")

        summary = {
            "sample_id": sample_id,
            "accession_number": acc_num,
            "serial_number": sample["serial_number"],
            "lot_number": sample["lot_number"],
            "commercial_name": sample["commercial_name"],
            "aliquot_code": aliquot["aliquot_code"],
            "reagent_batch": crm_batch["lot_number"],
            "test_id": test_id,
            "test_name": test_obj["name"],
            "result_value": 17.8,
            "unit": "atm",
            "outcome": "APROVADO",
            "report_number": report["report_number"],
            "sha256_hash": report["sha256_hash"],
            "auth_token": report["auth_token"],
            "is_valid": verify_data["is_valid"],
            "verification_url": f"http://localhost:8000/api/v1/reports/verify/{report['auth_token']}",
        }
        return summary


if __name__ == "__main__":
    result = asyncio.run(run_flow())
    print("\n" + "=" * 80)
    print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO! RESUMO DO FLUXO:")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
