# プログラム実装定義 兼 プログラミング指示書 — 目次

> 本書は `spec-driven-dev` Skill フェーズP007の成果物。`docs/P005-impl-plan.md` のスプリント構成にもとづき、各スプリントの実装指示を `docs/P007-impl-direction/U00N-*.md` に分割して作成する。単体テストの指示もここに含む。スプリント内/モジュール間の結合テストは `docs/P008-test-direction.md`、スプリントをまたぐ結合テスト・受け入れテストは `docs/P009-acceptance-direction.md` を参照(本書では指示しない)。

## コード格納先

※P021初回実行時に、本節の暫定ADR番号(見込み表記)を確定番号に更新した。

* フロントエンド: `client/`(フロントエンド技術の選定根拠はADR-001を参照。ビルドツールはnpmを用いる)
* バックエンド: `server/`(バックエンド技術の選定根拠はADR-002を参照。ビルドツールはuvを用いる)
* いずれも本フェーズ実行時点では未初期化のため、対象スプリントの該当タスクで標準ビルドツールによる初期化を行う。各スプリントファイル内の実装内容説明では、具体的な技術名(React/TypeScript/Vite、FastAPI等)への言及自体は妨げない(`SKILL-P007-impl-direction.md` のハードコード禁止は目次・見出し・概要文が対象であり、実装内容の詳細説明は対象外)。

## スプリント一覧(OKF形式)

- [x] U001 [foundation-and-auth](./P007-impl-direction/U001-foundation-and-auth.md) — DBスキーマ・マイグレーション基盤、認証(login/logout/me)、S01、会議室読み取りAPI
- [x] U002 [reservation-core](./P007-impl-direction/U002-reservation-core.md) — 予約の新規作成・一覧取得(重複チェック・収容人数チェック)、S02/S03/S05 ※CR-001対応済み(U002-T7追加)
- [x] U003 [reservation-management-and-rooms](./P007-impl-direction/U003-reservation-management-and-rooms.md) — 予約の更新・取消、会議室管理者機能、S04/S06 ※CR-001対応済み(U003-T7追加)
- [x] U004 [user-administration](./P007-impl-direction/U004-user-administration.md) — ユーザー管理者機能、S07、横断的認可の最終確認

## 未解決事項

* 現時点で、`docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md` の記述範囲内で実装指示を作成するにあたり、追加の不足・矛盾は見つかっていない。P010(設計書横断レビュー)で新たに矛盾が見つかった場合は、その修正結果を本書および各スプリントファイルに反映する。
* **(P102実装中に発見、U002-T6)** S03(予約作成画面)の「参加者(社員)」入力(`docs/P002-frontend-spec.md` §3 S03)には、選択肢として社員一覧が必要だが、`docs/P001-requirement.md`・`docs/P002-frontend-spec.md`・`docs/P003-backend-spec.md` のいずれにも一般ユーザーが呼べる社員一覧取得APIが定義されていない。唯一のユーザー一覧API `GET /api/users` は `docs/P003-backend-spec.md` §5.11により管理者専用である。P010(設計書横断レビュー)・P004(トレーサビリティマトリクス)のいずれもこの不整合を検出していなかった(トレーサビリティマトリクスはAPIの存在有無のみを確認し、認可範囲とUIの利用者層との整合までは確認していなかったため)。仕様外の拡張(新規API追加や既存APIの認可緩和)は行わず、`docs/P007-impl-direction/U002-reservation-core.md` U002-T6では参加者選択UIを「現在利用不可」の注記付きで実装し、`participant_ids` は常に空配列を送信する形にとどめた。人間の判断(新規API追加/認可範囲の見直し/CR起票)を要する。
* **(CR-001対応中(P903実装作業中)に発見、既存実装の欠陥)** `docs/P002-frontend-spec.md` §2 が定めるバリデーションエラーの共通レスポンス形式(`{"error_code": "VALIDATION_ERROR", "message": "..."}`, HTTP 400)は、`title`・`notes`・(今回追加の)`internal_memo` のような `Field(max_length=...)` 制約の違反時には実際には返っていない。FastAPI/Pydanticの既定の入力検証がPydanticスキーマ構築段階で先に例外を送出し、アプリ側の`ApiError`ハンドラを経由しないため、実際のレスポンスはPydantic/FastAPI既定の `{"detail": [...]}` 形式・HTTP 422になる(実際に `POST /api/reservations` へ101文字の`title`を送るスクリプトで確認した実測結果)。これはCR-001が原因で新たに生じた不整合ではなく、既存の全ての長さ・形式制約フィールド(`title`の100文字、`notes`の500文字等)に共通する既存の欠陥であり、P003・P004・P010のいずれの工程でも検出されていなかった(理由: 従来のテストはPydanticスキーマ単体の構築時バリデーションのみを確認しており、実際のHTTPエンドポイント経由での応答形式までは確認していなかったため)。CR-001のスコープ外(CRと無関係な既存実装の修正)のため、本CRでは修正しない。今回追加した `internal_memo` の300文字超過テストは、この実際の422/`detail`形式を前提に書く(架空のカスタム形式を期待値にしない)。人間の判断(既存フィールドを含めた一括修正のCR起票/バリデーション例外ハンドラの追加)を要する。
