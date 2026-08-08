あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T019 — ※CR-001 オンライン会議URLの登録・更新・削除と入力検証(API)

## 【目的】

* CR-001(`docs/P901-cr-direction/CR-001.md`)で追加した `meeting_url` について、API-15(登録)・API-14(詳細)・API-16(更新)・API-12(一覧)が仕様どおりに振る舞うことを、DB↔Repository↔Service↔APIを通して確認する。
* あわせて、マイグレーション `004-meeting-url.sql` が既存DB(`003` までが適用済みのDB)に対して差分適用され、**2回目の起動でも失敗しない**ことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` 3.1 V-F-01 / V-F-02 / V-F-03 / **V-F-16**、3.3 V-O-01 / V-O-02
* 仕様: `docs/P002-frontend-spec.md` 3.3(検証仕様)・5.3(`meeting_url` は常に文字列)・5.7 API-15/16、`docs/P003-backend-spec.md` 3.5・4.2・6.4

## 【対象モジュール】

* `server/migrations/004-meeting-url.sql`、`server/src/meeting_room/schemas.py`、`server/src/meeting_room/repositories/reservations_repo.py`、`server/src/meeting_room/services/reservation_service.py`、`server/src/meeting_room/handlers/reservation_handlers.py`

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* Sprint 3(U003。CR-001のタスク U003-T5 を含む)のサーバー単体テストが全件PASSしていること。

## 【使用するテストデータ】

* 基準データセット(`docs/P006-test-plan.md` 5章)。既存予約1件は `meeting_url` 未登録(空文字)。
* 会議室A(収容10)、ユーザー `user001`。

## 【事前準備】

1. DBファイルを削除し、サーバーを起動し、基準データセットを投入する。
2. `user001` でログインする。

## 【実行手順】

1. 既存予約(基準データセットの1件)を API-14 で取得する。
2. `meeting_url` を指定せずに(キー自体を送らずに)API-15 で予約を登録する(本日+2日、会議室A 09:00-10:00)。
3. `meeting_url` に `https://example.com/meet/abc` を指定して API-15 で予約を登録する(本日+2日、会議室A 11:00-12:00)。
4. 手順3の予約を API-14 で取得する。
5. `meeting_url` に `http://example.com/meet/xyz` を指定して API-16 で手順3の予約を更新する。
6. `meeting_url` に空文字を指定して API-16 で手順3の予約を更新する。
7. `meeting_url` に `example.com/meet`(スキームなし)を指定して API-15 で登録する(本日+2日、会議室A 13:00-14:00)。
8. `meeting_url` に `ftp://example.com/meet` を指定して API-15 で登録する(同上の時間帯)。
9. `meeting_url` に `https://` + 493文字(合計501文字)を指定して API-15 で登録する(同上の時間帯)。
10. `meeting_url` に `https://` + 492文字(合計500文字)を指定して API-15 で登録する(同上の時間帯)。
11. API-12(`date_from`/`date_to` = 本日+2日)で一覧を取得する。
12. サーバープロセスを停止し、**同じDBファイルのまま**もう一度起動して、API-12 を呼ぶ。

## 【実行コマンド】

* `cd server && python3 -m unittest tests.integration.test_t019_meeting_url -v`

## 【期待結果】

* 手順1: 200。`reservation.meeting_url` が `""`(空文字)である(`null` ではない)。**マイグレーション `004` 適用前に相当する既存データが、URL未登録として読める。**
* 手順2: 201。応答の `meeting_url` が `""`。
* 手順3: 201。応答の `meeting_url` が `https://example.com/meet/abc`。
* 手順4: 200。`meeting_url` が `https://example.com/meet/abc`。
* 手順5: 200。`meeting_url` が `http://example.com/meet/xyz`(全置換更新で置き換わる)。
* 手順6: 200。`meeting_url` が `""`(全置換更新でURLが削除される。P002 5.7 API-16 ※CR-001)。
* 手順7: 400 `VALIDATION_ERROR`。`details` に `field="meeting_url"` と「オンライン会議URLは http:// または https:// で始まるURLを入力してください。」が含まれる。予約は作成されていない。
* 手順8: 手順7と同じ 400。
* 手順9: 400 `VALIDATION_ERROR`。`details` に `field="meeting_url"` と「オンライン会議URLは500文字以内で入力してください。」が含まれる。
* 手順10: 201。`meeting_url` の長さが 500 である。
* 手順11: 200。各要素に `meeting_url` キーが存在する(一覧APIでも `Reservation` 表現は共通)。
* 手順12: **正常に起動し** 200 が返る。`schema_migrations` の行数が 4 のままで増えていない(`004-meeting-url.sql` が2回適用されない)。`duplicate column name` エラーが発生しない。

## 【合否判定基準】

* 上記すべてが一致すればPASS。特に手順12が失敗した場合は、データモデル変更の冪等性の欠陥であり、必ずFAILとして記録する。

## 【失敗時に記録する内容】

* テストID、実行日時、実行コマンド、終了コード
* 期待結果と実際の結果(HTTPステータス、レスポンス本文、DBの該当行)
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
