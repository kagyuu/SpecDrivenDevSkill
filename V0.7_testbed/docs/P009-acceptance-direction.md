# 受け入れ結合テスト定義(スプリント横断/システム/受入) 兼 テスト指示書(目次)

> 本書は `spec-driven-dev` Skill フェーズP009の成果物(OKF形式の目次)です。
> インプット: `docs/P001-requirement.md`、`docs/P006-test-plan.md`
> **改訂(CR-001 / P903 2026-08-05)**: CR-001(予約にオンライン会議URL)により A001 に手順を追加し、A007(再起動耐性)を必須の再実行対象としました。

## 1. 本書の範囲

* 対象は、**スプリントをまたぐ結合テスト、システムテスト、受け入れテスト**、および実行可能な範囲の非機能テストである。
* 単体テストは `docs/P007-impl-direction.md`(P007)、スプリント内に閉じた結合テストは `docs/P008-test-direction.md`(P008)で指示済みのため、ここでは指示しない。
* 実行はP201(Reviewer Loop)が行う。本フェーズでは実行しない。

## 2. 実行担当(Reviewer Loop)への共通指示

* **テスト前に必ず全モジュールをビルドする。**
  * ビルド対象: `server/`(Pythonパッケージ)と `client/`(依存パッケージなし。構文検査で代替)。
  * ビルドコマンド: `cd server && python3 -m compileall -q src` および `cd client && node --check src/main.js`(★FIXME★ 全モジュールの構文検査方法は実装構成に合わせて読み替えること。ESモジュールを個別に `node --check` する、またはテスト実行時のimportで代替する)。
  * 成功条件: いずれのコマンドも終了コード0。
  * 失敗時: 失敗内容をテスト記録に残し、当該テストを **BLOCKED** とする。**ビルド失敗時はテストへ進まない。**
* **テスト失敗時に、その場で修正しないこと。**
  * アプリケーションコードを修正しない / テストコードをその場で都合よく変更しない / 失敗したテストをスキップしない / 期待値を変更して成功扱いにしない / 同じ失敗に対して場当たり的な再テストを繰り返さない。
  * 失敗内容をテスト記録に残し、修正が必要な場合はP202(修正計画)以降に引き渡す。
* **テスト記録**: `docs/test-records/YYYYMMDD-HHMM-test-record.md` に、`TEMPLATE-test-record.md` の共通形式で記録する。
* テストタスクが完了したら(PASS / FAIL / BLOCKED のいずれであっても記録が残った時点で)、本書の該当行のチェックボックスを `[x]` に更新すること。全テストが `[x]` になるまでP201は完了しない。
* **FAIL / BLOCKED が1件でも残っている場合は、P202(修正計画)への引き渡しが必要である。** その旨を第5章に記録すること。

## 3. 共通の前提とテストデータ

* 基準データセットは `docs/P006-test-plan.md` 5章に定めたもの(`admin001` / `user001` / `user002` / `user003`(無効)、会議室A(収容10)/ B(収容4)/ C(無効))。
* 各テストは、原則として開始時にDBファイルを作り直して基準データセットを投入する。**A007(再起動耐性)だけは同じDBファイルを使い回す。**
* 日付は固定値をハードコードせず、実行時に「本日」から相対で計算する。
* 画面操作を伴うテストは、実ブラウザを使わず、画面モジュールの描画関数とイベントハンドラを実サーバーに接続して実行する(`docs/P006-test-plan.md` 1.1)。実ブラウザでしか確認できない事項(CSSレイアウト、実クリック)は、A011の手動確認手順として記載する。

## 4. テスト一覧(WBS)

### 業務シナリオ(スプリント横断の結合)

