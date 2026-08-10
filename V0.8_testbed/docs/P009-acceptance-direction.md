# 受け入れ結合テスト定義(目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP009の成果物です。スプリントをまたぐ結合テスト・システムテスト・受入テストの目次(OKF形式)です。詳細は `docs/P009-acceptance-direction/A0NN-{test-name}.md` を参照してください。実行はP201(Reviewer Loop)で行います。
>
> テスト記録は `docs/test-records/YYYYMMDD-HHMM-test-record.md` に `TEMPLATE-test-record.md` の形式で残します。P201第1回(2026-08-09)で全11件実行(`docs/test-records/20260809-1900-test-record.md`、FAIL 5件・BLOCKED 1件含む)。P202・P203・P205を経て、当時のFAIL/BLOCKEDはすべて修正・再確認済み(`docs/test-records/20260809-2100-test-record.md`、`docs/P202-fix-plan/P202-fix-resolved.md`参照)。現時点で全11件PASS。

## テスト一覧(OKF形式)

- [x] A001 [主要業務フロー一気通貫シナリオ](./P009-acceptance-direction/A001-main-business-flow.md) — ログイン〜予約作成〜編集〜取消〜ログアウト(CR-001: オンライン会議URLの作成・API経由確認・編集を手順に追加、PASS。`docs/test-records/20260809-2230-test-record.md`参照)
- [x] A002 [権限まわり総合確認](./P009-acceptance-direction/A002-authorization-crosscheck.md) — 一般ユーザーの管理者専用画面・API拒否(PASS)
- [x] A003 [無効化された会議室名の履歴表示](./P009-acceptance-direction/A003-inactive-room-history-display.md) — U002とU003をまたぐ連携(PASS。当初FAILの原因(S05側はF001、S04側はF003)はいずれも修正済み)
- [x] A004 [参加者選択からの予約作成フロー](./P009-acceptance-direction/A004-participant-selection-flow.md) — U001(ユーザー)とU003(予約)をまたぐ連携(PASS。当初FAILの原因はF001で修正済み)
- [x] A005 [同時アクセスによる二重予約防止](./P009-acceptance-direction/A005-concurrent-booking-prevention.md) — 非機能(負荷)、実HTTPレベルの同時リクエスト(PASS)
- [x] A006 [カレンダー画面表示性能確認](./P009-acceptance-direction/A006-calendar-performance.md) — 非機能(性能)、3秒以内(PASS。当初BLOCKEDの原因はF001で修正済み。計測値は参考値)
- [x] A007 [セキュリティ総合確認](./P009-acceptance-direction/A007-security-crosscheck.md) — 非機能(セキュリティ)、未認証・パスワード保存(PASS)
- [x] A008 [構造化ログ出力確認](./P009-acceptance-direction/A008-structured-logging.md) — 非機能(運用・ログ監視)(PASS。当初FAILの原因(login_failedログ未実装)はF004で修正済み)
- [x] A009 [再起動耐性確認](./P009-acceptance-direction/A009-restart-resilience.md) — 運用観点(必須)、マイグレーション冪等性の実地検証(PASS)
- [x] A010 [受け入れシナリオ(初期セットアップ〜実運用)](./P009-acceptance-direction/A010-acceptance-setup-to-operation.md) — 発注者・運用者視点(PASS。当初FAILの原因はF001で修正済み)
- [x] A011 [予約作成のエラーハンドリング一連確認](./P009-acceptance-direction/A011-error-handling-sequence.md) — バリデーション→修正→重複→修正→成功の一連シナリオ(PASS)

## ビルド手順(全テスト共通の前提)

* ビルド対象: `server/`・`client/` の全モジュール(U001〜U005の全スプリントが完了していること)
* ビルドコマンド: `cd server && python -m pip install -e . && python -m pytest --collect-only`、`cd client && npm install && npm run build`
* 成功条件: いずれもエラー・警告なく終了すること
* 失敗時の記録方法: `docs/test-records/YYYYMMDD-HHMM-test-record.md` にビルド失敗の旨と出力ログを記録し、全テストタスクを `BLOCKED` として扱う
* ビルド失敗時はテストへ進まない

各テストタスクの詳細な前提条件・テストデータ・実行手順・合否判定基準は、`docs/P009-acceptance-direction/A0NN-*.md` を参照してください。
