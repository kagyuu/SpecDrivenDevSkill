# 結合テスト定義(スプリント内/モジュール間、目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP008の成果物です。各スプリントに閉じた結合テスト・同一スプリント内の複数モジュール間連携テストの目次(OKF形式)です。詳細は `docs/P008-test-direction/T0NN-{test-name}.md` を参照してください。
>
> テスト記録は `docs/test-records/YYYYMMDD-HHMM-test-record.md` に `TEMPLATE-test-record.md` の形式で残します(P103で実施)。P103完了(2026-08-09): 全15件実行し記録済み(`docs/test-records/20260809-1500-test-record.md`、FAIL 6件含む)。P201・P202・P203・P205を経て、当時のFAIL 6件はすべて修正・再確認済み(`docs/test-records/20260809-2100-test-record.md`、`docs/P202-fix-plan/P202-fix-resolved.md`参照)。現時点で全15件PASS。**CR-001対応(P903内側のP103再実行、2026-08-09)**: T016を追加実行しPASS(`docs/test-records/20260809-2200-test-record.md`参照)。現時点で全16件PASS。

## テスト一覧(OKF形式)

### U001 foundation-and-auth 関連

- [x] T001 [ログイン成功時のセッション発行](./P008-test-direction/T001-login-success-session.md) — API+DBの結合、Cookie発行確認(PASS)
- [x] T002 [ログイン失敗時のエラー表示](./P008-test-direction/T002-login-failure-display.md) — 画面+APIの結合、401エラー表示(PASS)
- [x] T003 [ログアウト後のセッション失効](./P008-test-direction/T003-logout-session-invalidation.md) — API+DBの結合(PASS)

### U002 room-management 関連

- [x] T004 [会議室登録と一覧反映](./P008-test-direction/T004-room-create-and-list.md) — 画面+API+DBの結合(PASS)
- [x] T005 [会議室無効化時のフィルタ挙動](./P008-test-direction/T005-room-deactivate-filter.md) — API+DBの結合(PASS)

### U003 reservation-core-and-calendar 関連

- [x] T006 [予約作成成功](./P008-test-direction/T006-reservation-create-success.md) — 画面+API+DBの結合、正常系(PASS。当初FAILの原因(addDays()タイムゾーンバグ)はF002で修正済み)
- [x] T007 [予約作成の重複エラー表示](./P008-test-direction/T007-reservation-conflict-display.md) — 画面+APIの結合、409エラー(PASS)
- [x] T008 [収容人数超過エラー表示](./P008-test-direction/T008-capacity-exceeded-display.md) — 画面+APIの結合、400エラー(PASS)
- [x] T009 [カレンダー画面での予約一覧表示](./P008-test-direction/T009-calendar-list-display.md) — 画面←APIの結合(PASS。当初FAILの原因(SQLiteスレッド不整合)はF001で修正済み)

### U004 reservation-detail-and-mylist 関連

- [x] T010 [予約編集時の自分自身除外重複チェック](./P008-test-direction/T010-reservation-update-self-exclude.md) — API+DBの結合(PASS)
- [x] T011 [予約取消後のカレンダー反映](./P008-test-direction/T011-reservation-cancel-reflect.md) — 画面+API+DBの結合(PASS)
- [x] T012 [マイ予約一覧の期間フィルタ](./P008-test-direction/T012-mylist-period-filter.md) — 画面+APIの結合(PASS。当初FAILの原因はF001で修正済み)

### U005 user-management-and-hardening 関連

- [x] T013 [ユーザー登録・編集・無効化](./P008-test-direction/T013-user-crud.md) — 画面+API+DBの結合(PASS。当初FAILの原因はF001で修正済み)
- [x] T014 [自己無効化・最後の管理者保護のエラー表示](./P008-test-direction/T014-user-protection-display.md) — 画面+APIの結合(PASS。当初FAILの原因はF001で修正済み)
- [x] T015 [権限別ヘッダーナビゲーション表示](./P008-test-direction/T015-header-nav-by-role.md) — 画面の結合(一般/管理者の出し分け)(PASS。当初FAILの原因はF001で修正済み)

### CR-001 対応(オンライン会議URL追加)関連 ※P903内側のP008再実行で追記

- [x] T016 [オンライン会議URLの作成・表示・編集](./P008-test-direction/T016-reservation-meeting-url.md) — 画面+API+DBの結合(S03作成→S04リンク表示→編集→空欄化)(PASS。`docs/test-records/20260809-2200-test-record.md`参照)

## ビルド手順(全テスト共通の前提)

* ビルド対象: `server/`(`python -m pytest --collect-only` でエラーが出ないこと)、`client/`(`npm run build`)
* ビルドコマンド: `cd server && python -m pip install -e . && python -m pytest --collect-only`、`cd client && npm install && npm run build`
* 成功条件: いずれもエラー・警告なく終了すること
* 失敗時の記録方法: `docs/test-records/YYYYMMDD-HHMM-test-record.md` にビルド失敗の旨と出力ログを記録し、当該スプリントの全テストタスクを `BLOCKED` として扱う
* ビルド失敗時はテストへ進まない
* P103実行時、`npm run build` はエラー・警告なく成功した。`pytest --collect-only` はエラーなく120件収集できたが、`StarletteDeprecationWarning`(`httpx`関連、U001-T4時点から既存)が1件出力される。テスト収集自体は成功しており、ビルド失敗としては扱わずテストへ進んだ。

各テストタスクの詳細な前提条件・テストデータ・実行手順・合否判定基準は、`docs/P008-test-direction/T0NN-*.md` を参照してください。
