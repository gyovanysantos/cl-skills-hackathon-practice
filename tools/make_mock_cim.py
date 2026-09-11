#!/usr/bin/env python3
"""
Fabricates a mock CIM/SIM PDF for a fictional company, "Northbridge Packaging
Holdings", plus the expected extraction/normalisation JSON fixtures that match
it exactly. Run this script whenever the PDF changes -- it is the single
source of truth for both, so the PDF and the fixtures can never drift apart.

Everything in this file is fabricated for a hackathon practice run. No real
company, deal, or financial data is represented.

Usage:
    python3 tools/make_mock_cim.py
Writes:
    tests/fixtures/mock-cim.pdf
    tests/fixtures/extracted.expected.json
    tests/fixtures/normalised.expected.json
"""
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(HERE, "..", "tests", "fixtures")
PDF_PATH = os.path.join(FIXTURES_DIR, "mock-cim.pdf")
EXTRACTED_PATH = os.path.join(FIXTURES_DIR, "extracted.expected.json")
NORMALISED_PATH = os.path.join(FIXTURES_DIR, "normalised.expected.json")

COMPANY = "Northbridge Packaging Holdings"
UNIT = "USD_millions"

# ---------------------------------------------------------------------------
# The ground-truth financial table. This is what a careful human reader would
# conclude from the PDF. FY2023A's ebitda_adjustments line is deliberately
# ambiguous in the PDF text (a footnoted, disputed one-time item) -- the
# extraction stage is expected to flag it, not silently pick a value.
# ---------------------------------------------------------------------------
HISTORICAL_PERIODS = ["FY2020A", "FY2021A", "FY2022A", "FY2023A", "FY2024A"]
FORECAST_PERIODS = ["FY2025E", "FY2026E", "FY2027E", "FY2028E", "FY2029E", "FY2030E"]
ALL_PERIODS = HISTORICAL_PERIODS + FORECAST_PERIODS

# period -> {row: value or None}
FINANCIALS = {
    "FY2020A": {"net_revenue": 142.3, "gross_profit": 51.9, "reported_ebitda": 18.5, "ebitda_adjustments": 3.2, "adjusted_ebitda": 21.7},
    "FY2021A": {"net_revenue": 156.8, "gross_profit": 57.7, "reported_ebitda": 21.0, "ebitda_adjustments": 2.8, "adjusted_ebitda": 23.8},
    "FY2022A": {"net_revenue": 171.4, "gross_profit": 63.4, "reported_ebitda": 23.9, "ebitda_adjustments": 4.1, "adjusted_ebitda": 28.0},
    # FY2023A ebitda_adjustments is the deliberately ambiguous line -- see footnote (1).
    "FY2023A": {"net_revenue": 189.6, "gross_profit": 70.7, "reported_ebitda": 27.2, "ebitda_adjustments": 5.1, "adjusted_ebitda": 32.3},
    "FY2024A": {"net_revenue": 204.1, "gross_profit": 77.6, "reported_ebitda": 31.8, "ebitda_adjustments": 3.6, "adjusted_ebitda": 35.4},
    "FY2025E": {"net_revenue": 221.0, "gross_profit": 85.1, "reported_ebitda": 35.9, "ebitda_adjustments": 2.0, "adjusted_ebitda": 37.9},
    "FY2026E": {"net_revenue": 239.5, "gross_profit": 93.9, "reported_ebitda": 40.2, "ebitda_adjustments": 1.8, "adjusted_ebitda": 42.0},
    "FY2027E": {"net_revenue": 259.8, "gross_profit": 103.4, "reported_ebitda": 45.1, "ebitda_adjustments": 1.5, "adjusted_ebitda": 46.6},
    "FY2028E": {"net_revenue": 281.9, "gross_profit": 113.7, "reported_ebitda": 50.5, "ebitda_adjustments": 1.2, "adjusted_ebitda": 51.7},
    # Not disclosed in the source deck -- must come through as missing, never invented.
    "FY2029E": {"net_revenue": None, "gross_profit": None, "reported_ebitda": None, "ebitda_adjustments": None, "adjusted_ebitda": None},
    "FY2030E": {"net_revenue": None, "gross_profit": None, "reported_ebitda": None, "ebitda_adjustments": None, "adjusted_ebitda": None},
}

ROW_LABELS = {
    "net_revenue": "Net revenue",
    "gross_profit": "Gross profit",
    "reported_ebitda": "Reported EBITDA",
    "ebitda_adjustments": "Adjustments to EBITDA",
    "adjusted_ebitda": "Adjusted EBITDA",
}

