あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T005

## 【目的】

* 会議室を無効化(論理削除)した際に、`GET /api/rooms`(既定)からは除外され、`GET /api/rooms?include_inactive=true`(管理者)では引き続き取得できることを確認する(API+DBの結合。S03の選択肢除外はU003実装後にT007等で間接的に確認するため、本テストはAPI層に閉じる)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 2.3節

## 【対象モジュール】

* `server/app/routers/rooms.py`, `server/app/services/room_service.py`, `server/app/repositories/room_repository.py`, SQLite(`rooms`テーブル)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* U002の全タスクが完了していること

## 【使用するテストデータ】

* T004で登録した「第一会議室」、または新規に登録した会議室

## 【事前準備】

* 管理者セッションで会議室を1件登録済みにしておく

## 【実行手順】

1. `DELETE /api/rooms/{room_id}` を呼び出す
2. `GET /api/rooms`(`include_inactive` 指定なし)を呼び出す
3. `GET /api/rooms?include_inactive=true`(管理者セッション)を呼び出す
4. 一般ユーザーのセッションで `GET /api/rooms?include_inactive=true` を呼び出す

## 【実行コマンド】

* `cd server && python -m pytest tests/integration/test_room_deactivate_integration.py -v`

## 【期待結果】

* 手順1: 200、`is_active: false`
* 手順2: 該当会議室が結果に含まれない
* 手順3: 該当会議室が `is_active: false` として含まれる
* 手順4: 一般ユーザーの指定は無視され、該当会議室は結果に含まれない(`docs/P002-frontend-spec.md` 4.4節)

## 【合否判定基準】

* 上記すべてを満たせばPASS

## 【失敗時に記録する内容】

* 各手順のレスポンス実際の内容

## 【修正禁止事項】

* アプリケーションコードを修正しない。テストコードをその場で都合よく変更しない。失敗したテストをスキップしない。期待値を変更して成功扱いにしない。同じ失敗に対して場当たり的な再テストを繰り返さない。

## 【次タスクへ進む条件】

* 結果を記録したらT006へ進む(U003のテストタスクへ移行)

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。
