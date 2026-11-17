"""Serviço de Avaliação de Incerteza de Medição GUM e Regras de Decisão ILAC-G8 (Sprint 4.2)."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.errors import NotFoundError, ValidationDomainError
from app.core.serialization import jsonable
from app.models.electronic_signature import ElectronicSignature
from app.models.enums import (
    AuditAction,
    AuditEntity,
    ConformityStatus,
    DecisionRuleType,
    SignatureAction,
    TestOutcome,
    UncertaintyDistribution,
    UncertaintySourceType,
)
from app.models.equipment import LaboratoryEquipment
from app.models.lab_test import LabTest
from app.models.test_execution import TestExecution
from app.models.test_method import TestMethod
from app.models.uncertainty import UncertaintyBudget
from app.models.user import User
from app.schemas.uncertainty import (
    UncertaintyBudgetCreateIn,
    UncertaintyBudgetOut,
    UncertaintyCalculationOut,
    UncertaintyComponentIn,
    UncertaintyComponentOut,
    UncertaintySimulateIn,
)
from app.services import audit_service, signature_service
from app.services.audit_service import snapshot

Q6 = Decimal("0.000001")
Q3 = Decimal("0.001")
Q2 = Decimal("0.01")

# Tabela t de Student (JCGM 100:2008 / GUM Tabela G.2) para p = 95,45%
_T_TABLE_9545: list[tuple[float, float]] = [
    (1.0, 13.97),
    (2.0, 4.53),
    (3.0, 3.31),
    (4.0, 2.87),
    (5.0, 2.65),
    (6.0, 2.52),
    (7.0, 2.43),
    (8.0, 2.37),
    (9.0, 2.32),
    (10.0, 2.28),
    (12.0, 2.23),
    (15.0, 2.18),
    (20.0, 2.13),
    (25.0, 2.10),
    (30.0, 2.09),
    (40.0, 2.06),
    (50.0, 2.05),
    (100.0, 2.025),
]

# Tabela t de Student bilateral para p = 95,00%
_T_TABLE_9500: list[tuple[float, float]] = [
    (1.0, 12.71),
    (2.0, 4.30),
    (3.0, 3.18),
    (4.0, 2.78),
    (5.0, 2.57),
    (6.0, 2.45),
    (7.0, 2.36),
    (8.0, 2.31),
    (9.0, 2.26),
    (10.0, 2.23),
    (12.0, 2.18),
    (15.0, 2.13),
    (20.0, 2.09),
    (25.0, 2.06),
    (30.0, 2.04),
    (40.0, 2.02),
    (50.0, 2.01),
    (100.0, 1.984),
]


def _q(value: float | Decimal, quant: Decimal = Q6) -> Decimal:
    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)


def _student_k(effective_df: float | None, confidence_level: Decimal) -> Decimal:
    """Determina o fator de abrangência k pela tabela t de Student (GUM Tabela G.2)."""
    use_9500 = abs(float(confidence_level) - 95.0) < abs(float(confidence_level) - 95.45)
    table = _T_TABLE_9500 if use_9500 else _T_TABLE_9545
    k_inf = 1.960 if use_9500 else 2.000

    if effective_df is None or effective_df > 100.0:
        return _q(k_inf, Q3)
    if effective_df <= table[0][0]:
        return _q(table[0][1], Q3)

    for idx in range(len(table) - 1):
        df0, k0 = table[idx]
        df1, k1 = table[idx + 1]
        if df0 <= effective_df <= df1:
            ratio = (effective_df - df0) / (df1 - df0)
            return _q(k0 + ratio * (k1 - k0), Q3)

    return _q(k_inf, Q3)


def _default_divisor(
    distribution: UncertaintyDistribution,
    source_type: UncertaintySourceType,
) -> float:
    if distribution == UncertaintyDistribution.NORMAL:
        return 2.0 if source_type == UncertaintySourceType.TYPE_B else 1.0
    if distribution == UncertaintyDistribution.RECTANGULAR:
        return math.sqrt(3.0)
    if distribution == UncertaintyDistribution.TRIANGULAR:
        return math.sqrt(6.0)
    if distribution == UncertaintyDistribution.U_SHAPED:
        return math.sqrt(2.0)
    return math.sqrt(3.0)


def _evaluate_conformity(
    *,
    measured_value: Decimal,
    lower_limit: Decimal | None,
    upper_limit: Decimal | None,
    expanded_uncertainty: Decimal,
    guard_band_width: Decimal,
    decision_rule: DecisionRuleType,
    unit: str,
) -> tuple[Decimal | None, Decimal | None, ConformityStatus, TestOutcome, str]:
    """Aplica a regra de decisão metrológica ILAC-G8:09/2019 e ISO/IEC 17025 §7.8.6."""
    lower_acc = (
        (lower_limit + guard_band_width).quantize(Q6, rounding=ROUND_HALF_UP)
        if lower_limit is not None
        else None
    )
    upper_acc = (
        (upper_limit - guard_band_width).quantize(Q6, rounding=ROUND_HALF_UP)
        if upper_limit is not None
        else None
    )

    if lower_limit is None and upper_limit is None:
        return (
            None,
            None,
            ConformityStatus.CONFORME_CONDICIONAL,
            TestOutcome.INCONCLUSIVO,
            (
                "Sem limites de especificação definidos para avaliação quantitativa de conformidade "
                f"(ISO/IEC 17025 §7.8.6; U = ±{expanded_uncertainty:.4f} {unit})."
            ),
        )

    out_of_spec = (lower_limit is not None and measured_value < lower_limit) or (
        upper_limit is not None and measured_value > upper_limit
    )
    within_guard_acceptance = (lower_acc is None or measured_value >= lower_acc) and (
        upper_acc is None or measured_value <= upper_acc
    )

    if decision_rule == DecisionRuleType.SIMPLE_ACCEPTANCE:
        if out_of_spec:
            return (
                lower_acc,
                upper_acc,
                ConformityStatus.NAO_CONFORME,
                TestOutcome.REPROVADO,
                (
                    "NÃO CONFORME segundo regra de Aceitação Simples (ILAC-G8 §4.2.1; risco compartilhado, "
                    f"w = 0). Valor medido ({measured_value:.4f} {unit}) fora dos limites de especificação."
                ),
            )
        return (
            lower_acc,
            upper_acc,
            ConformityStatus.CONFORME,
            TestOutcome.APROVADO,
            (
                "CONFORME segundo regra de Aceitação Simples (ILAC-G8 §4.2.1; risco compartilhado, "
                f"w = 0). Valor medido ({measured_value:.4f} ± {expanded_uncertainty:.4f} {unit}) dentro da especificação."
            ),
        )

    if decision_rule == DecisionRuleType.GUARD_BAND_CONSERVATIVE:
        if within_guard_acceptance:
            return (
                lower_acc,
                upper_acc,
                ConformityStatus.CONFORME,
                TestOutcome.APROVADO,
                (
                    "CONFORME segundo regra de Aceitação Binária com Faixa de Guarda Conservadora "
                    f"(ILAC-G8 §4.2.2; w = {guard_band_width:.4f} {unit}). Intervalo de incerteza integralmente contido nos limites."
                ),
            )
        detail = (
            "valor nominal fora do limite de especificação"
            if out_of_spec
            else "resultado situado na zona de guarda (risco específico superior ao limite aceitável)"
        )
        return (
            lower_acc,
            upper_acc,
            ConformityStatus.NAO_CONFORME,
            TestOutcome.REPROVADO,
            (
                "NÃO CONFORME segundo regra de Aceitação Binária com Faixa de Guarda Conservadora "
                f"(ILAC-G8 §4.2.2; w = {guard_band_width:.4f} {unit}): {detail}."
            ),
        )

    # GUARD_BAND_NON_BINARY (4 desfechos: ILAC-G8 §4.2.3)
    if within_guard_acceptance:
        return (
            lower_acc,
            upper_acc,
            ConformityStatus.CONFORME,
            TestOutcome.APROVADO,
            (
                "CONFORME (Pass) segundo regra Não-Binária com Faixa de Guarda "
                f"(ILAC-G8 §4.2.3; w = {guard_band_width:.4f} {unit})."
            ),
        )

    if not out_of_spec:
        return (
            lower_acc,
            upper_acc,
            ConformityStatus.CONFORME_CONDICIONAL,
            TestOutcome.INCONCLUSIVO,
            (
                "CONFORME CONDICIONAL / ZONA DE GUARDA (Conditional Pass — ILAC-G8 §4.2.3 / ISO 17025 §7.8.6): "
                f"valor medido ({measured_value:.4f} {unit}) dentro da especificação, porém a diferença para o limite "
                f"é menor que a faixa de guarda w = {guard_band_width:.4f} {unit}."
            ),
        )

    within_outer_guard = (
        lower_limit is None or measured_value >= (lower_limit - guard_band_width)
    ) and (upper_limit is None or measured_value <= (upper_limit + guard_band_width))
    if within_outer_guard:
        return (
            lower_acc,
            upper_acc,
            ConformityStatus.NAO_CONFORME_CONDICIONAL,
            TestOutcome.INCONCLUSIVO,
            (
                "NÃO CONFORME CONDICIONAL / ZONA DE GUARDA (Conditional Fail — ILAC-G8 §4.2.3 / ISO 17025 §7.8.6): "
                f"valor medido ({measured_value:.4f} {unit}) excede o limite de especificação dentro da faixa "
                f"de incerteza w = {guard_band_width:.4f} {unit}."
            ),
        )

    return (
        lower_acc,
        upper_acc,
        ConformityStatus.NAO_CONFORME,
        TestOutcome.REPROVADO,
        (
            "NÃO CONFORME (Fail) segundo regra Não-Binária com Faixa de Guarda "
            f"(ILAC-G8 §4.2.3; w = {guard_band_width:.4f} {unit}): resultado além dos limites e da faixa de guarda."
        ),
    )


def calculate_uncertainty_budget(payload: UncertaintySimulateIn) -> UncertaintyCalculationOut:
    """Executa o cálculo completo de incerteza GUM e decisão ILAC-G8 em memória."""
    readings = [float(r) for r in payload.repeatability_readings]
    rep_count = len(readings)
    rep_mean: Decimal | None = None
    rep_std_dev: Decimal | None = None
    u_type_a: float | None = None

    if rep_count >= 2:
        mean_val = sum(readings) / rep_count
        variance = sum((x - mean_val) ** 2 for x in readings) / (rep_count - 1)
        std_dev = math.sqrt(variance)
        u_type_a = std_dev / math.sqrt(rep_count)
        rep_mean = _q(mean_val, Q6)
        rep_std_dev = _q(std_dev, Q6)
    elif rep_count == 1:
        rep_mean = _q(readings[0], Q6)
        rep_std_dev = Decimal("0.000000")

    measured_value = payload.measured_value if payload.measured_value is not None else rep_mean
    if measured_value is None:
        raise ValidationDomainError(
            "Informe o valor medido ou ao menos 1 leitura experimental de repetibilidade."
        )

    raw_components = list(payload.components)
    has_explicit_type_a = any(c.source_type == UncertaintySourceType.TYPE_A for c in raw_components)
    if u_type_a is not None and not has_explicit_type_a:
        raw_components.insert(
            0,
            UncertaintyComponentIn(
                name="Repetibilidade Experimental das Leituras (Tipo A)",
                symbol="u_A",
                source_type=UncertaintySourceType.TYPE_A,
                distribution=UncertaintyDistribution.NORMAL,
                half_width=_q(u_type_a, Q6),
                divisor=Decimal("1.0"),
                sensitivity_coefficient=Decimal("1.0"),
                degrees_of_freedom=rep_count - 1,
            ),
        )

    computed_entries: list[dict[str, Any]] = []
    sum_sq = 0.0
    ws_denom = 0.0

    for comp in raw_components:
        div = (
            float(comp.divisor)
            if comp.divisor is not None
            else _default_divisor(comp.distribution, comp.source_type)
        )
        u_i = float(comp.half_width) / div
        c_i = float(comp.sensitivity_coefficient)
        contrib = abs(c_i * u_i)
        sum_sq += contrib**2
        if comp.degrees_of_freedom is not None and contrib > 0.0:
            ws_denom += (contrib**4) / float(comp.degrees_of_freedom)

        computed_entries.append(
            {
                "comp": comp,
                "divisor": div,
                "u_i": u_i,
                "contrib": contrib,
            }
        )

    uc_val = math.sqrt(sum_sq)
    combined_uncertainty = _q(uc_val, Q6)

    effective_df_val: float | None = None
    if ws_denom > 0.0 and uc_val > 0.0:
        effective_df_val = (uc_val**4) / ws_denom
    effective_df = _q(effective_df_val, Q2) if effective_df_val is not None else None

    if payload.coverage_factor is not None:
        coverage_factor = _q(payload.coverage_factor, Q3)
    else:
        coverage_factor = _student_k(effective_df_val, payload.confidence_level)

    expanded_val = float(coverage_factor) * uc_val
    expanded_uncertainty = _q(expanded_val, Q6)

    if payload.decision_rule == DecisionRuleType.SIMPLE_ACCEPTANCE:
        guard_band_width = Decimal("0.000000")
    else:
        guard_band_width = _q(payload.guard_band_multiplier * expanded_uncertainty, Q6)

    components_out: list[UncertaintyComponentOut] = []
    for entry in computed_entries:
        comp = entry["comp"]
        contrib = entry["contrib"]
        weight = (contrib**2 / sum_sq * 100.0) if sum_sq > 0.0 else 0.0
        components_out.append(
            UncertaintyComponentOut(
                name=comp.name,
                symbol=comp.symbol,
                source_type=comp.source_type,
                distribution=comp.distribution,
                half_width=_q(comp.half_width, Q6),
                divisor=_q(entry["divisor"], Q6),
                sensitivity_coefficient=_q(comp.sensitivity_coefficient, Q6),
                degrees_of_freedom=comp.degrees_of_freedom,
                standard_uncertainty=_q(entry["u_i"], Q6),
                combined_contribution=_q(contrib, Q6),
                weight_percent=_q(weight, Q2),
            )
        )

    lower_acc, upper_acc, conf_status, rec_outcome, statement = _evaluate_conformity(
        measured_value=_q(measured_value, Q6),
        lower_limit=payload.lower_limit,
        upper_limit=payload.upper_limit,
        expanded_uncertainty=expanded_uncertainty,
        guard_band_width=guard_band_width,
        decision_rule=payload.decision_rule,
        unit=payload.unit,
    )

    formatted_result = (
        f"{_q(measured_value, Q6):.4f} ± {expanded_uncertainty:.4f} {payload.unit} "
        f"(k = {coverage_factor:.2f}, {payload.confidence_level:.2f}%)"
    )

    return UncertaintyCalculationOut(
        unit=payload.unit,
        measured_value=_q(measured_value, Q6),
        lower_limit=payload.lower_limit,
        upper_limit=payload.upper_limit,
        lower_acceptance_limit=lower_acc,
        upper_acceptance_limit=upper_acc,
        repeatability_mean=rep_mean,
        repeatability_std_dev=rep_std_dev,
        repeatability_count=rep_count,
        components=components_out,
        combined_uncertainty=combined_uncertainty,
        effective_df=effective_df,
        coverage_factor=coverage_factor,
        confidence_level=payload.confidence_level,
        expanded_uncertainty=expanded_uncertainty,
        guard_band_multiplier=payload.guard_band_multiplier,
        guard_band_width=guard_band_width,
        decision_rule=payload.decision_rule,
        conformity_status=conf_status,
        recommended_outcome=rec_outcome,
        conformity_statement=statement,
        formatted_result=formatted_result,
    )


def to_budget_out(budget: UncertaintyBudget) -> UncertaintyBudgetOut:
    """Converte o modelo persistido `UncertaintyBudget` em schema completo de saída."""
    readings = [Decimal(str(r)) for r in (budget.repeatability_readings or [])]
    rep_count = len(readings)
    rep_mean: Decimal | None = None
    rep_std_dev: Decimal | None = None
    if rep_count >= 2:
        floats = [float(x) for x in readings]
        mean_val = sum(floats) / rep_count
        variance = sum((x - mean_val) ** 2 for x in floats) / (rep_count - 1)
        rep_mean = _q(mean_val, Q6)
        rep_std_dev = _q(math.sqrt(variance), Q6)
    elif rep_count == 1:
        rep_mean = _q(readings[0], Q6)
        rep_std_dev = Decimal("0.000000")

    lower_acc = (
        (budget.lower_limit + budget.guard_band_width).quantize(Q6, rounding=ROUND_HALF_UP)
        if budget.lower_limit is not None
        else None
    )
    upper_acc = (
        (budget.upper_limit - budget.guard_band_width).quantize(Q6, rounding=ROUND_HALF_UP)
        if budget.upper_limit is not None
        else None
    )

    components_out = [UncertaintyComponentOut.model_validate(c) for c in (budget.components or [])]
    formatted_result = (
        f"{budget.measured_value:.4f} ± {budget.expanded_uncertainty:.4f} {budget.unit} "
        f"(k = {budget.coverage_factor:.2f}, {budget.confidence_level:.2f}%)"
    )

    return UncertaintyBudgetOut(
        id=budget.id,
        method_id=budget.method_id,
        lab_test_id=budget.lab_test_id,
        execution_id=budget.execution_id,
        equipment_id=budget.equipment_id,
        unit=budget.unit,
        measured_value=budget.measured_value,
        lower_limit=budget.lower_limit,
        upper_limit=budget.upper_limit,
        lower_acceptance_limit=lower_acc,
        upper_acceptance_limit=upper_acc,
        repeatability_readings=readings,
        repeatability_mean=rep_mean,
        repeatability_std_dev=rep_std_dev,
        repeatability_count=rep_count,
        components=components_out,
        combined_uncertainty=budget.combined_uncertainty,
        effective_df=budget.effective_df,
        coverage_factor=budget.coverage_factor,
        confidence_level=budget.confidence_level,
        expanded_uncertainty=budget.expanded_uncertainty,
        guard_band_multiplier=budget.guard_band_multiplier,
        guard_band_width=budget.guard_band_width,
        decision_rule=budget.decision_rule,
        conformity_status=budget.conformity_status,
        recommended_outcome=budget.recommended_outcome,
        conformity_statement=budget.conformity_statement,
        formatted_result=formatted_result,
        calculated_by_id=budget.calculated_by_id,
        calculated_by_name=budget.calculated_by.full_name if budget.calculated_by else None,
        method_code=budget.method.code if budget.method else None,
        test_name=budget.lab_test.name if budget.lab_test else None,
        equipment_code=budget.equipment.code if budget.equipment else None,
        signature_id=budget.signature_id,
        notes=budget.notes,
        version=budget.version,
        created_at=budget.created_at,
    )


async def create_uncertainty_budget(
    db: AsyncSession,
    *,
    payload: UncertaintyBudgetCreateIn,
    actor: User,
    signature_token: str | None = None,
    context: RequestContext | None = None,
) -> tuple[UncertaintyBudget, int]:
    """Calcula e persiste o orçamento de incerteza GUM vinculado opcionalmente ao ensaio."""
    lab_test: LabTest | None = None
    method_id = payload.method_id
    equipment_id = payload.equipment_id
    unit = payload.unit
    lower_limit = payload.lower_limit
    upper_limit = payload.upper_limit

    if payload.lab_test_id is not None:
        lab_test = await db.get(LabTest, payload.lab_test_id)
        if lab_test is None:
            raise NotFoundError("Ensaio laboratorial não encontrado.")
        if method_id is None:
            method_id = lab_test.method_id
        if equipment_id is None:
            equipment_id = lab_test.equipment_id
        if lower_limit is None:
            lower_limit = lab_test.lower_limit
        if upper_limit is None:
            upper_limit = lab_test.upper_limit
        if payload.unit == "UN" and lab_test.unit:
            unit = lab_test.unit

    if method_id is not None:
        method = await db.get(TestMethod, method_id)
        if method is None:
            raise NotFoundError("Método analítico não encontrado.")
        if lower_limit is None:
            lower_limit = method.default_lower_limit
        if upper_limit is None:
            upper_limit = method.default_upper_limit

    if payload.execution_id is not None:
        execution = await db.get(TestExecution, payload.execution_id)
        if execution is None:
            raise NotFoundError("Execução de ensaio não encontrada.")

    if equipment_id is not None:
        equipment = await db.get(LaboratoryEquipment, equipment_id)
        if equipment is None:
            raise NotFoundError("Equipamento não encontrado.")

    sim_payload = UncertaintySimulateIn(
        unit=unit,
        measured_value=payload.measured_value,
        repeatability_readings=payload.repeatability_readings,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
        components=payload.components,
        coverage_factor=payload.coverage_factor,
        confidence_level=payload.confidence_level,
        guard_band_multiplier=payload.guard_band_multiplier,
        decision_rule=payload.decision_rule,
    )
    calc = calculate_uncertainty_budget(sim_payload)

    sig_record: ElectronicSignature | None = None
    if signature_token:
        request_ctx = context or RequestContext(
            ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
        )
        if lab_test is not None:
            target_entity, target_id, target_action = (
                "LabTest",
                str(lab_test.id),
                SignatureAction.UPDATE,
            )
        elif method_id is not None:
            target_entity, target_id, target_action = (
                "TestMethod",
                str(method_id),
                SignatureAction.UPDATE,
            )
        else:
            target_entity, target_id, target_action = (
                "UncertaintyBudget",
                str(actor.id),
                SignatureAction.CREATE,
            )

        sig_record = await signature_service.consume(
            db,
            token=signature_token,
            user=actor,
            entity_type=target_entity,
            entity_id=target_id,
            action=target_action,
            context=request_ctx,
        )

    budget_id = uuid4()
    budget = UncertaintyBudget(
        id=budget_id,
        method_id=method_id,
        lab_test_id=payload.lab_test_id,
        execution_id=payload.execution_id,
        equipment_id=equipment_id,
        unit=calc.unit,
        measured_value=calc.measured_value,
        lower_limit=calc.lower_limit,
        upper_limit=calc.upper_limit,
        repeatability_readings=jsonable(payload.repeatability_readings),
        components=jsonable([c.model_dump(mode="json") for c in calc.components]),
        combined_uncertainty=calc.combined_uncertainty,
        effective_df=calc.effective_df,
        coverage_factor=calc.coverage_factor,
        confidence_level=calc.confidence_level,
        expanded_uncertainty=calc.expanded_uncertainty,
        guard_band_multiplier=calc.guard_band_multiplier,
        guard_band_width=calc.guard_band_width,
        decision_rule=calc.decision_rule,
        conformity_status=calc.conformity_status,
        recommended_outcome=calc.recommended_outcome,
        conformity_statement=calc.conformity_statement,
        calculated_by_id=actor.id,
        signature_id=sig_record.id if sig_record else None,
        notes=payload.notes,
        attributes={
            "formatted_result": calc.formatted_result,
            "lower_acceptance_limit": str(calc.lower_acceptance_limit)
            if calc.lower_acceptance_limit is not None
            else None,
            "upper_acceptance_limit": str(calc.upper_acceptance_limit)
            if calc.upper_acceptance_limit is not None
            else None,
        },
    )
    db.add(budget)
    await db.flush()

    if sig_record is not None:
        await signature_service.bind_record(
            db,
            sig_record,
            {"uncertainty_budget": snapshot(budget)},
        )

    audit_entry = await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.UNCERTAINTY_BUDGET.value,
        entity_id=budget.id,
        actor=actor,
        old_value=None,
        new_value=snapshot(budget),
        reason=(
            f"Registro de orçamento de incerteza GUM ({calc.formatted_result}) — "
            f"Regra {calc.decision_rule.value}: {calc.conformity_status.value}"
        ),
        context=context,
        signature_id=sig_record.id if sig_record else None,
    )

    if (
        calc.conformity_status
        in (ConformityStatus.NAO_CONFORME, ConformityStatus.NAO_CONFORME_CONDICIONAL)
        and payload.lab_test_id is not None
    ):
        from app.models.capa_action import CapaAction
        from app.models.enums import CapaStatus
        from app.services import capa_service

        existing_capa = await db.scalar(
            select(CapaAction).where(
                CapaAction.lab_test_id == payload.lab_test_id,
                CapaAction.status.in_([CapaStatus.ABERTA, CapaStatus.EM_ANDAMENTO]),
            )
        )
        if existing_capa is None:
            ctx = context or RequestContext(
                ip_address="127.0.0.1", user_agent="LIMS-Internal", request_id="internal"
            )
            await capa_service.open_capa_from_uncertainty(
                db, budget=budget, actor=actor, context=ctx
            )

    await db.commit()
    await db.refresh(
        budget,
        ["calculated_by", "method", "lab_test", "equipment"],
    )
    return budget, audit_entry.sequence


async def list_uncertainty_budgets(
    db: AsyncSession,
    *,
    lab_test_id: UUID | None = None,
    method_id: UUID | None = None,
    execution_id: UUID | None = None,
    conformity_status: ConformityStatus | None = None,
) -> list[UncertaintyBudget]:
    """Lista os orçamentos de incerteza registrados ordenados do mais recente ao mais antigo."""
    stmt = select(UncertaintyBudget)
    if lab_test_id is not None:
        stmt = stmt.where(UncertaintyBudget.lab_test_id == lab_test_id)
    if method_id is not None:
        stmt = stmt.where(UncertaintyBudget.method_id == method_id)
    if execution_id is not None:
        stmt = stmt.where(UncertaintyBudget.execution_id == execution_id)
    if conformity_status is not None:
        stmt = stmt.where(UncertaintyBudget.conformity_status == conformity_status)
    stmt = stmt.order_by(UncertaintyBudget.created_at.desc())
    result = await db.scalars(stmt)
    return list(result.all())


async def get_uncertainty_budget(db: AsyncSession, budget_id: UUID) -> UncertaintyBudget:
    """Busca um orçamento de incerteza pelo identificador."""
    budget = await db.get(UncertaintyBudget, budget_id)
    if budget is None:
        raise NotFoundError("Orçamento de incerteza não encontrado.")
    return budget
