あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F004

## 【対応する失敗テスト】A004

## 【障害記録】

* `docs/test-records/20260811-0530-test-record.md` A004参照。手順3(既存予約10:00-11:00に対し、背中合わせの11:00-12:00を新規作成)で、テストは409 `RESERVATION_CONFLICT` を期待していたが、実際は201(予約成立)だった。手順4(09:00-10:00、逆側の背中合わせ)も同様の構造であり、手順3で停止したため未到達だが同じ結果になると判断できる。
* 原因区分: **テスト指示側の誤り**。

### 証拠(矛盾する上位文書の該当箇所)

* `docs/P003-backend-spec.md` §5.9「重複判定ロジック」に以下の記載がある(原文引用):
  > この判定式の性質上、`new.start_time == existing.end_time` または `new.end_time == existing.start_time`(前後の予約と時刻がぴったり接する、いわゆる背中合わせの予約)は**重複とみなさない**。例: 会議室Xに10:00-11:00の予約が既にある場合、同じ会議室Xに11:00-12:00の予約を新規作成することは重複エラーにならず成立する。この境界仕様は意図的な設計判断であり(半開区間モデルの自然な帰結)、実装・テストの双方でこの通りに扱うこと。
* `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md` の手順3・4の期待結果は、この明文の規定と正面から矛盾する(手順3・4はまさに「背中合わせの予約」のケースであるにもかかわらず、409を期待している)。
* コード側が本当にP003 §5.9どおりに実装されているかを、本タスクの一部として再確認した。
  * `server/app/validation/reservation.py` の `overlaps()` は `NOT (new_end <= existing_start or new_start >= existing_end)` を実装しており、P003 §5.9のSQL実装例と一致する。
  * `server/app/repositories/reservations.py` の `find_conflicting()` のSQLも同一のロジック。
  * これらは `server/tests/validation/test_reservation.py::test_overlaps_false_when_back_to_back_new_starts_at_existing_end` / `test_overlaps_false_when_back_to_back_new_ends_at_existing_start`、および `server/tests/api/test_reservations_api.py::test_post_reservation_back_to_back_is_not_conflict` によってすでに単体・API両レベルで「背中合わせは重複にならない(201になる)」ことが検証され、いずれもPASSしている。
  * したがって、コード側は仕様(P003 §5.9)どおりに正しく実装されている。誤っているのはA004のテスト指示(手順3・4の期待結果)である。

### カバレッジが失われないことの根拠

* 「背中合わせの予約は重複にならない」という観点は、上記のとおり以下のテストで既に確認されている。
  * `server/tests/validation/test_reservation.py`(純粋関数レベル、境界値2パターン)
  * `server/tests/api/test_reservations_api.py::test_post_reservation_back_to_back_is_not_conflict`(API レベル)
* A004の期待結果を訂正しても、この観点の検証がテストスイートから失われることはない。A004自体は、訂正後も「複数ユーザーがまたがるシステム全体のフロー」としての価値(手順2の重なりケースがシステム全体を通して409になることの確認)を維持する。

## 【参照ファイル】

* `docs/P003-backend-spec.md` §5.9
* `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md`
* `server/app/validation/reservation.py`
* `server/app/repositories/reservations.py`
* `server/tests/validation/test_reservation.py`
* `server/tests/api/test_reservations_api.py`

## 【調査方針】

* 上記のとおり完了。追加調査は不要と判断する。

## 【修正方針】

* `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md` の【期待結果】・【合否判定基準】を、P003 §5.9の規定に合わせて訂正する。
  * 手順3・4は「重複にならず201(予約成立)になる」ことを期待結果とする。
  * 訂正の経緯(なぜ409から201に変わったか、根拠は何か)を、本文中に「※P202 F004にもとづき訂正」の注記とともに残す(後から読む人が、これが改ざんではなく訂正であることを判別できるようにする)。
* `client/tests/acceptance/a004_reservation_conflict_system_check.spec.ts` の該当アサーションを、訂正後の期待結果(201)に合わせて更新する。
* コード修正は行わない。

## 【試行錯誤してよい範囲】

* 該当なし(ソースコード変更を伴わない)。テスト指示ドキュメントとテストコードの期待値のみを訂正する。

## 【修正成功時に更新するdocs】

* `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md`(訂正)

## 【ロールバック条件】

* 該当なし(ソースコード変更を伴わない)。

## 【検証コマンド】

* `cd client && npx playwright test tests/acceptance/a004_reservation_conflict_system_check.spec.ts`

## 【完了条件】

* 上記検証コマンドが成功する(訂正後の期待値=201で手順3・4がPASSする)。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* この修正はソースコード変更を伴いません(テスト指示側の誤りの訂正)。
* 訂正内容と根拠を `docs/P202-fix-plan/P202-fix-resolved.md` に明記してください(「変更したソースコード: なし(テスト指示側の誤りのため、docs/P009-acceptance-direction/A004-*.mdを修正)」の形式)。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 該当なし(本タスクは未解決になる見込みがない)。

---

## 修正結果(P203)

* 実施日: 2026-08-11
* 変更したソースコード: **なし(テスト指示側の誤りのため、`docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md` および `client/tests/acceptance/a004_reservation_conflict_system_check.spec.ts` を修正)**。
* 更新したdocs: `docs/P009-acceptance-direction/A004-reservation-conflict-system-check.md`(【期待結果】・【合否判定基準】を、`docs/P003-backend-spec.md` §5.9の規定に合わせて訂正し、訂正の経緯・根拠へのリンクを本文に追記)。
* 実行したテスト: `cd client && npx playwright test tests/acceptance/a004_reservation_conflict_system_check.spec.ts`
* テスト結果: PASS。A004はFAIL→PASSに変わった。
* 残課題: なし。
* 修正経緯: 初回対応で解決(過去ループでの未解決記録なし)。判定根拠は本ファイル冒頭の【障害記録】に記載したとおり(P003 §5.9の明文引用、コード実装が仕様どおりであることの確認、既存テストによりカバレッジが失われないことの確認)。
