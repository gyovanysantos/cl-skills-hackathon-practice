"""
Self-tests for the extraction eval (tests/eval_extract.py).

These prove the eval actually discriminates: it passes the real fixture
against itself, and it FAILS on each of the mistakes it exists to catch --
a nudged value, an invented forecast, and (the most important case) a
candidate that picks a plausible number for the ambiguous line but fails
to flag it as uncertain.
"""
import copy
import importlib.util
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures")

_spec = importlib.util.spec_from_file_location("eval_extract", os.path.join(REPO_ROOT, "tests", "eval_extract.py"))
eval_extract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_extract)


def _expected():
    with open(os.path.join(FIXTURES_DIR, "extracted.expected.json")) as f:
        return json.load(f)


def _find(data, row, period):
    return next(e for e in data if e["row"] == row and e["period"] == period)


def test_expected_fixture_passes_against_itself():
    expected = _expected()
    passed, report = eval_extract.grade(copy.deepcopy(expected), expected)
    assert passed, "\n".join(report)


def test_a_nudged_reliable_value_fails():
    expected = _expected()
    candidate = copy.deepcopy(expected)
    entry = _find(candidate, "net_revenue", "FY2024A")
    entry["value"] += 5.0  # well outside the 0.05 tolerance

    passed, report = eval_extract.grade(candidate, expected)
    assert not passed
    assert any("FAIL" in line and "net_revenue / FY2024A" in line for line in report)


def test_an_invented_undisclosed_period_fails():
    expected = _expected()
    candidate = copy.deepcopy(expected)
    entry = _find(candidate, "net_revenue", "FY2029E")
    assert entry["value"] is None  # sanity: this is the undisclosed case
    entry["value"] = 300.0  # invented

    passed, report = eval_extract.grade(candidate, expected)
    assert not passed
    assert any("invented a value" in line for line in report)


def test_missing_the_ambiguous_flag_fails_even_with_a_plausible_value():
    # This is the case that matters most: a candidate that quietly resolves
    # the disputed FY2023A adjustment to a reasonable-looking number instead
    # of flagging it. Confidently wrong beats nothing -- and that is exactly
    # what this eval must never let through.
    expected = _expected()
    candidate = copy.deepcopy(expected)
    entry = _find(candidate, "ebitda_adjustments", "FY2023A")
    assert expected_entry_is_flagged(expected)
    entry["review"] = False
    entry["confidence"] = 0.96
    entry["checks"] = {"schema": True, "arithmetic": True, "two_pass": True}

    passed, report = eval_extract.grade(candidate, expected)
    assert not passed
    assert any("must be flagged for review" in line for line in report)


def expected_entry_is_flagged(expected):
    entry = _find(expected, "ebitda_adjustments", "FY2023A")
    return entry["review"] is True


def test_candidate_may_pick_either_plausible_value_for_the_ambiguous_row_as_long_as_flagged():
    expected = _expected()
    candidate = copy.deepcopy(expected)
    entry = _find(candidate, "ebitda_adjustments", "FY2023A")
    entry["value"] = 3.9  # a different plausible reading than the fixture's 5.1
    entry["review"] = True
    entry["confidence"] = 0.5

    passed, report = eval_extract.grade(candidate, expected)
    assert passed, "\n".join(report)


def test_missing_row_entirely_fails():
    expected = _expected()
    candidate = [e for e in copy.deepcopy(expected) if not (e["row"] == "gross_profit" and e["period"] == "FY2022A")]

    passed, report = eval_extract.grade(candidate, expected)
    assert not passed
    assert any("missing from candidate entirely" in line for line in report)
