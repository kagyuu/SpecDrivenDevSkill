# プログラム実装定義(目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズP007の成果物です。Executor(実装担当Agent)への実装指示の目次(OKF形式)です。各スプリントの詳細な実装指示は `docs/P007-impl-direction/U0NN-{sprint-name}.md` を参照してください。
>
> コード格納先: `client/`(フロントエンド技術。`docs/ADR.md` ADR-001参照)、`server/`(バックエンド技術。`docs/ADR.md` ADR-002参照)。両ディレクトリともこのフェーズで新規に初期化する(現時点で存在しないため、U001タスクで標準のビルドツール — フロントエンドはnpm、バックエンドはuv — によるディレクトリ初期化を行う)。ADR番号は当初「ADR-001見込み」「ADR-002見込み」と暫定表記していたが、P021(Overview Step)実行により確定した(旧暫定表記は解消済み)。

## スプリント一覧(OKF形式)

- [x] U001 [foundation-and-auth](./P007-impl-direction/U001-foundation-and-auth.md) — プロジェクト基盤・全データモデル・認証・S01ログイン画面
- [x] U002 [room-management](./P007-impl-direction/U002-room-management.md) — 会議室CRUD API・S06会議室管理画面
- [x] U003 [reservation-core-and-calendar](./P007-impl-direction/U003-reservation-core-and-calendar.md) — 予約作成・一覧・重複チェック(排他制御)・S02カレンダー画面・S03予約作成画面(CR-001: オンライン会議URL追加、U003-T7〜T9完了)
- [x] U004 [reservation-detail-and-mylist](./P007-impl-direction/U004-reservation-detail-and-mylist.md) — 予約詳細・更新・取消・マイ予約一覧・S04/S05画面(CR-001: オンライン会議URL追加、U004-T6〜T7完了)
- [x] U005 [user-management-and-hardening](./P007-impl-direction/U005-user-management-and-hardening.md) — ユーザーCRUD API・S07画面・横断ナビゲーション結線・ログ/エラー形式の最終確認

## 未解決事項

現時点で `docs/P002-frontend-spec.md`〜`docs/P006-test-plan.md` を参照した範囲では、実装タスクに落とし込めない不足・矛盾は見つからなかった。各文書中の★FIXME★項目(社員ID書式、営業時間帯、パスワードポリシー等)は、いずれも各タスクの「参照すべき仕様箇所」でその仮定を踏襲する形で実装可能なため、本節への追加記載はない。
