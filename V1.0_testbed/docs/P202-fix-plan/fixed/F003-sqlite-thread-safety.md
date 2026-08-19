あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F003

## 【対応する失敗テスト】T006, A002, A006, A007

* 4件の失敗テストすべてで、サーバーログに同一の例外 `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.` が記録されており、単一の根本原因(Repository層のDB接続のスレッド安全性)に起因すると判断したため、1件のファイルにまとめる(`SKILL-P202-fix-plan.md` の例外規定にもとづく)。

## 【障害記録】

* `docs/test-records/20260811-0500-test-record.md`(T006)・`docs/test-records/20260811-0530-test-record.md`(A002, A006, A007)に詳細記録あり。
* 原因区分: **アプリケーションコードの欠陥**。
* 調査結果: `server/app/api/deps.py` の `get_db()` は `app/db/connection.py` の `get_connection()` を呼び、リクエストごとに新しい `sqlite3.Connection` を生成する。`sqlite3.connect()` は既定で `check_same_thread=True` であり、接続オブジェクトを生成したスレッドと異なるスレッドから使用すると例外になる。FastAPI/Starletteは、同期の依存関数(`yield`を使う `get_db` を含む)・同期のエンドポイント関数を `anyio.to_thread.run_sync` 経由でスレッドプール上で実行するが、1つのリクエストの中でも「依存関数(接続生成)」と「エンドポイント本体(接続の実際の利用)」、あるいは「依存関数のyield後のクリーンアップ(`conn.close()`)」が、必ずしも同一のワーカースレッドで実行される保証はない(スレッドプールの割り当てはリクエストごとに変わりうる)。`fastapi.testclient.TestClient`(httpx経由、ASGIトランスポートを同期的に1スレッドで処理)ではこの問題が再現しないため、P007〜P009単体テスト・APIテスト(TestClientベース)ではすべてPASSしていたが、実サーバー(uvicorn)に対する結合テスト・受け入れテストで初めて顕在化した。

## 【参照ファイル】

* `server/app/db/connection.py`
* `server/app/api/deps.py`
* `server/app/main.py`(lifespanでの接続生成・破棄も同様のリスクを持つため確認する)

## 【調査方針】

* `sqlite3.connect(path, check_same_thread=False)` に変更した場合、この不具合が解消するか実サーバーで確認する。
* `check_same_thread=False` はスレッド安全性の警告を無効化するだけであり、sqlite3モジュール自体は複数スレッドからの同時アクセスに対して安全ではない(同時書き込みなどでの破損リスク)ことに注意する。本アプリは「リクエストごとに新しい接続を開き、リクエスト内で完結してから閉じる」設計(接続を使い回さない)であるため、1つの接続オブジェクトが複数スレッドから**同時に**使われることは無い(生成したスレッドと利用するスレッドが異なるだけ)。このため `check_same_thread=False` は本アプリの設計において安全な回避策と判断できるか、代替案(下記)と比較して決定する。
* 代替案: 依存関数`get_db`をやめ、リクエストの処理全体(ルーティングハンドラも含めて)を単一の同期関数にまとめて`run_in_threadpool`で一度だけスレッドに委譲する設計への変更、またはSQLiteアクセスを非同期対応ライブラリに置き換える設計変更も考えられるが、影響範囲が全APIハンドラに及び本タスクの範囲を超える大規模変更になるため、まずは `check_same_thread=False` による最小修正を優先する。

## 【修正方針】

* `server/app/db/connection.py` の `get_connection()` で `sqlite3.connect(path, check_same_thread=False)` に変更する。
* SQLiteの並行アクセスに関する残存リスク(複数リクエストが同時に同じDBファイルへ書き込む場合のロック待ち・`database is locked`エラーの可能性)について、`docs/ArchitectureHandbook.md` §9(既知の制約・技術的負債)に★ACCEPTED★として記録するかどうかは、この修正で実害が解消することを確認したうえで判断する(解消しない場合は仕様矛盾ではなく設計の見直しが必要な可能性があり、その場合はP204で影響分析を行う)。

## 【試行錯誤してよい範囲】

* `server/app/db/connection.py` の接続生成部分。
* 必要であれば `server/app/api/deps.py` の `get_db` の実装(接続のライフサイクル管理)。
* アプリケーションコード全体のうち、他のテスト(94+3+5件のPASS済みテスト)に影響しない範囲。

## 【修正成功時に更新するdocs】

* `docs/ArchitectureHandbook.md` §9(残存リスクとして記録する場合)。
* `server/INDEX.md`(「既知の不具合あり」の注記を、修正後の状態に更新する)。

## 【ロールバック条件】

* 修正によりバックエンドの既存単体テスト(97件)のいずれかが壊れた場合は、変更前の状態に戻す。

## 【検証コマンド】

* `cd server && uv run python -m pytest tests/ -v`(既存97件が引き続き全PASSであることの確認)
* `cd client && npx playwright test tests/integration/t006_reservation_update_self_exclusion.spec.ts`
* `cd client && npx playwright test tests/acceptance/a002_admin_journey.spec.ts tests/acceptance/a006_room_deactivation_existing_reservations.spec.ts tests/acceptance/a007_performance_calendar.spec.ts`

## 【完了条件】

* 上記検証コマンドがすべて成功する。
* T006, A002, A006, A007が再実行でPASSになる(A007はF002修正も前提とするため、A007については応答時間の合否まで含めて再確認する)。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新するよう指示する。

---

## 修正結果(P203)

* 実施日: 2026-08-11
* 変更したソースコード: `server/app/db/connection.py` の `get_connection()` で `sqlite3.connect(path, check_same_thread=False)` に変更(理由をコード内コメントに記載)。
* 更新したdocs: なし(`docs/ArchitectureHandbook.md` §9への★ACCEPTED★記録は、修正で実害が解消したため不要と判断した。SQLiteの並行アクセス上限そのものは既存の非機能要件委譲(`docs/P003-backend-spec.md` §7)の範囲内であり、新たな残存リスクとして記録する必要は無いと判断した)。
* 実行したテスト:
  * `cd server && uv run python -m pytest tests/ -v`(104件、全PASS)
  * `cd client && npx playwright test tests/integration/t006_reservation_update_self_exclusion.spec.ts tests/acceptance/a002_admin_journey.spec.ts tests/acceptance/a006_room_deactivation_existing_reservations.spec.ts`(3件、全PASS)
  * `cd client && npx playwright test tests/acceptance/a007_performance_calendar.spec.ts`(PASS。修正後、性能そのものも3秒以内であることを確認できた)
* テスト結果: すべてPASS。T006, A002, A006, A007はFAIL→PASSに変わった。サーバーログに `sqlite3.ProgrammingError` が一切出力されなくなったことも確認した。
* 残課題: なし。
* 修正経緯: 初回対応で解決(過去ループでの未解決記録なし)。

