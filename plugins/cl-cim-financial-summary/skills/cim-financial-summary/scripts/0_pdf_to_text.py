#!/usr/bin/env python3
"""
Stage 0 -- PDF to page-tagged text.

Deterministic. Dumps a CIM/SIM PDF's text with an explicit page marker
around each page, so the LLM extraction step (stage 1, run by the skill
itself -- not this script) gets clean, page-numbered input instead of
having to infer page boundaries from raw PDF layout.

Dependencies: Python standard library plus pypdf only, so this runs in any
sandbox that has pypdf available (no native/binary dependencies).

Usage:
    python3 0_pdf_to_text.py <input.pdf> [output.txt]

If output.txt is omitted, the text is written to stdout.
"""
import sys

from pypdf import PdfReader

PAGE_MARKER_START = "=== PAGE {n} ==="
PAGE_MARKER_END = "=== END PAGE {n} ==="


def pdf_to_page_tagged_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    chunks = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.append(PAGE_MARKER_START.format(n=i))
        chunks.append(text.rstrip("\n"))
        chunks.append(PAGE_MARKER_END.format(n=i))
        chunks.append("")  # blank line between pages
    return "\n".join(chunks)


def main(argv):
    if len(argv) < 2:
        print("usage: 0_pdf_to_text.py <input.pdf> [output.txt]", file=sys.stderr)
        return 2

    pdf_path = argv[1]
    output_path = argv[2] if len(argv) > 2 else None

    text = pdf_to_page_tagged_text(pdf_path)

    if output_path:
        with open(output_path, "w") as f:
            f.write(text)
        print(f"wrote {output_path}", file=sys.stderr)
    else:
        print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
