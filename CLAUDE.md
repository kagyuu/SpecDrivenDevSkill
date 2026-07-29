# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is not an application codebase. It is the source of a Claude Code **Skill** (`spec-driven-dev`) that makes Claude Code follow the phases of a traditional Japanese waterfall/V-model software development process instead of jumping straight from a vague request to code. The Skill itself never writes source code or runs tests — it only produces Markdown deliverables (specs, plans, and per-task execution instructions). Those instruction Markdown files are later handed to *separate* Claude Code sessions (acting as implementation/test/fix agents) that do the actual coding and testing.

There is no build, lint, or test tooling in this repo — it is pure Markdown. "Development" here means editing the Skill's instruction files themselves.

## Repository layout: versioned snapshots, not a normal source tree

This repo doubles as the version history of the Skill, so each top-level folder (`V0.1/`, `V0.2/`, future `V0.x/`) is a **complete, self-contained snapshot** of the Skill at that point in time — not an incremental diff or a shared module structure.

- Always work in the **highest-numbered `Vx.y/` folder** unless explicitly told to look at an older version for history/comparison.
- When asked to improve or fix the Skill, create a **new `Vx.y/` folder** by copying the latest version's files rather than editing an old version in place, unless the user explicitly says to patch the current latest version directly.
- Each version folder is what actually gets deployed: its contents (`SKILL.md`, `SKILL-01..09-*.md`, `TEMPLATE-*.md`) are copied as-is into a target project's `.claude/skills/spec-driven-dev/` to be used.
- If a version folder introduces user-visible changes, add/update a `review-report.md` in that folder describing what changed and why (see `V0.2/review-report.md` for the expected depth: consistency issues, executability issues, and phrasing/structure consistency issues, each with a rationale and resolution).

## The 9-phase structure (the thing to keep internally consistent)

`SKILL.md` in each version folder is the entry point and defines 9 phases, each producing one primary Markdown deliverable under the target project's `docs/`:

| Phase | Name | Output |
|---|---|---|
| 1 | System requirements | `docs/01-requirement.md` |
| 2 | Frontend/UI spec | `docs/02-frontend-spec.md` |
| 3 | Backend/detailed spec | `docs/03-backend-spec.md` |
| 4 | Implementation plan | `docs/04-impl-plan.md` |
| 5 | Test plan | `docs/05-test-plan.md` |
| 6 | Implementation directions | `docs/06-impl-direction.md` + `docs/06-impl-direction/U000-*.md` |
| 7 | Integration test directions | `docs/07-test-direction.md` + `docs/07-test-direction/T000-*.md` |
| 8 | Fix plan | `docs/08-fix-plan.md` + `docs/08-fix-plan/F000-*.md` (+ `fixed/`, `08-fix-resolved.md`, `08-fix-unresolved.md`) |
| 9 | Delivery summary | `docs/09-deliver.md` |

Each phase's driver file is `SKILL-0N-*.md`; `SKILL.md`'s per-phase sections just say "execute `SKILL-0N-*.md`". Phases 6–8 also reference a `TEMPLATE-0N-*.md` that defines the required structure of each per-task file (`U000-*`, `T000-*`, `F000-*`).

Critical invariant when editing any of these files: **inputs, outputs, file names, and folder names must match exactly across `SKILL.md`, the individual `SKILL-0N-*.md` files, and the `TEMPLATE-0N-*.md` files.** Most historical bugs in this Skill (see `V0.2/review-report.md`) were exactly this kind of cross-file drift — e.g. downstream phases referencing an input filename (`01-overview.md`) that phase 1 never actually produced, a sub-folder name not matching its parent document's name, or a template missing a field that its driver file requires. When changing a phase's output filename/location or a template's fields, grep the whole version folder for every other reference to it before considering the change done.

Only one phase runs per Claude Code invocation, and it stops for human review before the next phase begins — this rule (and the phase-detection logic in `SKILL.md`'s "ステップ0") is core to the Skill's design intent and should not be relaxed when editing.

## Structural conventions each `SKILL-0N-*.md` file follows

Every phase driver file uses the same frontmatter and section shape — preserve this when adding or editing a phase file:

```yaml
---
name: {phase-name}-dev   # pattern: {フェーズ名}-dev, must be unique per file
description: 仕様駆動でアプリケーションを開発するときに、{このフェーズの成果物}を作成する。
---
```

Body section order: `目的` → `インプット文書` → `アウトプット文書` (containing `### アウトプットの記載内容` then `### アウトプットを参照する文書`) → `## 動作`. Phases 1–5 are human-collaborative planning docs (short `## 動作`, often just "共通指示以外は特になし"); phases 6–9 are agent-facing execution instructions with a much longer `## 動作`/`アウトプットの記載内容`. This length asymmetry is intentional (see `review-report.md` §3-3), not something to "fix" by padding phases 1–5.

Common rules referenced by every phase (defined once in `SKILL.md`'s "各フェーズ共通指示" section — don't duplicate them into individual phase files, just reference them):

- Diagrams inside generated Markdown must use Mermaid syntax.
- Missing/sparse output sections → ask the human whether to generate a FIXME-marked template or co-author interactively.
- The phase 6/7/8 table-of-contents files use a checkbox-based progress format (historically mislabeled "OKF format" — see below): `- [状態] 番号 [タイトル](相対リンク) — 一言概要`, where 状態 is one of `[ ]` / `[~]` / `[x]`. A phase isn't complete until every item in its table of contents is `[x]`.

## Naming trap: "OKF format" does not mean Google's Open Knowledge Format

`SKILL.md` and several phase files call the checkbox+link table-of-contents format "OKF形式". Per `V0.2/review-report.md`'s appendix, this was investigated and confirmed to be an unrelated, self-invented format (checkbox + number + link + summary) that only superficially resembles Google Cloud's actual Open Knowledge Format — adopting the real OKF standard was deliberately rejected because it lacks task-lifecycle/status semantics. The name is intentionally kept as-is in V0.2 (renaming was recommended for a future version but not yet done). Do not "correct" this format toward Google's OKF spec, and if renaming it in a new version, update every occurrence across `SKILL.md` and all `SKILL-04/05/06/07-*.md` files consistently.

## When revising a version

Read `V0.2/review-report.md` first — it documents the exact categories of defects already found and fixed once (cross-file consistency, executability, phrasing/structure consistency) plus known open issues (e.g. sub-folder progress tracking is unverified end-to-end; the full 9-phase pipeline has not been run against a real target project). Treat it as the checklist for reviewing any new version, and append to it (or add an equivalent report in the new version folder) rather than silently fixing things with no record.
