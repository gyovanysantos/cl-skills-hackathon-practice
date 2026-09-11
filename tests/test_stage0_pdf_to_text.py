"""
Exact-equality tests for stage 0 (deterministic script).
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(
    REPO_ROOT, "plugins", "cl-cim-financial-summary", "skills", "cim-financial-summary", "scripts"
)
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures")
sys.path.insert(0, SCRIPTS_DIR)

import importlib.util

_spec = importlib.util.spec_from_file_location("stage0", os.path.join(SCRIPTS_DIR, "0_pdf_to_text.py"))
stage0 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stage0)


def test_page_count_matches_pdf():
    text = stage0.pdf_to_page_tagged_text(os.path.join(FIXTURES_DIR, "mock-cim.pdf"))
    assert text.count("=== PAGE ") == 20
    assert text.count("=== END PAGE ") == 20


def test_page_markers_are_paired_and_in_order():
    text = stage0.pdf_to_page_tagged_text(os.path.join(FIXTURES_DIR, "mock-cim.pdf"))
    for n in range(1, 21):
        assert f"=== PAGE {n} ===" in text
        assert f"=== END PAGE {n} ===" in text
        start = text.index(f"=== PAGE {n} ===")
        end = text.index(f"=== END PAGE {n} ===")
        assert start < end


def test_real_financial_table_is_on_page_12():
    text = stage0.pdf_to_page_tagged_text(os.path.join(FIXTURES_DIR, "mock-cim.pdf"))
    start = text.index("=== PAGE 12 ===")
    end = text.index("=== END PAGE 12 ===")
    page_12 = text[start:end]
    assert "Consolidated Financial Overview" in page_12
    assert "Adjustments to EBITDA" in page_12
    assert "5.1" in page_12


def test_decoy_pages_do_not_contain_the_full_table():
    text = stage0.pdf_to_page_tagged_text(os.path.join(FIXTURES_DIR, "mock-cim.pdf"))
    for n in (7, 8):
        start = text.index(f"=== PAGE {n} ===")
        end = text.index(f"=== END PAGE {n} ===")
        page = text[start:end]
        assert "Reported EBITDA" not in page
        assert "Adjusted EBITDA" not in page
