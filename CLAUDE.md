# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state — start here

**V0.9 is the latest version and is committed** (`git log` HEAD is `8a3ce80 V0.9`, working tree clean). V0.1–V0.7 were developed in Claude Cowork sessions running in a cloud sandbox; that workflow has since been fully handed off to Claude Code running locally, and V0.8/V0.9 were both developed and committed locally without incident.

**Pending human decision: whether to create V0.10 (or V1.0), and what goes in it.** `V0.9_testbed/e2e-validation-report.md` §3 documents **5 newly found issues, all low severity**: (1) P007's "コード格納先を初期化する" reads as if P007 itself performs it, when Executor (P102) actually does; (2) the word "完了" means different things in the Executor's per-task OKF sense vs. the Plan Loop Step's exit-condition sense, and only each phase's own text disambiguates it; (3) no phase assigns ownership of E2E harness topology decisions (proxying, cross-origin cookies) in a split client/server setup; (4) `docs/CR.md`'s priority column has no value for "rejected, not applicable"; (5) `SKILL-P302-deliver.md`'s version-bump policy only covers CR-driven increments, not the initial 0.x.x→1.0.0 baseline. As before, do **not** start the next version on your own initiative — the standing rule in this project is that the human decides each version's direction after reading the validation report. Summarize and ask; don't fix speculatively.

**Repo hygiene left over from the cloud sessions (still not cleaned up).** `_to_delete/` holds discarded files from the device-bridge era (stale `HEAD.lock*`/`index.lock*` variants, `_incoming_v06`/`_incoming_v07` diff staging dirs) — the bridge could not delete files, only move them, so cleanup was deferred. `.git/objects/` has 400+ stale `tmp_obj_*` files for the same reason. Locally you can just remove `_to_delete/` and run `git gc`. Also note some `V0.1/`/`V0.3/` files may still show as modified-unstaged from before these sessions (likely line-ending normalization); leave them unless asked.

## What this repository is

This is not an application codebase. It is the source of a Claude Code **Skill** (`spec-driven-dev`) that makes Claude Code follow the phases of a traditional Japanese waterfall/V-model development process instead of jumping from a vague request straight to code.

"Development" here means editing the Skill's own instruction Markdown. There is no build or lint tooling for the Skill itself. **However, the `Vx.y_testbed/` folders are different** — from `V0.4_testbed/` onward they contain a real, working meeting-room reservation application (Python backend, JS/TS frontend, hundreds of real tests) that was built *by* the Skill in order to validate it. Those have real test commands; see "Testbeds" below.

## Repository layout: versioned snapshots, not a normal source tree

Each top-level `Vx.y/` folder is a **complete, self-contained snapshot** of the Skill at that point — not an incremental diff or a shared module structure.

