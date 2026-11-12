"""Serviço de Catálogo de Métodos de Ensaio (Fase 2 / M2.1)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import ConflictError, NotFoundError
from app.models.enums import AuditAction, AuditEntity
from app.models.test_method import TestMethod
from app.models.user import User
from app.schemas.test_method import TestMethodCreate, TestMethodUpdate
from app.services import audit_service


async def get_method(db: AsyncSession, method_id: UUID) -> TestMethod:
    method = await db.get(TestMethod, method_id)
    if method is None:
        raise NotFoundError("Método de ensaio não encontrado.")
    return method


async def get_method_by_code(db: AsyncSession, code: str) -> TestMethod | None:
    return await db.scalar(
        select(TestMethod).where(TestMethod.code == code.strip())
    )


async def list_methods(
    db: AsyncSession,
    *,
    category: str | None = None,
    active_only: bool = True,
) -> list[TestMethod]:
    query = select(TestMethod)
    if active_only:
        query = query.where(TestMethod.is_active.is_(True))
    if category is not None:
        query = query.where(TestMethod.category == category.strip())
    query = query.order_by(TestMethod.code.asc())
    result = await db.scalars(query)
    return list(result.all())


async def create_method(
    db: AsyncSession,
    *,
    payload: TestMethodCreate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestMethod, int]:
    existing = await get_method_by_code(db, payload.code)
    if existing is not None:
        raise ConflictError(f"Já existe método cadastrado com o código '{payload.code}'.")

    method = TestMethod(
        code=payload.code.strip(),
        name=payload.name.strip(),
        standard=payload.standard.strip(),
        version=payload.version,
        category=payload.category.strip() if payload.category else None,
        description=payload.description.strip() if payload.description else None,
        parameters_schema=payload.parameters_schema,
        default_unit=payload.default_unit.strip(),
        default_lower_limit=payload.default_lower_limit,
        default_upper_limit=payload.default_upper_limit,
        default_acceptance_criteria=payload.default_acceptance_criteria,
        is_active=payload.is_active,
    )
    db.add(method)
    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.TEST_METHOD.value,
        entity_id=method.id,
        actor=actor,
        new_value=audit_service.snapshot(method),
        reason="Criação de método no catálogo",
        context=context,
    )
    return method, audit_entry.sequence


async def update_method(
    db: AsyncSession,
    method_id: UUID,
    *,
    payload: TestMethodUpdate,
    actor: User,
    context: RequestContext | None = None,
) -> tuple[TestMethod, int]:
    method = await get_method(db, method_id)
    old_value = audit_service.snapshot(method)

    if payload.name is not None:
        method.name = payload.name.strip()
    if payload.standard is not None:
        method.standard = payload.standard.strip()
    if payload.category is not None:
        method.category = payload.category.strip() if payload.category else None
    if payload.description is not None:
        method.description = payload.description.strip() if payload.description else None
    if payload.parameters_schema is not None:
        method.parameters_schema = payload.parameters_schema
    if payload.default_unit is not None:
        method.default_unit = payload.default_unit.strip()
    if payload.default_lower_limit is not None:
        method.default_lower_limit = payload.default_lower_limit
    if payload.default_upper_limit is not None:
        method.default_upper_limit = payload.default_upper_limit
    if payload.default_acceptance_criteria is not None:
        method.default_acceptance_criteria = payload.default_acceptance_criteria
    if payload.is_active is not None:
        method.is_active = payload.is_active

    await db.flush()

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.TEST_METHOD.value,
        entity_id=method.id,
        actor=actor,
        old_value=old_value,
        new_value=audit_service.snapshot(method),
        reason="Atualização de método no catálogo",
        context=context,
    )
    return method, audit_entry.sequence


async def ensure_standard_methods(
    db: AsyncSession,
    actor: User,
    context: RequestContext | None = None,
) -> list[TestMethod]:
    """Cria métodos padrão caso o catálogo esteja vazio."""
    standards = [
        TestMethodCreate(
            code="MET-ELETRO-01",
            name="Ensaio de Tensão Aplicada e Rigidez Dielétrica",
            standard="ABNT NBR IEC 60601-1",
            category="Elétrica",
            default_unit="mA",
            default_lower_limit=Decimal("0.0"),
            default_upper_limit=Decimal("5.0"),
            default_acceptance_criteria="Corrente de fuga não deve exceder 5.0 mA sob tensão de 1500V.",
            parameters_schema={"tensao_teste_v": 1500, "tempo_rampa_s": 5, "tempo_patamar_s": 60},
        ),
        TestMethodCreate(
            code="MET-TERMO-01",
            name="Ensaio de Elevação de Temperatura em Operação Contínua",
            standard="ABNT NBR NM 60335-1",
            category="Térmica",
            default_unit="°C",
            default_lower_limit=Decimal("15.0"),
            default_upper_limit=Decimal("65.0"),
            default_acceptance_criteria="A elevação máxima de temperatura dos enrolamentos não deve exceder 65°C.",
            parameters_schema={"potencia_w": 1000, "duracao_min": 120, "taxa_aquisicao_s": 10},
        ),
        TestMethodCreate(
            code="MET-MEC-01",
            name="Ensaio de Resistência a Impacto Mecânico",
            standard="ABNT NBR IEC 60068-2-75",
            category="Mecânica",
            default_unit="J",
            default_lower_limit=Decimal("0.5"),
            default_upper_limit=Decimal("2.0"),
            default_acceptance_criteria="O invólucro não deve apresentar trincas após impactos de 0.5 J.",
            parameters_schema={"energia_impacto_j": 0.5, "numero_golpes": 3, "massa_martelo_kg": 0.25},
        ),
    ]

    created: list[TestMethod] = []
    for item in standards:
        existing = await get_method_by_code(db, item.code)
        if existing is None:
            m, _ = await create_method(db, payload=item, actor=actor, context=context)
            created.append(m)
        else:
            created.append(existing)
    return created
