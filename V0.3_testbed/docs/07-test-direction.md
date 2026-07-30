# 結合テスト定義(目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズ7の成果物です(V0.3ルールで再生成)。OKF形式(`SKILL.md`参照)の目次です。
> インプット: `docs/02-frontend-spec.md`, `docs/03-backend-spec.md`, `docs/04-impl-plan.md`, `docs/05-test-plan.md`

## ビルド手順(テスト前提)

* ビルド対象: `server/`(Python, Starlette/Pydantic — `docs/06-impl-direction.md`記載のFastAPI代替方針を継続)
* ビルドコマンド: 本検証環境はネットワーク分離のため `uv sync` は実行不可。事前インストール済みシステムパッケージ(`starlette`, `uvicorn`, `pydantic`)を用い、`cd server && python3 -c "from app.main import create_app; create_app(':memory:')"` でモジュールが正常にimport・初期化できることをビルド成功の代替確認とする。
* 成功条件: 上記コマンドが例外なく終了すること。
* 失敗時の記録方法: `docs/test-records/*.md` の該当タスクに「事前ビルド結果: FAIL」として記録し、以降のテストを `NOT RUN` とする。
* ビルド失敗時はテストへ進まない。

## テストタスク一覧(OKF形式)

- [x] T001 [フルユーザージャーニー(スプリント横断)](./07-test-direction/T001-full-user-journey.md) — ログイン→会議室登録→予約作成→カレンダー反映→編集→取消
- [x] T002 [権限をまたぐアクセス制御確認](./07-test-direction/T002-cross-cutting-authorization.md) — 一般ユーザーによる管理者専用API/画面へのアクセス拒否
- [x] T003 [同時実行時の排他制御(二重予約防止)](./07-test-direction/T003-concurrent-booking.md) — 同一会議室・同一時間帯への同時リクエストで二重予約が発生しないこと
- [x] T004 [エラーハンドリング一連の確認](./07-test-direction/T004-error-handling.md) — 不正なリクエストボディ・存在しないリソースへのアクセス時の挙動確認(参加者ID実在チェック・会議室capacity検証を含む。**手順6追加分が2026-07-30 17:00にFAIL → フェーズ8へ引き渡し、F002修正後の再テストでPASS**。詳細は`docs/test-records/`, `docs/08-fix-plan/08-fix-resolved.md`参照)
- [x] T005 [性能観点: カレンダー表示APIの応答時間](./07-test-direction/T005-performance-calendar.md) — ローカル計測での目安確認(参考値)

## フェーズ8への引き渡し状況(確認観点4)

今回のコードは、V0.2でT004においてFAILの原因となった「予約作成時に存在しない参加者IDを指定すると500エラーになる」不具合の修正を、実装時点(フェーズ6, U003-T2)から組み込んだ状態でスタートしている(`docs/03-backend-spec.md` 4章に既に明記されている仕様どおり)。そのため当初のT001〜T005は**全件PASS**した(詳細は `docs/test-records/20260730-1600-test-record.md` を参照)。この時点で確認観点4(フェーズ7全PASS→フェーズ8自動完了)を確認済み。

その後、確認観点2・3(修正サイクルが実際に回る場合の`ALL_RESOLVED`表記・OKF目次の`fixed/`付け替え)を実地検証するため、意図的に1件のバグ(`POST /api/rooms`のcapacity検証漏れによる500)を仕込みT004手順6として追加した(`docs/07-test-direction/T004-error-handling.md`補足参照)。2026-07-30 17:00の再実行でT004手順6のみFAILし(`docs/test-records/20260730-1700-test-record.md`)、フェーズ8でF002として修正指示を作成・修正・再テストしPASSした(`docs/test-records/20260730-1730-test-record.md`、`docs/08-fix-plan/08-fix-resolved.md`参照)。最終的にT001〜T005は全件PASSであり、未解決の修正課題は0件である。
