あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T002

## 【目的】

* 未認証・無効(期限切れ/削除済み)セッションで保護APIにアクセスした際、認証ミドルウェア(U001-T4)が一貫して401 `UNAUTHENTICATED` を返すことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2(認可エラー観点)

## 【対象モジュール】

* `server/app/api/deps.py`, `server/app/api/routers/auth.py`, `server/app/api/routers/rooms.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* `cd server && uv run python -m pytest tests/ -v` が全PASSであること

## 【使用するテストデータ】

* シードユーザー `user001`(§ `docs/P006-test-plan.md` §5)

## 【事前準備】

* 一時DBファイルにマイグレーション適用済みの状態でバックエンドを起動する。

## 【実行手順】

1. Cookie無しで `GET /api/me` を呼ぶ。
2. `user001` でログインしてCookieを取得後、`POST /api/auth/logout` を呼び、同じCookieで再度 `GET /api/me` を呼ぶ。
3. ログイン後に取得したセッショントークンをDB上で `expires_at` を過去日時に直接書き換え、そのCookieで `GET /api/rooms` を呼ぶ。

## 【実行コマンド】

* `cd server && uv run python -m pytest tests/integration/test_t002_unauthenticated.py -v`

## 【期待結果】

* 手順1・2・3のいずれも401、`error_code: "UNAUTHENTICATED"`、メッセージ「ログインが必要です」が返る。

## 【合否判定基準】

* 3ケースすべてが期待結果どおりであればPASS。1つでも異なればFAIL。

## 【失敗時に記録する内容】

* 失敗したケース番号、実際のステータスコード・レスポンスボディ。

## 【修正禁止事項】

* アプリケーションコードを修正しない。テストコードをその場で都合よく変更しない。失敗したテストをスキップしない。期待値を変更して成功扱いにしない。同じ失敗に対して場当たり的な再テストを繰り返さない。失敗内容をテスト記録に残し、次工程に引き渡す。

## 【次タスクへ進む条件】

* 結果を `docs/test-records/YYYYMMDD-HHMM-test-record.md` に記録した時点で次へ進んでよい。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
