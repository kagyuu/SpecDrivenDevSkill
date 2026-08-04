> ## 【対応結果(P203で追記)】
>
> * ステータス: **RESOLVED**(2026-08-03)
> * 変更したソースコード: なし(方針どおりドキュメントのみ)。
> * 更新したdocs: `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md`(手順2の期待結果をscrypt形式前提に更新)。
> * 実行したテスト・結果: A008を再実行し、手順1・2・3すべてPASS(`docs/test-records/20260803-1930-test-record.md`参照)。
> * 残課題: なし。
> * 修正経緯: 当初「未解決」記録はなかった(1回目の修正で解決)。

---

あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F003(A008手順2の期待結果がbcrypt前提のままで、承認済みのscrypt代替実装と食い違っている)

## 【対応する失敗テスト】A008(手順2)

## 【障害記録】

* `docs/test-records/20260803-1900-test-record.md` 根本原因3。
* `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md` の期待結果は「`password_hash`がbcrypt形式(`$2b$...`)であり平文と異なる」と明記しているが、実装は `docs/P101-impl-context.md` で承認済みの代替方式(`hashlib.scrypt`、`scrypt1$<salt>$<hash>` 形式)を一貫して使用している。これはコードの不具合ではなく、P009文書(Plan Loop Step完了時点で作成)がP101(Executor開始時点)のサンドボックス制約による代替決定を反映していないために生じたテスト指示書側の記述の古さである。

## 【参照ファイル】

* `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md`
* `docs/P101-impl-context.md`
* `server/app/core/password.py`

## 【調査方針】

* 該当なし(原因は既に特定済み、`docs/test-records/20260803-1900-test-record.md` 参照)。

## 【修正方針】

* ソースコードは修正しない(scrypt代替は既に全プロジェクトで承認済みの決定であり、ここだけbcryptに戻すのは範囲外の後退修正になる)。
* `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md` の期待結果・合否判定基準を、実装済みの代替方式(scrypt、`scrypt1$...`形式)を前提にした表現に更新する。「平文と異なる、既知の安全なハッシュアルゴリズムのタグ付き形式であること」を判定基準にする。

## 【試行錯誤してよい範囲】

* `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md` のみ(ソースコードは変更しない)。

## 【修正成功時に更新するdocs】

* `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md`
* `docs/P202-fix-plan/P202-fix-resolved.md`

## 【ロールバック条件】

* 該当なし(ドキュメントのみの修正)。

## 【検証コマンド】

* F001修正後、A008を再実行し、手順1・2・3すべてPASSすることを確認する(P205)。

## 【完了条件】

* `docs/P009-acceptance-direction/A008-security-password-and-sql-injection.md` の期待結果が実装済みの代替方式と一致する。
* F001修正後の再実行でA008がPASSする。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 本タスクはドキュメントのみの修正であり、ソースコードは変更しません。

## 完了条件:

* `docs/P202-fix-plan/P202-fix-resolved.md` に修正結果が記録されている。

## 未解決時の記録方法:

* 該当なし(想定される未解決理由はない)。
