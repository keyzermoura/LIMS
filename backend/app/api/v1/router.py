"""Agregador da API v1."""

from fastapi import APIRouter

from app.api.v1.routes import (
    attachments,
    audit,
    auth,
    capas,
    checklists,
    custody,
    decisions,
    equipment,
    executions,
    methods,
    qualifications,
    receipts,
    reports,
    reviews,
    samples,
    solicitations,
    tests,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(solicitations.router)
api_router.include_router(receipts.receipts_router)
api_router.include_router(receipts.custody_objects_router)
api_router.include_router(checklists.templates_router)
api_router.include_router(checklists.checklist_eval_router)
api_router.include_router(decisions.decisions_router)
api_router.include_router(decisions.coordination_router)
api_router.include_router(methods.router)
api_router.include_router(equipment.router)
api_router.include_router(executions.test_executions_router)
api_router.include_router(executions.executions_router)
api_router.include_router(reviews.reviews_router)
api_router.include_router(reports.reports_router)
api_router.include_router(attachments.attachments_router)
api_router.include_router(qualifications.router)
api_router.include_router(samples.router)
api_router.include_router(custody.router)
api_router.include_router(tests.router)
api_router.include_router(capas.router)
api_router.include_router(audit.router)
api_router.include_router(users.router)

__all__ = ["api_router"]
