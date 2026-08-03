# 結合テスト定義(スプリント内/モジュール間) 兼 結合テスト指示書 — 目次(OKF形式)

> 本書は `spec-driven-dev` Skill フェーズP008の成果物です。インプット文書: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`、`docs/P007-impl-direction.md` およびU001〜U004。
> 対象範囲: 各スプリントに閉じて実行できる結合テスト、および同一スプリント内の複数モジュール間の連携テストのみ。スプリントをまたぐ結合テスト・システムテスト・受入テストは `docs/P009-acceptance-direction.md` を参照する。
> テスト記録の記録先: `docs/test-records/YYYYMMDD-HHMM-test-record.md`(P103で作成)。

## 目次

- [x] T001 [ログイン成功とGET /api/me疎通](./P008-test-direction/T001-login-success.md) — sprint1、正常系
- [x] T002 [ログイン失敗(ID/パスワード不一致)](./P008-test-direction/T002-login-invalid-credentials.md) — sprint1、異常系
- [x] T003 [無効化済みユーザーのログイン拒否](./P008-test-direction/T003-login-inactive-user.md) — sprint1、異常系
- [x] T004 [ログアウト後のGET /api/me拒否](./P008-test-direction/T004-logout-then-me.md) — sprint1、モジュール間連携
- [x] T005 [会議室登録と一覧反映](./P008-test-direction/T005-room-create-and-list.md) — sprint2、正常系
- [x] T006 [会議室名重複エラー](./P008-test-direction/T006-room-duplicate-name.md) — sprint2、異常系
- [x] T007 [一般ユーザーによる会議室管理API拒否](./P008-test-direction/T007-room-forbidden-general-user.md) — sprint2、異常系
- [x] T008 [ユーザー登録と初期パスワードでのログイン](./P008-test-direction/T008-user-create-and-login.md) — sprint2、モジュール間連携(sprint1のログインAPIを利用)
- [x] T009 [社員ID重複エラー](./P008-test-direction/T009-user-duplicate-employee-id.md) — sprint2、異常系
- [x] T010 [管理者の自己無効化禁止](./P008-test-direction/T010-user-self-deactivation-blocked.md) — sprint2、異常系
- [x] T011 [予約作成とカレンダー一覧反映](./P008-test-direction/T011-reservation-create-and-calendar.md) — sprint3、正常系
- [x] T012 [予約重複エラー(409)](./P008-test-direction/T012-reservation-overlap-conflict.md) — sprint3、異常系
- [x] T013 [終了時刻が開始時刻以前のバリデーションエラー](./P008-test-direction/T013-reservation-invalid-time-range.md) — sprint3、異常系
- [x] T014 [存在しない会議室IDでの予約作成エラー](./P008-test-direction/T014-reservation-room-not-found.md) — sprint3、異常系
- [x] T015 [予約詳細取得](./P008-test-direction/T015-reservation-detail.md) — sprint4、正常系
- [x] T016 [予約者本人による編集成功](./P008-test-direction/T016-reservation-edit-by-owner.md) — sprint4、正常系
- [x] T017 [予約者本人・管理者以外による編集拒否](./P008-test-direction/T017-reservation-edit-forbidden.md) — sprint4、異常系
- [x] T018 [予約取消と参加者データのCASCADE削除確認](./P008-test-direction/T018-reservation-delete-cascade.md) — sprint4、正常系
- [x] T019 [マイ予約一覧の期間フィルタ](./P008-test-direction/T019-my-reservations-period-filter.md) — sprint4、正常系
- [x] T020 [予約更新時の重複チェック(自分自身除外・他予約との重複)](./P008-test-direction/T020-reservation-update-overlap.md) — sprint4、異常系

## 進捗更新ルール

* 各テストタスクが完了したら(PASS/FAIL/BLOCKEDいずれの結果であっても記録が残った時点で)、Executorは該当行のチェックボックスを `[x]` に更新する。
* 全テストが `[x]` になるまでP103は完了しない。FAIL/BLOCKEDが残っている場合は、Reviewer Loop(P201〜)への引き渡しが必要である旨をここに明記する(現時点では未実施のため空欄)。

## P103実行結果 (2026-08-03)

* T001〜T020すべて実施・PASS。詳細記録: `docs/test-records/20260803-1830-test-record.md`。
* Reviewer Loop(P201〜)への引き渡しが必要なFAIL/BLOCKEDは無し。
* 実行コマンドは指示書記載の `uv run pytest` ではなく `python3 -m unittest`(同一テストID)で代替した。理由は `docs/P101-impl-context.md`(サンドボックスがpypi.orgに接続できずpytestを導入できない)を参照。

## 未解決事項

* 特になし。
