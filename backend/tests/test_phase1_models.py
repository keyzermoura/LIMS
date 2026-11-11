"""Testes unitários e de integridade dos modelos da Fase 1 (M0.3).

Valida a persistência e relacionamentos de Solicitation, Receipt, CustodyObject,
ChecklistTemplate e ReceiptDecision no banco de dados.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from app.models.checklist import ChecklistAnswer, ChecklistCriterion, ChecklistTemplate
from app.models.decision import CoordinationReview, ReceiptDecision
from app.models.enums import (
    ChecklistResult,
    ConferenceStatus,
    CoordinationReviewStatus,
    CriterionClass,
    CustodyEventType,
    CustodyObjectStatus,
    PresentationStatus,
    ReceiptDecisionEnum,
    ReceiptStatus,
    SolicitationStatus,
    UserRole,
)
from app.models.receipt import CustodyEvent, CustodyObject, Receipt, ReceiptItem
from app.models.solicitation import Solicitation, SolicitationItem
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_solicitation_creation_and_items(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida cadastro de solicitação com itens declarados (M0.3)."""
    async with db_factory() as db_session:
        user = User(
            username=f"operador_{uuid4().hex[:6]}",
            email=f"operador_{uuid4().hex[:6]}@sefi.funed.mg.gov.br",
            full_name="Operador de Cadastro",
            role=UserRole.TECNICO,
            hashed_password="hash",
        )
        db_session.add(user)
        await db_session.flush()

        solicitation = Solicitation(
            solicitation_number="SOL-2026-TEST-001",
            requester_name="Vigilância Sanitária Estadual",
            requester_email="visa@saude.mg.gov.br",
            requester_organization="VISA Estadual",
            created_by_id=user.id,
            purpose="Fiscalização orientada de lote suspeito",
            status=SolicitationStatus.SUBMETIDA,
        )
        db_session.add(solicitation)
        await db_session.flush()

        item1 = SolicitationItem(
            solicitation_id=solicitation.id,
            item_number=1,
            product_name="Equipo Macrogotas com Filtro",
            manufacturer="Fabricante Alfa",
            lot_number="LOTE-2026-A",
            declared_quantity=Decimal("50.0000"),
            unit_of_measure="UN",
        )
        item2 = SolicitationItem(
            solicitation_id=solicitation.id,
            item_number=2,
            product_name="Agulha Hipodérmica 25x7",
            manufacturer="Fabricante Beta",
            lot_number="LOTE-2026-B",
            declared_quantity=Decimal("100.0000"),
            unit_of_measure="UN",
        )
        db_session.add_all([item1, item2])
        await db_session.flush()

        # Consulta com relacionamento
        stmt = select(Solicitation).where(Solicitation.id == solicitation.id)
        res = await db_session.execute(stmt)
        loaded = res.scalar_one()

        assert loaded.solicitation_number == "SOL-2026-TEST-001"
        assert len(loaded.items) == 2
        assert loaded.items[0].declared_quantity == Decimal("50.0000")
        assert loaded.items[1].product_name == "Agulha Hipodérmica 25x7"


