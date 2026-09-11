# Stage 3 — Implementation Design

The agreed design — basis for the build, no free-form development. Mirrors the pipeline board
from the hackathon-prep canvas.

## File layout

```
plugins/cl-cim-financial-summary/
├── .claude-plugin/plugin.json
├── skills/cim-financial-summary/
│   ├── SKILL.md                    # trigger description + orchestration steps
│   ├── scripts/
│   │   ├── 0_pdf_to_text.py
│   │   ├── 2_validate_map.py
│   │   ├── 3_review_xlsx.py
│   │   └── 4_populate.py
│   ├── schemas/
│   │   ├── extracted.schema.json
│   │   └── normalised.schema.json
│   └── assets/
│       └── financial-summary-template.xlsx
└── config/
    └── mock-client.json
```

## Orchestration (SKILL.md)

1. Run `0_pdf_to_text.py` on the supplied PDF → `pages.txt`.
2. Read `pages.txt`, locate the consolidated financial overview (skip decoy chart pages), and
   write `extracted.json` matching `extracted.schema.json` — this step is Claude's own reasoning,
   not a script.
3. Run `2_validate_map.py extracted.json config/mock-client.json` → `normalised.json`.
4. Run `3_review_xlsx.py normalised.json` → `review.xlsx`. Tell the user which rows need review
   and why (confidence, or a failed check).
5. Wait for the human to confirm/correct `review.xlsx` and clear every review flag.
6. Run `4_populate.py review.xlsx config/mock-client.json` → `financial-summary.xlsx`. The script
   itself checks for outstanding flags and refuses if any remain — this is not merely a prompt
   instruction to the model, it's enforced in code (per the AI-native SDLC playbook: "a skill is
   an advisory control; a hook/check is enforced every time, for everyone").

## Template contract

`assets/financial-summary-template.xlsx` defines named entry cells for each (row, period) pair
plus formula rows for growth % and margin %. `4_populate.py` writes ONLY the declared entry cells
and never touches a cell containing a formula — enforced by reading `data_only=False` and asserting
`cell.value` is not already a formula string before writing.

## Confidence object (shared shape, reused verbatim from the hackathon canvas)

```json
{
  "row": "adjusted_ebitda",
  "period": "FY2024A",
  "value": 12.4,
  "unit": "USD_millions",
  "source": { "page": 31, "label": "Adj. EBITDA" },
  "confidence": 0.94,
  "checks": { "schema": true, "arithmetic": true, "two_pass": true },
  "review": false
}
```

## Mock data

`tools/make_mock_cim.py` fabricates a ~20-page CIM for the fictional **"Northbridge Packaging
Holdings"**: cover, disclaimer, business overview, market, two decoy chart pages (segment revenue,
gross margin trend — must NOT be picked up by extraction), management, then the Consolidated
Financial Overview table (FY2020A–FY2030E, blank after FY2028E for forecast rows), with one
adjustment line deliberately ambiguous so the confidence gate has a real case to catch. The same
script emits the expected JSON fixtures alongside the PDF, so fixtures and PDF cannot drift apart.

## Out of scope for this build (per business requirements)

Broader CIM analyser, real client data, Skill 1/Skill 3, any destination-system submission.
