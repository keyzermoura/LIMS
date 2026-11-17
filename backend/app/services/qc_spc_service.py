"""Serviço de Controle Estatístico de Processo e Regras de Westgard (H2.5).

Implementa:
- Regras múltiplas de Westgard (1_2s, 1_3s, 2_2s, R_4s, 4_1s, 10_x)
- Gráfico e estatística de Levey-Jennings
- Intertravamento com report_service.py (ISO 17025 §7.7.1)
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.db.dialect import next_sequence
from app.models.base import utcnow
from app.models.enums import AuditAction, AuditEntity, QCStatus
from app.models.qc_spc import QCRun
from app.models.test_method import TestMethod
from app.models.user import User
from app.schemas.qc_spc import LeveyJenningsChartData, LeveyJenningsPoint, QCRunCreate, QCRunResolve
from app.services import audit_service


def evaluate_westgard_rules(
    historical_z_scores: list[float], new_z_score: float
) -> tuple[QCStatus, list[str]]:
    """Avalia o novo ponto contra o histórico aplicando as 6 regras clássicas de Westgard.

    Regras:
    1. 1_2s (Aviso): |z| > 2.0 (sinaliza alerta, não bloqueia isoladamente)
    2. 1_3s (Rejeição Randômica): |z| > 3.0 (rejeição analítica imediata)
    3. 2_2s (Rejeição Sistemática): 2 pontos consecutivos com z > 2.0 ou ambos com z < -2.0
    4. R_4s (Rejeição Randômica): Dois pontos consecutivos onde um está > +2s e o outro < -2s (amplitude >= 4s)
    5. 4_1s (Rejeição Sistemática): 4 pontos consecutivos no mesmo lado além de ±1s (todos > 1.0 ou todos < -1.0)
    6. 10_x (Rejeição por Viés): 10 pontos consecutivos no mesmo lado da média (todos > 0 ou todos < 0)
    """
    violations: list[str] = []
    has_alarm = False
    has_warning = False

    series = historical_z_scores + [new_z_score]
    n = len(series)

    # 1. Regra 1_3s (Alarme Crítico)
    if abs(new_z_score) > 3.0:
        violations.append("1_3s")
        has_alarm = True

    # 2. Regra 1_2s (Warning) - se não for 1_3s
    elif abs(new_z_score) > 2.0:
        violations.append("1_2s")
        has_warning = True

    # 3. Regra 2_2s (Alarme Sistemático)
    if n >= 2:
        last2 = series[-2:]
        if (last2[0] > 2.0 and last2[1] > 2.0) or (last2[0] < -2.0 and last2[1] < -2.0):
            violations.append("2_2s")
            has_alarm = True

    # 4. Regra R_4s (Alarme Randômico)
    if n >= 2:
        last2 = series[-2:]
        if (last2[0] > 2.0 and last2[1] < -2.0) or (last2[0] < -2.0 and last2[1] > 2.0):
            violations.append("R_4s")
            has_alarm = True

    # 5. Regra 4_1s (Alarme Sistemático / Deslocamento)
    if n >= 4:
        last4 = series[-4:]
        if all(z > 1.0 for z in last4) or all(z < -1.0 for z in last4):
            violations.append("4_1s")
            has_alarm = True

    # 6. Regra 10_x (Alarme de Tendência / Drift)
    if n >= 10:
        last10 = series[-10:]
        if all(z > 0.0 for z in last10) or all(z < 0.0 for z in last10):
            violations.append("10_x")
            has_alarm = True

    # Determinação do Status Final
    if has_alarm:
        return QCStatus.REJECTED, violations
    if has_warning:
        return QCStatus.WARNING, violations
    return QCStatus.CONFORMING, violations


async def record_qc_run(
    db: AsyncSession,
    *,
    payload: QCRunCreate,
    actor: User,
    context: RequestContext,
) -> QCRun:
    """Registra uma medição de Controle de Qualidade Interno (CQI) e avalia regras de Westgard."""
    method = await db.get(TestMethod, payload.method_id)
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de ensaio não encontrado.",
        )

    # Busca histórico recente de z-scores desse método para análise de série temporal
    stmt = (
        select(QCRun.z_score)
        .where(QCRun.method_id == payload.method_id)
        .order_by(QCRun.run_at.asc())
        .limit(20)
    )
    history_z = list(await db.scalars(stmt))

    # Cálculo do z-score do ponto atual
    z_score = (payload.measured_value - payload.target_mean) / payload.target_sd
    qc_status_result, violations = evaluate_westgard_rules(history_z, z_score)

    now = utcnow()
    seq = await next_sequence(db, "qc_run_seq")
    code = f"CQI-{now.year}-{seq:04d}"

    run = QCRun(
        code=code,
        method_id=method.id,
        equipment_id=payload.equipment_id,
        reagent_batch_id=payload.reagent_batch_id,
        operator_id=actor.id,
        run_at=now,
        target_mean=payload.target_mean,
        target_sd=payload.target_sd,
        measured_value=payload.measured_value,
        z_score=round(z_score, 3),
        status=qc_status_result,
        violation_rules=violations,
        is_active_violation=(qc_status_result == QCStatus.REJECTED),
        corrective_notes=payload.notes,
        version=1,
    )
    db.add(run)
    await db.flush()

    # Trilha de Auditoria
    await audit_service.append(
        db,
        action=AuditAction.CREATE,
        entity_type=AuditEntity.QC_RUN.value,
        entity_id=run.id,
        actor=actor,
        new_value={
            "code": run.code,
            "method_code": method.code,
            "measured_value": run.measured_value,
            "z_score": run.z_score,
            "status": run.status.value,
            "violations": run.violation_rules,
        },
        reason=f"Registro de CQI {run.code} com avaliação multiregra de Westgard",
        context=context,
    )
    await db.commit()
    await db.refresh(run)
    return run


async def list_qc_runs(
    db: AsyncSession,
    *,
    method_id: UUID | None = None,
    status_filter: QCStatus | None = None,
    is_active_violation: bool | None = None,
) -> Sequence[QCRun]:
    """Lista corridas de CQI com opções de filtros analíticos."""
    stmt = (
        select(QCRun)
        .options(
            selectinload(QCRun.method),
            selectinload(QCRun.operator),
            selectinload(QCRun.equipment),
            selectinload(QCRun.reagent_batch),
        )
        .order_by(QCRun.run_at.desc())
    )
    if method_id is not None:
        stmt = stmt.where(QCRun.method_id == method_id)
    if status_filter is not None:
        stmt = stmt.where(QCRun.status == status_filter)
    if is_active_violation is not None:
        stmt = stmt.where(QCRun.is_active_violation == is_active_violation)
    result = await db.scalars(stmt)
    return result.all()


async def get_qc_chart_data(db: AsyncSession, method_id: UUID) -> LeveyJenningsChartData:
    """Consolida os pontos e estatísticas para a Carta de Controle de Levey-Jennings."""
    method = await db.get(TestMethod, method_id)
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de ensaio não encontrado.",
        )

    stmt = (
        select(QCRun)
        .options(selectinload(QCRun.operator))
        .where(QCRun.method_id == method_id)
        .order_by(QCRun.run_at.asc())
    )
    runs = (await db.scalars(stmt)).all()

    if runs:
        latest = runs[-1]
        target_mean = latest.target_mean
        target_sd = latest.target_sd
    else:
        target_mean = 0.0
        target_sd = 1.0

    points: list[LeveyJenningsPoint] = []
    active_rej = 0
    active_war = 0

    for r in runs:
        if r.status == QCStatus.REJECTED and r.is_active_violation:
            active_rej += 1
        elif r.status == QCStatus.WARNING:
            active_war += 1

        points.append(
            LeveyJenningsPoint(
                run_id=r.id,
                code=r.code,
                run_at=r.run_at.strftime("%d/%m %H:%M"),
                measured_value=r.measured_value,
                z_score=r.z_score,
                status=r.status,
                violation_rules=r.violation_rules,
                operator_name=r.operator.full_name if r.operator else "Operador",
            )
        )

    return LeveyJenningsChartData(
        method_id=method.id,
        method_name=method.name,
        target_mean=round(target_mean, 3),
        target_sd=round(target_sd, 3),
        plus_1s=round(target_mean + 1.0 * target_sd, 3),
        minus_1s=round(target_mean - 1.0 * target_sd, 3),
        plus_2s=round(target_mean + 2.0 * target_sd, 3),
        minus_2s=round(target_mean - 2.0 * target_sd, 3),
        plus_3s=round(target_mean + 3.0 * target_sd, 3),
        minus_3s=round(target_mean - 3.0 * target_sd, 3),
        points=points,
        total_runs=len(runs),
        active_rejections=active_rej,
        active_warnings=active_war,
    )


async def resolve_qc_violation(
    db: AsyncSession,
    *,
    run_id: UUID,
    payload: QCRunResolve,
    actor: User,
    context: RequestContext,
) -> QCRun:
    """Registra parecer corretivo e desativa a flag de bloqueio da corrida de controle."""
    run = await db.get(QCRun, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corrida de CQI não encontrada.",
        )

    run.is_active_violation = False
    run.corrective_notes = payload.corrective_notes
    run.version += 1

    await audit_service.append(
        db,
        action=AuditAction.UPDATE,
        entity_type=AuditEntity.QC_RUN.value,
        entity_id=run.id,
        actor=actor,
        new_value={"is_active_violation": False, "corrective_notes": run.corrective_notes},
        reason=f"Resolução técnica da violação da corrida CQI {run.code}",
        context=context,
    )
    await db.commit()
    await db.refresh(run)
    return run


async def check_method_has_active_violation(
    db: AsyncSession, method_id: UUID
) -> tuple[bool, str | None]:
    """Intertravamento: Verifica se o método analítico possui corrida de CQI rejeitada e não corrigida."""
    active_rej = await db.scalar(
        select(QCRun)
        .where(
            QCRun.method_id == method_id,
            QCRun.status == QCStatus.REJECTED,
            QCRun.is_active_violation == True,  # noqa: E712
        )
        .order_by(QCRun.run_at.desc())
        .limit(1)
    )
    if active_rej:
        rules_str = ", ".join(active_rej.violation_rules)
        return True, (
            f"Corrida de Controle {active_rej.code} violou regra(s) de Westgard [{rules_str}] "
            f"(z-score={active_rej.z_score:.2f}) e permanece ativa sem liberação técnica."
        )
    return False, None
