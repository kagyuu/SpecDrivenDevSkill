あなたはExecutor(実装担当)です。このスプリント(U005: cr-001-all-day-checkbox)には1個のタスク(U005-1)があります。**1回に1タスクだけ**実施し、完了条件を満たしたら報告してください。

前提: U003(reservation-core)が完了し、S03(予約作成画面)が実装済みであること。
本スプリントは通常の新規スプリントではなく、変更要求 `docs/CR.md` CR-001(反映後は `docs/cr-records/CR-001.md`)に対応する差分実装である。既存のS03実装・テストのうちCR-001と無関係な部分は変更しないこと。
参照する仕様書: `docs/P001-requirement.md`「S03 予約作成画面」(※CR-001により追加の行)、`docs/P002-frontend-spec.md` §3 S03「終日チェックボックス」、§4.11備考、`docs/P006-test-plan.md` S03行(※CR-001により追加の記述)。

---

# 【タスクID】U005-1

## 【目的】

* S03(予約作成画面)に「終日」チェックボックスを追加し、ONにした瞬間に開始時刻`09:00`・終了時刻`18:00`を自動入力する(自動入力後は手動編集を優先する)。

## 【作成・編集対象ファイル】

* `client/js/pages/reservationCreatePage.js`(既存ファイルに追記): 純粋関数 `getAllDayDefaults()`、DOM描画・イベント配線 `mountReservationCreatePage` への「終日」チェックボックスの追加。
* `client/tests/reservationCreatePage.test.mjs`(既存ファイルに追記): `getAllDayDefaults` の単体テスト。

## 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3 S03「終日チェックボックス」の行

## 【実装内容】

* `getAllDayDefaults()`: 引数なしで `{ startTime: "09:00", endTime: "18:00" }` を返す純粋関数。
* `mountReservationCreatePage` の描画内容(フォーム)に「終日」チェックボックス(`name="all_day"`)を1項目追加する。
* チェックボックスの `change` イベントで、`checked === true` のときのみ `getAllDayDefaults()` の値を開始時刻・終了時刻の入力欄(`start_time`/`end_time`)へ設定する。`checked === false`(チェックを外した)ときは既存の入力値をそのまま維持し、時刻を消去・変更しない。
* 上記の自動入力はDOMの `value` を書き換えるのみであり、その後利用者が開始時刻・終了時刻を手動編集した場合はDOM上の値がそのままフォーム送信時に読み取られるため、実装上あらためて「手動編集を優先する」ための特別な分岐は不要である(自動入力を1回きりのDOM操作として実装すれば、期待する振る舞いを満たす)。
* `all_day` チェックボックスの状態自体は `controller.submit()` に渡すペイロードに含めない(`docs/P002-frontend-spec.md` §4.11備考のとおり、APIに新規フィールドを追加しない)。

## 【実装してはいけないこと】

* `validateReservationInput` の変更(バリデーションルール自体はCR-001の対象外)。
* サーバー側(`server/`)の変更(CR-001はクライアント側の入力補助のみで、APIリクエストボディの形式に変更はないため)。
* S04(予約詳細・編集画面)への同様の変更(CR-001の対象はS03のみ、`docs/CR.md` CR-001「影響が想定される範囲」参照)。

## 【Unit Test内容】

* テスト対象: `getAllDayDefaults`
* 正常系テスト: `getAllDayDefaults()` が `{ startTime: "09:00", endTime: "18:00" }` を返すこと。
* 主要な異常系テスト: 該当なし(引数を取らない純粋関数のため)。
* 補足: `mountReservationCreatePage` 自体のDOM描画・イベント配線は、本プロジェクトの既存方針(`client/INDEX.md` 記載、jsdom等がインストール不可のためDOM描画は自動テスト対象外)にもとづき単体テスト対象外とする。チェックボックスのDOM上の動作は、`getAllDayDefaults` の単体テストと目視確認(`docs/test-records/`に記録)で担保する。
* 実行するテストコマンド: `cd client && node --test tests/reservationCreatePage.test.mjs`
* 合格条件: 全テストPASS(既存分含む)。

## 【実行コマンド】

* `cd client && node --test tests/*.test.mjs`(既存の他画面のテストに回帰がないことも合わせて確認する)

## 【完了条件】

* 上記テストが全てPASSする。

## 【次タスクに進む前の停止条件】

* 3回修正してもテストがPASSしない場合は停止し内容を記録する。
