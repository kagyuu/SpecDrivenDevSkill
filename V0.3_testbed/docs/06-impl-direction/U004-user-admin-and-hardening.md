# U004: user-admin-and-hardening — ユーザー管理・横断機能仕上げ

対象スプリント位置づけ: `docs/04-impl-plan.md` スプリント4。U001〜U003に依存する。

参照仕様: `docs/02-frontend-spec.md`(S07, users API), `docs/03-backend-spec.md`(4章 ユーザー系, 5章 エラーハンドリング共通方針)

---

## タスク U004-T1: ユーザーCRUD API

【タスクID】U004-T1
【目的】`GET/POST/PUT/DELETE /api/users` を実装する。
【作成・編集対象ファイル】`server/app/routers/users.py`, `server/app/repositories/users.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 4章「ユーザー系」
【実装内容】一覧・作成(社員ID重複チェック)・更新(パスワード未指定なら変更しない)・論理削除。全て`require_admin`。
【実装してはいけないこと】レスポンスへの`password_hash`混入。
【Unit Test内容】`server/tests/test_users_repo.py`: 作成→取得→更新(パスワード変更あり/なし)→論理削除、社員ID重複エラー。
【実行コマンド】`cd server && python3 -m unittest tests.test_users_repo -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U004-T2: S07フロントエンド画面 + 管理者ナビゲーション仕上げ

【タスクID】U004-T2
【目的】ユーザー管理画面(S07)を実装し、全画面のヘッダーで管理者専用リンク(会議室管理/ユーザー管理)の出し分けを最終確認する。
【作成・編集対象ファイル】`client/views/users-admin.js`, `client/app.js`(ナビゲーション仕上げ)
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 1章 S07、`docs/01-requirement.md` 画面遷移図
【実装内容】ユーザー一覧・登録・編集・論理削除。一般ユーザーには管理者用リンクを表示しない(表示制御のみ。サーバー側403は既存のまま)。
【実装してはいけないこと】フロントエンドの表示制御のみで認可を代替すること(サーバー側の403チェックは必須のまま)。
【Unit Test内容】UIコンポーネント単体テストは対象外。
【実行コマンド】(該当なし)
【完了条件】目視確認。
【次タスクに進む前の停止条件】なし。

## タスク U004-T3: エラーハンドリング・認可の横断的仕上げ

【タスクID】U004-T3
【目的】未捕捉例外時の共通500ハンドラ、Pydanticバリデーションエラーの共通400変換、ヘルスチェック/バージョン確認用エンドポイント(`GET /health`)を追加する。
【作成・編集対象ファイル】`server/app/main.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 5章
【実装内容】Starletteの例外ハンドラ登録。`GET /health`は`docs/01-requirement.md`にないエンドポイントだが、`docs/09-deliver.md`(フェーズ9)でのバージョン確認手段として`docs/03-backend-spec.md`5章のエラーハンドリング方針の範囲内の運用上のエンドポイントとして追加する(業務APIではないため仕様外拡張には当たらないと判断)。
【実装してはいけないこと】業務仕様(画面・業務API)の追加。
【Unit Test内容】`server/tests/test_error_handling.py`: 存在しないパスへのアクセスで404、バリデーションエラーで400+共通形式、`/health`で200。
【実行コマンド】`cd server && python3 -m unittest tests.test_error_handling -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U004-T4(結合確認用の薄いタスク): ユーザー管理・権限 結合確認

【タスクID】U004-T4
【目的】ユーザーCRUDと、一般ユーザーによる管理者API/画面アクセス拒否をHTTP経由で確認する。
【作成・編集対象ファイル】`server/tests/integration/test_u004_users_and_authz.py`
【参照すべき仕様箇所】`docs/01-requirement.md` テスト方針(権限まわり)
【実装内容】admin でユーザー作成→一般ユーザーでログインし`/api/users`にアクセスして403、`/api/rooms`へのPOSTで403となることを確認。
【実装してはいけないこと】アプリケーションコードの修正。
【Unit Test内容】(結合テスト)
【実行コマンド】`cd server && python3 -m unittest tests.integration.test_u004_users_and_authz -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時はフェーズ6を完了としない。

---

このスプリントの実装(全タスクのUnit Test・結合確認を含む)が完了したら、`docs/06-impl-direction.md` のU004行のチェックボックスを `[x]` に更新する。全スプリントが `[x]` になった時点でフェーズ6は完了とする。

## 実施結果

* U004-T1〜T4: 全実施・全PASS。
