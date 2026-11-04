"""Serialização determinística usada na cadeia de auditoria.

A mesma função é usada ao gravar e ao verificar. Qualquer alteração no
algoritmo invalida a cadeia inteira — por isso ela é versionada.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

CANONICALIZATION_VERSION = "lims-canon-v1"


def jsonable(value: Any) -> Any:
    """Converte tipos do domínio em tipos JSON estritos."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return jsonable(value.value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        # Representação decimal sem notação científica, preservando escala.
        return format(value, "f")
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
