#!/usr/bin/env python3
"""
Eval for stage 1 (LLM extraction) -- a tolerance check, not exact equality.

Stage 1 is Claude's own reasoning inside the skill, not a script, so its
output is non-deterministic: two correct reads of the same PDF can land on
slightly different numbers due to rounding, or can reasonably disagree on
whether a footnoted figure is trustworthy. Exact-equality tests (as used
for stages 0/2/3/4) would be the wrong tool here and would flake.

What this eval actually checks, against tests/fixtures/extracted.expected.json:
  1. Every expected (row, period) key is present in the candidate.
  2. For values the expected fixture considers reliable (review: false):
     the candidate's value is within ABS_TOLERANCE of the expected value,
     and the source page matches.
  3. For values the expected fixture considers genuinely ambiguous
     (review: true -- there is exactly one such case in the mock CIM, the
     FY2023A EBITDA adjustment): the candidate must ALSO have flagged it
     (review: true, confidence < REVIEW_THRESHOLD). The exact value is not
     checked here -- that is the point of flagging it, a human decides.
     A candidate that picks a plausible number but fails to flag it as
     uncertain FAILS this eval, even if the number happens to be right --
     confidently wrong is worse than flagged.
  4. For periods the source genuinely does not disclose (value: null in
     the expected fixture): the candidate must also have value: null.
     Inventing a number for an undisclosed period FAILS this eval
     regardless of how close it lands.

Every production mis-extraction a reviewer catches should be added here as
a new case, per the AI-native SDLC playbook: "each production incident
gets an eval, written by the team that owned the incident, and stays in
the suite as a regression test."

Usage:
    python3 tests/eval_extract.py <candidate_extracted.json>
Exit code 0 on pass, 1 on fail (with a report on stdout either way).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED_PATH = os.path.join(HERE, "fixtures", "extracted.expected.json")

ABS_TOLERANCE = 0.05
REVIEW_THRESHOLD = 0.90


def _key(entry):
    return (entry["row"], entry["period"])


def _index(entries):
    return {_key(e): e for e in entries}


def grade(candidate_data, expected_data=None):
    """Returns (passed: bool, report: list[str])."""
    if expected_data is None:
        with open(EXPECTED_PATH) as f:
            expected_data = json.load(f)

    expected_by_key = _index(expected_data)
    candidate_by_key = _index(candidate_data)

    report = []
    failures = 0

    for key, expected in expected_by_key.items():
        row, period = key
        label = f"{row} / {period}"

        if key not in candidate_by_key:
            report.append(f"FAIL  {label}: missing from candidate entirely")
            failures += 1
            continue

        candidate = candidate_by_key[key]

        # Case: undisclosed period -- must stay null, never invented.
        if expected["value"] is None:
            if candidate["value"] is not None:
                report.append(
                    f"FAIL  {label}: source does not disclose this period, but candidate "
                    f"invented a value ({candidate['value']})"
                )
                failures += 1
            else:
                report.append(f"pass  {label}: correctly left blank (undisclosed)")
            continue

        # Case: expected fixture says this is genuinely ambiguous -- the candidate
        # must flag it too, regardless of which value it picked.
        if expected["review"]:
            if not candidate.get("review") or candidate.get("confidence", 1.0) >= REVIEW_THRESHOLD:
                report.append(
                    f"FAIL  {label}: this value is genuinely ambiguous in the source and must be "
                    f"flagged for review (candidate: review={candidate.get('review')}, "
                    f"confidence={candidate.get('confidence')})"
                )
                failures += 1
            else:
                report.append(f"pass  {label}: correctly flagged as ambiguous")
            continue

        # Case: a reliable value -- check tolerance and source page.
        diff = abs(candidate["value"] - expected["value"])
        if diff > ABS_TOLERANCE:
            report.append(
                f"FAIL  {label}: value {candidate['value']} is outside tolerance of expected "
                f"{expected['value']} (diff {diff:.3f} > {ABS_TOLERANCE})"
            )
            failures += 1
            continue

        if candidate["source"]["page"] != expected["source"]["page"]:
            report.append(
                f"FAIL  {label}: source page {candidate['source']['page']} does not match "
                f"expected page {expected['source']['page']}"
            )
            failures += 1
            continue

        report.append(f"pass  {label}: value within tolerance, page matches")

    passed = failures == 0
    report.append("")
    report.append(f"{'PASS' if passed else 'FAIL'}: {len(expected_by_key) - failures}/{len(expected_by_key)} checks passed")
    return passed, report


def main(argv):
    if len(argv) < 2:
        print("usage: eval_extract.py <candidate_extracted.json>", file=sys.stderr)
        return 2

    with open(argv[1]) as f:
        candidate_data = json.load(f)

    passed, report = grade(candidate_data)
    print("\n".join(report))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
