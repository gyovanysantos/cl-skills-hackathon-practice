# Stage 1 — Business Requirements

**Skill:** CIM Financial Summary (practice build of Hackathon Skill 2)
**Status:** Drafted by Claude, agreed before build. Fabricated data only — this is a rehearsal, not client work.

## Problem

A PE deal analyst receives a ~70-page Confidential/Selling Information Memorandum (CIM/SIM) for a
target company. Today they manually locate the consolidated financial overview inside the deck,
retype net revenue, gross profit, reported EBITDA and the adjustments bridging to adjusted EBITDA
into a house Excel template, one column per historical/forecast period. This is slow and error-prone,
and a mis-transcribed figure can carry into an investment committee memo unchecked.

## Who it's for

The deal-team analyst reviewing a new opportunity, and the associate who spot-checks their work
before it goes into the IC memo.

## What "done" looks like

1. Given a CIM PDF, the skill produces a **review workbook** showing every extracted value, its
   source page, and a confidence score — flagging anything under ~90% for human sign-off.
2. Once confirmed, it **populates the Financial Summary template** deterministically: dynamic
   period columns pulled from the source (not fixed years), net revenue (not gross), and an
   EBITDA bridge (reported → adjustments → adjusted). Growth/margin rows stay formulas.
3. The skill **never silently accepts an uncertain value** and never invents a period that isn't
   in the source — unavailable forecast years are left blank.
4. A human reviews and is the one who ultimately signs off before the summary is used downstream.

## Explicitly out of scope for this build

- The broader CIM analyser (business summary, deal strengths/risks) — future extension.
- Real client palettes, real client data, real iLEVEL/Skill 1 work.
- Any destination system integration — output is a workbook, not a submission.

## Success signal

An analyst can drop in a CIM and get a reviewable summary in minutes instead of by hand, with the
confidence flags doing the job of "what to double-check" instead of "recheck everything."
