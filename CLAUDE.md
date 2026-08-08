# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Handoff note (2026-08-05).** V0.1–V0.7 were developed in Claude Cowork sessions running in a cloud sandbox, reaching this folder through a device bridge. That has now been handed off to Claude Code running locally. Read "Current state — start here" below before doing anything, because there is uncommitted work and a pending human decision.

## Current state — start here

**V0.7 is the latest version and is complete, but not committed.** ~300 files (`V0.7/`, `V0.7_testbed/`, `README.md`) are staged in git awaiting a commit. The Cowork session could not complete `git commit` because the device bridge has a 45-second per-command limit and this repo is now ~1,500 tracked files. Running locally you have no such limit:

```
git commit -m "V0.7"
git push
```

Verify with `git log --oneline -3` first — the expected HEAD before this commit is `4993860 V0.7向け: CR運用の変更仕様を追加`.

**Pending human decision: whether to create V0.8, and what goes in it.** `V0.7_testbed/e2e-validation-report.md` documents **44 findings** (5 high, 22 medium, 17 low). Do **not** start V0.8 on your own initiative — the standing rule in this project is that the human decides each version's direction after reading the validation report. Two of the high findings are concrete data-loss defects (P902 backup overwrite on resume; `.inprogress` unable to represent "inside P903", causing a resume to ignore the CR). Summarize and ask; don't fix speculatively.

**Repo hygiene left over from the cloud sessions.** `_to_delete/` holds discarded files (old zips, cleared git lock files) — the bridge could not delete files, only move them, so cleanup was deferred. `.git/objects/` has ~390 stale `tmp_obj_*` files for the same reason. Locally you can just remove `_to_delete/` and run `git gc`. Also note some `V0.1/`/`V0.3/` files show as modified-unstaged from before these sessions (likely line-ending normalization); leave them unless asked.

## What this repository is

This is not an application codebase. It is the source of a Claude Code **Skill** (`spec-driven-dev`) that makes Claude Code follow the phases of a traditional Japanese waterfall/V-model development process instead of jumping from a vague request straight to code.

"Development" here means editing the Skill's own instruction Markdown. There is no build or lint tooling for the Skill itself. **However, the `Vx.y_testbed/` folders are different** — from `V0.4_testbed/` onward they contain a real, working meeting-room reservation application (Python backend, JS frontend, hundreds of real tests) that was built *by* the Skill in order to validate it. Those have real test commands; see "Testbeds" below.

## Repository layout: versioned snapshots, not a normal source tree

Each top-level `Vx.y/` folder is a **complete, self-contained snapshot** of the Skill at that point — not an incremental diff or a shared module structure.

- Always work in the **highest-numbered `Vx.y/` folder** (currently `V0.7/`) unless told to look at an older one for comparison.
- To improve the Skill, create a **new `Vx.y/` folder** by copying the latest, rather than editing an existing version in place — unless the human explicitly says to patch the current latest directly (which they have done, e.g. for typo/表記ゆれ fixes).
- A version folder's contents are copied as-is into a target project's `.claude/skills/spec-driven-dev/` to be used.
- Every version that changes behavior gets a `review-report.md` in its folder. Match the established depth — see `V0.6/review-report.md` and `V0.7/review-report.md`: each change gets 事象 (what was wrong) / V0.x での変更 (what was changed) / rationale, plus explicit sections for what was deliberately *not* changed.
- `V0.7/USER_GUIDE.md` is the human-facing manual (requirement definition → initial build → change requests). Keep it in sync when CR handling or the build flow changes. Filename stays `USER_GUIDE.md`.
- `CR運用変更仕様.md` (repo root) is the agreed design spec that V0.7's CR restructure implements. Historical reference.

## Phase structure (P-number scheme, V0.4 onward)

`SKILL.md` in each version folder is the entry point. **From V0.4 the numbering changed** from sequential phases 1–9 (`docs/01-requirement.md` …) to 3-digit P-numbers grouped into 7 Steps. V0.1–V0.3 use the old scheme; do not mix them up.

