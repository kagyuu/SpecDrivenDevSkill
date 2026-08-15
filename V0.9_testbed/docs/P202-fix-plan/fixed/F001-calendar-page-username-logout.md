あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F001

## 【対応する失敗テスト】T001

## 【障害記録】

* `docs/test-records/20260811-0500-test-record.md` T001参照。`user001`でログインしS02(`/calendar`)へ遷移しても、画面上のどこにもログインユーザーの氏名が表示されない。また、`docs/P002-frontend-spec.md` §4(画面遷移図)・`docs/P001-requirement.md` の画面遷移図が示す「S02 -- ログアウト --> S01」の導線(ログアウトボタン/リンク)も実装されていない。
* 原因区分: **アプリケーションコードの欠陥**(未実装)。`docs/P007-impl-direction/U002-reservation-core.md` U002-T5(S02実装タスク)の完了条件にはこれらの要素が明記されておらず、P007自体の記載漏れが実装時にそのまま欠落として現れた。

## 【参照ファイル】

* `client/src/pages/CalendarPage.tsx`
* `docs/P002-frontend-spec.md` §1(認証方式の外部契約)、§4(画面遷移図)
* `server/app/api/routers/auth.py`(`POST /api/auth/logout` は既に実装済み)

## 【調査方針】

* `CalendarPage.tsx` が `GET /api/me` の結果(`me.name`)をどこにも描画していないこと、およびログアウトを呼ぶUI要素が存在しないことをコードリーディングで確認する(既に`docs/test-records/20260811-0500-test-record.md`で確認済みのため、再調査は簡易でよい)。
* `POST /api/auth/logout` は既に実装・単体テスト済み(U001-T4)であるため、バックエンド側の修正は不要と想定されるが、念のためエンドポイントの動作を再確認する。

## 【修正方針】

* `CalendarPage.tsx` の `<nav>` 内に、ログイン中ユーザーの氏名を表示する要素(例: `<span>{me.name} さん</span>`)を追加する。
* 同じ `<nav>` 内に「ログアウト」ボタンを追加し、押下で `POST /api/auth/logout` を呼び、成功後にS01(`/`)へ遷移する処理を実装する。
* `docs/P002-frontend-spec.md` に、このヘッダー要素(ユーザー名表示・ログアウトボタン)の存在が明記されていないことに気づいたため、修正と合わせて `docs/P002-frontend-spec.md` §3 S02 に一言追記する(仕様の明確化。判断を伴わない範囲の追記のため、このタスク内で行ってよい)。

## 【試行錯誤してよい範囲】

* `client/src/pages/CalendarPage.tsx` の表示・イベントハンドラの実装。
* 対応するテスト `client/src/tests/CalendarPage.test.tsx` へのテストケース追加(ログアウトボタンの存在・クリック時の遷移確認)。

## 【修正成功時に更新するdocs】

* `docs/P002-frontend-spec.md` §3 S02(ヘッダーのユーザー名表示・ログアウト導線を明記)。

## 【ロールバック条件】

* `client/src/pages/CalendarPage.tsx` の変更によりビルド(`npm run build`)または既存の `CalendarPage.test.tsx` の他のテストが壊れた場合は、変更前の状態に戻す。

## 【検証コマンド】

* `cd client && npm run build`
* `cd client && npx vitest run src/tests/CalendarPage.test.tsx`
* `cd client && npx playwright test tests/integration/t001_login_flow.spec.ts`

## 【完了条件】

* 上記検証コマンドがすべて成功する。
* T001が再実行でPASSになる。

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
* 変更したソースコード:
  * `client/src/pages/CalendarPage.tsx`: `<nav>` 内にログインユーザー名表示(`{me.name} さん`)と「ログアウト」ボタン(`POST /api/auth/logout` 呼び出し→`/`へ遷移)を追加。
  * `client/src/tests/CalendarPage.test.tsx`: ユーザー名表示・ログアウト動作を確認する単体テストを2件追加。`mockApiFetch` に `/api/auth/logout` のモック応答を追加。
* 更新したdocs: `docs/P002-frontend-spec.md` §3 S02(ヘッダー要素の明記を追記)。
* 実行したテスト: `npm run build`、`npx vitest run src/tests/CalendarPage.test.tsx`(5件PASS)、`npx playwright test tests/integration/t001_login_flow.spec.ts`。
* テスト結果: すべてPASS。T001はFAIL→PASSに変わった。
* 残課題: なし。
* 修正経緯: 初回対応で解決(過去ループでの未解決記録なし)。

