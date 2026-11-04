"""RBAC central — usado pela API e exposto ao front-end em /auth/me."""

from __future__ import annotations

from app.models.enums import UserRole

# Permissões funcionais (o front-end esconde ações; a API SEMPRE revalida).
ROLE_PERMISSIONS: dict[UserRole, list[str]] = {
    UserRole.ADMIN: ["*"],
    UserRole.FISCAL: [
        "samples:read",
        "samples:create",
        "samples:update",
        "custody:read",
        "custody:transfer",
        "tests:read",
        "tests:create",
        "capa:read",
        "capa:create",
        "capa:update",
        "users:read",
    ],
    UserRole.TECNICO: [
        "samples:read",
        "samples:create",
        "samples:update",
        "custody:read",
        "custody:transfer",
        "tests:read",
        "tests:create",
        "tests:sign",
        "capa:read",
        "capa:create",
        "capa:update",
        "users:read",
    ],
    UserRole.CUSTODIANTE: [
        "samples:read",
        "custody:read",
        "custody:transfer",
        "tests:read",
        "users:read",
    ],
    UserRole.AUDITOR: [
        "samples:read",
        "custody:read",
        "tests:read",
        "capa:read",
        "audit:read",
        "audit:verify",
        "users:read",
    ],
}

WRITE_ROLES = (UserRole.ADMIN, UserRole.FISCAL, UserRole.TECNICO)