@pytest.mark.asyncio
async def test_receipt_and_custody_object_chain(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida chegada física com itens apresentados, custódia pré-amostra e conferência."""
    async with db_factory() as db_session:
        user = User(
            username=f"recebedor_{uuid4().hex[:6]}",
            email=f"recebedor_{uuid4().hex[:6]}@sefi.funed.mg.gov.br",
            full_name="Servidor da Recepção",
            role=UserRole.CUSTODIANTE,
            hashed_password="hash",
        )
        db_session.add(user)
        await db_session.flush()

        solicitation = Solicitation(
            solicitation_number=f"SOL-{uuid4().hex[:8].upper()}",
            requester_name="Fiscalização Anvisa",
            created_by_id=user.id,
            status=SolicitationStatus.SUBMETIDA,
        )
        db_session.add(solicitation)
        await db_session.flush()

        solicitation_item = SolicitationItem(
            solicitation_id=solicitation.id,
            item_number=1,
            product_name="Seringa Descartável 10ml",
            declared_quantity=Decimal("20.0000"),
            unit_of_measure="UN",
        )
        db_session.add(solicitation_item)
        await db_session.flush()

        # 1. Registrar chegada física (Receipt)
        receipt = Receipt(
            solicitation_id=solicitation.id,
            receipt_number=f"REC-{uuid4().hex[:8].upper()}",
            arrived_at=solicitation.created_at,
            received_by_id=user.id,
            arrival_location="Doca de Entrada SEFI",
            external_protocol="HARPYA-998877",
            status=ReceiptStatus.REGISTRADO,
        )
        db_session.add(receipt)
        await db_session.flush()

        # 2. Registrar Item do Recebimento (apresentação parcial: 20 declaradas, 10 entregues)
        receipt_item = ReceiptItem(
            receipt_id=receipt.id,
            solicitation_item_id=solicitation_item.id,
            presentation_status=PresentationStatus.PRESENTED,
            presented_quantity=Decimal("10.0000"),
            conference_status=ConferenceStatus.PENDENTE,
        )
        db_session.add(receipt_item)
        await db_session.flush()

        # 3. Gerar Objeto de Custódia para o material sob guarda
        custody_obj = CustodyObject(
            receipt_item_id=receipt_item.id,
            object_code=f"OBJ-{uuid4().hex[:8].upper()}",
            grouping_description="10 seringas intactas lacradas",
            represented_quantity=Decimal("10.0000"),
            current_location="Armário A1 - Doca",
            seal_number="LACRE-12345",
            status=CustodyObjectStatus.SOB_GUARDA,
            current_custodian_id=user.id,
        )
        db_session.add(custody_obj)
        await db_session.flush()

        # 4. Registrar evento de ingresso na custódia
        custody_event = CustodyEvent(
            custody_object_id=custody_obj.id,
            event_type=CustodyEventType.INGRESSO,
            reason="Entrada física na recepção do SEFI",
            to_custodian_id=user.id,
            to_location="Armário A1 - Doca",
            registered_by_id=user.id,
        )
        db_session.add(custody_event)
        await db_session.flush()

        # Asserções
        stmt = select(Receipt).where(Receipt.id == receipt.id)
        loaded_receipt = (await db_session.execute(stmt)).scalar_one()

        assert loaded_receipt.receipt_number.startswith("REC-")
        assert len(loaded_receipt.items) == 1
        assert loaded_receipt.items[0].presented_quantity == Decimal("10.0000")
        assert len(loaded_receipt.items[0].custody_objects) == 1
        assert loaded_receipt.items[0].custody_objects[0].status == CustodyObjectStatus.SOB_GUARDA
        assert len(loaded_receipt.items[0].custody_objects[0].custody_events) == 1


@pytest.mark.asyncio
async def test_checklist_and_decision_with_coordination(
    db_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Valida preenchimento de checklist C01-C03, decisão com ressalva e revisão da coordenação."""
    async with db_factory() as db_session:
        conferente = User(
            username=f"conferente_{uuid4().hex[:6]}",
            email=f"conferente_{uuid4().hex[:6]}@sefi.funed.mg.gov.br",
            full_name="Conferente Técnico",
            role=UserRole.TECNICO,
            hashed_password="hash",
        )
        coordenador = User(
            username=f"coord_{uuid4().hex[:6]}",
            email=f"coord_{uuid4().hex[:6]}@sefi.funed.mg.gov.br",
            full_name="Coordenador do SEFI",
            role=UserRole.FISCAL,
            hashed_password="hash",
        )
        db_session.add_all([conferente, coordenador])
        await db_session.flush()

        # Template e Critérios E/S/I
        template = ChecklistTemplate(
            code="CHK-DISPOSITIVOS-V1",
            name="Checklist Padrão de Dispositivos Médicos",
            category="DISPOSITIVOS",
            version=1,
        )
        db_session.add(template)
        await db_session.flush()

        c1 = ChecklistCriterion(
            template_id=template.id,
            code="C01",
            description="Embalagem íntegra e sem violação de lacre",
            criterion_class=CriterionClass.ELIMINATORIO,
            order=1,
        )
        c2 = ChecklistCriterion(
            template_id=template.id,
            code="C09",
            description="Divergência menor em rotulagem passível de saneamento",
            criterion_class=CriterionClass.SANEAVEL,
            order=2,
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        # Solicitação e Recebimento
        sol = Solicitation(
            solicitation_number=f"SOL-{uuid4().hex[:8].upper()}",
            requester_name="Anvisa GGMED",
            created_by_id=conferente.id,
        )
        db_session.add(sol)
        await db_session.flush()

        sol_item = SolicitationItem(
            solicitation_id=sol.id,
            product_name="Máscara Cirúrgica",
            declared_quantity=Decimal("500"),
        )
        db_session.add(sol_item)
        await db_session.flush()

        rec = Receipt(
            solicitation_id=sol.id,
            receipt_number=f"REC-{uuid4().hex[:8].upper()}",
            arrived_at=sol.created_at,
            received_by_id=conferente.id,
        )
        db_session.add(rec)
        await db_session.flush()

        rec_item = ReceiptItem(
            receipt_id=rec.id,
            solicitation_item_id=sol_item.id,
            presented_quantity=Decimal("500"),
        )
        db_session.add(rec_item)
        await db_session.flush()

        # Respostas do Checklist: C01 Conforme, C09 Não Conforme (Saneável)
        ans1 = ChecklistAnswer(
            receipt_item_id=rec_item.id,
            criterion_id=c1.id,
            result=ChecklistResult.CONFORME,
            evaluated_by_id=conferente.id,
        )
        ans2 = ChecklistAnswer(
            receipt_item_id=rec_item.id,
            criterion_id=c2.id,
            result=ChecklistResult.NAO_CONFORME,
            justification="Rotulagem apresenta rasura leve no lote, mas legível no código de barras",
            evaluated_by_id=conferente.id,
        )
        db_session.add_all([ans1, ans2])
        await db_session.flush()

        # Decisão do conferente: Pendente / Encaminhado para Coordenação
        decision = ReceiptDecision(
            receipt_item_id=rec_item.id,
            decision=ReceiptDecisionEnum.PENDING,
            justification="Submetido à coordenação devido a apontamento no critério saneável C09",
            decided_by_id=conferente.id,
            requires_coordination_review=True,
        )
        db_session.add(decision)
        await db_session.flush()

        # Revisão da Coordenação: Aprovado com ressalva
        coord_review = CoordinationReview(
            decision_id=decision.id,
            status=CoordinationReviewStatus.APROVADO,
            reviewed_by_id=coordenador.id,
            reviewed_at=sol.created_at,
            review_notes="Ressalva aceita: código de barras legível e embalagem primária inviolada.",
        )
        db_session.add(coord_review)
        await db_session.flush()

        # Asserções finais
        stmt = select(ReceiptDecision).where(ReceiptDecision.id == decision.id)
        loaded_dec = (await db_session.execute(stmt)).scalar_one()

        assert loaded_dec.requires_coordination_review is True
        assert loaded_dec.coordination_review is not None
        assert loaded_dec.coordination_review.status == CoordinationReviewStatus.APROVADO
        assert loaded_dec.coordination_review.reviewed_by_id == coordenador.id

