"""Configuração central da aplicação (12-factor, via variáveis de ambiente).

Nenhum segredo é versionado: os valores padrão abaixo são explicitamente
inseguros e o `model_validator` impede a inicialização com eles em produção.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Chaves de desenvolvimento. Em produção DEVEM ser substituídas por segredos
# gerenciados (AWS Secrets Manager / Vault / KMS).
_DEV_JWT_SECRET = "dev-insecure-jwt-secret-change-me-please-32bytes"
_DEV_AUDIT_KEY = "dev-insecure-audit-hmac-key-change-me-32bytes"
_DEV_QR_KEY = "dev-insecure-qr-signing-key-change-me-32bytes"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "LIMS — Fiscalização Pós-Mercado de Dispositivos Médicos"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Banco de dados -------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://lims:lims@localhost:5432/lims"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE_SECONDS: int = 1800

    # --- Sessão / JWT ---------------------------------------------------
    JWT_SECRET: SecretStr = SecretStr(_DEV_JWT_SECRET)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_HOURS: int = 12
    # Janela máxima para o usuário "assinar" após reautenticar (Part 11).
    ESIGNATURE_TTL_SECONDS: int = 300

    # --- Integridade ----------------------------------------------------
    AUDIT_HMAC_KEY: SecretStr = SecretStr(_DEV_AUDIT_KEY)
    QR_SIGNING_KEY: SecretStr = SecretStr(_DEV_QR_KEY)
    # Limites defensivos para não materializar a trilha inteira em memória.
    AUDIT_EXPORT_MAX_RECORDS: int = 50_000
    AUDIT_EXPORT_MAX_BYTES: int = 25 * 1024 * 1024

    # --- CORS -----------------------------------------------------------
    # Lista separada por vírgula (evita parsing JSON do pydantic-settings).
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Políticas de acesso -------------------------------------------
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    SESSION_IDLE_TIMEOUT_MINUTES: int = 15
    PASSWORD_MIN_LENGTH: int = Field(default=12, ge=8)

    # --- Rate limiting (janela deslizante por processo) -----------------
    # `<= 0` desabilita o limite. Em vários workers o limite efetivo é
    # multiplicado pelo número de processos (ver app/core/ratelimit.py).
    LOGIN_RATE_LIMIT: int = 20
    LOGIN_RATE_WINDOW_SECONDS: int = 60
    SIGN_RATE_LIMIT: int = 20
    SIGN_RATE_WINDOW_SECONDS: int = 60

    # --- Regras de negócio ---------------------------------------------
    AUTO_OPEN_CAPA_ON_FAILURE: bool = True
    AUTO_CREATE_SCHEMA: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _forbid_insecure_defaults_in_prod(self) -> Settings:
        if self.ENVIRONMENT != "prod":
            return self
        unsafe = {
            "JWT_SECRET": _DEV_JWT_SECRET,
            "AUDIT_HMAC_KEY": _DEV_AUDIT_KEY,
            "QR_SIGNING_KEY": _DEV_QR_KEY,
        }
        found = [
            name
            for name, default in unsafe.items()
            if getattr(self, name).get_secret_value() == default
        ]
        if found:
            raise ValueError(
                "Segredos padrão de desenvolvimento detectados em produção: "
                + ", ".join(found)
            )
        if self.DEBUG:
            raise ValueError("DEBUG deve ser False em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
