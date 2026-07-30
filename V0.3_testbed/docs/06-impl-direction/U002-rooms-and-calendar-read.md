# U002: rooms-and-calendar-read — 会議室CRUD・予約参照系・カレンダー系画面

対象スプリント位置づけ: `docs/04-impl-plan.md` スプリント2。U001の認証基盤に依存する。

参照仕様: `docs/02-frontend-spec.md`(S02,S05,S06、rooms/reservations参照系API), `docs/03-backend-spec.md`(4章 会議室系・予約系)

---

## タスク U002-T1: 会議室CRUD API

【タスクID】U002-T1
【目的】`GET/POST/PUT/DELETE /api/rooms` を実装する。
【作成・編集対象ファイル】`server/app/routers/rooms.py`, `server/app/repositories/rooms.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 4章「会議室系」
【実装内容】一覧取得(`is_active`絞り込み)、作成・更新(名称重複チェック)、論理削除。`require_admin`で書き込み系を保護。
【実装してはいけないこと】物理削除。
【Unit Test内容】`server/tests/test_rooms_repo.py`: 作成→取得→更新→論理削除の一連、名称重複時にエラーとなること(正常系+異常系)。
【実行コマンド】`cd server && python3 -m unittest tests.test_rooms_repo -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U002-T2: 予約参照系API

【タスクID】U002-T2
【目的】`GET /api/reservations`, `GET /api/reservations/mine`, `GET /api/reservations/{id}` を実装する。
【作成・編集対象ファイル】`server/app/routers/reservations.py`, `server/app/repositories/reservations.py`
【参照すべき仕様箇所】`docs/03-backend-spec.md` 4章「予約系」参照クエリ部分
【実装内容】期間・会議室での絞り込み、JOINによる`room_name`/`created_by_name`付与、`participant_ids`付与。
【実装してはいけないこと】予約の作成・更新・削除ロジック(U003で実装)。
【Unit Test内容】`server/tests/test_reservations_repo_read.py`: 事前投入した複数予約に対し、期間絞り込み・room_id絞り込み・mine(future/past)・詳細取得(不存在時None)が正しいこと。
【実行コマンド】`cd server && python3 -m unittest tests.test_reservations_repo_read -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時は先に進まない。

## タスク U002-T3: S02/S05/S06 フロントエンド画面

【タスクID】U002-T3
【目的】カレンダーグリッド(S02)、マイ予約一覧(S05)、会議室管理(S06)画面を実装する。
【作成・編集対象ファイル】`client/app.js`, `client/style.css`, `client/views/calendar.js`, `client/views/my-reservations.js`, `client/views/rooms-admin.js`
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 1章(S02,S05,S06バリデーション)
【実装内容】S02: 会議室×時間帯のグリッド表示、週送り、会議室フィルタ。S05: 自分の予約一覧、期間フィルタ。S06(管理者のみナビゲーション表示): 会議室一覧・登録・編集・論理削除。
【実装してはいけないこと】予約の作成・編集(U003で実装するため、S02のセルクリックはこの時点ではプレースホルダで可)。
【Unit Test内容】UIコンポーネント単体の自動テストは`docs/05-test-plan.md`記載の方針により対象外(手動確認 + U002-T4のAPIシナリオで代替)。
【実行コマンド】(該当なし)
【完了条件】目視確認で3画面のレイアウトが仕様の入出力項目を満たすこと。
【次タスクに進む前の停止条件】なし。

## タスク U002-T4(結合確認用の薄いタスク): 会議室・予約参照 結合確認

【タスクID】U002-T4
【目的】ログイン後、会議室CRUDと予約参照APIがHTTP経由で連携して動くことを確認する。
【作成・編集対象ファイル】`server/tests/integration/test_u002_rooms_calendar.py`
【参照すべき仕様箇所】`docs/02-frontend-spec.md` 2章
【実装内容】admin でログイン→会議室作成→一般ユーザーでログイン→会議室一覧に反映されていることを確認→予約参照系APIが空配列を返すことを確認(この時点では予約作成APIが未実装のため)。
【実装してはいけないこと】アプリケーションコードの修正。
【Unit Test内容】(結合テスト)
【実行コマンド】`cd server && python3 -m unittest tests.integration.test_u002_rooms_calendar -v`
【完了条件】全テストPASS。
【次タスクに進む前の停止条件】FAIL時はU003へ進まない。

---

このスプリントの実装(全タスクのUnit Test・結合確認を含む)が完了したら、`docs/06-impl-direction.md` のU002行のチェックボックスを `[x]` に更新する。

## 実施結果

* U002-T1〜T4: 全実施・全PASS(V0.3ルールでの再実行、2026-07-30)。
* 補足: フェーズ7・8の確認観点2・3を実地検証する目的で、U002-T1(会議室CRUD)の`create_room_handler`に意図的にcapacity検証漏れのバグを仕込み、フェーズ8でF002として検出・修正した(`docs/08-fix-plan/fixed/F002-invalid-room-capacity-500.md`参照)。検証目的であり、U002完了時点(16:00)では発生していなかった。
