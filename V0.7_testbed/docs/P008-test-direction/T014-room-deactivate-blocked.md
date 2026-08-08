あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T014 — 今後の予約がある会議室の無効化拒否

## 【目的】

* Sprint 2 で暫定実装(常に0件を返す)としていた `count_future_reservations` が Sprint 3 で本実装に差し替えられ、今後の予約が残る会議室の無効化が 409 で拒否されることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 4.2(Sprint 3)、3.1 V-F-08。`docs/P005-impl-plan.md` 5章 リスク#5
* 仕様: `docs/P002-frontend-spec.md` 5.5(API-07)、`docs/P003-backend-spec.md` 6.2

## 【対象モジュール】

* `services/room_service.py`(`deactivate_room` / `count_future_reservations`)、`repositories/reservations_repo.py`(`count_future`)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 3 の単体テストが全件PASSしていること。

## 【使用するテストデータ】

* 会議室A(今後の予約1件)、会議室B(過去の予約1件のみ)、会議室D(予約なし)。
* 過去の予約は、日付検証を回避するため**リポジトリ経由で直接INSERT**する(APIからは過去日を登録できないため)。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、基準データセットを投入する。
2. `user001` で会議室Aに「本日+1日」の予約を1件登録する。
3. 会議室Bに「本日-3日」の予約を1件、リポジトリ経由で直接INSERTする。
4. `admin001` でログインする。

## 【実行手順】

1. `DELETE /api/rooms/{会議室A}` を呼ぶ。
2. 会議室Aの予約を取り消してから、再度 `DELETE /api/rooms/{会議室A}` を呼ぶ。
3. `DELETE /api/rooms/{会議室B}` を呼ぶ。
4. `DELETE /api/rooms/{会議室D}` を呼ぶ。
5. `server/src/meeting_room/services/room_service.py` に `TODO(U003-T2)` の文字列が残っていないことを確認する。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t014_room_deactivate_blocked -v`
* `grep -rn "TODO(U003-T2)" server/src || true`

## 【期待結果】

* 手順1: 409 `CONSTRAINT_VIOLATION`。メッセージに件数「1」が含まれる。会議室Aは `is_active=1` のまま。
* 手順2: 204。
* 手順3: 204(**過去の予約は無効化を妨げない**)。
* 手順4: 204。
* 手順5: 該当なし(TODOが解消されている)。

## 【合否判定基準】

* 上記すべてが一致すればPASS。手順1が204になる場合は暫定実装が残っている(FAIL)。

## 【失敗時に記録する内容】

* テストID、実行日時、実行コマンド、終了コード
* 期待結果と実際の結果(HTTPステータス、レスポンス本文、DBの該当行、画面の描画結果のうち該当するもの)
* サーバーの標準出力ログのうち、当該リクエストに対応する行(`sid`・パスワードは伏せる)
* 失敗が再現するかどうか(同一手順を1回だけ再実行して確認する。3回以上繰り返さない)
* 関連しそうな仕様箇所(`docs/P002-frontend-spec.md` / `docs/P003-backend-spec.md` の節番号)

## 【修正禁止事項】

* アプリケーションコードを修正しない
* テストコードをその場で都合よく変更しない
* 失敗したテストをスキップしない
* 期待値を変更して成功扱いにしない
* 同じ失敗に対して場当たり的な再テストを繰り返さない

## 【次タスクへ進む条件】

* 本テストの結果(PASS / FAIL / BLOCKED のいずれか)が `docs/test-records/YYYYMMDD-HHMM-test-record.md` に記録されていること。
* `docs/P008-test-direction.md` の該当行のチェックボックスが `[x]` になっていること。
* **FAILであっても次のテストタスクへ進む**(修正はReviewer Loopで行う)。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
