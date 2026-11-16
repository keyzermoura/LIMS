"""Serviço de Renderização Determinística de Laudos Oficiais e Emendas em PDF (Fase 6 / Sprint 6.1).

Conforme requisitos ISO/IEC 17025:2017 (§7.8 e §7.8.8), 21 CFR Part 11 e ALCOA+.
"""

from __future__ import annotations

import io
from typing import Any

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_official_report_pdf(
    report_number: str,
    title: str,
    conclusion: str,
    summary: str | None,
    version: int,
    is_latest: bool,
    amendment_reason: str | None,
    supersedes_number: str | None,
    sample_data: dict[str, Any],
    tests_data: list[dict[str, Any]],
    issuer_name: str,
    issuer_role: str,
    issued_at_iso: str,
    auth_token: str,
    verify_url: str | None = None,
) -> bytes:
    """Gera um PDF binário formatado e determinístico do laudo pericial oficial."""
    buffer = io.BytesIO()

    # Margens estreitas para caber o laudo em páginas bem aproveitadas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Laudo Pericial {report_number}",
        author=issuer_name,
    )

    styles = getSampleStyleSheet()

    # Estilos customizados
    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=1,  # Centralizado
        textColor=colors.HexColor("#0f172a"),
    )
    header_sub_style = ParagraphStyle(
        "HeaderSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#475569"),
    )
    report_title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#0369a1"),
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=6,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )
    body_bold = ParagraphStyle(
        "ReportBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    conclusion_style = ParagraphStyle(
        "ConclusionText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=colors.white,
    )
    footer_text_style = ParagraphStyle(
        "FooterText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748b"),
    )

    story: list[Any] = []

    # 1. Cabeçalho Institucional
    story.append(Paragraph("ESTADO DE MINAS GERAIS", header_title_style))
    story.append(
        Paragraph(
            "SECRETARIA DE ESTADO DE FAZENDA (SEFI) · FUNDAÇÃO EZEQUIEL DIAS (FUNED)",
            header_sub_style,
        )
    )
    story.append(
        Paragraph(
            "Laboratório de Fiscalização e Metrologia Analítica · Acreditação ISO/IEC 17025",
            header_sub_style,
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10
        )
    )

    # 2. Título do Documento e Faixa de Versão (ISO 17025 §7.8.8)
    story.append(Paragraph(f"LAUDO PERICIAL OFICIAL Nº {report_number}", report_title_style))
    story.append(Paragraph(title, header_sub_style))
    story.append(Spacer(1, 3 * mm))

    is_amendment = version > 1
    if is_amendment:
        version_text = (
            f"<b>EMENDA RETIFICADORA (VERSÃO {version})</b> — Substitui e cancela o laudo nº "
            f"{supersedes_number or 'anterior'} (ISO/IEC 17025 §7.8.8)"
        )
        version_bg = colors.HexColor("#fef3c7")
        version_border = colors.HexColor("#d97706")
        version_color = colors.HexColor("#92400e")
    else:
        version_text = "<b>DOCUMENTO PERICIAL ORIGINAL (VERSÃO 1)</b>"
        version_bg = colors.HexColor("#f0fdf4")
        version_border = colors.HexColor("#16a34a")
        version_color = colors.HexColor("#166534")

    version_table = Table(
        [[Paragraph(f"<font color='{version_color}'>{version_text}</font>", body_style)]],
        colWidths=[18 * cm],
    )
    version_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), version_bg),
                ("BOX", (0, 0), (-1, -1), 1, version_border),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(version_table)
    story.append(Spacer(1, 3 * mm))

    # Justificativa formal da emenda (se aplicável)
    if is_amendment and amendment_reason:
        reason_table = Table(
            [
                [
                    Paragraph(
                        f"<b>Motivação Técnica da Emenda:</b> {amendment_reason}",
                        body_style,
                    )
                ]
            ],
            colWidths=[18 * cm],
        )
        reason_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f59e0b")),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(reason_table)
        story.append(Spacer(1, 3 * mm))

    # 3. Dados Cadastrais da Amostra e Coleta
    story.append(Paragraph("1. DADOS DA AMOSTRA E FISCALIZAÇÃO", section_title_style))
    sample_info_data = [
        [
            Paragraph(f"<b>Nº Registro:</b> {sample_data.get('accession_number', '—')}", body_style),
            Paragraph(f"<b>Lote Fiscal:</b> {sample_data.get('lot_number', '—')}", body_style),
            Paragraph(f"<b>Série:</b> {sample_data.get('serial_number', '—')}", body_style),
        ],
        [
            Paragraph(f"<b>Fabricante / Alvo:</b> {sample_data.get('manufacturer', '—')}", body_style),
            Paragraph(f"<b>Tipo / Apresentação:</b> {sample_data.get('device_type', '—')}", body_style),
            Paragraph(f"<b>Data de Coleta:</b> {sample_data.get('collected_at', '—')}", body_style),
        ],
    ]
    sample_table = Table(sample_info_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    sample_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(sample_table)
    story.append(Spacer(1, 4 * mm))

    # 4. Resultados dos Ensaios Analíticos
    story.append(Paragraph("2. RESULTADOS DOS ENSAIOS LABORATORIAIS", section_title_style))

    tests_header = [
        Paragraph("<b>Ensaio / Procedimento</b>", body_style),
        Paragraph("<b>Especificação Aceitável</b>", body_style),
        Paragraph("<b>Valor Encontrado</b>", body_style),
        Paragraph("<b>Incerteza Exp. (U)</b>", body_style),
        Paragraph("<b>Parecer</b>", body_style),
    ]
    tests_rows = [tests_header]

    for t in tests_data:
        outcome = t.get("outcome", "APROVADO")
        outcome_color = "#16a34a" if outcome == "APROVADO" else "#dc2626"
        uncertainty = t.get("uncertainty_u", "—")
        tests_rows.append(
            [
                Paragraph(t.get("parameter_name", "Ensaio"), body_style),
                Paragraph(t.get("specification", "—"), body_style),
                Paragraph(f"{t.get('result_value', '—')} {t.get('unit', '')}".strip(), body_bold),
                Paragraph(str(uncertainty), body_style),
                Paragraph(f"<font color='{outcome_color}'><b>{outcome}</b></font>", body_style),
            ]
        )

    tests_table = Table(tests_rows, colWidths=[5 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm])
    tests_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("ALIGN", (2, 1), (4, -1), "CENTER"),
            ]
        )
    )
    story.append(tests_table)
    story.append(Spacer(1, 4 * mm))

    # 5. Conclusão Pericial
    story.append(Paragraph("3. CONCLUSÃO PERICIAL", section_title_style))
    if summary:
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 2 * mm))

    is_conforme = "APROVADO" in conclusion.upper() or "CONFORME" in conclusion.upper()
    concl_text = "AMOSTRA EM CONFORMIDADE COM AS ESPECIFICAÇÕES ANALÍTICAS" if is_conforme else "AMOSTRA EM NÃO CONFORMIDADE COM AS ESPECIFICAÇÕES REGULAMENTARES"
    concl_bg = colors.HexColor("#16a34a") if is_conforme else colors.HexColor("#dc2626")

    concl_table = Table([[Paragraph(concl_text, conclusion_style)]], colWidths=[18 * cm])
    concl_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), concl_bg),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(concl_table)
    story.append(Spacer(1, 6 * mm))

    # 6. Assinatura Digital e QR Code de Validação Pública (21 CFR Part 11)
    qr_url = verify_url or f"https://lims.fazenda.mg.gov.br/verify/{auth_token}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    sig_box_content = [
        Paragraph("<b>ASSINATURA ELETRÔNICA QUALIFICADA (21 CFR PART 11)</b>", body_bold),
        Spacer(1, 1 * mm),
        Paragraph(f"<b>Responsável Técnico:</b> {issuer_name} ({issuer_role})", body_style),
        Paragraph(f"<b>Data/Hora de Homologação:</b> {issued_at_iso} UTC", body_style),
        Paragraph(f"<b>Token Criptográfico:</b> <font name='Courier'>{auth_token[:32]}...</font>", body_style),
        Paragraph("Documento emitido com carimbo de tempo inviolável e assinatura baseada em ICP-Brasil / HMAC-SHA256.", footer_text_style),
    ]

    sig_table_data = [
        [
            sig_box_content,
            Image(qr_buffer, width=2.5 * cm, height=2.5 * cm),
        ]
    ]

    sig_table = Table(sig_table_data, colWidths=[15 * cm, 3 * cm])
    sig_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(KeepTogether(sig_table))

    # 7. Construção do PDF
    doc.build(story)
    return buffer.getvalue()
