"""Seed de demonstração.

Cria usuários, amostras, transferências de custódia, ensaios assinados e uma
CAPA automática. A trilha de auditoria gerada é REAL (cadeia de hashes), mas
as assinaturas são "fixtures" já consumidas — o fluxo interativo de
reautenticação é exercitado pela UI.

Uso:
    python -m app.seed
"""

from __future__ import annotations

import asyncio
import secrets
from datetime import timedelta
from decimal import Decimal
from typing import TypedDict
from uuid import UUID, uuid4

from sqlalchemy import func, select

from app.core.context import RequestContext
from app.core.security import hash_password, sha256_hex
from app.core.serialization import canonical_json
from app.db.database import SessionFactory, init_db
from app.models.base import utcnow
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    SignatureAction,
    SignatureMeaning,
    UserRole,
)
from app.models.user import User
from app.schemas.capa import CapaCreate
from app.schemas.sample import CustodyTransferRequest, SampleCreate
from app.schemas.test import LabTestCreate, LabTestResultIn
from app.services import (
    capa_service,
    custody_service,
    sample_service,
    test_service,
)

CONTEXT = RequestContext(
    ip_address="127.0.0.1", user_agent="seed-script/1.0", request_id="seed"
)

class DemoUser(TypedDict):
    username: str
    email: str
    full_name: str
    role: UserRole
    password: str
    registration_number: str | None


DEMO_USERS: list[DemoUser] = [
    {
        "username": "admin",
        "email": "admin@lims.local",
        "full_name": "Ana Administradora",
        "role": UserRole.ADMIN,
        "password": "Admin@Lims2026",
        "registration_number": None,
    },
    {
        "username": "auditor",
        "email": "auditor@lims.local",
        "full_name": "Clara Auditora",
        "role": UserRole.AUDITOR,
        "password": "Auditor@Lims2026",
        "registration_number": "CQA-4412",
    },
    {
        "username": "fiscal",
        "email": "fiscal@lims.local",
        "full_name": "Marina Prado",
        "role": UserRole.FISCAL,
        "password": "Fiscal@Lims2026",
        "registration_number": "ANVISA-7781",
    },
    {
        "username": "tecnico",
        "email": "tecnico@lims.local",
        "full_name": "Rafael Nunes",
        "role": UserRole.TECNICO,
        "password": "Tecnico@Lims2026",
        "registration_number": "CRF-3391",
    },
    {
        "username": "custodiante",
        "email": "custodia@lims.local",
        "full_name": "Helena Castro",
        "role": UserRole.CUSTODIANTE,
        "password": "Custodia@Lims2026",
        "registration_number": None,
    },
]


async def fixture_signature(
    db,
    *,
    user: User,
    entity_type: str,
    entity_id: str,
    action: SignatureAction,
    meaning: SignatureMeaning,
    reason: str,
) -> ElectronicSignature:
    """Assinatura já consumida, para popular dados de demonstração."""
    now = utcnow()
    signature_id = uuid4()
    jti = secrets.token_urlsafe(24)
    manifest = {
        "manifest_version": "1.0",
        "signature_id": str(signature_id),
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "registration_number": user.registration_number,
        },
        "entity": {"type": entity_type, "id": entity_id},
        "action": action.value,
        "meaning": meaning.value,
        "reason": reason,
        "method": "PASSWORD",
        "signed_at": now.isoformat(),
        "ip_address": CONTEXT.ip_address,
        "request_id": CONTEXT.request_id,
        "seed": True,
    }
    record = ElectronicSignature(
        id=signature_id,
        user_id=user.id,
        username_snapshot=user.username,
        full_name_snapshot=user.full_name,
        role_snapshot=user.role.value,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        meaning=meaning,
        reason=reason,
        method="PASSWORD",
        manifest=manifest,
        manifest_hash=sha256_hex(canonical_json(manifest)),
        ip_address=CONTEXT.ip_address,
        user_agent=CONTEXT.user_agent,
        request_id=CONTEXT.request_id,
        token_jti=jti,
        signed_at=now,
        expires_at=now + timedelta(seconds=300),
        consumed_at=now,
        consumed_ip=CONTEXT.ip_address,
        consumed_user_agent=CONTEXT.user_agent,
        consumed_request_id=CONTEXT.request_id,
    )
    db.add(record)
    await db.flush()
    return record


