# 影響分析(修正実施後)(P204)

> 本書は `spec-driven-dev` Skill フェーズP204の成果物です。
> インプット: `docs/P202-fix-plan/fixed/F001-t016-capacity-expectation.md`、`docs/P202-fix-plan/fixed/F002-a001-half-open-slot-expectation.md`、`docs/P202-fix-plan.md`(残存未解決項目)、変更されたソースコードの差分

## 1. 変更差分の全体像

作業前に退避した資産(`meeting-room-20260805161135.zip`)との比較結果:

| 区分 | 変更 |
| --- | --- |
| `server/src/**`(アプリケーションコード) | **差分0** |
| `server/tests/**` | 差分0(P201で新設した `tests/acceptance/**` は本修正の前に作成済み) |
| `client/src/**`(アプリケーションコード) | **差分0** |
| `client/tests/integration/test_t016_create_flow.js` | 手順7のアサーションのみ変更(F001) |
| `client/tests/acceptance/test_a001_business_flow.js` | 手順5のアサーションのみ変更(F002) |
| `docs/P008-test-direction/T016-create-flow.md` | 手順7の記述・期待結果(F001) |
| `docs/P009-acceptance-direction/A001-reservation-business-flow.md` | 手順5・期待結果(F002) |
| `docs/P007-impl-direction.md` | 5章 未解決事項 #18 の「扱い」を解決済みに更新(F001) |
| `docs/P202-fix-plan.md` / `docs/P202-fix-plan/**` | 修正計画・修正記録(P202・P203の成果物) |

**アプリケーションコードに一切変更がないため、機能を壊す経路は原理的に存在しない。** 以下では「テストの期待結果を変更したことによる被覆の劣化がないか」を主な観点として分析する。

## 2. F001(T016 手順7)の影響

### 影響しうる他の画面・API・モジュール

| 対象 | 影響 | 確認方法と結果 |
| --- | --- | --- |
| S03 予約作成画面(`client/src/views/s03-reservation-new.js`) | コード変更なし。影響なし | `client/tests/test_s03_reservation_new.js`(単体)PASS |
| 予約フォーム部品(`client/src/components/reservation-form.js`) | コード変更なし。S04の編集モードでも同じ部品を共有するが、変更していないため影響なし | `client/tests/test_reservation_form.js`(単体)PASS / T017(S04)PASS |
| `client/src/lib/validation.js` の `validateAttendeeCount` | コード変更なし | `client/tests/test_validation.js` PASS |
| API-15 `POST /api/reservations` のサーバー側 `CAPACITY_EXCEEDED` | **被覆の劣化がないかを重点確認**。T016 手順7 がAPIレベルの400確認をやめたため、代替の担当を確認した | `docs/P008-test-direction/T013-capacity-and-authz.md` 手順1が「`attendee_count=5` は収容人数(4)超過 → 400 `CAPACITY_EXCEEDED`」を確認しており、実測PASS。加えてサーバー単体 `tests/test_reservation_service.py` / `tests/test_reservation_write_handlers.py` にも400の検証がある。A004 手順5(新規予約 6 > 収容5 → 400)もAPIレベルでPASS。**被覆は失われていない** |
| S04 の 400 `CAPACITY_EXCEEDED` 表示経路(`showCapacityError`) | コード変更なし。T016 の変更で `capacity-error` 領域の検証が減るが、A004 手順4(更新時の400)およびクライアント単体テストで経路自体は維持 | `client/tests/test_s04_reservation_detail.js` PASS |

### 判定

* 他機能を壊している疑いは**ない**。被覆の劣化も**ない**(APIレベルの400はT013・A004・サーバー単体が担当)。
* むしろ検証項目は増えている(T016 手順7 の検証は1点→4点: POSTが増えないこと / フィールド直下の文言完全一致 / `capacity-error` が空であること / 画面遷移しないこと)。

## 3. F002(A001 手順5)の影響

### 影響しうる他の画面・API・モジュール

