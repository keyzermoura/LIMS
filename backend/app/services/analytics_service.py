"""Serviço de Agregação Analítica, BI e Controle Estatístico de Processo (Fase 5 / Sprint 5.1).

Implementa os cálculos de tempos de ciclo (TAT), estratificação de backlog, taxas de
conformidade técnica, eficácia de ações corretivas e Cartas de Controle de Shewhart
com regras multiregra de Westgard (ISO/IEC 17025:2017 §7.7 e §8.8).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.capa_action import CapaAction
from app.models.device_sample import DeviceSample
from app.models.enums import (
    CapaEffectivenessStatus,
    CapaStatus,
    EquipmentCalibrationStatus,
    SampleStatus,
    TestOutcome,
    TestStatus,
    UserRole,
)
from app.models.equipment import LaboratoryEquipment
from app.models.lab_test import LabTest
from app.models.official_report import OfficialReport
from app.models.test_method import TestMethod
from app.models.user import User
from app.schemas.analytics import (
    AnalystWorkloadItem,
    CapaMetrics,
    OperationalAnalyticsOut,
    QualityControlAnalyticsOut,
    QualityControlPoint,
    SampleBacklogMetrics,
    TestConformityMetrics,
    TurnaroundTimeMetrics,
    WestgardViolation,
)


async def get_operational_analytics(db: AsyncSession) -> OperationalAnalyticsOut:
    """Consolida as métricas operacionais e de tempos de ciclo do laboratório."""
    now = datetime.now(UTC)

    # 1. Turnaround Time (TAT)
    # 1.1 Laudos emitidos e tempo total de ciclo
    reports_stmt = select(OfficialReport).order_by(OfficialReport.created_at.desc()).limit(100)
    reports = (await db.scalars(reports_stmt)).all()

    tat_global_deltas: list[float] = []
    receipt_to_testing_deltas: list[float] = []
    testing_to_review_deltas: list[float] = []

    for report in reports:
        # Busca amostra vinculada
        sample = await db.get(DeviceSample, report.device_sample_id)
        if sample and sample.created_at and report.created_at:
            delta_hours = (report.created_at - sample.created_at).total_seconds() / 3600.0
            if delta_hours >= 0:
                tat_global_deltas.append(delta_hours)

    # 1.2 Delays intermediários baseados em testes e revisões
    tests_stmt = (
        select(LabTest)
        .where(LabTest.status == TestStatus.CONCLUIDO, LabTest.tested_at.is_not(None))
        .limit(100)
    )
    completed_tests = (await db.scalars(tests_stmt)).all()

    for test in completed_tests:
        sample = await db.get(DeviceSample, test.device_sample_id)
        if sample and sample.created_at and test.tested_at:
            d_hours = (test.tested_at - sample.created_at).total_seconds() / 3600.0
            if d_hours >= 0:
                receipt_to_testing_deltas.append(d_hours)

        # Checa revisões associadas
        if test.reviews and test.tested_at:
            for rev in test.reviews:
                if rev.reviewed_at:
                    d_rev = (rev.reviewed_at - test.tested_at).total_seconds() / 3600.0
                    if d_rev >= 0:
                        testing_to_review_deltas.append(d_rev)

    # Médias seguras (sem dados sintéticos / ALCOA+)
    global_avg = (
        round(sum(tat_global_deltas) / len(tat_global_deltas), 2)
        if tat_global_deltas
        else None
    )
    rec_test_avg = (
        round(sum(receipt_to_testing_deltas) / len(receipt_to_testing_deltas), 2)
        if receipt_to_testing_deltas
        else None
    )
    test_rev_avg = (
        round(sum(testing_to_review_deltas) / len(testing_to_review_deltas), 2)
        if testing_to_review_deltas
        else None
    )
    rev_rep_avg = (
        round(max(0.0, global_avg - (rec_test_avg + test_rev_avg)), 2)
        if (global_avg is not None and rec_test_avg is not None and test_rev_avg is not None)
        else None
    )

    tat_data_quality = "sufficient" if len(tat_global_deltas) >= 5 else "insufficient"

    tat_metrics = TurnaroundTimeMetrics(
        global_avg_hours=global_avg,
        receipt_to_testing_avg_hours=rec_test_avg,
        testing_to_review_avg_hours=test_rev_avg,
        review_to_report_avg_hours=rev_rep_avg,
        samples_measured_count=len(tat_global_deltas),
        data_quality=tat_data_quality,
    )

    # 2. Backlog de Amostras
    samples_stmt = select(DeviceSample).where(
        DeviceSample.status.in_([SampleStatus.RECEBIDO, SampleStatus.EM_TESTE])
    )
    active_samples = (await db.scalars(samples_stmt)).all()

    age_0_5 = 0
    age_6_15 = 0
    age_above_15 = 0

    for s in active_samples:
        if s.created_at:
            age_days = (now - s.created_at).total_seconds() / 86400.0
            if age_days <= 5.0:
                age_0_5 += 1
            elif age_days <= 15.0:
                age_6_15 += 1
            else:
                age_above_15 += 1

    backlog_metrics = SampleBacklogMetrics(
        age_0_to_5_days=age_0_5,
        age_6_to_15_days=age_6_15,
        age_above_15_days=age_above_15,
        total_active=len(active_samples),
    )

    # 3. Conformidade Técnica de Ensaios
    all_tests_stmt = select(LabTest)
    all_tests = (await db.scalars(all_tests_stmt)).all()

    conforming = sum(1 for t in all_tests if t.outcome == TestOutcome.APROVADO)
    non_conforming = sum(1 for t in all_tests if t.outcome == TestOutcome.REPROVADO)
    inconclusive = sum(1 for t in all_tests if t.outcome == TestOutcome.INCONCLUSIVO)
    pending = sum(
        1 for t in all_tests if t.status == TestStatus.PENDENTE or t.outcome is None
    )
    total_evaluated = conforming + non_conforming + inconclusive
    conf_rate = (
        round((conforming / total_evaluated) * 100.0, 1) if total_evaluated > 0 else None
    )
    conf_quality = "sufficient" if total_evaluated >= 5 else "insufficient"

    conformity_metrics = TestConformityMetrics(
        total_tests=len(all_tests),
        conforming_count=conforming,
        non_conforming_count=non_conforming,
        inconclusive_count=inconclusive,
        pending_count=pending,
        conformity_rate_pct=conf_rate,
        data_quality=conf_quality,
    )

    # 4. CAPA Metrics
    all_capas_stmt = select(CapaAction)
    all_capas = (await db.scalars(all_capas_stmt)).all()

    open_capas = sum(1 for c in all_capas if c.status != CapaStatus.CONCLUIDA)
    closed_capas = sum(1 for c in all_capas if c.status == CapaStatus.CONCLUIDA)
    effective = sum(
        1 for c in all_capas if c.effectiveness_status == CapaEffectivenessStatus.EFICAZ
    )
    ineffective = sum(
        1 for c in all_capas if c.effectiveness_status == CapaEffectivenessStatus.INEFICAZ
    )
    eff_rate = (
        round((effective / (effective + ineffective)) * 100.0, 1)
        if (effective + ineffective) > 0
        else None
    )
    capa_quality = "sufficient" if (effective + ineffective) >= 3 else "insufficient"

    capa_metrics = CapaMetrics(
        total_capas=len(all_capas),
        open_capas=open_capas,
        closed_capas=closed_capas,
        effective_capas=effective,
        ineffective_capas=ineffective,
        effectiveness_rate_pct=eff_rate,
        data_quality=capa_quality,
    )

    # 5. Carga de Trabalho por Analista
    analysts_stmt = select(User).where(
        User.role.in_([UserRole.TECNICO, UserRole.FISCAL, UserRole.ADMIN]),
        User.is_active == True,  # noqa: E712
    )
    analysts = (await db.scalars(analysts_stmt)).all()

    workload_items: list[AnalystWorkloadItem] = []
    for a in analysts:
        active_t = sum(
            1
            for t in all_tests
            if (t.assigned_to_id == a.id or t.tested_by_id == a.id)
            and t.status != TestStatus.CONCLUIDO
        )
        comp_t = sum(
            1
            for t in all_tests
            if (t.assigned_to_id == a.id or t.tested_by_id == a.id)
            and t.status == TestStatus.CONCLUIDO
        )
        workload_items.append(
            AnalystWorkloadItem(
                user_id=a.id,
                full_name=a.full_name,
                active_tests_count=active_t,
                completed_tests_count=comp_t,
            )
        )

    # 6. Status de Calibração dos Equipamentos
    equipments_stmt = select(LaboratoryEquipment)
    equipments = (await db.scalars(equipments_stmt)).all()

    equip_summary: dict[str, int] = {
        EquipmentCalibrationStatus.CALIBRADO.value: 0,
        EquipmentCalibrationStatus.VENCIDO.value: 0,
        EquipmentCalibrationStatus.EM_MANUTENCAO.value: 0,
        EquipmentCalibrationStatus.NAO_APLICAVEL.value: 0,
    }
    for eq in equipments:
        val = eq.calibration_status.value
        equip_summary[val] = equip_summary.get(val, 0) + 1

    return OperationalAnalyticsOut(
        turnaround_time=tat_metrics,
        sample_backlog=backlog_metrics,
        test_conformity=conformity_metrics,
        capa_metrics=capa_metrics,
        analysts_workload=workload_items,
        equipment_status_summary=equip_summary,
    )


def _evaluate_westgard(
    values: list[float], mean: float, std_dev: float
) -> tuple[list[str | None], list[WestgardViolation]]:
    """Aplica as regras multiregra de Westgard (ISO 17025 §7.7) sobre os pontos amostrais.

    Regras:
    - 1_3s: Um ponto além de 3s (Alarme / Rejeição)
    - 2_2s: Dois pontos consecutivos além de 2s do mesmo lado (Alarme / Rejeição)
    - R_4s: Diferença >= 4s entre dois pontos consecutivos (Rejeição por dispersão)
    - 4_1s: Quatro pontos consecutivos além de 1s do mesmo lado (Aviso sistemático)
    - 10_x: Dez pontos consecutivos do mesmo lado da média (Aviso de tendência)
    """
    n = len(values)
    point_violations: list[str | None] = [None] * n
    violations: list[WestgardViolation] = []

    if std_dev <= 0:
        return point_violations, violations

    # Regra 1_3s
    for i in range(n):
        diff = abs(values[i] - mean)
        if diff > 3.0 * std_dev:
            point_violations[i] = "1_3s"
            violations.append(
                WestgardViolation(
                    rule_code="1_3s",
                    description=f"Corrida #{i+1} ({values[i]:.3f}) excedeu o limite de ação de 3 desvios padrão (±3s).",
                    run_numbers=[i + 1],
                    severity="ALARM",
                )
            )

    # Regra 2_2s
    for i in range(1, n):
        v1, v2 = values[i - 1], values[i]
        if (v1 - mean > 2.0 * std_dev and v2 - mean > 2.0 * std_dev) or (
            v1 - mean < -2.0 * std_dev and v2 - mean < -2.0 * std_dev
        ):
            if not point_violations[i]:
                point_violations[i] = "2_2s"
            violations.append(
                WestgardViolation(
                    rule_code="2_2s",
                    description=f"Corridas #{i} e #{i+1} ultrapassaram 2 desvios padrão no mesmo lado da média.",
                    run_numbers=[i, i + 1],
                    severity="ALARM",
                )
            )

    # Regra R_4s
    for i in range(1, n):
        v1, v2 = values[i - 1], values[i]
        if (v1 - mean > 2.0 * std_dev and v2 - mean < -2.0 * std_dev) or (
            v1 - mean < -2.0 * std_dev and v2 - mean > 2.0 * std_dev
        ):
            if not point_violations[i]:
                point_violations[i] = "R_4s"
            violations.append(
                WestgardViolation(
                    rule_code="R_4s",
                    description=f"Dispersão de 4 desvios padrão detectada entre corridas #{i} e #{i+1}.",
                    run_numbers=[i, i + 1],
                    severity="ALARM",
                )
            )

    # Regra 4_1s
    for i in range(3, n):
        w = values[i - 3 : i + 1]
        all_above = all(x - mean > 1.0 * std_dev for x in w)
        all_below = all(x - mean < -1.0 * std_dev for x in w)
        if all_above or all_below:
            if not point_violations[i]:
                point_violations[i] = "4_1s"
            violations.append(
                WestgardViolation(
                    rule_code="4_1s",
                    description=f"Quatro corridas consecutivas (#{i-2} a #{i+1}) excederam 1 desvio padrão no mesmo lado.",
                    run_numbers=[i - 2, i - 1, i, i + 1],
                    severity="WARNING",
                )
            )

    # Regra 10_x
    for i in range(9, n):
        w = values[i - 9 : i + 1]
        all_above = all(x > mean for x in w)
        all_below = all(x < mean for x in w)
        if all_above or all_below:
            if not point_violations[i]:
                point_violations[i] = "10_x"
            violations.append(
                WestgardViolation(
                    rule_code="10_x",
                    description=f"Tendência sistemática: 10 corridas consecutivas (#{i-8} a #{i+1}) do mesmo lado da média.",
                    run_numbers=list(range(i - 8, i + 2)),
                    severity="WARNING",
                )
            )

    return point_violations, violations


async def get_quality_control_analytics(
    db: AsyncSession, method_id: UUID | None = None
) -> QualityControlAnalyticsOut:
    """Calcula os parâmetros da Carta de Controle de Shewhart / Levey-Jennings e avalia regras de Westgard."""
    selected_method: TestMethod | None = None

    if method_id:
        selected_method = await db.get(TestMethod, method_id)

    if not selected_method:
        # Pega o primeiro método cadastrado
        selected_method = (
            await db.scalars(select(TestMethod).order_by(TestMethod.created_at.desc()).limit(1))
        ).first()

    method_name = selected_method.name if selected_method else "Ensaio Físico-Químico Geral"
    unit = "mg/L"

    # Busca resultados numéricos dos ensaios
    tests_stmt = select(LabTest).where(
        LabTest.result_value.is_not(None),
        LabTest.status == TestStatus.CONCLUIDO,
    )
    if selected_method:
        tests_stmt = tests_stmt.where(LabTest.method_id == selected_method.id)

    tests_stmt = tests_stmt.order_by(LabTest.tested_at.asc()).limit(30)
    db_tests = (await db.scalars(tests_stmt)).all()

    values: list[float] = []
    points: list[dict[str, Any]] = []

    for idx, t in enumerate(db_tests, start=1):
        if t.result_value is not None:
            val = float(t.result_value)
            values.append(val)
            dt_str = t.tested_at.strftime("%d/%m %H:%M") if t.tested_at else f"Run {idx}"
            op_name = t.tested_by.full_name if t.tested_by else "Analista"
            points.append(
                {
                    "run_number": idx,
                    "measured_at": dt_str,
                    "value": round(val, 3),
                    "operator_name": op_name,
                }
            )

    n = len(values)
    violations: list[WestgardViolation] = []
    point_violations: list[str | None] = []

    if n == 0:
        mean_val = None
        std_dev = None
        w_upper = None
        w_lower = None
        a_upper = None
        a_lower = None
    elif n == 1:
        mean_val = values[0]
        std_dev = None
        w_upper = None
        w_lower = None
        a_upper = None
        a_lower = None
        point_violations = [None]
    else:
        mean_val = sum(values) / n
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        std_dev = math.sqrt(variance)
        w_upper = round(mean_val + 2.0 * std_dev, 3)
        w_lower = round(mean_val - 2.0 * std_dev, 3)
        a_upper = round(mean_val + 3.0 * std_dev, 3)
        a_lower = round(mean_val - 3.0 * std_dev, 3)
        point_violations, violations = _evaluate_westgard(values, mean_val, std_dev)

    qc_points: list[QualityControlPoint] = []
    for i, p in enumerate(points):
        qc_points.append(
            QualityControlPoint(
                run_number=p["run_number"],
                measured_at=p["measured_at"],
                value=p["value"],
                operator_name=p["operator_name"],
                violation=point_violations[i] if i < len(point_violations) else None,
            )
        )

    data_quality = "sufficient" if n >= 20 else "insufficient"

    return QualityControlAnalyticsOut(
        method_id=selected_method.id if selected_method else None,
        method_name=method_name,
        parameter_name="Concentração / Determinação Quantitativa",
        unit=unit,
        mean=round(mean_val, 3) if mean_val is not None else None,
        standard_deviation=round(std_dev, 3) if std_dev is not None else None,
        warning_limit_upper=w_upper,
        warning_limit_lower=w_lower,
        action_limit_upper=a_upper,
        action_limit_lower=a_lower,
        data_points=qc_points,
        violations=violations,
        data_quality=data_quality,
    )
