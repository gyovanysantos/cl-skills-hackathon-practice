"""
Structural tests for the Financial Summary Excel template asset.
"""
import os

from openpyxl import load_workbook

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(
    REPO_ROOT,
    "plugins", "cl-cim-financial-summary", "skills", "cim-financial-summary",
    "assets", "financial-summary-template.xlsx",
)

ENTRY_ROWS = ["net_revenue", "gross_profit", "reported_ebitda", "ebitda_adjustments"]
PERIODS = [
    "FY2020A", "FY2021A", "FY2022A", "FY2023A", "FY2024A",
    "FY2025E", "FY2026E", "FY2027E", "FY2028E", "FY2029E", "FY2030E",
]


def _wb():
    return load_workbook(TEMPLATE_PATH)


def test_defined_names_cover_every_entry_row_and_period():
    wb = _wb()
    expected = {f"{row}__{period}" for row in ENTRY_ROWS for period in PERIODS}
    assert expected.issubset(set(wb.defined_names.keys()))
    assert len(expected) == 44


def test_entry_cells_are_blank_in_the_template():
    wb = _wb()
    ws = wb.active
    for name in [f"{row}__{p}" for row in ENTRY_ROWS for p in PERIODS]:
        dn = wb.defined_names[name]
        # attr_text looks like "'Financial Summary'!$F$4"
        _, addr = dn.attr_text.split("!")
        assert ws[addr.replace("$", "")].value is None, f"{name} should start blank"


def test_adjusted_ebitda_is_a_formula_not_an_entry_cell():
    wb = _wb()
    assert "adjusted_ebitda__FY2024A" not in wb.defined_names
    ws = wb.active
    for col in range(2, 2 + len(PERIODS)):
        cell = ws.cell(row=11, column=col)
        assert isinstance(cell.value, str) and cell.value.startswith("="), (
            "Adjusted EBITDA must be a live formula (reported EBITDA + adjustments), "
            "not a pasted value, so it stays correct if an upstream cell is edited."
        )


def test_growth_and_margin_rows_are_formulas():
    wb = _wb()
    ws = wb.active
    formula_rows = [5, 7, 9, 12]  # growth%, gross margin%, ebitda margin%, adj ebitda margin%
    for row in formula_rows:
        # skip column B (index 2) for growth row -- no prior period
        for col in range(3, 2 + len(PERIODS)):
            cell = ws.cell(row=row, column=col)
            assert isinstance(cell.value, str) and cell.value.startswith("=")