| 対象 | 影響 | 確認方法と結果 |
| --- | --- | --- |
| `client/src/lib/grid.js`(`occupiedSlots` / `buildOccupancy`) | コード変更なし。影響なし | `client/tests/test_grid.js`(単体)PASS |
| S02 カレンダー(`client/src/views/s02-calendar.js`) | コード変更なし | `client/tests/test_s02_calendar.js` PASS / T015 PASS |
| ADR-007 の半開区間規約 | 変更なし。むしろA001の記述をADR-007へ整合させた | サーバー側の重複判定は T012(境界時刻)/ A002 が PASS |
| 他の受け入れテストの占有スロット期待値 | A005 手順1・A011 手順1・T015・T016 手順8 も占有セルを検証している。半開区間の解釈が揺れていないかを確認した | いずれもPASS。A001 手順8(15:00-16:00 → 15:00・15:30 占有)も PASS |

### 判定

* 他機能を壊している疑いは**ない**。A001 手順5 の期待値は「13:00 に予約表示」の検証を維持したうえで「13:30 は空き」を追加しており、被覆は劣化していない。

## 4. 既存PASS済みテストの再実行(P204時点の軽い確認)

本格的な再実行はP205で行うが、退行の有無を確認するため主要スイートを実行した。

| レベル | コマンド | 結果 |
| --- | --- | --- |
| バックエンド 全体(単体+結合+受入) | `cd server && python3 -m unittest discover -s tests -t .` | **Ran 240 tests / OK** |
| バックエンド 単体のみ | `cd server && python3 -m unittest tests.test_*`(15モジュール) | **Ran 213 tests / OK** |
| フロントエンド 単体 | `cd client && node --test 'tests/*.js'` | **126 tests / 126 pass** |
| フロントエンド 結合(T003・T010・T015〜T018) | `cd client && node --test 'tests/integration/*.js'` | **41 tests / 41 pass** |
| フロントエンド 受け入れ(A001・A003UI・A004UI・A005・A006UI・A008描画・A011) | `cd client && node --test 'tests/acceptance/test_*.js'` | **31 tests / 31 pass** |

退行は検出されなかった。

## 5. P202への差し戻し判定

* **差し戻しは不要**。他機能を壊している疑いはなく、未解決の修正課題も0件である(`docs/P202-fix-plan/P202-fix-unresolved.md`)。
* **P205(結合テスト再実施)に進む。**

## 6. 人間への申し送り(P302へ引き継ぐ)

`SKILL-P202-fix-plan.md` の「仕様判断を伴う場合はP204で扱う」に該当する事項、およびP201で合否対象外として記録した事項を、`docs/P302-deliver.md` の「未整備事項・人間による確認事項」へ引き継ぐ。

| # | 内容 | 種別 |
| --- | --- | --- |
| 1 | 会議室の収容人数を減らした後、既存予約(参加予定人数が新収容人数を超える)の**件名だけを変更する `PUT`** も 400 `CAPACITY_EXCEEDED` になる(A004 手順4の実測)。仕様に明示がなく、業務上「過去に成立した予約の軽微な変更を止めてよいか」は人間の判断を要する。A004 の【合否判定基準】が「合否には含めない」と定めているため、本ループでは修正していない | 仕様判断 |
| 2 | 実ブラウザでのレイアウト崩れ・実クリック・エラーメッセージの物理的な表示位置の目視確認(A011 手順7 = NOT RUN)。ブラウザ自動化ツールを取得できない環境のため実施不能(ADR-001 / P006 1.1 の★ACCEPTED★)。静的配信は実HTTPで確認済み(`/` 200 text/html、`/src/main.js` 200 text/javascript、`/src/styles.css` 200 text/css) | 環境制約 |
| 3 | TLS(HTTPS)終端、プロセス監視・自動再起動、ログ集約先への転送は `docs/P003-backend-spec.md` 8章によりP302へ委譲。**ADRの決定自体は正しく、前提が本実行環境に存在しないだけ**であるため、`SKILL-P202-fix-plan.md` の規定どおりコード・テスト・仕様書はいずれも変更していない | 環境制約(既知の制約) |
| 4 | 401時に `api.js` が画面遷移とメッセージ設定の後に例外を再送出するため、呼び出し側が捕捉していない経路(S02の週送りなど)で未処理のPromise拒否が残る。P002 2.4 は遷移とメッセージのみを規定しており仕様違反ではないため所見として記録 | 所見 |
| 5 | テスト指示の細部の記述(A003 手順7 の「会議室1件」/ A007 手順8 の「WALファイルが残っている状態」)。実施時の読み替え内容は `docs/test-records/20260805-1603-test-record.md` に明記済み。指示文の整備が必要なら人間がCR(P901)で起票する(重大度「低」) | 文書整備 |
