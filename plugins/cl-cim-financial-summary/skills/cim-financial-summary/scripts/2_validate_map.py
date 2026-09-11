#!/usr/bin/env python3
"""
Stage 2 -- validate and map extracted values.

Deterministic. Validates stage 1's extracted.json against
schemas/extracted.schema.json, then for each value:
  - maps the canonical row key to the client's template row key
    (config.row_map -- identity for a client whose template uses the
    same names; a real client can rename or combine lines here without
    touching this script), and
  - rescales the value to the client's reporting unit
    (config.reporting_unit), preserving the original value/unit for
    audit.

"Net revenue, not gross": enforced upstream by the schema itself -- the
extraction row enum has no gross-revenue option, so there is nothing to
discard here.

Dependencies: Python standard library plus jsonschema only.

Usage:
    python3 2_validate_map.py <extracted.json> <config.json> [output.json]

If output.json is omitted, the normalised data is written to stdout.
"""
import json
import os
import sys

import jsonschema

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "schemas", "extracted.schema.json")

# Conversion factors to USD_millions. Extend here, never by special-casing a
# client in code -- unit handling stays generic.
_TO_MILLIONS = {
    "USD_millions": 1.0,
    "USD_thousands": 1.0 / 1000.0,
    "USD_actuals": 1.0 / 1_000_000.0,
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def validate_extracted(data, schema=None):
    """Raises jsonschema.ValidationError if `data` doesn't match extracted.schema.json."""
    if schema is None:
        schema = load_json(SCHEMA_PATH)
    jsonschema.validate(data, schema)


def convert_unit(value, from_unit, to_unit):
    """Convert `value` from `from_unit` to `to_unit`. Both must be USD_* units.
    Returns None unchanged (an undisclosed period stays undisclosed)."""
    if value is None:
        return None
    if from_unit not in _TO_MILLIONS:
        raise ValueError(f"unknown source unit: {from_unit}")
    if to_unit not in _TO_MILLIONS:
        raise ValueError(f"unknown target unit: {to_unit}")
    in_millions = value * _TO_MILLIONS[from_unit]
    return in_millions / _TO_MILLIONS[to_unit]


def resolve_config_path(config, config_path, key):
    """Resolve a config value that is a path, relative to the config file's own directory."""
    return os.path.normpath(os.path.join(os.path.dirname(config_path), config[key]))


def map_and_scale(extracted_data, config):
    row_map = config["row_map"]
    reporting_unit = config["reporting_unit"]

    normalised = []
    for entry in extracted_data:
        row = entry["row"]
        if row not in row_map:
            raise KeyError(f"no row_map entry for extracted row '{row}' -- add it to config.row_map")

        template_row = row_map[row]
        value_scaled = convert_unit(entry["value"], entry["unit"], reporting_unit)

        norm = dict(entry)
        norm["template_row"] = template_row
        norm["value_scaled"] = value_scaled
        normalised.append(norm)

    return normalised


def main(argv):
    if len(argv) < 3:
        print("usage: 2_validate_map.py <extracted.json> <config.json> [output.json]", file=sys.stderr)
        return 2

    extracted_path = argv[1]
    config_path = argv[2]
    output_path = argv[3] if len(argv) > 3 else None

    extracted_data = load_json(extracted_path)
    config = load_json(config_path)

    validate_extracted(extracted_data)
    normalised = map_and_scale(extracted_data, config)

    output = json.dumps(normalised, indent=2) + "\n"
    if output_path:
        with open(output_path, "w") as f:
            f.write(output)
        print(f"wrote {output_path} ({len(normalised)} values)", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
