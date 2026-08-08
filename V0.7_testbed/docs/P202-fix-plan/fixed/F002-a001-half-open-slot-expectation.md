あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F002 — A001 手順5 の期待結果(占有スロット)を半開区間の設計判断に合わせる

## 【対応する失敗テスト】A001

* 1件のみ。`docs/P009-acceptance-direction/A001-reservation-business-flow.md` 手順5。
* 本F002は **T016 とは根本原因が異なる**ため、まとめない(T016 は F001 で扱う)。

## 【障害記録】

* テスト記録: `docs/test-records/20260805-1603-test-record.md` の A001 ブロック(P201 第1回で検出)。
* 失敗コマンド: `cd client && node --test tests/acceptance/test_a001_business_flow.js`
* 失敗内容: 手順5「S02に戻り、13:00・13:30 のセルに予約が表示されることを確認する(終了時刻は 13:30 とする)」に対し、13:00 のセルは「山田 太郎 / 定例会議」が表示されるが、**13:30 のセルは空き(`+`)**である。

```text
not ok 5 - 手順5: S02に戻り 13:00・13:30 のセルに予約が表示される(終了時刻は13:30)
    13:30 のセルにも予約が表示されること(A001 手順5)
    + actual - expected
    + '+'
    - '山田 太郎 / 定例会議'
```

* 手順1〜4・6〜10 はすべて期待どおり(10手順中9手順 PASS)。

## 【参照ファイル】

* `docs/ADR.md` ADR-007「決定内容」(重複の定義=半開区間 `[start, end)` の交差。境界一致は重複しない)
* `docs/P002-frontend-spec.md` 3.2(S02のグリッド定義)
* `docs/P009-acceptance-direction/A001-reservation-business-flow.md` 手順5・手順8・期待結果
* `client/src/lib/grid.js`(`occupiedSlots` / `buildOccupancy` / `reservationAt`)
* `client/src/views/s02-calendar.js`(`dayGrid`)
* `client/tests/acceptance/test_a001_business_flow.js`
* `client/tests/test_grid.js`(`occupiedSlots` の単体テスト)

## 【調査方針】

1. ADR-007 の決定内容を確認する。「同一 `room_id`・同一 `reserved_date` の2予約 A・B が `A.start_time < B.end_time AND B.start_time < A.end_time` を満たすとき重複とする(半開区間 `[start, end)` の交差)。境界一致(09:00-10:00 と 10:00-11:00)は重複しない。」
2. `client/src/lib/grid.js` の `occupiedSlots` が同じ規約(`at >= start && at < end`)であることを確認する。13:00-13:30 の予約が占有するのは 13:00 のみである。
3. A001 の**同一文書内の整合性**を確認する。手順8は「15:00・15:30 に予約が表示される」(予約は 15:00-16:00)と書かれており、半開区間と整合している。すなわち矛盾しているのは手順5の「13:30」の記述だけである。
4. 仮に「13:30 も占有する」ように実装を変えた場合の波及を確認する。終了時刻スロットまで占有色になると、13:00-13:30 と 13:30-14:00 の連続予約(ADR-007により重複しない、正当な予約)がグリッド上で同一セルを争うことになり、ADR-007 と P002 3.2 の両方に反する。したがって実装側の変更は取り得ない。

## 【修正方針】

* **結論: テスト指示(A001 手順5)の期待結果が誤り**である。`SKILL-P202-fix-plan.md` の「テスト指示や期待結果に誤りがあった → `docs/P009-acceptance-direction.md` および各 `A000-{test-name}.md` を修正する」に該当する。**アプリケーションコードは変更しない。**
* 具体的な修正内容:
  1. `docs/P009-acceptance-direction/A001-reservation-business-flow.md` 手順5 を、半開区間に整合する記述へ書き換える。
     * 「S02に戻り、**13:00 のセルに予約が表示され、13:30 のセルは空きのまま**であることを確認する(終了時刻は 13:30。ADR-007 の半開区間 `[start, end)` により、終了時刻のスロットは占有しない)」。
     * 【期待結果】側にも、占有スロットの判定規約が ADR-007 に従うことを1行で明記する。
  2. `client/tests/acceptance/test_a001_business_flow.js` の手順5 のアサーションを、上記の期待結果に合わせて書き換える(13:00 は予約表示・13:30 は `+`)。**アサーションを削除して回避するのではなく、正しい期待値に置き換える。**
* 範囲を広げないこと。`grid.js`・`s02-calendar.js`・ADR-007・P002 3.2 はいずれも変更しない。

## 【試行錯誤してよい範囲】

* 上記【参照ファイル】の読み取り、`node --test` によるテスト再実行。
* 占有スロットの実測確認(一時的なログ出力。確認後に必ず除去する)。
* アプリケーションコード(`client/src/**`、`server/src/**`)の恒久的な変更は行わない。