| Step | Phases | Purpose |
|---|---|---|
| Require Development | P001 | Requirement definition — the only human-collaborative phase |
| Plan Loop | P002–P012 | UI spec, detail spec, traceability, impl plan, test plan, impl/test/acceptance directions, cross-document review loop |
| Overview | P020–P022 | Source-tree INDEX, ADR, ArchitectureHandbook |
| Executor | P101–P104 | Impl context, implementation, integration test, INDEX update (iterates per sprint) |
| Reviewer Loop | P201–P205 | Acceptance test, fix plan, fix execution, impact analysis, retest |
| Closing | P301–P302 | Root INDEX, deliverables + release verdict |
| Refactor | P901–P905 | Apply a human change request (CR) |

Note **P021 is ADR and P022 is ArchitectureHandbook** — these were swapped in V0.5 because the Handbook consumes `docs/ADR.md` as input. Don't restore the older order.

### The V0.4 design change — do not reintroduce per-phase human review

Earlier versions (and the previous edition of this file) stated that only one phase runs per invocation and then stops for human review. **V0.4 deliberately removed that.** After P001, the pipeline runs continuously to P302 with no human gate; execution stops only when a Step's own 停止条件 is met. Human input arrives afterwards, as a change request processed by the Refactor Step. This is the Skill's central design commitment — treat any instruction that tells the executor to "stop and wait for the next task" as a defect to remove (V0.5 fixed exactly that in three templates).

## Critical invariant: cross-file consistency

**Inputs, outputs, file names, folder names, and P-numbers must match exactly across `SKILL.md`, each `SKILL-P0NN-*.md`, and each `TEMPLATE-*.md`.** Most historical defects in this Skill were this kind of cross-file drift — a phase referencing an input its producer never creates, a table row contradicting the phase file it points at, a template missing a field its driver requires.

When you change a phase's output filename, a folder name, or a template's fields, **grep the entire version folder for every other reference before considering the change done.** This is the repo's core quality property and every validation round has found violations of it.

## Structural conventions for each `SKILL-P0NN-*.md`

```yaml
---
name: {phase-name}-dev   # unique per file
description: 仕様駆動でアプリケーションを開発するときに、{このフェーズの成果物}を作成する。
---
```

Body order: `## 目的` → `## インプット文書` → `## アウトプット文書` (with `### アウトプットの記載内容` then `### アウトプットを参照する文書`) → `## 動作`.

Planning phases have a short `## 動作` (often 「共通指示以外は特になし」); agent-facing execution phases have a much longer one. **This asymmetry is intentional** — do not "fix" it by padding the short ones.

Common rules live once in `SKILL.md`'s 各フェーズ共通指示 — reference them from phase files, don't duplicate them.

## Two inline notations — keep them distinct

- **★FIXME★** — the Agent filled something in from its own assumption; **a human still needs to confirm it**. Unresolved.
- **★ACCEPTED★** (new in V0.7) — a limitation that was **considered and consciously accepted**, with what was considered, why it was rejected, and the residual risk written adjacent to it. Resolved; **reviewers and later validation rounds should not raise it again.**

Both go **inline, adjacent to the specific text they concern** — never batched at a document's end. ★ACCEPTED★ exists because the V0.6 validation round re-raised an already-settled decision: the decision lived only in `review-report.md`, which reviewers don't read — they read the SKILL files. So settled decisions belong in the SKILL files themselves.

## Design questions permanently closed by human decision — do not re-propose

These were each proposed, considered, and **rejected by the human**. They are marked ★ACCEPTED★ in the relevant SKILL files. Re-proposing them wastes a round:

| Topic | Why rejected |
|---|---|
| Structurally guaranteeing P008 test IDs match P102 implementation naming | 自動検証は複雑化し破綻しやすい |
| A formal granularity rule for fix files when one root cause breaks many tests | 形式化はAIが苦手で誤判定が増える |
| Automating CR scope classification (an impact-analysis engine) | 影響分析エンジンは破綻リスクが高い |
| Proving *sufficiency* of the migration-idempotency check (2 consecutive runs) | 十分性の証明はコストに見合わない — necessary-but-not-sufficient is accepted deliberately |

The underlying principle, settled in V0.6: **leave judgment to the AI, but require it to record the judgment and its reasoning so a human can verify afterwards** — rather than replacing judgment with mechanical rules.

