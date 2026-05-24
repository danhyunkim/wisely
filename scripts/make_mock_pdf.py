"""Generate a mock Fidelity 401(k) statement PDF for end-to-end testing."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def build_pdf(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "title", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1a6e3a")
    )
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13)
    body = styles["BodyText"]

    story = []
    story.append(Paragraph("Fidelity Investments", title))
    story.append(Paragraph("Workplace Savings Plan — Quarterly Statement", h2))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        Paragraph(
            "<b>Account Holder:</b> Jordan A. Sample<br/>"
            "<b>Plan:</b> Acme Corporation 401(k) Plan<br/>"
            "<b>Statement Period:</b> January 1, 2026 — March 31, 2026<br/>"
            "<b>Account Number:</b> ****1234",
            body,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Account Summary by Money Type", h2))
    story.append(Spacer(1, 0.1 * inch))

    data = [
        ["Money Type", "Beginning Balance", "Contributions", "Earnings", "Ending Balance"],
        ["Pre-Tax (Employee)", "$84,210.55", "$2,400.00", "$3,118.42", "$89,728.97"],
        ["Employer Match", "$41,802.10", "$1,200.00", "$1,548.91", "$44,551.01"],
        ["After-Tax (Non-Roth)", "$12,330.40", "$800.00", "$455.18", "$13,585.58"],
        ["Roth 401(k)", "$22,008.15", "$1,000.00", "$812.07", "$23,820.22"],
        ["Total", "$160,351.20", "$5,400.00", "$5,934.58", "$171,685.78"],
    ]
    tbl = Table(data, colWidths=[1.7 * inch, 1.3 * inch, 1.2 * inch, 1.1 * inch, 1.3 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a6e3a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f1ea")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Vesting", h2))
    story.append(
        Paragraph(
            "Employer contributions are subject to a 4-year graded vesting schedule. "
            "You are currently 100% vested.",
            body,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Investment Holdings", h2))
    holdings = [
        ["Fund", "Ticker", "Shares", "Price", "Market Value"],
        ["Fidelity 500 Index Fund", "FXAIX", "412.331", "$192.55", "$79,394.32"],
        ["Fidelity Total Intl Index", "FTIHX", "1,204.118", "$15.84", "$19,073.23"],
        ["Fidelity US Bond Index", "FXNAX", "2,815.667", "$10.12", "$28,494.55"],
        ["Vanguard Target Date 2050", "VFIFX", "1,512.881", "$29.05", "$43,949.20"],
        ["Stable Value Fund", "—", "—", "—", "$774.48"],
    ]
    htbl = Table(holdings, colWidths=[2.3 * inch, 0.9 * inch, 1.0 * inch, 1.0 * inch, 1.3 * inch])
    htbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a6e3a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(htbl)
    story.append(Spacer(1, 0.3 * inch))

    story.append(
        Paragraph(
            "<i>This statement is a mock document generated for software testing. "
            "It is not a real financial statement and does not represent any real account.</i>",
            body,
        )
    )

    doc.build(story)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "samples" / "mock_fidelity_401k.pdf"
    build_pdf(out)
    print(f"Wrote {out}")