## 【修正成功時に更新するdocs】

* `docs/P009-acceptance-direction/A001-reservation-business-flow.md`(手順5 と期待結果。必須)
* `docs/P202-fix-plan/fixed/F002-a001-half-open-slot-expectation.md`(修正内容の詳細)
* `docs/P202-fix-plan/P202-fix-resolved.md`(概要)

## 【ロールバック条件】

* 作業開始前に、資産一式を `meeting-room-YYYYMMDDHHMMSS.zip` として退避しておく(本プロジェクトはGit管理外)。
* A001 が PASS にならない場合、または他の受け入れ結合テスト・単体テストに退行が出た場合は、退避した資産から本タスクの変更のみを戻す。F001 の変更は戻さない。

## 【検証コマンド】

* `cd client && node --test tests/acceptance/test_a001_business_flow.js`(手順1〜10すべてPASS)
* `cd client && node --test 'tests/acceptance/test_*.js'`(他の受け入れテストが退行していないこと)
* `cd client && node --test 'tests/*.js'`(単体126件、特に `test_grid.js` が退行していないこと)

## 【完了条件】

* A001 の10手順すべてが PASS。
* クライアント単体・結合・受け入れに退行がない。
* `docs/P009-acceptance-direction/A001-reservation-business-flow.md` が更新されている。
* アプリケーションコードの差分が0であること。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

---

# 【修正結果】(P203で追記)

## 判定

* **RESOLVED**(2026/08/05)

## 実施した内容

1. **どちらが正か**の確定(【調査方針】1〜4を実施):
   * `docs/ADR.md` ADR-007「決定内容」が「半開区間 `[start, end)` の交差」「境界一致(09:00-10:00 と 10:00-11:00)は重複しない」と定めている。ADRは設計判断の根拠文書であり、テスト指示より上流である。
   * `client/src/lib/grid.js` の `occupiedSlots` は `at >= start && at < end` で占有スロットを決めており、ADR-007 と一致する。13:00-13:30 の予約が占有するのは 13:00 のみである。
   * A001 の**同一文書内**でも、手順8「15:00・15:30 に予約が表示される」(予約は 15:00-16:00)は半開区間と整合している。矛盾していたのは手順5の「13:30」の記述だけである。
   * 仮に終了時刻スロットまで占有させると、13:00-13:30 と 13:30-14:00 という(ADR-007により重複しない)正当な連続予約が同一セルを争うことになり、ADR-007・P002 3.2 の双方に反する。よって**実装側の変更は取り得ない**。
2. **テスト指示の修正**: `docs/P009-acceptance-direction/A001-reservation-business-flow.md`
   * 手順5 を「**13:00 のセルに予約が表示され、13:30 のセルは空きのまま**であることを確認する(終了時刻は 13:30 とする)」に変更し、ADR-007 への参照を併記した。
   * 【期待結果】の「手順8・10」を「手順5・8・10」に拡張し、占有スロットの判定規約(ADR-007)と具体例(13:00-13:30 → 13:00 のみ / 15:00-16:00 → 15:00・15:30)を明記した。修正経緯(F002)も記載した。
3. **テストコードの修正**: `client/tests/acceptance/test_a001_business_flow.js` 手順5
   * 13:30 のセルが `+` であること、`is-reserved` が付いていないことを検証する形に置き換えた(13:00 側の検証はそのまま維持)。

## 変更したソースコード

* **アプリケーションコードの変更は0件**(`client/src/**` / `server/src/**` に差分なし)。
* テストコード: `client/tests/acceptance/test_a001_business_flow.js`(手順5のみ)

## 更新したdocs

* `docs/P009-acceptance-direction/A001-reservation-business-flow.md`

## 実行したテスト / テスト結果

| コマンド | 結果 |
| --- | --- |
| `cd client && node --test tests/acceptance/test_a001_business_flow.js` | 10 tests / **10 pass / 0 fail** |
| `cd client && node --test 'tests/acceptance/test_*.js'` | 31 tests / **31 pass** |
| `cd client && node --test 'tests/*.js'`(`test_grid.js` を含む) | 126 tests / **126 pass** |

## 残課題

* なし。ADR-007・P002 3.2・`grid.js` はいずれも変更していない。

## 修正経緯

* P201 第1回(2026/08/05 16:03)で A001 手順5 がFAIL(10手順中9手順PASS)。テスト記録 `docs/test-records/20260805-1603-test-record.md` に記録。
* P202 で F002 を起票し、P203 で **テスト指示側の誤り**と確定して修正。`docs/P202-fix-plan/P202-fix-unresolved.md` に該当記載はない(未解決として記録されたことがないため、コピー・削除の対象なし)。
