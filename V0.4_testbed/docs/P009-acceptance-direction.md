# 受け入れ結合テスト定義(スプリント横断/システム/受入) 兼 テスト指示書 — 目次(OKF形式)

> 本書は `spec-driven-dev` Skill フェーズP009の成果物です。インプット文書: `docs/P001-requirement.md`、`docs/P006-test-plan.md`。
> 対象範囲: 複数スプリントをまたぐ連携、システムテスト相当(P001要件・非機能要件充足確認)、受入テスト相当(利用者視点シナリオ)。単体テスト・スプリント内結合テストは対象外(`docs/P007-impl-direction.md`/`docs/P008-test-direction.md` を参照)。
> テスト記録の記録先: `docs/test-records/YYYYMMDD-HHMM-test-record.md`(P201で追記)。

## 目次

- [x] A001 [会議室無効化後の新規予約選択肢からの除外](./P009-acceptance-direction/A001-room-deactivation-excludes-new-reservation.md) — sprint2→3、業務フロー
- [x] A002 [予約作成〜カレンダー反映〜マイ予約〜取消の一連業務シナリオ](./P009-acceptance-direction/A002-reservation-lifecycle-scenario.md) — sprint3→4、業務フロー
- [x] A003 [管理者による他人予約の編集・取消](./P009-acceptance-direction/A003-admin-edit-others-reservation.md) — sprint2×4、権限をまたぐ確認
- [x] A004 [一般ユーザーによる管理者専用機能への全面的なアクセス不可確認](./P009-acceptance-direction/A004-general-user-cannot-access-admin-features.md) — 認証・認可をまたぐ横断確認
- [x] A005 [無効化されたユーザーの遅延失効確認](./P009-acceptance-direction/A005-deactivated-user-session-expiry.md) — sprint1×2、認証をまたぐ確認
- [x] A006 [カレンダー表示の性能確認(3秒以内)](./P009-acceptance-direction/A006-calendar-performance.md) — 非機能(性能)
- [x] A007 [同一枠への同時予約リクエストの排他制御確認](./P009-acceptance-direction/A007-concurrent-reservation-requests.md) — 非機能(同時実行)
- [x] A008 [パスワード非平文保持・SQLインジェクション対策確認](./P009-acceptance-direction/A008-security-password-and-sql-injection.md) — 非機能(セキュリティ)
- [x] A009 [ログ出力(標準出力・構造化ログ)確認](./P009-acceptance-direction/A009-logging-output.md) — 非機能(運用)
- [x] A010 [利用者視点の受入シナリオ(ログインから予約完了・取消・ログアウトまで)](./P009-acceptance-direction/A010-end-to-end-user-scenario.md) — 受入テスト相当

## 進捗更新ルール

* 各テストタスクが完了したら(PASS/FAIL/BLOCKEDいずれの結果であっても記録が残った時点で)、Reviewer Loopは該当行のチェックボックスを `[x]` に更新する。
* 全テストが `[x]` になるまでP201は完了しない。FAIL/BLOCKEDが残っている場合は、P202(修正計画)への引き渡しが必要である旨をここに明記する。

## 未解決事項

* P201第1回実行(`docs/test-records/20260803-1900-test-record.md`)で、A001〜A007・A009がFAIL、A008が混合(手順3のみPASS)、A010がBLOCKEDと判定された。P202(修正計画)・P203(修正実施)に引き渡し済み。チェックボックスの `[x]` は「実行・記録が完了した」ことを示すのみで、合否とは独立である(`SKILL.md` の目次(OKF形式)についての定義を参照)。
* P202(`docs/P202-fix-plan.md` F001〜F003)・P203(修正実施)・P204(影響分析)・P205(再実行、`docs/test-records/20260803-1930-test-record.md`)を経て、A001〜A010はすべてPASSに至った(P201第2回、`docs/P201-review-report.md` 参照)。未解決事項は残っていない。
