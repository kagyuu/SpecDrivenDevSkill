あなたはExecutor(実装担当)です。このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクへ進んでください。

# 【テストID】T023

## 【目的】

* CR-002により、既に説明文が設定されている会議室に対し、説明文以外の項目(収容人数)だけを変更する更新を行った場合でも、`PUT /api/rooms/{room_id}` は全量更新(`docs/P002-frontend-spec.md` §4.6)であるため、リクエストに含めた既存の説明文がそのまま保持されることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` S06行(※CR-002により追記)
* `docs/CR.md` CR-002(反映後は `docs/cr-records/CR-002.md`)「期待する振る舞い」

## 【対象モジュール】

* `server/app/api/rooms.py`、`server/app/services/room_service.py`、`server/app/repositories/room_repository.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U006-1(CR-002バックエンド対応)が完了していること。

## 【使用するテストデータ】

* 管理者ユーザー: `employee_id=A0001`, `role=admin`
* 登録データ: `{"name": "会議室F", "capacity": 4, "equipment": [], "is_active": true, "description": "窓なし・防音仕様。"}`
* 更新データ(descriptionは登録時と同じ値を再送、capacityのみ変更): `{"name": "会議室F", "capacity": 10, "equipment": [], "is_active": true, "description": "窓なし・防音仕様。"}`

## 【事前準備】

* 管理者でログインしCookieを取得する。

## 【実行手順】

1. `POST /api/rooms` に登録データを送信し、`id` を取得する。
2. `PUT /api/rooms/{id}` に更新データ(descriptionは変更なし、capacityのみ変更)を送信する。
3. `GET /api/rooms` を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.test_api_rooms.RoomsApiTest.test_update_room_preserves_description_when_capacity_changes -v`

## 【期待結果】

* 手順1: `201 Created`。
* 手順2: `200 OK`、レスポンスボディの `capacity` が `10`、`description` が登録時と同じ「窓なし・防音仕様。」のまま。
* 手順3: `rooms` 配列中、該当会議室の `description` が「窓なし・防音仕様。」のまま(空文字やnullになっていない)。

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
* このタスクを実施したら、Executor Stepの停止条件に該当しない限り自動的に次のタスクに進んでください(本スプリントの最終テストのため、完了後はP103完了として報告してください)。
