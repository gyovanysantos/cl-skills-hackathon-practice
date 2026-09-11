# Installing the CIM Financial Summary plugin

This repo is not published to the Claude plugin store. It ships as a **versioned ZIP** (so it can
be reissued after tweaks) and, because it also carries a `.claude-plugin/marketplace.json`, it can
be added directly by repo URL from Claude Cowork or Claude Desktop.

Practice build — fabricated data only. See `docs/01-business-requirements.md` through
`03-design.md` for what this skill does and why.

## Option A — Add the marketplace by URL (Cowork / Claude Desktop)

1. Open **Cowork** (or Claude Desktop) → Settings → Plugins.
2. Choose **Add marketplace** (or equivalent) and paste this repo's URL:
   ```
   https://github.com/gyovanysantos/cl-skills-hackathon-practice
   ```
3. The marketplace exposes one plugin: **cl-cim-financial-summary**. Install it.
4. Start a task and share a CIM/SIM PDF, asking for its financial summary — the skill's
   description is written to trigger on that request. See
   `plugins/cl-cim-financial-summary/skills/cim-financial-summary/SKILL.md` for exactly what it
   does, step by step, including where it will pause for your review.

## Option B — Install from the versioned ZIP

Use this if the client environment can't add a marketplace by URL, or you want a specific
version pinned.

1. Go to the [Releases page](https://github.com/gyovanysantos/cl-skills-hackathon-practice/releases)
   and download `cl-cim-financial-summary-vX.Y.Z.zip` from the release you want.
2. In Cowork/Claude Desktop, choose **Install plugin from file** and select the downloaded ZIP.
3. Confirm the install, then use it the same way as Option A, step 4.

## Verifying a clean install

After installing (either option), confirm before relying on it:

- The plugin shows one skill: **cim-financial-summary**.
- Sharing `tests/fixtures/mock-cim.pdf` (in this repo) and asking for its financial summary
  produces a `review.xlsx` that flags exactly one value (the FY2023A EBITDA adjustment) for
  review, and refuses to produce `financial-summary.xlsx` until that row is confirmed.

## Reissuing after a tweak

Push a new tag (`git tag vX.Y.Z && git push --tags`) — `.github/workflows/release.yml` builds a
fresh ZIP and attaches it to a new GitHub Release automatically. No manual packaging step.

## What this build does not include

Client-specific configuration beyond the fabricated `config/mock-client.json`, the broader CIM
analyser, and any destination-system submission. This is a hackathon-practice rehearsal, not a
client deliverable.
