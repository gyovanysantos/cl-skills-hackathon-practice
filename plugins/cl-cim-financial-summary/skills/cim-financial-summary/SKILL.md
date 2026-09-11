---
name: cim-financial-summary
description: Extract a financial summary from a CIM/SIM PDF into a bridged EBITDA template, with a confidence review gate before anything is written. Triggers on "financial summary from CIM", "CIM extraction", "populate the financial summary template", "SIM financial overview", or when a user shares a confidential information memorandum and asks for its financials pulled into the house template.
---

# CIM Financial Summary

You turn a Confidential/Selling Information Memorandum (CIM/SIM) PDF into a reviewed, populated
Financial Summary workbook. A human always confirms anything uncertain before the template is
written — you never silently accept a low-confidence value, and you never invent a period that
isn't in the source.

This is a **practice build** using fabricated data (see `../../../../tests/fixtures/mock-cim.pdf`,
a fictional company called "Northbridge Packaging Holdings"). Do not treat any figure it contains
as real.

## When this triggers

The user shares or references a CIM/SIM PDF and wants its consolidated financials pulled into a
Financial Summary template — historical and projected net revenue, gross profit, EBITDA, and the
EBITDA bridge (reported → adjustments → adjusted).

## What you do, step by step

1. **Run stage 0** on the supplied PDF to get clean, page-numbered text:
   ```
   python3 scripts/0_pdf_to_text.py <the CIM pdf> pages.txt
   ```

2. **Extract the consolidated financial overview yourself** (this is the one step no script does —
   it's your judgment call, not code). Read `pages.txt` and find the **Consolidated Financial
   Overview** section. A ~70-page CIM has decoys: single-year segment charts, a margin-trend chart,
   or other partial views elsewhere in the deck. The real overview is the one section that gives a
   full period-by-period walk (historicals *and* forecasts) for net revenue, gross profit, reported
   EBITDA, the EBITDA adjustments, and adjusted EBITDA — it may span two adjacent pages (a
   historical table and a projections table under the same heading).

   For each (row, period) value you find, write an entry matching `schemas/extracted.schema.json`:
   - `row`: one of `net_revenue`, `gross_profit`, `reported_ebitda`, `ebitda_adjustments`,
     `adjusted_ebitda`. **Always net revenue, never gross** — there is no gross-revenue option in
     this list on purpose.
   - `period`: exactly as labeled in the source (`FY2023A`, `FY2027E`, ...). Never a fixed example
     year — periods come from the document, historicals and forecasts both.
   - `value`: the number, in the unit reported. Use `null` — never a guess — for a period the
     source genuinely does not disclose (e.g. late forecast years past what management prepared).
   - `source.page` / `source.label`: the PDF page number and the line label exactly as printed.
   - `confidence` and `checks` (`schema`, `arithmetic`, `two_pass`): be honest here. Set
     `two_pass: false` if a second read of the passage could plausibly land on a different number
     (a footnoted, disputed, or ambiguous figure). Set `arithmetic: false` if the line doesn't
     reconcile with a related line (e.g. `reported_ebitda + ebitda_adjustments` doesn't tie to the
     `adjusted_ebitda` the source itself prints). `confidence` should be low (well under 0.90) when
     any check fails.
   - `review`: `true` whenever confidence is below `config.review_threshold` (0.90 in
     `../../config/mock-client.json`) or any check is false.

   Save this list as `extracted.json`.

3. **Run stage 2** to validate and map:
   ```
   python3 scripts/2_validate_map.py extracted.json ../../config/mock-client.json normalised.json
   ```
   This validates against the schema, maps each row to its template row (config-driven — no
   client name or path is hardcoded in any script), and rescales units.

4. **Run stage 3** to build the review workbook:
   ```
   python3 scripts/3_review_xlsx.py normalised.json review.xlsx
   ```
   Tell the user plainly what needs their attention: how many values were flagged, which ones, and
   why (the script's stderr output already says this — relay it, don't just say "done").

5. **Wait for the human.** Do not proceed until the user has opened `review.xlsx`, checked the
   "Needs review" sheet against the source pages, corrected any value if needed, and set
   `Confirmed = TRUE` on every flagged row. If they ask you to just proceed, remind them this step
   exists precisely because an unattended run should never ship an unverified figure — you can
   still help them look at the flagged page and decide, but the workbook is what has to be marked
   confirmed.

6. **Run stage 4** to populate the template:
   ```
   python3 scripts/4_populate.py review.xlsx ../../config/mock-client.json financial-summary.xlsx
   ```
   This is the enforced gate — if anything is still unconfirmed, the script refuses and writes
   nothing (non-zero exit). That's expected behavior, not a bug: go back to step 5. Once it
   succeeds, hand the user `financial-summary.xlsx`. Growth %, margin %, and Adjusted EBITDA itself
   are live formulas in that file, not pasted values — they will recompute if the user edits a cell.

## What "done" looks like

The user has `financial-summary.xlsx` with every disclosed period populated, every uncertain value
having gone through a human sign-off, and every unavailable forecast period left genuinely blank.

## Out of scope for this skill

The broader CIM analyser (business summary, deal strengths/risks), any destination-system
submission, and real client configuration — this build only ships `../../config/mock-client.json`, a
fabricated stand-in.
