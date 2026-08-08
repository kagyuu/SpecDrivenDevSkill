# 結合テスト定義(スプリント内/モジュール間) 兼 結合テスト指示書(目次)

> 本書は `spec-driven-dev` Skill フェーズP008の成果物(OKF形式の目次)です。
> インプット: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`、`docs/P007-impl-direction.md` と各 `U00N-*.md`
> **改訂(CR-001 / P903 2026-08-05)**: CR-001(予約にオンライン会議URL)により T019 を新規追加し、T016・T017 に手順を追加しました。

## 1. 本書の範囲

* 対象は、**各スプリントに閉じて実行できる結合テスト**(同一スプリント内のモジュール間連携、画面とAPIの接続、DB↔Repository↔Service↔APIの組み合わせ確認)である。
* 単体テストは `docs/P007-impl-direction.md`(P007)で指示済みのため、ここでは指示しない。
* スプリントをまたぐ結合テスト、システムテスト、受け入れテスト、非機能テストは `docs/P009-acceptance-direction.md`(P009)の対象であり、ここでは指示しない。
* 実行はP103でExecutorが行う。本フェーズでは実行しない。

## 2. 実行担当(Executor)への共通指示

* **テスト前に必ず対象スプリントの全モジュールをビルドする。** 手順は各テストタスクの「事前準備」に記載する。ビルドに失敗した場合はテストへ進まず、失敗内容を記録して BLOCKED とすること。
* **テスト失敗時に、その場で修正しないこと。** 具体的には次を禁止する。
  * アプリケーションコードを修正しない
  * テストコードをその場で都合よく変更しない
  * 失敗したテストをスキップしない
  * 期待値を変更して成功扱いにしない
  * 同じ失敗に対して場当たり的な再テストを繰り返さない
* 失敗内容はテスト記録に残し、次工程(Reviewer Loop、P201〜)の修正フェーズに引き渡す。
* **テスト記録**: `docs/test-records/YYYYMMDD-HHMM-test-record.md` に、`TEMPLATE-test-record.md` の共通形式で記録する。
* テストタスクが完了したら(PASS / FAIL / BLOCKED のいずれであっても記録が残った時点で)、本書の該当行のチェックボックスを `[x]` に更新すること。全テストが `[x]` になるまでP103は完了しない。
* **FAIL / BLOCKED が1件でも残っている場合は、Reviewer Loop(P201〜)への引き渡しが必要である。** その旨を第5章に記録すること。

## 3. 共通の前提とテストデータ

* 基準データセットは `docs/P006-test-plan.md` 5章に定めたものを用いる(`admin001` / `user001` / `user002` / `user003`(無効)、会議室A(収容10)/ B(収容4)/ C(無効)、翌営業日の予約1件)。
* 各テストタスクは、**開始時にDBファイルを削除して作り直し**、基準データセットを投入した状態から始める。ただし **T004(再起動確認)だけは例外**で、同じDBファイルを意図的に使い回す。
* 日付は固定値をハードコードせず、実行時に「本日」から相対で計算する。
* サーバーの起動方法・HTTPクライアントの選択は `docs/P006-test-plan.md` 1.1 に従う(`httpx` が使えない場合は、サーバープロセスを起動して `urllib.request` で叩く)。

## 4. テスト一覧(WBS)

### Sprint 1 `foundation-auth`

- [x] T001 [ログインとセッションCookieの発行](./P008-test-direction/T001-login-session.md) — API-01→API-03の連携とCookie属性
- [x] T002 [認証失敗と未認証アクセス](./P008-test-direction/T002-auth-failure.md) — 401系のエラー系シナリオ
- [x] T003 [S01ログイン画面とログインAPIの接続](./P008-test-direction/T003-s01-login-api.md) — 画面↔API連携
- [x] T004 [既存DBに対する再起動とマイグレーション差分適用](./P008-test-direction/T004-restart-migration.md) — 起動処理とDBの連携(同一DBを使い回す)

### Sprint 2 `master-management`

- [x] T005 [会議室CRUDの一気通貫](./P008-test-direction/T005-room-crud.md) — API↔Service↔Repository↔DB
- [x] T006 [会議室名の一意性と無効化後の再登録](./P008-test-direction/T006-room-name-uniqueness.md) — 部分ユニークインデックスの確認
- [x] T007 [管理者専用APIの認可](./P008-test-direction/T007-admin-authz.md) — 一般ユーザーによるアクセスの403
- [x] T008 [ユーザーCRUDと最後の管理者の保護](./P008-test-direction/T008-user-crud-last-admin.md) — 業務制約409
- [x] T009 [参加者候補スコープの権限と射影](./P008-test-direction/T009-attendee-candidates-scope.md) — `scope=attendee_candidates`
- [x] T010 [S06・S07画面とマスタAPIの接続](./P008-test-direction/T010-master-screens-api.md) — 画面↔API連携

### Sprint 3 `reservation-core`

- [x] T011 [予約の登録→一覧→詳細→更新→取消](./P008-test-direction/T011-reservation-lifecycle.md) — 予約APIのモジュール間連携
- [x] T012 [予約の重複検出と境界時刻](./P008-test-direction/T012-reservation-conflict.md) — 409とその境界
- [x] T013 [収容人数超過と予約の認可](./P008-test-direction/T013-capacity-and-authz.md) — 400/403のエラー系シナリオ
- [x] T014 [今後の予約がある会議室の無効化拒否](./P008-test-direction/T014-room-deactivate-blocked.md) — Sprint 2の暫定実装差し替えの確認

### Sprint 4 `reservation-ui`

- [x] T015 [S02カレンダーと予約APIの接続](./P008-test-direction/T015-calendar-grid-api.md) — グリッド描画とAPI
- [x] T016 [S02→S03の値の引き継ぎと登録完了](./P008-test-direction/T016-create-flow.md) — 画面間の連携。※CR-001の手順9〜10(オンライン会議URL)を追加して再実行しPASS
- [x] T017 [S04の編集・取消と権限による表示制御](./P008-test-direction/T017-detail-edit-cancel.md) — 画面↔API連携。※CR-001の手順8〜10(オンライン会議URLのリンク表示・編集)を追加して再実行しPASS
- [x] T018 [S05の期間フィルタ](./P008-test-direction/T018-my-reservations-filter.md) — 画面↔API連携

### ※CR-001 による追加(Sprint 3 / Sprint 4 の差分)

- [x] T019 [オンライン会議URLの登録・更新・削除と入力検証(API)](./P008-test-direction/T019-meeting-url.md) — API-14/15/16 と `004-meeting-url.sql` の差分適用

## 5. 引き渡し状況(Executorが更新する)

| 項目 | 値 |
| --- | --- |
| 全テスト完了 | **完了**(※CR-001 反映後: T001〜T019 の全19件を実施済み。第4章の全行が `[x]`) |
| FAIL件数 | **0**(T016 のFAILは Reviewer Loop の修正タスク F001 で解消済み) |
| BLOCKED件数 | 0 |
| Reviewer Loopへの引き渡し要否 | **不要**(引き渡し済み・解消済み。P205 での再実行で T016 は PASS) |

* ※CR-001(2026-08-05 / P903): T019 を新規実施(**PASS**)、T016・T017 を手順追加のうえ再実行(いずれも **PASS**)、`004-meeting-url.sql` 追加に伴い T004 を再実行(**PASS**)。FAIL / BLOCKED は0件。実行記録は `docs/test-records/20260805-1723-test-record.md`。

* 実行記録: `docs/test-records/20260805-1152-test-record.md`(T001〜T010、初回)/ `docs/test-records/20260805-1226-test-record.md`(T011〜T018、および T001〜T010 の退行確認としての再実行)
* T016 のFAILは、S03の参加予定人数チェックについて **クライアント側検証(P002 3.3 / U004-T2)が送信前に成立するため 400 `CAPACITY_EXCEEDED` に到達できない**という、設計文書間の矛盾に起因するものだった。**Reviewer Loop の修正タスク F001 で「T016 手順7 の期待結果が誤り」と確定し、P002 3.3・2.4・7.2 を根拠に手順7の期待結果を修正した(実装コードは変更なし)。** 詳細は `docs/P202-fix-plan/fixed/F001-t016-capacity-expectation.md`、`docs/P202-fix-plan/P202-fix-resolved.md`、および `docs/P007-impl-direction.md` 5章「未解決事項」#18 を参照。再実行記録は `docs/test-records/20260805-1620-test-record.md`。
* T016 の残り7手順、および T011〜T015・T017・T018 はすべてPASSである。
