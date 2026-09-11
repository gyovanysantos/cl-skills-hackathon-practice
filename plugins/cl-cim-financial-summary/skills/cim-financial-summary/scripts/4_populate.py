#!/usr/bin/env python3
"""
Stage 4 -- deterministic template population. The enforced gate.

Reads the human-confirmed review.xlsx and fills ONLY the template's
declared entry cells (located by workbook-level defined name, never by
hardcoded row/column). Growth/margin/adjusted-EBITDA rows are formulas in
the template and are never written to.

This script REFUSES TO RUN -- writes nothing, exits non-zero -- while any
row in review.xlsx has Confirmed != TRUE. This is not an instruction in a
skill's prose; it is enforced here in code, the same way the AI-native
SDLC playbook distinguishes an advisory skill from an enforced hook: "a
skill is a control, though an advisory one... hooks are the approval
gates. The gate condition is enforced every time, for everyone."

Dependencies: Python standard library plus openpyxl only.

Usage:
    python3 4_populate.py <review.xlsx> <config.json> <output.xlsx>
"""
import json
import os
import sys

from openpyxl import load_workbook


class ReviewNotConfirmedError(RuntimeError):
    """Raised when one or more rows in review.xlsx are not yet confirmed."""


def load_review_rows(review_path):
    """Read the 'All values' sheet into a list of dicts, keyed by header text."""
    wb = load_workbook(review_path, data_only=True)
    ws = wb["All values"]
    headers = [c.value for c in ws[1]]

    rows = []
    for r in range(2, ws.max_row + 1):
        row = {headers[i]: ws.cell(row=r, column=i + 1).value for i in range(len(headers))}
        rows.append(row)
    return rows


def find_unconfirmed(rows):
    """Return the subset of rows that are flagged for review but not yet confirmed."""
    return [r for r in rows if r["Review"] and not r["Confirmed"]]


def resolve_template_path(config, config_path):
    return os.path.normpath(os.path.join(os.path.dirname(config_path), config["template_path"]))


# Rows that are extracted and reviewed (they have their own confidence score
# and appear in review.xlsx) but are NEVER written to the template, because
# the template computes them live as a formula. Adjusted EBITDA is the
# bridge total (reported EBITDA + adjustments) -- see docs/03-design.md.
# Extending this pipeline to a new formula-derived row means adding it here,
# not silently dropping a KeyError into production.
FORMULA_DERIVED_ROWS = set()  # DEMO BUG (issue #23): deliberately dropped "adjusted_ebitda"


def populate_template(rows, template_path, output_path):
    """Write value_scaled into each entry cell by defined name. Refuses (raises)
    if any target cell already holds a formula -- entry cells never should,
    but this is the second, independent guard the design calls for."""
    wb = load_workbook(template_path)  # keep formulas as formula strings
    defined_names = wb.defined_names

    written = 0
    skipped_missing = 0
    skipped_derived = 0

    for row in rows:
        template_row = row["Template row"]
        period = row["Period"]

        if template_row in FORMULA_DERIVED_ROWS:
            skipped_derived += 1
            continue  # the template computes this live; never paste a static value over it

        value = row["Value (scaled)"]
        if value is None:
            skipped_missing += 1
            continue  # undisclosed period -- leave the template cell blank, never invent one

        name = f"{template_row}__{period}"

        if name not in defined_names:
            raise KeyError(f"template has no entry cell named '{name}' -- check the template and config.row_map")

        dn = defined_names[name]
        _, addr = dn.attr_text.split("!")
        addr = addr.replace("$", "")
        # dn.attr_text sheet name may be quoted, e.g. 'Financial Summary'!$F$4
        sheet_name = dn.attr_text.split("!")[0].strip("'")
        ws = wb[sheet_name]
        cell = ws[addr]

        if isinstance(cell.value, str) and cell.value.startswith("="):
            raise RuntimeError(
                f"refusing to overwrite formula cell {sheet_name}!{addr} (defined name '{name}')"
            )

        cell.value = value
        written += 1

    wb.save(output_path)
    return written, skipped_missing, skipped_derived


def main(argv):
    if len(argv) < 4:
        print("usage: 4_populate.py <review.xlsx> <config.json> <output.xlsx>", file=sys.stderr)
        return 2

    review_path, config_path, output_path = argv[1], argv[2], argv[3]

    rows = load_review_rows(review_path)
    unconfirmed = find_unconfirmed(rows)

    if unconfirmed:
        print(
            f"REFUSING to populate: {len(unconfirmed)} row(s) in {review_path} are still flagged "
            f"for review and not confirmed. Open the workbook, resolve each item on the "
            f"'Needs review' sheet, and set Confirmed = TRUE before running this stage.",
            file=sys.stderr,
        )
        for r in unconfirmed:
            print(f"  - {r['Row']} / {r['Period']} (confidence {r['Confidence']:.0%})", file=sys.stderr)
        return 1

    with open(config_path) as f:
        config = json.load(f)
    template_path = resolve_template_path(config, config_path)

    written, skipped_missing, skipped_derived = populate_template(rows, template_path, output_path)
    print(
        f"wrote {output_path}: {written} cell(s) populated, {skipped_missing} left blank "
        f"(undisclosed periods), {skipped_derived} left to the template's own formula "
        f"(e.g. adjusted EBITDA)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