# Page numbers where the real consolidated financial overview lives (1-indexed,
# matching the PDF page count including the cover as page 1).
HISTORICAL_PAGE = 12
FORECAST_PAGE = 13
DECOY_SEGMENT_PAGE = 7
DECOY_MARGIN_PAGE = 8

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=26, leading=32)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceBefore=6, spaceAfter=10)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=4, spaceAfter=8)
body = ParagraphStyle("Body", parent=styles["BodyText"], spaceAfter=8, leading=14)
small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.grey)
confidential = ParagraphStyle("Confidential", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#b91c1c"), spaceAfter=4)


def money_table(periods, financials, footnote_period=None, footnote_row=None, footnote_mark="(1)"):
    """Build a period-by-row financial table flowable."""
    header = ["US$ millions"] + periods
    rows = [header]
    for row_key, label in ROW_LABELS.items():
        line = [label]
        for p in periods:
            v = financials[p][row_key]
            if v is None:
                cell = "N/A"
            else:
                cell = f"{v:,.1f}"
                if footnote_period == p and footnote_row == row_key:
                    cell += f" {footnote_mark}"
            line.append(cell)
        rows.append(line)

    t = Table(rows, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e2130")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def decoy_segment_chart():
    d = Drawing(420, 220)
    chart = VerticalBarChart()
    chart.x, chart.y = 50, 30
    chart.width, chart.height = 340, 170
    chart.data = [[38.4, 29.1, 22.9]]
    chart.categoryAxis.categoryNames = ["Rigid Packaging", "Flexible Packaging", "Specialty Films"]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 45
    chart.bars[0].fillColor = colors.HexColor("#3d7fff")
    d.add(chart)
    d.add(String(50, 205, "FY2024 Segment Revenue Mix (% of total)", fontSize=10))
    return d


def decoy_margin_chart():
    d = Drawing(420, 220)
    chart = LinePlot()
    chart.x, chart.y = 50, 30
    chart.width, chart.height = 340, 170
    years = [2020, 2021, 2022, 2023, 2024]
    margins = [36.5, 36.8, 37.0, 37.3, 38.0]
    chart.data = [list(zip(years, margins))]
    chart.lines[0].strokeColor = colors.HexColor("#f47c2f")
    chart.lines[0].strokeWidth = 2
    chart.xValueAxis.valueMin = 2019.5
    chart.xValueAxis.valueMax = 2024.5
    chart.yValueAxis.valueMin = 35
    chart.yValueAxis.valueMax = 39
    d.add(chart)
    d.add(String(50, 205, "Gross Margin Trend, FY2020-FY2024 (%)", fontSize=10))
    return d


def build_pdf():
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title=f"Project Northbridge - Confidential Information Memorandum",
        author="Hackathon Practice (fabricated)",
    )
    story = []

    # Page 1 -- cover
    story += [
        Spacer(1, 1.2 * inch),
        Paragraph("FICTIONAL DATA -- FOR HACKATHON PRACTICE ONLY. NOT A REAL COMPANY OR TRANSACTION.", confidential),
        Spacer(1, 0.4 * inch),
        Paragraph("Project Northbridge", title_style),
        Paragraph(f"Confidential Information Memorandum &mdash; {COMPANY}", h2),
        Spacer(1, 1.5 * inch),
        Paragraph("Prepared for the exclusive use of holders of this Memorandum. Not for distribution.", body),
        Paragraph("September 2026", body),
        PageBreak(),
    ]

    # Page 2 -- disclaimer
    story += [
        Paragraph("Disclaimer", h1),
        Paragraph(
            "This Confidential Information Memorandum (\"CIM\") has been prepared solely for informational "
            "purposes in connection with a possible transaction involving " + COMPANY + " (the \"Company\"). "
            "The information contained herein is fabricated for a Claude Skills Hackathon practice exercise "
            "and does not describe any real business, financial results, or transaction. No representation "
            "or warranty, express or implied, is made as to the accuracy or completeness of this material.",
            body,
        ),
        Paragraph(
            "Recipients should conduct their own independent investigation. This document does not constitute "
            "an offer or solicitation to buy or sell any security.",
            body,
        ),
        PageBreak(),
    ]

    # Pages 3-4 -- business overview
    story += [
        Paragraph("Business Overview", h1),
        Paragraph(
            f"{COMPANY} is a fabricated, diversified packaging manufacturer serving the food, beverage, and "
            "consumer goods end markets. The Company operates through three segments: Rigid Packaging, "
            "Flexible Packaging, and Specialty Films, supplying blow-molded containers, laminated pouches, "
            "and barrier films to a broad customer base.",
            body,
        ),
        Paragraph(
            "The Company operates six manufacturing facilities across North America and employs approximately "
            "1,150 people. Management believes the Company is well positioned to benefit from continued "
            "substitution of rigid packaging with flexible formats and from sustainability-driven demand for "
            "recyclable film structures.",
            body,
        ),
        PageBreak(),
        Paragraph("Business Overview (continued)", h1),
        Paragraph(
            "Key competitive advantages include long-standing customer relationships (average tenure of 11 "
            "years with the top ten customers), vertically integrated resin compounding capability, and a "
            "track record of new product introductions in barrier-film technology.",
            body,
        ),
        Paragraph(
            "The Company's customer base is diversified across more than 340 active accounts, with the top "
            "ten customers representing approximately 46% of FY2024 net revenue.",
            body,
        ),
        PageBreak(),
    ]

    # Pages 5-6 -- market overview
    story += [
        Paragraph("Market Overview", h1),
        Paragraph(
            "The North American packaging market is estimated at approximately $145 billion, growing at a "
            "low-single-digit CAGR. The flexible packaging sub-segment is growing faster than the overall "
            "market, driven by lightweighting, e-commerce growth, and sustainability initiatives.",
            body,
        ),
        Paragraph(
            "Management estimates the Company's addressable market at approximately $6.2 billion, with the "
            "Company currently holding a low single-digit share, implying meaningful runway for organic and "
            "inorganic growth.",
            body,
        ),
        PageBreak(),
        Paragraph("Market Overview (continued)", h1),
        Paragraph(
            "Industry consolidation has accelerated over the past five years, with several strategic and "
            "financial acquirers active in the space. Recent precedent transactions have been completed at "
            "EBITDA multiples in the low double digits, reflecting continued investor appetite for "
            "diversified packaging platforms with strong customer retention.",
            body,
        ),
        PageBreak(),
    ]

    # Page 7 -- decoy chart: segment revenue mix
    story += [
        Paragraph("Segment Overview", h1),
        Paragraph(
            "The chart below illustrates the Company's FY2024 revenue mix by segment. Rigid Packaging "
            "remains the largest segment, though Flexible Packaging and Specialty Films have grown their "
            "combined share over the past three years.",
            body,
        ),
        decoy_segment_chart(),
        Paragraph(
            "This single-year segment view is illustrative only and does not represent the Company's "
            "consolidated financial overview across the full historical and projected period.",
            small,
        ),
        PageBreak(),
    ]

    # Page 8 -- decoy chart: gross margin trend
    story += [
        Paragraph("Margin Trends", h1),
        Paragraph(
            "Gross margin has expanded steadily as the Company has shifted mix toward higher-margin "
            "flexible and specialty film products, as shown below.",
            body,
        ),
        decoy_margin_chart(),
        Paragraph(
            "Margin percentages only; see the Consolidated Financial Overview later in this Memorandum for "
            "full period-by-period financial detail.",
            small,
        ),
        PageBreak(),
    ]

    # Pages 9-11 -- management, strategy, investment thesis
    story += [
        Paragraph("Management Team", h1),
        Paragraph(
            "The Company is led by an experienced management team with an average of 18 years of industry "
            "experience. Key executives include the Chief Executive Officer, Chief Financial Officer, and "
            "Chief Operating Officer (names withheld in this fabricated CIM).",
            body,
        ),
        PageBreak(),
        Paragraph("Growth Strategy", h1),
        Paragraph(
            "Management's growth strategy centers on three pillars: (1) organic share gains in Flexible "
            "Packaging and Specialty Films, (2) targeted bolt-on acquisitions to expand geographic footprint, "
            "and (3) continued operational efficiency initiatives across the manufacturing network.",
            body,
        ),
        PageBreak(),
        Paragraph("Investment Thesis", h1),
        Paragraph(
            "The Company represents an attractive platform investment opportunity given its diversified "
            "end-market exposure, consistent margin expansion, and multiple avenues for continued growth "
            "under new ownership.",
            body,
        ),
        PageBreak(),
    ]

    # Page 12 -- REAL consolidated financial overview, historical
    story += [
        Paragraph("Consolidated Financial Overview", h1),
        Paragraph("Historical Financial Performance (US$ in millions)", h2),
        money_table(HISTORICAL_PERIODS, FINANCIALS, footnote_period="FY2023A", footnote_row="ebitda_adjustments"),
        Spacer(1, 10),
        Paragraph(
            "(1) FY2023A adjustments include a disputed one-time relocation charge; advisors have not reached "
            "agreement on the appropriate add-back treatment for this item. See Footnotes for detail.",
            small,
        ),
        PageBreak(),
    ]

    # Page 13 -- REAL consolidated financial overview, projected
    story += [
        Paragraph("Consolidated Financial Overview (continued)", h1),
        Paragraph("Financial Projections (US$ in millions)", h2),
        money_table(FORECAST_PERIODS, FINANCIALS),
        Spacer(1, 10),
        Paragraph(
            "FY2029E and FY2030E detail has not been prepared by management at this time and is not "
            "included in this Memorandum.",
            small,
        ),
        PageBreak(),
    ]

    # Page 14 -- footnotes
    story += [
        Paragraph("Footnotes", h1),
        Paragraph(
            "(1) The FY2023A EBITDA adjustment of $5.1m reflects a one-time facility relocation charge. "
            "The Company's advisors and management have not reached final agreement on whether the full "
            "amount qualifies as a non-recurring add-back; a lower adjustment figure has been discussed in "
            "diligence but is not reflected in this draft. Buyers should treat this line as indicative "
            "pending further diligence.",
            body,
        ),
        PageBreak(),
    ]

    # Pages 15-20 -- filler / decoys
    filler_sections = [
        ("Organizational Structure", "The Company operates a lean corporate structure with functional leads reporting to the CEO across finance, operations, sales, and human resources."),
        ("Customer Overview", "The Company serves customers across food and beverage, household products, and industrial end markets, with no single customer representing more than 9% of FY2024 net revenue."),
        ("Facilities", "The Company operates six manufacturing facilities and two distribution centers across the United States and Canada, with an aggregate of approximately 1.4 million square feet."),
        ("Risk Factors", "Risks include raw material price volatility (principally resin), customer concentration among the top ten accounts, and competitive pressure from both regional and global packaging suppliers."),
        ("Appendix: Definitions", "References to \"Adjusted EBITDA\" in this Memorandum reflect reported EBITDA plus non-recurring and non-operating adjustments as determined by management. See Footnotes for FY2023A treatment."),
        ("Legal and Regulatory", "The Company is subject to customary environmental, health, and safety regulations applicable to packaging manufacturers. Management is not aware of any material pending litigation."),
    ]
    for i, (heading, text) in enumerate(filler_sections):
        story.append(Paragraph(heading, h1))
        story.append(Paragraph(text, body))
        if i < len(filler_sections) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"wrote {PDF_PATH}")