## Naming trap: "OKF形式" is not Google's Open Knowledge Format

`SKILL.md` and several phase files call the checkbox+link table-of-contents format 「OKF形式」. This was investigated (`V0.2/review-report.md` appendix) and confirmed to be a self-invented format (`- [状態] 番号 [タイトル](相対リンク) — 一言概要`, 状態 ∈ `[ ]`/`[~]`/`[x]`) that only superficially resembles Google Cloud's OKF. Adopting the real standard was deliberately rejected — it lacks task-lifecycle semantics. Do not "correct" it toward Google's spec. If renaming it, update every occurrence consistently.

Related: `docs/CR.md` deliberately uses a **table, not OKF format**, because CR state has 5 values that 3-state checkboxes cannot express. This is documented in `TEMPLATE-CR.md` itself so the question doesn't get re-raised.

## CR handling (restructured in V0.7)

Three files with separated responsibilities. Before V0.7, `docs/CR.md` held both state and CR bodies, and that role collision generated defects in both V0.5 and V0.6; separating them removed the defect class structurally.

| File | Role | Written by |
|---|---|---|
| `docs/CR.md` | Status ledger only — table, no bodies, completed rows never deleted, single source of truth for state and priority | P901 / P903 / P904 |
| `docs/P901-cr-direction/CR-NNN.md` | The request. Human may edit it until state reaches 対応中 | P901 |
| `docs/P903-cr-records/CR-NNN.md` | Handling record. **Created by P903 before implementing** (the scope decision is a before-the-work judgment), then appended by P903 on completion, P904, P905 | P903/P904/P905 |

CR numbers are 3 digits, matching `U001`/`T001`/`A001`/`F001`/`ADR-001`. There is intentionally **no** `docs/P901-cr-direction.md` index file — `docs/CR.md` plays that role.

## Testbeds

Each `Vx.y_testbed/` validates that version by actually running it. `testbed.md` holds the 確認観点 and verdicts; `e2e-validation-report.md` holds the detailed findings that drive the next version. Read the latest one before revising the Skill — it is the working checklist.

`V0.7_testbed/` is the most useful reference: unlike the two before it (which were differential — copy the previous testbed, swap the Skill), it was **rebuilt from `docs/P001-requirement.md`** through the whole pipeline plus one full CR. 486 tests, all passing. Because it exercised phases the differential rounds never re-ran, it found far more (44) — that reflects the method change, not a regression in V0.7.

**Important about the technology stack.** The testbed apps use Starlette + Pydantic v2 + stdlib sqlite3, hashlib.scrypt, `unittest`, plain HTML/ES-module JS, and `node --test`. `docs/P001-requirement.md` asks for React+TS+Vite and FastAPI. **This divergence is intentional and is not a Skill defect** — the cloud sandbox had no access to pypi.org or registry.npmjs.org, so substitutes were chosen and recorded in ADR-001–003 and `docs/P101-impl-context.md`. Do not "fix" the existing testbeds toward the requirement document. Running locally you likely *do* have network access, so a future testbed could use the real stack — but that would be a new testbed, and the substitution rationale in the existing ones must stay.

Test commands for `V0.7_testbed/`:

```
cd server && python3 -m unittest discover -s tests -t .        # 262 tests
cd client && node --test 'tests/*.js'                          # 146
cd client && node --test 'tests/integration/*.js'              # 46
cd client && node --test 'tests/acceptance/test_*.js'          # 32
```

The quoted globs matter: `node --test tests/` fails with a module-resolution error, and Node's default pattern does not match these `test_*.js` filenames — it would silently run zero tests.

## When revising a version

1. Read the latest `Vx.y_testbed/e2e-validation-report.md` — it is the defect checklist.
2. Confirm with the human which findings are in scope. Some are deliberately deferred or closed (see above).
3. Copy the latest `Vx.y/` to a new folder; edit there.
4. Grep the new folder for cross-file consistency after every structural change.
5. Write `review-report.md` in the new folder, matching the established structure.
6. Build a new `Vx.y_testbed/` and actually run the Skill against it — every version so far has had defects that only appeared when executed, not when reviewed.
7. Update `README.md` (repo root) and `USER_GUIDE.md` if user-visible behavior changed.
