# 修正計画書 — 目次(OKF形式)

> 本書は `spec-driven-dev` Skill フェーズP202の成果物です。インプット文書: `docs/P201-review-report.md`、`docs/test-records/20260803-1900-test-record.md`。
> `docs/P201-review-report.md` でPASS以外と判定されたA001〜A007・A009(FAIL)、A008(混合)、A010(BLOCKED)を対象に、根本原因単位で3件の修正指示を作成した(根本原因1件が複数テストIDに波及しているケースがあるため、`SKILL-P202-fix-plan.md` の原則「失敗したテスト1件につき1ファイル」から意図的に外れている。詳細はF001冒頭の注記を参照)。
> F004はCR-002(Refactor、P901〜P905)の反映確認過程で検出したT022・T023の失敗に対する修正指示(同一根本原因のため1ファイルにまとめた。V0.5 defect 2-5対応の実地検証を兼ねる)。

## 目次

- [x] F001 [セッションCookieの`Secure`属性によるログイン後即時未認証化](./P202-fix-plan/fixed/F001-session-cookie-secure-flag.md) — 対応: A001, A002, A003, A004, A005, A006, A007, A008(手順1), A010
- [x] F002 [構造化ログ(JSON Lines)が標準出力に一切出力されていない](./P202-fix-plan/fixed/F002-structured-logging-missing.md) — 対応: A009
- [x] F003 [A008手順2の期待結果がbcrypt前提のままで承認済みのscrypt代替実装と食い違っている(ドキュメントのみの修正)](./P202-fix-plan/fixed/F003-a008-hash-format-expectation.md) — 対応: A008(手順2)
- [x] F004 [CR-002: room_service.update()がdescriptionをrepositoryへ渡し忘れていたため更新のたびに説明文が消去される](./P202-fix-plan/fixed/F004-room-update-drops-description.md) — 対応: T022, T023

## 進捗更新ルール

* 修正が完了した項目はチェックボックスを `[x]` に更新すると同時に、リンク先を `docs/P202-fix-plan/fixed/F00N-*.md` に書き換える。
* 全項目が `[x]` になったらP203は完了とみなし、P204(影響分析)に進む。
