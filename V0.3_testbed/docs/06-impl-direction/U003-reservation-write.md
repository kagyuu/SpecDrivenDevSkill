# U003: reservation-write — 予約作成・変更・取消(重複チェック)

対象スプリント位置づけ: `docs/04-impl-plan.md` スプリント3。U002に依存する。

参照仕様: `docs/02-frontend-spec.md`(S03,S04, 予約作成/更新/取消API), `docs/03-backend-spec.md`(4章 予約系 重複判定ロジック)

---

## タスク U003-T1: 重複判定・バリデーション純粋関数

【タスクID】U003-T1
【目的】時間帯重複判定と予約入力バリデーションを純粋関数として実装する。
【作成・編集対象ファイル】`server/app/validation.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 4章「予約系」重複判定ロジック、`docs/02-frontend-spec.md` 1章 S03
【実装内容】`time_ranges_overlap(start1,end1,start2,end2) -> bool`、`validate_reservation_input(payload) -> list[str]`(件名必須・100文字以内、時刻フォーマット、終了>開始、備考500文字以内)。
【実装してはいけないこと】DBアクセス(純粋関数のみ)。
【Unit Test内容】`server/tests/test_validation.py`: 重複あり/重複なし/隣接(重複しない)境界値、件名欠如、終了<=開始、文字数超過の各ケース。
【実行コマンド】`cd server && python3 -m unittest tests.test_validation -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U003-T2: 予約作成・更新・取消API

【タスクID】U003-T2
【目的】`POST /api/reservations`, `PUT /api/reservations/{id}`, `DELETE /api/reservations/{id}` を実装する。
【作成・編集対象ファイル】`server/app/repositories/reservations.py`(追記), `server/app/routers/reservations.py`(追記)
【参照すべき仕様箇所】`docs/03-backend-spec.md` 4章「予約系」、`docs/02-frontend-spec.md` 2章
【実装内容】`BEGIN IMMEDIATE`トランザクション内で重複チェック→INSERT/UPDATE。作成者/参加者(`reservation_participants`)登録。認可(本人or管理者)。会議室存在・有効性チェック。**`docs/03-backend-spec.md` 4章「予約系」に明記のとおり、`participant_ids`に指定された各IDが有効な(`is_active=1`)`users`に実在することをINSERT前にアプリケーション層で検証し、1件でも存在しなければ`400 VALIDATION_ERROR`を返す処理を、最初からこのタスクに含める(DBの外部キー制約任せにしない)。**
【実装してはいけないこと】仕様にない項目の追加。参加者以外のユーザーへの予約公開範囲変更。
【Unit Test内容】`server/tests/test_reservations_repo_write.py`: 正常作成、重複時エラー、更新時に自分自身を重複対象から除外、他人予約の更新は権限エラー、取消後は一覧に出ないこと、**存在しない参加者IDを指定した場合に400(VALIDATION_ERROR)になること(500にならないこと)**。
【実行コマンド】`cd server && python3 -m unittest tests.test_reservations_repo_write -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U003-T3: S03/S04 フロントエンド画面

【タスクID】U003-T3
【目的】予約作成画面(S03)・予約詳細/編集画面(S04)を実装し、S02のセルクリックから接続する。
【作成・編集対象ファイル】`client/views/reservation-form.js`, `client/views/reservation-detail.js`, `client/views/calendar.js`(接続)
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 1章 S03/S04, 4.2 シーケンス図
【実装内容】S03: 会議室・日付・時刻・件名・参加者・備考入力、重複時(409)にエラーメッセージ表示し画面遷移しない。S04: 予約内容表示、本人/管理者のみ編集・取消可、それ以外は読み取り専用表示。
【実装してはいけないこと】バックエンドの重複チェックをフロントエンドで代替・省略すること(サーバー側チェックは必須のまま維持する)。
【Unit Test内容】UIコンポーネント単体テストは対象外(方針は`docs/05-test-plan.md`参照)。
【実行コマンド】(該当なし)
【完了条件】目視確認で入出力項目が仕様と一致すること。
【次タスクに進む前の停止条件】なし。

## タスク U003-T4(結合確認用の薄いタスク): 予約作成・重複・更新・取消 結合確認

【タスクID】U003-T4
【目的】HTTP経由で予約作成→重複エラー→更新→取消の一連を確認する。
【作成・編集対象ファイル】`server/tests/integration/test_u003_reservation_flow.py`
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 4.2 シーケンス図
【実装内容】ログイン→会議室取得→予約作成(201)→同一時間帯で再度作成(409)→自分の予約を更新(200)→取消(204)→一覧に出ないことを確認。
【実装してはいけないこと】アプリケーションコードの修正。
【Unit Test内容】(結合テスト)
【実行コマンド】`cd server && python3 -m unittest tests.integration.test_u003_reservation_flow -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時はU004へ進まない。

---

このスプリントの実装(全タスクのUnit Test・結合確認を含む)が完了したら、`docs/06-impl-direction.md` のU003行のチェックボックスを `[x]` に更新する。

## 実施結果

* U003-T1〜T4: 全実施・全PASS。参加者ID実在チェック(V0.2のF001相当)は最初から実装済みで、修正サイクルを経ていない。
