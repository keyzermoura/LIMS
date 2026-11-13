"""Modelos de Anexos e Evidências de Bancada (Fase 3 / M3.3).

Armazena arquivos brutos (fotos do ensaio, curvas de aquisição de dados,
relatórios de instrumentos e certificados RBC) vinculados de forma indissociável
ao ensaio analítico com hash criptográfico SHA-256 (ALCOA+).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, utcnow

if TYPE_CHECKING:
    from app.models.lab_test import LabTest
    from app.models.test_execution import TestExecution
    from app.models.user import User


class TestAttachment(UUIDPrimaryKeyMixin, Base):
    """Evidência documental ou dado bruto anexado à execução analítica."""

    __tablename__ = "test_attachments"

    lab_test_id: Mapped[UUID] = mapped_column(
        ForeignKey("lab_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("test_executions.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    uploaded_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )

    # Relacionamentos
    lab_test: Mapped[LabTest] = relationship("LabTest", back_populates="attachments")
    execution: Mapped[TestExecution | None] = relationship("TestExecution", lazy="selectin")
    uploaded_by: Mapped[User] = relationship(
        "User", foreign_keys=[uploaded_by_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TestAttachment {self.filename} ({self.file_size} bytes, sha256={self.sha256_hash[:8]})>"
