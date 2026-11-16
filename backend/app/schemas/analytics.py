"""Schemas Pydantic para Painéis Gerenciais e Indicadores de BI / Metrologia (Fase 5 / Sprint 5.1).

Conforme ISO/IEC 17025:2017 (§8.8, §7.7) e boas práticas laboratoriais (ALCOA+).
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TurnaroundTimeMetrics(BaseModel):
    """Métricas de tempos de ciclo (Turnaround Time - TAT) em horas."""

    global_avg_hours: float | None = Field(None, description="Tempo médio global de recebimento até laudo final.")
    receipt_to_testing_avg_hours: float | None = Field(None, description="Tempo médio de recebimento até primeiro ensaio.")
    testing_to_review_avg_hours: float | None = Field(None, description="Tempo médio de ensaio até revisão técnica.")
    review_to_report_avg_hours: float | None = Field(None, description="Tempo médio de revisão até emissão de laudo.")
    samples_measured_count: int = Field(0, description="Amostras consideradas no cálculo de TAT.")
    data_quality: str = Field("insufficient", description="Qualidade dos dados: sufficient ou insufficient.")


class SampleBacklogMetrics(BaseModel):
    """Estratificação etária do backlog de amostras em processamento."""

    age_0_to_5_days: int = Field(0, description="Amostras ativas com até 5 dias de chegada.")
    age_6_to_15_days: int = Field(0, description="Amostras ativas com 6 a 15 dias de chegada.")
    age_above_15_days: int = Field(0, description="Amostras ativas com mais de 15 dias (risco de atraso).")
    total_active: int = Field(0, description="Total de amostras ativas em aberto.")


class TestConformityMetrics(BaseModel):
    """Estatísticas globais de conformidade técnica e ensaios."""

    total_tests: int = Field(0, description="Total de ensaios cadastrados.")
    conforming_count: int = Field(0, description="Ensaios aprovados / conformes.")
    non_conforming_count: int = Field(0, description="Ensaios reprovados / não conformes.")
    inconclusive_count: int = Field(0, description="Ensaios na faixa de guarda / inconclusivos.")
    pending_count: int = Field(0, description="Ensaios em execução ou pendentes.")
    conformity_rate_pct: float | None = Field(None, description="Percentual de conformidade analítica.")
    data_quality: str = Field("insufficient", description="Qualidade dos dados: sufficient ou insufficient.")


class CapaMetrics(BaseModel):
    """Indicadores de gestão de não conformidades e eficácia CAPA (ISO 17025 §8.7)."""

    total_capas: int = Field(0, description="Total de ações CAPA registradas.")
    open_capas: int = Field(0, description="CAPAs em aberto ou em investigação.")
    closed_capas: int = Field(0, description="CAPAs concluídas.")
    effective_capas: int = Field(0, description="CAPAs avaliadas como eficazes.")
    ineffective_capas: int = Field(0, description="CAPAs avaliadas como ineficazes.")
    effectiveness_rate_pct: float | None = Field(None, description="Percentual de eficácia de planos de ação.")
    data_quality: str = Field("insufficient", description="Qualidade dos dados: sufficient ou insufficient.")


class AnalystWorkloadItem(BaseModel):
    """Carga de trabalho individual por analista/técnico."""

    user_id: UUID
    full_name: str
    active_tests_count: int
    completed_tests_count: int


class OperationalAnalyticsOut(BaseModel):
    """Payload consolidado de BI operacional do laboratório."""

    turnaround_time: TurnaroundTimeMetrics
    sample_backlog: SampleBacklogMetrics
    test_conformity: TestConformityMetrics
    capa_metrics: CapaMetrics
    analysts_workload: list[AnalystWorkloadItem] = Field(default_factory=list)
    equipment_status_summary: dict[str, int] = Field(default_factory=dict)


class QualityControlPoint(BaseModel):
    """Ponto de medição para Carta de Controle de Shewhart / Levey-Jennings."""

    run_number: int
    measured_at: str
    value: float
    operator_name: str
    violation: str | None = None


class WestgardViolation(BaseModel):
    """Registro de quebra de regra de controle estatístico de processo (Westgard)."""

    rule_code: str
    description: str
    run_numbers: list[int]
    severity: str = "WARNING"  # WARNING ou ALARM


class QualityControlAnalyticsOut(BaseModel):
    """Payload metrológico para Carta de Controle e Regras de Westgard (ISO 17025 §7.7)."""

    method_id: UUID | None
    method_name: str
    parameter_name: str
    unit: str
    mean: float | None = None
    standard_deviation: float | None = None
    warning_limit_upper: float | None = None  # +2s
    warning_limit_lower: float | None = None  # -2s
    action_limit_upper: float | None = None   # +3s
    action_limit_lower: float | None = None   # -3s
    data_points: list[QualityControlPoint] = Field(default_factory=list)
    violations: list[WestgardViolation] = Field(default_factory=list)
    data_quality: str = Field("insufficient", description="Qualidade dos dados: sufficient ou insufficient.")