- [x] A001 [予約業務フロー全体](./P009-acceptance-direction/A001-reservation-business-flow.md) — ログイン→カレンダー→作成→詳細→編集→取消の一連。※CR-001の手順(オンライン会議URLの登録・リンク表示・保持)を追加して再実行しPASS
- [x] A002 [二重予約の防止](./P009-acceptance-direction/A002-double-booking-prevention.md) — 逐次・並行の両方で重複が通らないこと
- [x] A003 [権限分離の横断確認](./P009-acceptance-direction/A003-role-separation.md) — 一般ユーザーが管理者機能に到達できないこと
- [x] A004 [会議室マスタ変更の予約への波及](./P009-acceptance-direction/A004-room-master-impact.md) — 無効化・収容人数変更の影響
- [x] A005 [マイ予約とカレンダーの整合](./P009-acceptance-direction/A005-my-reservations-consistency.md) — 同一データの2画面表示の一致
- [x] A006 [認証セッションのライフサイクル](./P009-acceptance-direction/A006-session-lifecycle.md) — 期限切れ・ログアウト・ユーザー無効化

### システムテスト(要件・非機能要件の充足)

- [x] A007 [再起動耐性とデータ永続](./P009-acceptance-direction/A007-restart-resilience.md) — **運用観点 V-O-01 / V-O-02(必須)**。※CR-001で `004-meeting-url.sql`(`ALTER TABLE ... ADD COLUMN`)を追加したため再実行しPASS(3回起動・`schema_migrations` 4行のまま)
- [x] A008 [カレンダー表示の性能](./P009-acceptance-direction/A008-calendar-performance.md) — 3秒以内(V-N-01)
- [x] A009 [同時接続の負荷](./P009-acceptance-direction/A009-concurrent-load.md) — 同時30接続相当(V-N-02)
- [x] A010 [セキュリティの横断確認](./P009-acceptance-direction/A010-security-checks.md) — パスワード保存・Cookie属性・情報漏えい(V-N-03〜06)

### 受け入れテスト

- [x] A011 [利用者視点の受け入れシナリオ](./P009-acceptance-direction/A011-user-acceptance.md) — 社員が迷わず予約できること
- [x] A012 [運用者視点の受け入れシナリオ](./P009-acceptance-direction/A012-operator-acceptance.md) — 初期セットアップ・ログ・停止/再起動

## 5. 引き渡し状況(Reviewer Loopが更新する)

| 項目 | 値 |
| --- | --- |
| 全テスト完了 | **完了**(A001〜A012 の全12件を実施済み。第4章の全行が `[x]`) |
| FAIL件数 | **0**(A001 手順5 のFAILは Reviewer Loop の修正タスク F002 で解消済み) |
| BLOCKED件数 | 0 |
| P202(修正計画)への引き渡し要否 | **不要**(引き渡し済み・解消済み。P205 での再実行で A001 は PASS) |

* 実行記録: `docs/test-records/20260805-1603-test-record.md`(A001〜A012、P201 第1回)
* A011 手順7(実ブラウザでの目視確認)は **NOT RUN**(ブラウザ自動化ツールを取得できない環境。ADR-001 / P006 1.1)。A011の【合否判定基準】により手順1〜6の完了をもって A011 は PASS とし、手順7は `docs/P302-deliver.md` への申し送りとする。
* ※CR-001(2026-08-05 / P903 → P201): A001 に手順(オンライン会議URLの登録・S04でのリンク表示・更新後の保持)を追加して再実行し **PASS**。`004-meeting-url.sql`(`ALTER TABLE ... ADD COLUMN`)の追加に伴い A007(再起動耐性 V-O-01 / V-O-02)も再実行し **PASS**(3回起動して `schema_migrations` は4行のまま、`duplicate column name` なし)。実行記録は `docs/test-records/20260805-1723-test-record.md` および `docs/test-records/20260805-1731-test-record.md`。
* A001 手順5 のFAILは、**テスト指示(A001 手順5「13:00・13:30 のセルに予約が表示される」)が ADR-007 の半開区間 `[start, end)` と矛盾している**ことに起因していた。**Reviewer Loop の修正タスク F002 で「テスト指示の期待結果が誤り」と確定し、手順5と期待結果を ADR-007 に整合させた(実装コードは変更なし)。** 詳細は `docs/P202-fix-plan/fixed/F002-a001-half-open-slot-expectation.md`、`docs/P202-fix-plan/P202-fix-resolved.md`。再実行記録は `docs/test-records/20260805-1620-test-record.md`。
