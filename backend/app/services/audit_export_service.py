"""Exportação assinada da trilha de auditoria.

O bundle ZIP entregue ao auditor contém:

  * ``manifest.json`` — escopo, contagem, âncora/cabeça da cadeia e hashes;
  * ``events.jsonl`` — registros canônicos, um por linha (dado verificável);
  * ``events.csv`` ou ``events.json`` — apresentação legível do recorte.

O manifesto é autenticado com a mesma chave HMAC da trilha. A verificação
recalcula hash/HMAC de cada registro, confere o conteúdo dos arquivos e ancora
a cabeça exportada no banco atual. Assim, um arquivo entregue a um inspetor
pode ser validado mesmo fora da aplicação, desde que a chave seja conhecida
pelo verificador.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from dataclasses import dataclass
from typing import Any, Literal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext
from app.core.errors import ValidationDomainError
from app.core.security import constant_time_equals, hmac_sha256, sha256_hex
from app.core.serialization import CANONICALIZATION_VERSION, canonical_json, jsonable
from app.models.audit_log import AuditLog
from app.models.base import utcnow
from app.models.user import User
from app.services import audit_service

EXPORT_FORMAT = "lims-audit-export-v1"
PRESENTATION_NAMES: dict[str, str] = {"csv": "events.csv", "json": "events.json"}
ExportFormat = Literal["csv", "json"]

CSV_FIELDS = (
    "sequence",
    "occurred_at",
    "actor_username",
    "actor_role",
    "action",
    "entity_type",
    "entity_id",
    "reason",
    "ip_address",
    "request_id",
    "signature_id",
    "prev_hash",
    "hash",
    "hmac",
    "payload",
    "old_value",
    "new_value",
)


@dataclass(slots=True, frozen=True)
class ExportBundle:
    content: bytes
    filename: str
    manifest: dict[str, Any]
    manifest_hash: str
    hmac: str
    artifact_sha256: str


# --------------------------------------------------------------------------
# Serialização
# --------------------------------------------------------------------------
def _record(row: AuditLog) -> dict[str, Any]:
    """Representação completa e estável de um evento para o arquivo."""
    return {
        "id": row.id,
        "sequence": row.sequence,
        "occurred_at": jsonable(row.occurred_at),
        "actor_id": str(row.actor_id) if row.actor_id else None,
        "actor_username": row.actor_username,
        "actor_role": row.actor_role,
        "action": row.action.value if hasattr(row.action, "value") else str(row.action),
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "old_value": jsonable(row.old_value),
        "new_value": jsonable(row.new_value),
        "reason": row.reason,
        "payload": jsonable(row.payload),
        "ip_address": row.ip_address,
        "user_agent": row.user_agent,
        "request_id": row.request_id,
        "signature_id": str(row.signature_id) if row.signature_id else None,
        "prev_hash": row.prev_hash,
        "hash": row.hash,
        "hmac": row.hmac,
    }


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return canonical_json(value)
    return str(value)


def _csv_bytes(records: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_FIELDS,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for record in records:
        writer.writerow({field: _csv_cell(record.get(field)) for field in CSV_FIELDS})
    # Sem BOM: o CSV é uma apresentação; o arquivo canônico é o JSONL.
    return buffer.getvalue().encode("utf-8")


def _json_bytes(records: list[dict[str, Any]]) -> bytes:
    return (
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _zip_bytes(
    manifest_bytes: bytes, data_bytes: bytes, presentation_name: str, presentation_bytes: bytes
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        archive.writestr("events.jsonl", data_bytes)
        archive.writestr(presentation_name, presentation_bytes)
    return buffer.getvalue()


def _scope(filters: dict[str, Any]) -> dict[str, Any]:
    actor_id = filters.get("actor_id")
    action = filters.get("action")
    return {
        "entity_type": filters.get("entity_type"),
        "entity_id": filters.get("entity_id"),
        "actor_id": str(actor_id) if actor_id else None,
        "action": getattr(action, "value", action),
        "date_from": jsonable(filters.get("date_from")),
        "date_to": jsonable(filters.get("date_to")),
        "search": filters.get("search"),
    }


def _has_scope(scope: dict[str, Any]) -> bool:
    return any(value not in (None, "") for value in scope.values())


# --------------------------------------------------------------------------
# Exportação
# --------------------------------------------------------------------------
async def export_bundle(
    db: AsyncSession,
    *,
    actor: User,
    filters: dict[str, Any],
    fmt: ExportFormat,
    context: RequestContext | None = None,
) -> ExportBundle:
    stmt = audit_service.filtered_query(
        entity_type=filters.get("entity_type"),
        entity_id=filters.get("entity_id"),
        actor_id=filters.get("actor_id"),
        action=filters.get("action"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        search=filters.get("search"),
    )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    if total > settings.AUDIT_EXPORT_MAX_RECORDS:
        raise ValidationDomainError(
            "O recorte excede o limite de exportação. Aplique filtros mais "
            "restritos e tente novamente.",
            details={
                "records": int(total),
                "max_records": settings.AUDIT_EXPORT_MAX_RECORDS,
            },
        )

    rows = (
        await db.execute(stmt.order_by(AuditLog.sequence.asc()))
    ).scalars().all()
    records = [_record(row) for row in rows]

    now = utcnow()
    export_id = uuid4()
    key = settings.AUDIT_HMAC_KEY.get_secret_value()

    data_bytes = _jsonl_bytes(records)
    presentation_name = PRESENTATION_NAMES[fmt]
    presentation_bytes = (
        _csv_bytes(records) if fmt == "csv" else _json_bytes(records)
    )

    data_sha256 = sha256_hex(data_bytes)
    data_hmac = hmac_sha256(key, data_sha256)
    presentation_sha256 = sha256_hex(presentation_bytes)

    first = records[0] if records else None
    head = records[-1] if records else None

    core: dict[str, Any] = {
        "format": EXPORT_FORMAT,
        "export_id": str(export_id),
        "generated_at": jsonable(now),
        "generated_by": {
            "id": str(actor.id),
            "username": actor.username,
            "role": actor.role.value,
        },
        "scope": _scope(filters),
        "presentation": fmt,
        "record_count": len(records),
        "first_sequence": first["sequence"] if first else None,
        "last_sequence": head["sequence"] if head else None,
        "head_hash": head["hash"] if head else None,
        "head_hmac": head["hmac"] if head else None,
        "chain_anchor": (
            {"sequence": first["sequence"] - 1, "hash": first["prev_hash"]}
            if first
            else None
        ),
        "canonicalization": CANONICALIZATION_VERSION,
        "data_file": "events.jsonl",
        "data_sha256": data_sha256,
        "data_hmac": data_hmac,
        "files": [
            {
                "name": "events.jsonl",
                "sha256": data_sha256,
                "size": len(data_bytes),
            },
            {
                "name": presentation_name,
                "sha256": presentation_sha256,
                "size": len(presentation_bytes),
            },
        ],
    }
    manifest_hash = sha256_hex(canonical_json(core))
    manifest: dict[str, Any] = {
        **core,
        "manifest_hash": manifest_hash,
        "hmac": hmac_sha256(key, manifest_hash),
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    content = _zip_bytes(
        manifest_bytes, data_bytes, presentation_name, presentation_bytes
    )
    filename = (
        f"trilha-auditoria-{now.strftime('%Y%m%dT%H%M%SZ')}-"
        f"{str(export_id)[:8]}.zip"
    )

    return ExportBundle(
        content=content,
        filename=filename,
        manifest=manifest,
        manifest_hash=manifest_hash,
        hmac=manifest["hmac"],
        artifact_sha256=sha256_hex(content),
    )


# --------------------------------------------------------------------------
# Verificação do arquivo exportado
# --------------------------------------------------------------------------
def _new_report() -> dict[str, Any]:
    return {
        "ok": False,
        "export_id": None,
        "generated_at": None,
        "generated_by": None,
        "record_count": 0,
        "checked": 0,
        "first_sequence": None,
        "last_sequence": None,
        "head_hash": None,
        "manifest_hash": None,
        "manifest_hash_ok": False,
        "manifest_hmac_ok": False,
        "data_hash_ok": False,
        "data_hmac_ok": False,
        "files_ok": False,
        "chain_ok": False,
        "chain_contiguous": False,
        "chain_gaps": 0,
        "matches_database": False,
        "canonicalization": None,
        "issues": [],
    }


def _issue(
    report: dict[str, Any], sequence: int, kind: str, detail: str
) -> None:
    report["issues"].append(
        {"sequence": sequence, "type": kind, "detail": detail}
    )


async def verify_bundle(db: AsyncSession, content: bytes) -> dict[str, Any]:
    """Valida um ZIP exportado e ancora o resultado no banco atual."""
    report = _new_report()

    if len(content) > settings.AUDIT_EXPORT_MAX_BYTES:
        _issue(
            report,
            0,
            "BUNDLE_TOO_LARGE",
            "O arquivo excede o tamanho máximo aceito para verificação.",
        )
        return report

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except (zipfile.BadZipFile, OSError):
        _issue(
            report,
            0,
            "INVALID_BUNDLE",
            "O arquivo não é um pacote ZIP válido.",
        )
        return report

    with archive:
        infos = archive.infolist()
        if any(info.is_dir() for info in infos):
            _issue(
                report,
                0,
                "INVALID_BUNDLE",
                "O pacote contém diretórios inesperados.",
            )
            return report

        # Limita a expansão antes de descompactar (proteção contra zip bomb).
        expanded = sum(info.file_size for info in infos)
        if expanded > settings.AUDIT_EXPORT_MAX_BYTES:
            _issue(
                report,
                0,
                "BUNDLE_TOO_LARGE",
                "O conteúdo descompactado excede o limite permitido.",
            )
            return report

        names = {info.filename: info for info in infos}
        if "manifest.json" not in names:
            _issue(
                report,
                0,
                "MISSING_FILE",
                "O pacote não contém manifest.json.",
            )
            return report

        try:
            manifest = json.loads(archive.read("manifest.json"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            _issue(
                report,
                0,
                "INVALID_MANIFEST",
                "manifest.json não é um JSON válido.",
            )
            return report
        if not isinstance(manifest, dict):
            _issue(
                report,
                0,
                "INVALID_MANIFEST",
                "manifest.json deve conter um objeto.",
            )
            return report

        report["export_id"] = (
            manifest.get("export_id")
            if isinstance(manifest.get("export_id"), str)
            else None
        )
        report["generated_at"] = (
            manifest.get("generated_at")
            if isinstance(manifest.get("generated_at"), str)
            else None
        )
        report["canonicalization"] = (
            manifest.get("canonicalization")
            if isinstance(manifest.get("canonicalization"), str)
            else None
        )
        generated_by = manifest.get("generated_by")
        if isinstance(generated_by, dict):
            report["generated_by"] = (
                f"{generated_by.get('username', '—')} "
                f"({generated_by.get('role', '—')})"
            )

        if manifest.get("format") != EXPORT_FORMAT:
            _issue(
                report,
                0,
                "UNSUPPORTED_FORMAT",
                "O manifesto não declara o formato de exportação esperado.",
            )

        # 1. O próprio manifesto: hash canônico + HMAC.
        provided_hash = manifest.get("manifest_hash")
        provided_mac = manifest.get("hmac")
        core = {
            key: value
            for key, value in manifest.items()
            if key not in {"manifest_hash", "hmac"}
        }
        expected_hash = sha256_hex(canonical_json(core))
        report["manifest_hash"] = provided_hash if isinstance(provided_hash, str) else None
        report["manifest_hash_ok"] = isinstance(
            provided_hash, str
        ) and constant_time_equals(expected_hash, provided_hash)
        if not report["manifest_hash_ok"]:
            _issue(
                report,
                0,
                "MANIFEST_HASH_MISMATCH",
                "O conteúdo do manifesto não corresponde ao hash declarado.",
            )

        key = settings.AUDIT_HMAC_KEY.get_secret_value()
        report["manifest_hmac_ok"] = (
            isinstance(provided_mac, str)
            and isinstance(provided_hash, str)
            and constant_time_equals(
                hmac_sha256(key, provided_hash), provided_mac
            )
        )
        if not report["manifest_hmac_ok"]:
            _issue(
                report,
                0,
                "MANIFEST_HMAC_MISMATCH",
                "O manifesto não foi autenticado com a chave de integridade.",
            )

        # 2. Arquivo canônico de eventos.
        data_file = manifest.get("data_file")
        if not isinstance(data_file, str) or data_file not in names:
            _issue(
                report,
                0,
                "MISSING_FILE",
                "O arquivo canônico de eventos não está no pacote.",
            )
            return report

        data_bytes = archive.read(data_file)
        data_sha256 = sha256_hex(data_bytes)
        declared_data_hash = manifest.get("data_sha256")
        declared_data_mac = manifest.get("data_hmac")
        report["data_hash_ok"] = isinstance(
            declared_data_hash, str
        ) and constant_time_equals(data_sha256, declared_data_hash)
        report["data_hmac_ok"] = isinstance(
            declared_data_mac, str
        ) and constant_time_equals(
            hmac_sha256(key, data_sha256), declared_data_mac
        )
        if not report["data_hash_ok"]:
            _issue(
                report,
                0,
                "DATA_HASH_MISMATCH",
                "O conteúdo dos eventos não corresponde ao hash declarado.",
            )
        if not report["data_hmac_ok"]:
            _issue(
                report,
                0,
                "DATA_HMAC_MISMATCH",
                "O arquivo de eventos não foi autenticado com a chave de integridade.",
            )

        # 3. Todos os arquivos listados no manifesto.
        files = manifest.get("files")
        files_ok = False
        if isinstance(files, list) and files:
            files_ok = True
            for entry in files:
                if not isinstance(entry, dict) or not isinstance(
                    entry.get("name"), str
                ):
                    files_ok = False
                    _issue(
                        report,
                        0,
                        "INVALID_MANIFEST",
                        "Entrada de arquivo inválida no manifesto.",
                    )
                    continue
                name = entry["name"]
                if name not in names:
                    files_ok = False
                    _issue(
                        report,
                        0,
                        "MISSING_FILE",
                        f"O arquivo {name} não está no pacote.",
                    )
                    continue
                blob = archive.read(name)
                if not constant_time_equals(
                    sha256_hex(blob), str(entry.get("sha256", ""))
                ):
                    files_ok = False
                    _issue(
                        report,
                        0,
                        "FILE_HASH_MISMATCH",
                        f"O arquivo {name} foi alterado após a exportação.",
                    )
                if entry.get("size") != len(blob):
                    files_ok = False
                    _issue(
                        report,
                        0,
                        "FILE_SIZE_MISMATCH",
                        f"O tamanho declarado de {name} não corresponde.",
                    )
        else:
            _issue(
                report,
                0,
                "INVALID_MANIFEST",
                "O manifesto não lista os arquivos do pacote.",
            )
        report["files_ok"] = files_ok

        # 4. Cadeia interna dos registros exportados.
        try:
            text = data_bytes.decode("utf-8")
        except UnicodeDecodeError:
            _issue(
                report,
                0,
                "DATA_FORMAT",
                "O arquivo de eventos não está codificado em UTF-8.",
            )
            return report

        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                _issue(
                    report,
                    0,
                    "DATA_FORMAT",
                    f"A linha {line_number} do arquivo de eventos é inválida.",
                )
                continue
            if not isinstance(record, dict):
                _issue(
                    report,
                    0,
                    "DATA_FORMAT",
                    f"A linha {line_number} não contém um objeto.",
                )
                continue
            records.append(record)

        report["checked"] = len(records)
        report["record_count"] = len(records)

        scope = manifest.get("scope")
        filtered_export = isinstance(scope, dict) and _has_scope(scope)
        chain_ok = True
        chain_gaps = 0
        previous: dict[str, Any] | None = None
        for record in records:
            sequence = record.get("sequence")
            payload = record.get("payload")
            prev_hash = record.get("prev_hash")
            digest = record.get("hash")
            mac = record.get("hmac")
            if (
                not isinstance(sequence, int)
                or not isinstance(payload, dict)
                or not isinstance(prev_hash, str)
                or not isinstance(digest, str)
                or not isinstance(mac, str)
            ):
                chain_ok = False
                _issue(
                    report,
                    sequence if isinstance(sequence, int) else 0,
                    "RECORD_FORMAT",
                    "Registro sem os campos necessários para verificação.",
                )
                continue

            recomputed = sha256_hex(
                f"{sequence}:{prev_hash}:{canonical_json(payload)}"
            )
            if not constant_time_equals(recomputed, digest):
                chain_ok = False
                _issue(
                    report,
                    sequence,
                    "HASH_MISMATCH",
                    "Conteúdo do registro não corresponde ao hash gravado.",
                )
            if not constant_time_equals(hmac_sha256(key, digest), mac):
                chain_ok = False
                _issue(
                    report,
                    sequence,
                    "HMAC_MISMATCH",
                    "Registro não foi autenticado com a chave de integridade.",
                )

            if previous is not None:
                previous_sequence = previous.get("sequence")
                if not isinstance(previous_sequence, int) or sequence <= previous_sequence:
                    chain_ok = False
                    _issue(
                        report,
                        sequence,
                        "SEQUENCE_ORDER",
                        "Os registros não estão em ordem crescente de sequência.",
                    )
                elif sequence == previous_sequence + 1:
                    if prev_hash != previous.get("hash"):
                        chain_ok = False
                        _issue(
                            report,
                            sequence,
                            "PREV_HASH_MISMATCH",
                            "Encadeamento com o registro exportado anterior foi rompido.",
                        )
                else:
                    # Filtros produzem recortes com lacunas naturais; a âncora
                    # de cada lacuna é autenticada pelo HMAC do próprio registro.
                    chain_gaps += 1
                    if not filtered_export:
                        chain_ok = False
                        _issue(
                            report,
                            sequence,
                            "SEQUENCE_GAP",
                            "Há uma lacuna entre registros de uma exportação completa.",
                        )
            previous = record

        report["chain_gaps"] = chain_gaps
        report["chain_contiguous"] = chain_ok and chain_gaps == 0
        report["chain_ok"] = chain_ok

        if report["record_count"] != manifest.get("record_count"):
            _issue(
                report,
                0,
                "RECORD_COUNT_MISMATCH",
                "A quantidade de registros difere da declarada no manifesto.",
            )

        first = records[0] if records else None
        head = records[-1] if records else None
        report["first_sequence"] = first.get("sequence") if first else None
        report["last_sequence"] = head.get("sequence") if head else None
        report["head_hash"] = head.get("hash") if head else None

        if first and report["first_sequence"] != manifest.get("first_sequence"):
            _issue(
                report,
                0,
                "SEQUENCE_RANGE_MISMATCH",
                "A primeira sequência difere da declarada no manifesto.",
            )
        if (
            first
            and not filtered_export
            and report["first_sequence"] != 1
        ):
            _issue(
                report,
                0,
                "SEQUENCE_RANGE_MISMATCH",
                "Uma exportação sem filtros deve começar na sequência 1.",
            )
        if head and report["last_sequence"] != manifest.get("last_sequence"):
            _issue(
                report,
                0,
                "SEQUENCE_RANGE_MISMATCH",
                "A última sequência difere da declarada no manifesto.",
            )
        if head and report["head_hash"] != manifest.get("head_hash"):
            _issue(
                report,
                0,
                "HEAD_MISMATCH",
                "A cabeça exportada difere da declarada no manifesto.",
            )
        if first and isinstance(first.get("sequence"), int):
            anchor = manifest.get("chain_anchor")
            expected_anchor = first["sequence"] - 1
            if (
                not isinstance(anchor, dict)
                or anchor.get("sequence") != expected_anchor
                or anchor.get("hash") != first.get("prev_hash")
            ):
                _issue(
                    report,
                    first["sequence"],
                    "ANCHOR_MISMATCH",
                    "A âncora do recorte não corresponde ao primeiro registro.",
                )

        # 5. Ancoragem no banco atual (detecta restauração de backup antigo,
        #    remoção de registros ou troca de base).
        matches_database = True
        if first and head:
            first_sequence = first.get("sequence")
            last_sequence = head.get("sequence")
            if isinstance(first_sequence, int) and isinstance(last_sequence, int):
                anchor_sequence = first_sequence - 1
                if anchor_sequence == 0:
                    expected_anchor_hash = audit_service.GENESIS_HASH
                else:
                    anchor_hash = await db.scalar(
                        select(AuditLog.hash).where(
                            AuditLog.sequence == anchor_sequence
                        )
                    )
                    if anchor_hash is None:
                        matches_database = False
                        _issue(
                            report,
                            anchor_sequence,
                            "ANCHOR_NOT_FOUND",
                            "O registro âncora do recorte não existe no banco atual.",
                        )
                        expected_anchor_hash = None
                    else:
                        expected_anchor_hash = anchor_hash

                if (
                    expected_anchor_hash is not None
                    and first.get("prev_hash") != expected_anchor_hash
                ):
                    matches_database = False
                    _issue(
                        report,
                        first_sequence,
                        "ANCHOR_MISMATCH",
                        "O registro âncora do banco atual difere do exportado.",
                    )

                head_row = (
                    await db.execute(
                        select(AuditLog.hash, AuditLog.hmac).where(
                            AuditLog.sequence == last_sequence
                        )
                    )
                ).first()
                if head_row is None:
                    matches_database = False
                    _issue(
                        report,
                        last_sequence,
                        "HEAD_NOT_IN_DB",
                        "A cabeça exportada não existe no banco atual.",
                    )
                elif (
                    head_row.hash != head.get("hash")
                    or head_row.hmac != head.get("hmac")
                ):
                    matches_database = False
                    _issue(
                        report,
                        last_sequence,
                        "HEAD_MISMATCH",
                        "A cabeça exportada difere do registro correspondente no banco.",
                    )

        report["matches_database"] = matches_database

    report["ok"] = not report["issues"] and all(
        (
            report["manifest_hash_ok"],
            report["manifest_hmac_ok"],
            report["data_hash_ok"],
            report["data_hmac_ok"],
            report["files_ok"],
            report["chain_ok"],
            report["matches_database"],
        )
    )
    return report


__all__ = [
    "EXPORT_FORMAT",
    "ExportBundle",
    "export_bundle",
    "verify_bundle",
]
