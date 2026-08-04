あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T021

## 【目的】

* CR-002(会議室に説明文(description)を追加)により、管理者が説明文つきで会議室を新規登録でき、`GET /api/rooms` の一覧にその説明文が反映されることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S06行(※CR-002により追記)
* `docs/CR.md` CR-002(反映後は `docs/cr-records/CR-002.md`)「期待する振る舞い」

## 【対象モジュール】

* `server/app/api/rooms.py`、`server/app/services/room_service.py`、`server/app/repositories/room_repository.py`、`server/app/core/validators.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U001〜U005(既存)が完了していること。U006(CR-002対応)のバックエンド部分(U006-1)が完了していること。

## 【使用するテストデータ】

* 管理者ユーザー: `employee_id=A0001`, `role=admin`(シード投入済み)
* 登録データ: `{"name": "会議室D", "capacity": 8, "equipment": [], "is_active": true, "description": "役員会議専用の個室です。"}`

## 【事前準備】

* 管理者でログインしCookieを取得する。

## 【実行手順】

1. `POST /api/rooms` に登録データ(descriptionを含む)を送信する。
2. `GET /api/rooms` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_rooms.RoomsApiTest.test_create_room_with_description_then_list -v`

## 【期待結果】

* 手順1: `201 Created`、レスポンスボディの `description` が送信した文字列と一致する。
* 手順2: レスポンスの `rooms` 配列中、手順1で作成した会議室の `description` が送信した文字列と一致する。

## 【合否判定基準】

* 両手順が期待結果どおりであればPASS。

## 【失敗時に記録する内容】

* 実際のレスポンスボディ(`description` フィールドの値・有無)を記録する。

## 【修正禁止事項】

* アプリケーションコードを修正しないでください。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスク(T022)に進んでください。