- Always work in the **highest-numbered `Vx.y/` folder** (currently `V0.9/`) unless told to look at an older one for comparison.
- To improve the Skill, create a **new `Vx.y/` folder** by copying the latest, rather than editing an existing version in place — unless the human explicitly says to patch the current latest directly (which they have done, e.g. for typo/表記ゆれ fixes).
- A version folder's contents are copied as-is into a target project's `.claude/skills/spec-driven-dev/` to be used.
- Every version that changes behavior gets a `review-report.md` in its folder. Match the established depth — see `V0.7/review-report.md`, `V0.8/review-report.md`, `V0.9/review-report.md`: each change gets 事象 (what was wrong) / Vx.y での変更 (what was changed) / rationale, plus explicit sections for what was deliberately *not* changed.
- `V0.9/USER_GUIDE.md` is the human-facing manual (requirement definition → initial build → change requests). Keep it in sync when CR handling or the build flow changes. Filename stays `USER_GUIDE.md`; when copying to a new version folder, also update its title line and internal `Vx.y/SKILL.md` path reference (V0.9's copy was found with a stale "(V0.8)" label left over from the copy — check for this each time).

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

The P-number scheme itself has been stable since V0.4; V0.6–V0.9 all changed phase *content* without renumbering or regrouping phases.

### The V0.4 design change — do not reintroduce per-phase human review

Earlier versions (and the previous edition of this file) stated that only one phase runs per invocation and then stops for human review. **V0.4 deliberately removed that.** After P001, the pipeline runs continuously to P302 with no human gate; execution stops only when a Step's own 停止条件 is met. Human input arrives afterwards, as a change request processed by the Refactor Step. This is the Skill's central design commitment — treat any instruction that tells the executor to "stop and wait for the next task" as a defect to remove (V0.5 fixed exactly that in three templates).

## Structural additions from V0.8 (kept in V0.9)

V0.8 introduced several structural mechanisms — beyond ordinary content edits — that are now load-bearing parts of the Skill's design. A future revision touching these areas should preserve them, not rediscover the problems they solve:

- **Task-granularity checkboxes in P007.** `TEMPLATE-P007-impl-direction.md` nests per-task (`U0NN-Txx`) OKF checkboxes inside each sprint file, so mid-sprint interruption/resume has a finer unit than "whole sprint." `SKILL-P102-implement.md` requires re-verifying a task's completion condition (rerunning its unit tests) on resume rather than trusting the checkbox, and forbids "scope-ahead" work on not-yet-reached tasks.
- **Nested `.inprogress` notation for Refactor.** During P903's internal re-run of P002–P302, `docs/.inprogress` is written as `P903:P0NN` rather than a bare P-number, so Step 0's resume logic can tell it's inside a CR without needing to consult `docs/CR.md` first. `SKILL.md`'s Step 0 checks `.inprogress` before the ledger for exactly this reason — don't reorder that.
- **P902 is idempotent.** Before backing up `docs/P001-requirement.md`, P902 checks whether the backup file already exists and whether the body already carries the target CR's change annotation, so a re-run after an interrupted session doesn't overwrite the original backup or double-apply the edit.
- **"テスト指示側の誤り" as a first-class P202 result category**, distinct from an actual code defect — requires citing the contradicting upstream spec and confirming no test coverage is lost. Exercised end-to-end (not just designed) for the first time in `V0.9_testbed` via an intentionally seeded bad expectation in A004.
- **`DEVIATED` status** added to P004's and P302's status vocabularies, for an environment constraint that a re-do would not resolve (paired with a mandatory ★ACCEPTED★-style rationale, non-blocking for release verdicts).
- **Semantic-versioning policy in P302** for CR-driven version bumps (bugfix=PATCH, backward-compatible feature=MINOR, breaking change=MAJOR; API-contract or data-model CRs are MINOR at minimum). Confirmed live in `V0.9_testbed`: CR-001 bumped `VERSION` 1.0.0 → 1.1.0.

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

Both go **inline, adjacent to the specific text they concern** — never batched at a document's end, except where a section's whole subject *is* a list of accepted trade-offs (e.g. ArchitectureHandbook's dedicated 割り切り一覧 chapter) — there, self-contained list items are fine. ★ACCEPTED★ exists because the V0.6 validation round re-raised an already-settled decision: the decision lived only in `review-report.md`, which reviewers don't read — they read the SKILL files. So settled decisions belong in the SKILL files themselves. V0.9 clarified one more nuance: marking something ★ACCEPTED★ means the trade-off itself won't be re-litigated, but it does **not** exempt it from ordinary cross-document consistency checks (e.g. P010).

## Design questions permanently closed by human decision — do not re-propose

These were each proposed, considered, and **rejected by the human**. They are marked ★ACCEPTED★ in the relevant SKILL files. Re-proposing them wastes a round:

| Topic | Why rejected |
|---|---|
| Structurally guaranteeing P008 test IDs match P102 implementation naming | 自動検証は複雑化し破綻しやすい |
| A formal granularity rule for fix files when one root cause breaks many tests | 形式化はAIが苦手で誤判定が増える |
| Automating CR scope classification (an impact-analysis engine) | 影響分析エンジンは破綻リスクが高い |
| Proving *sufficiency* of the migration-idempotency check (2 consecutive runs) | 十分性の証明はコストに見合わない — necessary-but-not-sufficient is accepted deliberately |

The underlying principle, settled in V0.6: **leave judgment to the AI, but require it to record the judgment and its reasoning so a human can verify afterwards** — rather than replacing judgment with mechanical rules. V0.8 and V0.9 reinforced this principle in new areas (e.g. the "テスト指示側の誤り" category, DEVIATED status) but did not add to or revisit this specific closed list.

## Naming trap: "OKF形式" is not Google's Open Knowledge Format

`SKILL.md` and several phase files call the checkbox+link table-of-contents format 「OKF形式」. This was investigated (`V0.2/review-report.md` appendix) and confirmed to be a self-invented format (`- [状態] 番号 [タイトル](相対リンク) — 一言概要`, 状態 ∈ `[ ]`/`[~]`/`[x]`) that only superficially resembles Google Cloud's OKF. Adopting the real standard was deliberately rejected — it lacks task-lifecycle semantics. Do not "correct" it toward Google's spec. If renaming it, update every occurrence consistently.

Since V0.8, P007 nests a second, task-level OKF list (`U0NN-Txx`) inside each sprint file's own OKF entry — this is the asymmetric-grouping case referenced above, not a separate format.

Related: `docs/CR.md` deliberately uses a **table, not OKF format**, because CR state has 5 values that 3-state checkboxes cannot express. This is documented in `TEMPLATE-CR.md` itself so the question doesn't get re-raised.

## CR handling (restructured in V0.7)

Three files with separated responsibilities. Before V0.7, `docs/CR.md` held both state and CR bodies, and that role collision generated defects in both V0.5 and V0.6; separating them removed the defect class structurally. `CR運用変更仕様.md`, the design spec this restructure implemented, has been deleted from the repo root now that V0.7–V0.9 have all confirmed the structure in production and this file's content is fully superseded by this section plus each version's `review-report.md`.

| File | Role | Written by |
|---|---|---|
| `docs/CR.md` | Status ledger only — table, no bodies, completed rows never deleted, single source of truth for state and priority | P901 / P903 / P904 |
| `docs/P901-cr-direction/CR-NNN.md` | The request. Human may edit it until state reaches 対応中 | P901 |
| `docs/P903-cr-records/CR-NNN.md` | Handling record. **Created by P903 before implementing** (the scope decision is a before-the-work judgment), then appended by P903 on completion, P904, P905 | P903/P904/P905 |

CR numbers are 3 digits, matching `U001`/`T001`/`A001`/`F001`/`ADR-001`. There is intentionally **no** `docs/P901-cr-direction.md` index file — `docs/CR.md` plays that role. A rejected CR is the one documented exception to "P903 creates the record file": if P901 decides on rejection at intake, P901 itself creates the record file, since a rejected CR never reaches P903 (V0.9 made this exception explicit in `SKILL-P901-cr-create.md` rather than leaving it as an implicit gap).

## Testbeds

Each `Vx.y_testbed/` validates that version by actually running it. `testbed.md` holds the 確認観点 and verdicts; `e2e-validation-report.md` holds the detailed findings that drive the next version. Read the latest one before revising the Skill — it is the working checklist.

**`V0.9_testbed/` is currently the most useful reference.** Like `V0.7_testbed`, it was rebuilt from the same starting requirement document (`docs/P001-requirement.md` before CR-001) through the whole pipeline, so it's a full pipeline run rather than a differential one. It resolved effectively all of the V0.7_testbed backlog (high 5 + medium 28 across V0.8, low 20 + 2 new across V0.9) and, notably, intentionally seeded a wrong test-direction expectation in A004 to exercise the "テスト指示側の誤り" P202 category end-to-end for the first time — V0.8_testbed had the mechanism but never hit a real case to exercise it. It found only 5 new issues, all low severity (listed under "Current state" above).

**Important about the technology stack.** `docs/P001-requirement.md` asks for React+TS+Vite and FastAPI. **`V0.7_testbed` is the outlier here, not the norm**: it substituted Starlette + Pydantic v2 + stdlib sqlite3, hashlib.scrypt, `unittest`, plain HTML/ES-module JS, and `node --test`, because the cloud sandbox it ran in had no access to pypi.org or registry.npmjs.org (recorded in ADR-001–003 and `docs/P101-impl-context.md` of that testbed). **`V0.8_testbed` and `V0.9_testbed`, built locally with normal network access, use the actually-requested stack**: React + TypeScript + Vite + Playwright on the client, Python + FastAPI + SQLite + `uv` + pytest on the server. Do not "fix" `V0.7_testbed` toward the requirement document — the substitution rationale recorded in it must stay as-is; it documents a real environment constraint, not a Skill defect.

Test commands for `V0.9_testbed/` (see also `V0.9_testbed/README.md`):

```
cd server && uv sync && uv run python -m pytest tests/ -v      # 121 tests (backend unit+integration+acceptance)
cd client && npm install && npx vitest run                     # 25 tests (frontend unit)
cd client && npx playwright install --with-deps chromium       # first run only
cd client && npx playwright test tests/integration/            # 9 tests
cd client && npx playwright test tests/acceptance/              # 5 tests
```

`V0.7_testbed/`'s older commands (`python3 -m unittest discover`, `node --test 'tests/*.js'`) only apply to that testbed's substitute stack — don't copy them into a new testbed that uses the real one.

## When revising a version

1. Read the latest `Vx.y_testbed/e2e-validation-report.md` — it is the defect checklist.
2. Confirm with the human which findings are in scope. Some are deliberately deferred or closed (see above).
3. Copy the latest `Vx.y/` to a new folder; edit there.
4. Grep the new folder for cross-file consistency after every structural change, **including stray references to the previous version number** (e.g. in `USER_GUIDE.md`'s title/path — see the "Repository layout" note above).
5. Write `review-report.md` in the new folder, matching the established structure.
6. Build a new `Vx.y_testbed/` and actually run the Skill against it — every version so far has had defects that only appeared when executed, not when reviewed.
7. Update `README.md` (repo root) and `USER_GUIDE.md` if user-visible behavior changed.
