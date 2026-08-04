あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T022

## 【目的】

* CR-002により、管理者が既存会議室の説明文を編集(`PUT /api/rooms/{room_id}`)でき、更新後の説明文が `GET /api/rooms` の一覧に反映されることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S06行(※CR-002により追記)
* `docs/CR.md` CR-002(反映後は `docs/cr-records/CR-002.md`)「期待する振る舞い」

## 【対象モジュール】

* `server/app/api/rooms.py`、`server/app/services/room_service.py`、`server/app/repositories/room_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U006-1(CR-002バックエンド対応)が完了していること。

## 【使用するテストデータ】

* 管理者ユーザー: `employee_id=A0001`, `role=admin`
* 登録データ: `{"name": "会議室E", "capacity": 4, "equipment": [], "is_active": true, "description": ""}`(説明文なしで新規登録)
* 更新データ: `{"name": "会議室E", "capacity": 4, "equipment": [], "is_active": true, "description": "予約前に清掃予約が必要です。"}`

## 【事前準備】

* 管理者でログインしCookieを取得する。

## 【実行手順】

1. `POST /api/rooms` に登録データ(descriptionは空文字)を送信し、`id` を取得する。
2. `PUT /api/rooms/{id}` に更新データ(descriptionを追加)を送信する。
3. `GET /api/rooms` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_rooms.RoomsApiTest.test_update_room_description_then_fetch -v`

## 【期待結果】

* 手順1: `201 Created`。
* 手順2: `200 OK`、レスポンスボディの `description` が更新データの説明文と一致する。
* 手順3: `rooms` 配列中、該当会議室の `description` が更新データの説明文と一致する。

## 【合否判定基準】

* 3手順すべてが期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 手順2・3それぞれのレスポンスボディの `description` フィールドの実際の値を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスク(T023)に進んでください。
