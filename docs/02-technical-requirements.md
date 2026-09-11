# Stage 2 — Technical Requirements

Derived from `01-business-requirements.md`. Locked before design.

## Pipeline (4 stages, JSON as the contract between them)

| Stage | Kind | Input → Output | Notes |
|---|---|---|---|
| 0. Intake | script | `cim.pdf` → `pages.txt` (page-tagged plain text) | Deterministic (pypdf). Gives the LLM stage clean, page-numbered text instead of raw PDF layout. |
| 1. Extract | **LLM**, inside the skill | `pages.txt` → `extracted.json` | Finds the consolidated financial overview itself; ignores decoy charts elsewhere in the deck. Emits the shared confidence object (see below) per value. |
| 2. Validate + map | script | `extracted.json` + `config` → `normalised.json` | Validates against `extracted.schema.json`; applies per-line mapping to template rows; net revenue not gross; unit conversion to the config's target scale. |
| 3. Review workbook | script | `normalised.json` → `review.xlsx` | One row per value: period, value, unit, source page, confidence, review flag. Confidence < 0.90 highlighted and listed on a "Needs review" sheet. |
| 4. Populate | script | `review.xlsx` (post human sign-off) → `financial-summary.xlsx` | Deterministic fill of entry cells only. **Refuses to run** if any row is still flagged `review: true`. Growth/margin rows are formulas, left untouched. |

## Data contracts

- `schemas/extracted.schema.json` — required fields: `row`, `period`, `value` (number or null),
  `unit`, `source.page`, `confidence` (0–1), `checks` (`schema`, `arithmetic`, `two_pass` booleans),
  `review` (bool).
- `schemas/normalised.schema.json` — same shape, plus `template_row` (the target template row key)
  and `value_scaled` (converted to the config's reporting unit).
- Confidence computation (documented, not vibes): `two_pass` true only if two independent read
  attempts on the value agree within rounding; `arithmetic` true only if margin/EBITDA-derived
  checks reconcile; `schema` true if the value parses to the declared type/unit. `review = true`
  whenever `confidence < config.review_threshold` **or** any check is false.

## Config (`config/mock-client.json`)

Client-swappable: template path, unit scale (millions), `review_threshold` (0.90), and the
canonical row map (source-line aliases → template row keys) so the same code serves any client.
No client name or path is hard-coded in any script.

## Target runtime surface

Claude Cowork (per this practice run) and Claude Desktop chat. Scripts use **Python standard
library plus `openpyxl`, `pypdf`, `jsonschema`** only — no native deps — so they run in the
Anthropic-hosted sandbox without a client-side Python install.

## Testing requirement (feeds Stage 6)

- Stages 0, 2, 3, 4 are deterministic → exact-equality tests against fixtures.
- Stage 1 (LLM extraction) → tolerance eval: named rows present, values within ±0.05 of expected,
  correct source page, on the committed sample CIM.
- CI must fail if stage 4 ever writes outside the declared entry-cell range, or runs while a row
  is still flagged.