async def create_demo_sample(
    db,
    *,
    fiscal: User,
    tecnico: User,
    custodiante: User,
    data: dict,
    tests: list[dict],
    transfer_reason: str,
) -> UUID:
    sample_id = uuid4()
    signature = await fixture_signature(
        db,
        user=fiscal,
        entity_type="DeviceSample",
        entity_id=str(sample_id),
        action=SignatureAction.CREATE,
        meaning=SignatureMeaning.AUTORIA,
        reason="Registro de entrada de amostra coletada em fiscalização pós-mercado.",
    )
    sample, _ = await sample_service.create_sample(
        db,
        payload=SampleCreate(
            id=sample_id,
            received_at=utcnow() - timedelta(days=2),
            **data,
        ),
        actor=fiscal,
        signature=signature,
        context=CONTEXT,
    )

    transfer_signature = await fixture_signature(
        db,
        user=fiscal,
        entity_type="DeviceSample",
        entity_id=str(sample.id),
        action=SignatureAction.TRANSFER,
        meaning=SignatureMeaning.TRANSFERENCIA_DE_CUSTODIA,
        reason="Transferência da guarda para o laboratório de ensaios.",
    )
    _, sample, _ = await custody_service.transfer(
        db,
        payload=CustodyTransferRequest(
            device_sample_id=sample.id,
            to_custodian_id=custodiante.id,
            reason=transfer_reason,
            storage_location="Prateleira B3 — Sala de amostras",
            seal_number="SELO-2026-0091",
            version=sample.version,
        ),
        actor=fiscal,
        signature=transfer_signature,
        context=CONTEXT,
    )

    # Todos os ensaios são programados antes de qualquer resultado: assim a
    # amostra não é considerada aprovada no meio do processo (o que bloquearia
    # a programação dos ensaios restantes).
    created_tests = []
    for spec in tests:
        test_id = uuid4()
        test_signature = await fixture_signature(
            db,
            user=tecnico,
            entity_type="LabTest",
            entity_id=str(test_id),
            action=SignatureAction.CREATE,
            meaning=SignatureMeaning.AUTORIA,
            reason="Programação de ensaio conforme protocolo de fiscalização.",
        )
        test, _ = await test_service.create_test(
            db,
            payload=LabTestCreate(
                id=test_id,
                device_sample_id=sample.id,
                assigned_to_id=tecnico.id,
                **spec["definition"],
            ),
            actor=tecnico,
            signature=test_signature,
            context=CONTEXT,
        )
        created_tests.append((test, spec))

    for test, spec in created_tests:
        result_signature = await fixture_signature(
            db,
            user=tecnico,
            entity_type="LabTest",
            entity_id=str(test.id),
            action=SignatureAction.UPDATE,
            meaning=SignatureMeaning.RESPONSABILIDADE_TECNICA,
            reason="Assinatura do laudo de ensaio de bancada.",
        )
        await test_service.record_result(
            db,
            test_id=test.id,
            payload=LabTestResultIn(
                result_value=Decimal(spec["result"]),
                notes=spec.get("notes"),
                version=test.version,
            ),
            actor=tecnico,
            signature=result_signature,
            context=CONTEXT,
        )

    return sample.id


