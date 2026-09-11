"""
Exact-equality tests for stage 2 (deterministic script).
"""
import importlib.util
import json
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(
    REPO_ROOT, "plugins", "cl-cim-financial-summary", "skills", "cim-financial-summary", "scripts"
)
CONFIG_PATH = os.path.join(REPO_ROOT, "plugins", "cl-cim-financial-summary", "config", "mock-client.json")
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures")

_spec = importlib.util.spec_from_file_location("stage2", os.path.join(SCRIPTS_DIR, "2_validate_map.py"))
stage2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stage2)


def _load(name):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def test_normalised_output_matches_expected_fixture_exactly():
    extracted = _load("extracted.expected.json")
    config = json.load(open(CONFIG_PATH))

    stage2.validate_extracted(extracted)
    actual = stage2.map_and_scale(extracted, config)
    expected = _load("normalised.expected.json")

    assert actual == expected


def test_validate_extracted_rejects_bad_data():
    bad = [{"row": "not_a_real_row", "period": "FY2024A"}]
    with pytest.raises(Exception):
        stage2.validate_extracted(bad)


def test_row_map_missing_entry_raises():
    extracted = [
        {
            "row": "net_revenue",
            "period": "FY2024A",
            "value": 100.0,
            "unit": "USD_millions",
            "source": {"page": 12, "label": "Net revenue"},
            "confidence": 0.99,
            "checks": {"schema": True, "arithmetic": True, "two_pass": True},
            "review": False,
        }
    ]
    config = {"reporting_unit": "USD_millions", "row_map": {}}
    with pytest.raises(KeyError):
        stage2.map_and_scale(extracted, config)


def test_convert_unit_thousands_to_millions():
    # Real conversion exercise beyond the mock fixture, which is already in millions.
    assert stage2.convert_unit(2500.0, "USD_thousands", "USD_millions") == pytest.approx(2.5)


def test_convert_unit_actuals_to_millions():
    assert stage2.convert_unit(4_200_000.0, "USD_actuals", "USD_millions") == pytest.approx(4.2)


def test_convert_unit_preserves_none_for_missing_periods():
    assert stage2.convert_unit(None, "USD_millions", "USD_millions") is None


def test_convert_unit_identity_millions_to_millions():
    assert stage2.convert_unit(10.0, "USD_millions", "USD_millions") == 10.0
