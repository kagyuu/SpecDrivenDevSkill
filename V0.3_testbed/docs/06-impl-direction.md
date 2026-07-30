# プログラム実装定義(目次) — 会議室予約システム

> 本書は `spec-driven-dev` Skill フェーズ6の成果物です(V0.3ルールで再生成)。OKF形式(`SKILL.md`参照)の目次です。
> インプット: `docs/02-frontend-spec.md`, `docs/03-backend-spec.md`, `docs/04-impl-plan.md`, `docs/05-test-plan.md`

## コード格納先

* クライアント・サーバ型のため `server/`(Python, uv)、`client/`(静的フロントエンド)を用いる。
* **仕様からの逸脱(要記録)**: `docs/01-requirement.md` はフロントエンドに React 18 + TypeScript + Vite を、バックエンドに FastAPI を指定しているが、本検証環境はネットワーク分離されており `npm install`/`pip install` によるパッケージ取得が一切できない(レジストリへの到達が拒否される)。そのため `client/` は依存パッケージ不要の素のHTML/CSS/JavaScript(ES Modules、ビルド不要)で実装し、バックエンドは FastAPI の内部基盤である `Starlette` + `Pydantic`(いずれも事前インストール済み)を直接用いて同等のASGI REST APIを実装する。これは技術選定からの意図的な逸脱であり、`e2e-validation-report.md` に理由とともに記録する。V0.2と同一環境制約であり、SKILL自体の欠陥ではなく実行環境起因の制約である(`testbed.md`のとおり、V0.3ではこの点はSKILLルールに反映していない)。
* 今回のコードは、F001(参加者ID未検証による500エラー)の修正を**最初から**組み込んだ状態で実装する(`docs/03-backend-spec.md` 4章「予約系」に既に明記されている検証仕様に従う)。V0.2で見つかったバグを再現しない。

## スプリント一覧(OKF形式)

- [x] U001 [foundation: DBスキーマ・認証基盤・ログイン画面](./06-impl-direction/U001-foundation.md) — sessions/users/rooms/reservations等のスキーマ、ログイン/ログアウト/me API、S01画面
- [x] U002 [rooms-and-calendar-read: 会議室CRUD・予約参照系・カレンダー系画面](./06-impl-direction/U002-rooms-and-calendar-read.md) — 会議室CRUD API、予約参照API、S02/S05/S06画面
- [x] U003 [reservation-write: 予約作成・変更・取消(重複チェック)](./06-impl-direction/U003-reservation-write.md) — 予約作成/更新/取消API(参加者ID検証を最初から含む)、S03/S04画面
- [x] U004 [user-admin-and-hardening: ユーザー管理・横断機能仕上げ](./06-impl-direction/U004-user-admin-and-hardening.md) — ユーザーCRUD API、S07画面、エラーハンドリング/認可の仕上げ

## タスク粒度についての確認(確認観点5)

各スプリントのタスク数: U001=5, U002=4, U003=4, U004=4(合計17)。`SKILL-06-impl-direction.md` の「9観点は分割の目安であり1観点=1タスクである必要はない」「1スプリントあたり目安4〜6タスク程度に収める」旨のV0.3ルールに従い、関連の強い観点(型・スキーマ/Repository/Service/APIハンドラ層など)をまとめてタスク化した。9観点を機械的に9タスク化する形にはしていない。

## 実施結果サマリ

* 全4スプリントの実装・Unit Test・スプリント内結合テストを完了した(2026-07-30実施)。
* Unit Test: 45件 PASS / 0 FAIL(`server/tests/test_*.py`、`python3 -m unittest discover -s tests -p "test_*.py"`)。
* スプリント内結合テスト(結合確認用の薄いタスク): 10件 PASS / 0 FAIL(`server/tests/integration/test_u00{1,2,3,4}_*.py`、実サーバー(uvicorn)をサブプロセス起動しHTTPで検証)。
* `uv sync` によるビルドは、本検証環境がPyPIへのネットワークアクセスを持たないため実行できなかった(`docs/03-backend-spec.md`は変更していない。事前インストール済みのシステムPythonパッケージ(starlette/uvicorn/pydantic)で動作確認済み)。この制約は`e2e-validation-report.md`に記録する。

## 未解決事項

* なし(`docs/02-frontend-spec.md` / `docs/03-backend-spec.md` に対する不足・矛盾は発見されなかった)。
