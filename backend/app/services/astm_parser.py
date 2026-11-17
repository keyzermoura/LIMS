"""Parser de Protocolo ASTM E1381 / E1394 para Analisadores Laboratoriais (H3.3).

Conforme ESPECIFICACAO_CAMADA_INTEGRACAO_LIMS.md §5.2 e ISO/IEC 17025 §7.11.
Suporta mensagens de analisadores clínicos, hematológicos e bioquímicos:
- H: Header (Identificação do remetente e instrumento)
- P: Patient / Sample (Identificação da amostra e lote)
- O: Order (Solicitação / Pedido do ensaio)
- R: Result (Grandeza medida, unidade, faixas e status)
- L: Terminator (Fim da transmissão)
"""

from __future__ import annotations

import re
from typing import Any

from app.core.errors import ValidationDomainError


def parse_astm_e1394(raw_text: str) -> dict[str, Any]:
    """Interpreta fluxo de registros delimitados no padrão ASTM E1394."""
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        raise ValidationDomainError("Fluxo de dados ASTM está vazio.")

    # Remove caracteres de controle de transporte (ENQ, ACK, STX, ETX, EOT, CR, LF)
    cleaned_lines: list[str] = []
    for line in lines:
        cleaned = re.sub(r"[\x01-\x1f\x7f]", "", line).strip()
        if cleaned:
            cleaned_lines.append(cleaned)

    if not cleaned_lines:
        raise ValidationDomainError("Nenhum registro legível no fluxo ASTM.")

    header_info: dict[str, Any] = {}
    sample_info: dict[str, Any] = {}
    order_info: dict[str, Any] = {}
    results: list[dict[str, Any]] = []

    delimiter = "|"

    for line in cleaned_lines:
        parts = line.split(delimiter)
        record_type = parts[0].upper()

        if record_type == "H":
            # Header record: H|\^&|||SenderName^Model^Firmware|||||||P|1394-97
            header_info = {
                "record_type": "HEADER",
                "delimiters": parts[1] if len(parts) > 1 else "",
                "sender": parts[4] if len(parts) > 4 else "UNKNOWN_INSTRUMENT",
                "version": parts[12] if len(parts) > 12 else "ASTM-1394",
            }
        elif record_type == "P":
            # Patient / Sample record: P|1||SampleID||||||||||
            sample_info = {
                "sequence": parts[1] if len(parts) > 1 else "1",
                "sample_id": parts[3] if len(parts) > 3 else (parts[2] if len(parts) > 2 else "UNKNOWN"),
            }
        elif record_type == "O":
            # Order record: O|1|SampleBarcode||^^^TestCode||||||||||
            order_info = {
                "sequence": parts[1] if len(parts) > 1 else "1",
                "specimen_id": parts[2] if len(parts) > 2 else "",
                "test_code": parts[4].replace("^", "").strip() if len(parts) > 4 else "",
            }
        elif record_type == "R":
            # Result record: R|1|^^^TestParam|Value|Units|RefRange|AbnormalFlag|NatureAbnormal|Status
            test_param = parts[2].replace("^", " ").strip() if len(parts) > 2 else "UNKNOWN"
            value_str = parts[3].strip() if len(parts) > 3 else ""
            units = parts[4].strip() if len(parts) > 4 else ""
            ref_range = parts[5].strip() if len(parts) > 5 else None
            abnormal_flag = parts[6].strip() if len(parts) > 6 else "N"
            result_status = parts[8].strip() if len(parts) > 8 else "F"

            try:
                numeric_val = float(value_str.replace(",", "."))
            except ValueError:
                numeric_val = None

            results.append({
                "parameter": test_param,
                "value_raw": value_str,
                "value_numeric": numeric_val,
                "units": units,
                "reference_range": ref_range,
                "abnormal_flag": abnormal_flag,
                "status": result_status,
            })

    if not results:
        raise ValidationDomainError("Nenhum registro de resultado ('R') foi encontrado na mensagem ASTM.")

    return {
        "instrument_type": "ANALISADOR_ASTM_E1394",
        "header": header_info,
        "sample": sample_info,
        "order": order_info,
        "results_count": len(results),
        "results": results,
    }
