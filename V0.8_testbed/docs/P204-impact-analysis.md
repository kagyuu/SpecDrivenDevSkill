# P204 影響分析(修正実施後)

## 1. 対象

P203で実施した4件の修正(F001〜F004)それぞれについて、他の画面・API・モジュール・既存のPASS済みテストへの影響を確認した。

## 2. 修正ごとの影響分析

### F001(`server/app/db/connection.py`、`check_same_thread=False`追加)

* 影響しうる範囲: `get_connection()`はアプリケーション全体で唯一のDB接続生成箇所であり、`app/dependencies.py`の`get_db`依存性経由で認証必須の全APIエンドポイントが利用する。理論上は最も影響範囲が広い変更である。
* 実際に確認した内容:
  * `server/tests/`配下の全127件(単体テスト116件 + 結合テスト4件 + 受け入れ結合テスト7件)を再実行し、全件PASSを確認した(回帰なし)。
  * `client/tests/integration/`・`client/tests/acceptance/`配下の全19ファイルを個別に(それぞれ独立した実サーバープロセスに対して)再実行し、全件PASSを確認した。
  * 特に、この修正が「別のスレッド安全性の問題を覆い隠すことで別の不具合を見えなくしていないか」を懸念し、書き込み系のテスト(予約作成の重複チェック、A005の30並列同時実行テストなど)を重点的に再確認したが、いずれも修正前と同じ結果(PASS)のままだった。`BEGIN IMMEDIATE`によるファイルレベルの排他制御はコネクションレベルの`check_same_thread`設定と独立した機構であるため、これは想定どおりである。
* 疑いの有無: **無し**。

### F002(`client/src/pages/CalendarPage.tsx`、`addDays`のUTC化)

* 影響しうる範囲: `addDays`はCalendarPage内の「前へ」「次へ」ボタンからのみ呼び出される、影響範囲の小さい純粋関数。
* 実際に確認した内容:
  * `client/tests/CalendarPage.test.tsx`(4件)を再実行し、全件PASSを確認した。
  * `todayIsoDate()`（変更していない）との組み合わせ動作を、`addDays(todayIsoDate(), 1)`が常に元の値と異なることを確認するスクリプトで検証した。
* 疑いの有無: **無し**。

### F003(`client/src/pages/ReservationDetailPage.tsx`、`roomOptions`の追加)

* 影響しうる範囲: S04の会議室`<select>`と、収容人数バリデーション(`selectedRoom`参照)。S03(`ReservationCreatePage.tsx`)・S02(`CalendarPage.tsx`)など他画面のコードは変更していないため影響しない。
* 実際に確認した内容:
  * `client/tests/ReservationDetailPage.test.tsx`(5件)を再実行し、全件PASSを確認した(既存の「有効な会議室のみのケース」も引き続き正しく動作することを確認)。
  * `合成エントリのcapacity`を`Infinity`にしたことで、収容人数超過バリデーション自体が無効化会議室選択時に意図せず無効化されないか(=常にエラーにならない状態が固定化されないか)を確認したが、合成エントリを選んだまま保存しようとするとサーバー側`update_reservation`が404を返す(既存の`room.is_active`チェックによる、変更なし)ため、実質的な安全網は保たれている。
* 疑いの有無: **無し**。

### F004(`server/app/services/auth_service.py`、`login_failed`ログ追加)

* 影響しうる範囲: `login`関数の戻り値・例外仕様は変更していない(ログ出力の追加のみ)。呼び出し元(`app/routers/auth.py`)の挙動に変更はない。
* 実際に確認した内容:
  * `server/tests/test_auth_service.py`・`server/tests/test_auth_api.py`(計17件)を再実行し、全件PASSを確認した。
  * ログ追加によりレスポンスタイムやレスポンス内容自体に変化が無いことを、既存のAPIテストのアサーション(ステータスコード・ボディ)がそのままPASSすることで確認した。
* 疑いの有無: **無し**。

## 3. 修正の過程で発見・修正したテストコード側の不具合(参考)

F001適用後の確認過程で、以下3件はアプリケーションコードとは無関係な、今回のP103/P201ラウンドで新規作成したテストコード自体の作成時の不具合と判明したため、あわせて修正した(いずれもテストファイルの修正のみ、アプリケーションコードへの影響はない)。

* `client/tests/integration/calendarListDisplay.test.tsx`(T009): `queryByRole('columnheader', ...)`が実在しないアサーション(会議室フィルタは列の表示/非表示を切り替える設計ではなかった)で病的に低速化していた。アサーションを実際の仕様(フィルタは表示するデータを絞り込むだけ)に合わせて修正した。
* `client/tests/integration/mylistPeriodFilter.test.tsx`(T012): テストデータの予約件名に「過去の予約」を使っており、期間フィルタのラジオボタンラベル文字列と衝突し`queryByText`が曖昧一致で低速化していた。件名を重複しない文字列に変更した。
* `client/tests/integration/userCrud.test.tsx`(T013): 削除ボタンをDOM順の先頭インデックス(`[0]`)で取得しており、`admin`ユーザー(`user_id`昇順で常に先頭)を誤って操作していた。対象行にスコープした`within()`クエリに変更した。
* `client/tests/acceptance/setupToOperation.test.tsx`(A010)・`client/tests/integration/headerNavByRole.test.tsx`(T015): 非同期で描画される要素を同期クエリ(`getByLabelText`/`getByRole`)で参照しており、描画完了前に評価されることがあった。`findBy*`(リトライあり)に変更した。

これらはP202の対象(アプリケーションコードの欠陥)ではなく、F001の検証中に副次的に発見したテストコードの不具合であるため、新たなF00Nとしては起票せず、対応するF001の修正記録(`docs/P202-fix-plan/fixed/F001-sqlite-thread-safety.md`)内に経緯を記録した。

## 4. 結論

* 4件の修正いずれも、他機能・他テストを壊している疑いは**無い**。
* **P202への差し戻しは不要。P205(結合テスト再実施)に進む。**