def build_fixtures():
    """Emit extracted.expected.json and normalised.expected.json matching FINANCIALS exactly."""
    extracted = []
    for period in ALL_PERIODS:
        page = HISTORICAL_PAGE if period in HISTORICAL_PERIODS else FORECAST_PAGE
        for row_key, label in ROW_LABELS.items():
            value = FINANCIALS[period][row_key]
            is_ambiguous = period == "FY2023A" and row_key == "ebitda_adjustments"
            is_missing = value is None

            if is_missing:
                entry = {
                    "row": row_key,
                    "period": period,
                    "value": None,
                    "unit": UNIT,
                    "source": {"page": page, "label": label},
                    "confidence": 1.0,
                    "checks": {"schema": True, "arithmetic": True, "two_pass": True},
                    "review": False,
                }
            elif is_ambiguous:
                entry = {
                    "row": row_key,
                    "period": period,
                    "value": value,
                    "unit": UNIT,
                    "source": {"page": page, "label": label},
                    "confidence": 0.55,
                    "checks": {"schema": True, "arithmetic": False, "two_pass": False},
                    "review": True,
                }
            else:
                entry = {
                    "row": row_key,
                    "period": period,
                    "value": value,
                    "unit": UNIT,
                    "source": {"page": page, "label": label},
                    "confidence": 0.97,
                    "checks": {"schema": True, "arithmetic": True, "two_pass": True},
                    "review": False,
                }
            extracted.append(entry)

    with open(EXTRACTED_PATH, "w") as f:
        json.dump(extracted, f, indent=2)
        f.write("\n")
    print(f"wrote {EXTRACTED_PATH} ({len(extracted)} values)")

    normalised = []
    for entry in extracted:
        norm = dict(entry)
        norm["template_row"] = entry["row"]
        norm["value_scaled"] = entry["value"]  # config scale for this mock is already millions
        normalised.append(norm)

    with open(NORMALISED_PATH, "w") as f:
        json.dump(normalised, f, indent=2)
        f.write("\n")
    print(f"wrote {NORMALISED_PATH} ({len(normalised)} values)")


if __name__ == "__main__":
    build_pdf()
    build_fixtures()
