"""
PDF Report Generator.

Creates professional troubleshooting reports using ReportLab,
suitable for viva submission and documentation.
"""

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_pdf_report(
    analysis_data: dict[str, Any],
    user_name: str = "Unknown",
) -> bytes:
    """
    Generate a PDF troubleshooting report.

    Args:
        analysis_data: Dict containing issues, score, explanation, etc.
        user_name: Name of the analyst

    Returns:
        PDF as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#16213e"),
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
        leading=14,
    )
    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
    )

    # ── Title Page ──
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("Network Troubleshooting Report", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f3460")))
    elements.append(Spacer(1, 20))

    title = analysis_data.get("title", "Network Analysis")
    elements.append(Paragraph(f"<b>Analysis:</b> {title}", body_style))
    elements.append(Paragraph(f"<b>Analyst:</b> {user_name}", body_style))
    elements.append(Paragraph(
        f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        body_style,
    ))
    elements.append(Paragraph(
        f"<b>Health Score:</b> {analysis_data.get('health_score', 'N/A')}/100",
        body_style,
    ))

    # ── Health Score Section ──
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Network Health Score", heading_style))

    score = analysis_data.get("health_score", 0)
    score_color = colors.green if score >= 70 else colors.orange if score >= 40 else colors.red

    score_data = [
        ["Score", "Category", "Rating"],
        [
            f"{score}/100",
            "Overall Health",
            "Good" if score >= 70 else "Fair" if score >= 40 else "Poor",
        ],
    ]

    breakdown = analysis_data.get("score_breakdown", {})
    if breakdown:
        for cat in ["routing_score", "interface_score", "vlan_score", "ip_score"]:
            cat_score = breakdown.get(cat, 100)
            cat_label = cat.replace("_score", "").capitalize()
            score_data.append([
                f"{cat_score}%",
                cat_label,
                "OK" if cat_score >= 80 else "Degraded" if cat_score >= 50 else "Critical",
            ])

    score_table = Table(score_data, colWidths=[80, 200, 100])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
    ]))
    elements.append(score_table)

    # ── Detected Issues ──
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Detected Issues", heading_style))

    issues = analysis_data.get("issues", [])
    if not issues:
        elements.append(Paragraph("✅ No issues detected.", body_style))
    else:
        issue_data = [["#", "Severity", "Type", "Device", "Interface"]]
        for i, issue in enumerate(issues, 1):
            issue_data.append([
                str(i),
                issue.get("severity", "").upper(),
                issue.get("failure_type", "").replace("_", " ").title(),
                issue.get("device", "N/A"),
                issue.get("interface", "N/A"),
            ])

        issue_table = Table(issue_data, colWidths=[30, 70, 130, 80, 80])
        issue_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e94560")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff5f5")]),
        ]))
        elements.append(issue_table)

        # Issue details
        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Issue Details", heading_style))
        for i, issue in enumerate(issues, 1):
            elements.append(Paragraph(
                f"<b>Issue #{i}: {issue.get('failure_type', '').replace('_', ' ').title()}</b>",
                body_style,
            ))
            elements.append(Paragraph(f"Detail: {issue.get('detail', 'N/A')}", body_style))
            fix = issue.get("fix_command", "")
            if fix:
                elements.append(Paragraph(f"<b>Fix:</b>", body_style))
                for line in fix.split("\n"):
                    elements.append(Paragraph(f"  <font face='Courier'>{line}</font>", body_style))
            elements.append(Spacer(1, 8))

    # ── Explanation ──
    explanation = analysis_data.get("explanation", "")
    if explanation:
        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Analysis Summary", heading_style))
        for line in explanation.split("\n"):
            if line.strip():
                elements.append(Paragraph(line, body_style))

    # ── Footer ──
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        "Generated by Network Troubleshooting Assistant v1.0",
        small_style,
    ))

    doc.build(elements)
    return buffer.getvalue()