async def main() -> None:
    await init_db()

    async with SessionFactory() as db:
        existing = await db.scalar(select(func.count()).select_from(User))
        if existing:
            print("Seed ignorado: já existem usuários cadastrados.")
            return

        users: dict[str, User] = {}
        for spec in DEMO_USERS:
            user = User(
                username=spec["username"],
                email=spec["email"],
                full_name=spec["full_name"],
                role=spec["role"],
                hashed_password=hash_password(spec["password"]),
                registration_number=spec["registration_number"],
                password_changed_at=utcnow(),
            )
            db.add(user)
            users[spec["username"]] = user
        await db.flush()

        # CAPA manual de exemplo
        capa_id = uuid4()
        capa_signature = await fixture_signature(
            db,
            user=users["fiscal"],
            entity_type="CapaAction",
            entity_id=str(capa_id),
            action=SignatureAction.CREATE,
            meaning=SignatureMeaning.RESPONSABILIDADE_TECNICA,
            reason="Abertura de CAPA para investigação de desvio de rotulagem.",
        )

        aprovada = await create_demo_sample(
            db,
            fiscal=users["fiscal"],
            tecnico=users["tecnico"],
            custodiante=users["custodiante"],
            data={
                "serial_number": "SN-8842-A",
                "lot_number": "L2026-041",
                "manufacturer": "MedTech Brasil Indústria Ltda.",
                "commercial_name": "Monitor de Sinais Vitais VitalOne 5",
                "model": "VitalOne 5",
                "registration_number": "80012345678",
                "description": "Coletado em ação de fiscalização em hospital público.",
                "storage_location": "Prateleira B3 — Sala de amostras",
            },
            tests=[
                {
                    "definition": {
                        "name": "Resistência Mecânica",
                        "method": "ABNT NBR IEC 60601-1 — tração axial",
                        "parameters": {"velocidade": "5 mm/min", "corpo_de_prova": "3"},
                        "unit": "N",
                        "lower_limit": Decimal("10"),
                        "upper_limit": Decimal("50"),
                        "acceptance_criteria": "Força de ruptura entre 10 N e 50 N.",
                    },
                    "result": "32.5",
                    "notes": "Corpo de prova íntegro após o ensaio.",
                },
                {
                    "definition": {
                        "name": "Precisão de SpO2",
                        "method": "Simulador de oximetria — 3 repetições",
                        "parameters": {"frequencia_cardiaca": "72 bpm"},
                        "unit": "%",
                        "lower_limit": Decimal("95"),
                        "upper_limit": Decimal("100"),
                        "acceptance_criteria": "Erro máximo de ±2% em relação ao simulador.",
                    },
                    "result": "97.4",
                },
            ],
            transfer_reason="Amostra encaminhada ao laboratório para ensaios de conformidade.",
        )

        reprovada = await create_demo_sample(
            db,
            fiscal=users["fiscal"],
            tecnico=users["tecnico"],
            custodiante=users["custodiante"],
            data={
                "serial_number": "BI-7710-C",
                "lot_number": "L2026-118",
                "manufacturer": "Infusa Medical S.A.",
                "commercial_name": "Bomba de Infusão InfusaFlow 300",
                "model": "InfusaFlow 300",
                "registration_number": "80198765432",
                "description": "Suspeita de vazão acima do especificado relatada por serviço de saúde.",
                "storage_location": "Prateleira B4 — Quarentena",
            },
            tests=[
                {
                    "definition": {
                        "name": "Vazão de Infusão",
                        "method": "Gravimetria — 60 min a 5 ml/h",
                        "parameters": {"temperatura": "23 °C", "umidade": "48 %"},
                        "unit": "ml/h",
                        "lower_limit": Decimal("4.5"),
                        "upper_limit": Decimal("5.5"),
                        "acceptance_criteria": "Vazão média dentro de ±10% do ajuste.",
                    },
                    "result": "6.2",
                    "notes": "Vazão 24% acima do ajustado. Repetição confirmou o desvio.",
                }
            ],
            transfer_reason="Amostra sob suspeita de desvio de desempenho — prioridade alta.",
        )

        await capa_service.create_capa(
            db,
            payload=CapaCreate(
                id=capa_id,
                device_sample_id=aprovada,
                lab_test_id=None,
                title="Revisão do processo de rotulagem de dispositivos classe II",
                root_cause=(
                    "Investigação preliminar aponta ausência de verificação dupla na "
                    "linha de rotulagem."
                ),
                action_plan=(
                    "Implantar checklist de liberação de rótulos e treinar a equipe "
                    "até o fim do trimestre."
                ),
                owner_id=users["fiscal"].id,
                due_date=(utcnow() + timedelta(days=45)).date(),
            ),
            actor=users["fiscal"],
            signature=capa_signature,
            context=CONTEXT,
        )

        print("Seed concluído.")
        print(f"  Amostra aprovada: {aprovada}")
        print(f"  Amostra reprovada (CAPA automática): {reprovada}")
        print("  Usuários de demonstração:")
        for spec in DEMO_USERS:
            print(f"    {spec['username']:12s} / {spec['password']:18s} ({spec['role'].value})")


if __name__ == "__main__":
    asyncio.run(main())
