# プログラム実装定義 兼 プログラミング指示書(目次)

> 本書は `spec-driven-dev` Skill フェーズP007の成果物(OKF形式の目次)です。
> インプット: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`
> **改訂(CR-001 / P903 2026-08-05)**: CR-001(予約にオンライン会議URL)により U003-T5 と U004-T6 を追加しました。

## 1. 実装担当(Executor)への共通指示

* 各スプリントの指示ファイルを**上から順に**開き、その中のタスクを記載順に実施すること。
* 1タスクごとに人間の指示を待たない。Executor Stepの停止条件(`SKILL.md`: 単体テストが3回自己修正しても合格しない)に該当した場合のみ処理を止めて報告する。
* **仕様外の拡張を禁止する。** `docs/P002-frontend-spec.md` `docs/P003-backend-spec.md` にない画面・API・DB項目・業務ルールを追加しないこと。仕様に書かれていない判断が必要になった場合は、勝手に決めず本書「5. 未解決事項」に追記して、最も素直な解釈で実装を進めること。
* スプリントの実装(該当する単体テストを含む)が完了したら、本書の該当スプリント行のチェックボックスを `[x]` に更新すること(P102の一部)。
* 結合テストの実施は本書の対象外である。`docs/P008-test-direction.md` の指示に従ってP103で実施する。

## 2. コードの格納先

クライアント・サーバ型のため、プロジェクトルート直下に次の2つのソースツリーを置く(P007実行時に初期化済み)。

| ソースツリー | 内容 | 初期化方法 | テスト実行コマンド |
| --- | --- | --- | --- |
| `server/` | バックエンド(サーバサイド技術は `docs/ADR.md` の **ADR-002** を参照) | `uv init --lib`(実行済み。`pyproject.toml` / `src/meeting_room/` / `.python-version` を生成済み) | `cd server && python3 -m unittest discover -s tests -t .` |
| `client/` | フロントエンド(クライアントサイド技術は `docs/ADR.md` の **ADR-001** を参照) | `npm init`(実行済み。`package.json` のみ。依存パッケージは持たない) | `cd client && node --test tests` |

* 参照するADR番号(ADR-001 / ADR-002 / ADR-003)は、本書執筆時点では予定値だったが、**P021で `docs/ADR.md` が作成され、予定どおりの番号で確定した**(ADR-001 = フロントエンド技術の選定、ADR-002 = バックエンド技術の選定、ADR-003 = パスワードハッシュ方式)。P021にて本書および各スプリント指示ファイル(`U001`〜`U004`)の参照番号との一致を確認済みであり、本項は解消済みである(この前後関係は `SKILL.md` のフェーズ順序(P007 → P021)に起因する)。
* 併せて `docs/ADR.md` にはADR-004〜ADR-010(データストア、認証方式、セッション永続化、重複判定と排他制御、論理削除、マイグレーション方式、実行トポロジ)が追加されている。実装時はこれらも参照すること。
* 既に存在するディレクトリ・ファイルは再初期化しないこと。
* サーバー側の追加ディレクトリ(`server/src/meeting_room/repositories/` など)は、各タスクの指示に従って作成する。

## 3. スプリント一覧(WBS)

- [x] U001 [基盤・認証スプリント](./P007-impl-direction/U001-foundation-auth.md) — プロジェクト骨格、DB接続とマイグレーション基盤、`users`/`sessions`、認証API3本、S01ログイン画面、フロントエンド共通基盤
- [x] U002 [マスタ管理スプリント](./P007-impl-direction/U002-master-management.md) — `rooms`、会議室API4本、ユーザーAPI4本、S06会議室管理画面、S07ユーザー管理画面
- [x] U003 [予約コアスプリント](./P007-impl-direction/U003-reservation-core.md) — `reservations`/`reservation_attendees`、予約API6本、重複チェックと排他制御。※CR-001のタスク U003-T5(`meeting_url` の列追加とAPI反映)も実装・単体テスト完了
- [x] U004 [予約画面スプリント](./P007-impl-direction/U004-reservation-ui.md) — S02カレンダー、S03予約作成、S04予約詳細・編集、S05マイ予約一覧。※CR-001のタスク U004-T6(S03・S04のオンライン会議URL)も実装・単体テスト完了

* 実行順は上から順(U001 → U002 → U003 → U004)。`docs/P005-impl-plan.md` 3.4 の依存関係に従う。
* 全4行が `[x]` になるまで、P007の実行対象であるスプリント群は完了しない。

## 4. タスクIDの付け方

* 各スプリント指示ファイルの中で、タスクを `U00N-T1` 〜 `U00N-T6` の形式で番号付けする(例: `U001-T1`)。
* `SKILL.md` の「各フェーズで作成するドキュメント」表はスプリント単位のファイル(`U000-{sprint-name}.md`)を定め、`TEMPLATE-P007-impl-direction.md` はタスク単位の構成を定めている。本書は、**1つのスプリントファイルの中にテンプレートの構成をタスク数だけ繰り返す**形で両者を満たす。★FIXME★ この入れ子の表現方法はSKILL側に明示の規定がないため、本プロジェクトの規約として定めた。
* 目次(第3章)のチェックボックスは**スプリント単位**である(タスク単位ではない)。スプリント内の全タスクが完了した時点で `[x]` にすること。

## 5. 未解決事項

実装タスクには含めない。人間または後続フェーズの判断が必要な事項。

| # | 内容 | 検出元 | 扱い |
| --- | --- | --- | --- |
| 1 | P001指定の技術スタック(React 18 + TypeScript + Vite / FastAPI)が実行環境の制約で使えず、代替構成で実装する | `docs/P004-traceability-matrix.md` 3章(逸脱#1・#2) | 代替構成のまま実装する。人間が方針を確定するまで保留 |
| 2 | S07のパスワード入力欄、`GET /api/users?scope=attendee_candidates` の一般ユーザー開放、会議室・ユーザー無効化の業務制約は、P001に対応する要求がない | `docs/P004-traceability-matrix.md` 5章(過剰実装#2〜#5) | P002・P003の記載どおりに実装する(削除しない)。要求書への追記要否は人間が判断する |
| 3 | 初期管理者の払い出し手順(環境変数の受け渡し、初回パスワード変更の強制) | `docs/P003-backend-spec.md` 3.6 | 環境変数 `INITIAL_ADMIN_ID` / `INITIAL_ADMIN_PASSWORD` から読む実装とし、変更強制は実装しない |
| 4 | ロック競合時に 500 を返す方針(503 + Retry-After ではない) | `docs/P003-backend-spec.md` 5.3 | P003の記載どおり 500 で実装する |
| 5 | 結合テストのHTTPクライアント手段(`httpx` が入手できるか不明) | `docs/P006-test-plan.md` 1.1 | 単体テストでは影響しない。P008の実行時に確認する |
| 6 | フロントエンド単体テストの実行コマンド `cd client && node --test tests` が、実行環境の Node.js v22.22.2 では動作しない(ディレクトリ指定がモジュール解決エラー `Cannot find module '.../tests'` になる)。また既定のテストファイル検出パターンは `test_*.js` を拾わない | U001-T5・U001-T6・U002-T4・U002-T5 の【実行コマンド】、P101 3章 | ファイル名はP007の指定(`test_validation.js` など)のまま維持し、実行コマンドのみ `cd client && node --test 'tests/*.js'` に読み替えて実行した。P008 の結合テスト側はファイルを直接指定しているため影響なし。指示書の実行コマンドの修正要否は人間の判断を仰ぐ |
| 7 | 409 `DUPLICATE_KEY` のフィールド直下の表示文言が、P002 2.4(「同じ値がすでに登録されています。」)と `docs/P008-test-direction/T010-master-screens-api.md` 手順4(「同じ名前の会議室がすでに登録されています。」= APIの `message`)で食い違う | P002 2.4 / P008 T010 | APIが `message` を返す場合はそれを優先して該当フィールド直下に表示し、無い場合のみP002 2.4の既定文言を使う実装とした(両者を同時に満たす)。P002 2.4 の記述を「APIの message を優先」に更新すべきかは人間の判断を仰ぐ |
| 8 | 会議室名が50文字を超えた場合、および最後の有効な管理者を保護する場合のエラー文言がP002・P003に無い | P002 3.6 / 5.6、P003 6.3 | 他項目の言い回しに合わせてAgentの想定で補い、該当箇所に★FIXME★を付記した(`client/src/lib/validation.js`、`server/src/meeting_room/schemas.py`、`server/src/meeting_room/services/user_service.py`) |
| 9 | `GET /api/users?scope=` に未知の値が来たときの挙動がP002 5.6・P003 6.3に無い | P002 5.6 | 400 `VALIDATION_ERROR`(`field="scope"`)と解釈して実装した(★FIXME★ を `handlers/user_handlers.py` に付記) |
| 10 | U002の単体テスト `tests/test_rooms_repo.py` が `schema_migrations` の内容を `["001-init.sql", "002-rooms.sql"]` と完全一致で検証しており、U003で `003-reservations.sql` を追加した時点で必ずFAILになる。U003の「タスクの範囲外のファイルは編集しない」と「単体テストが全件PASS」が両立しない | U003-T1 実行時 | 先頭2件のみを固定で検証する形(`versions[:2]`)に緩め、行数比較を「適用前後で増えないこと」に変更した。スプリント境界をまたぐ既存テストの前提更新は許容せざるを得ないため、この扱いの妥当性は人間の判断を仰ぐ |
| 11 | 予約入力のうち「30分刻み違反」「業務時間外」「参加者の重複選択」「無効・存在しない参加者の指定」のエラー文言がP002 3.3に無い | U003-T2、P002 3.3 | 他項目の言い回しに合わせてAgentの想定で補い、★FIXME★ を `schemas.py`(`TIME_STEP_MESSAGE` / `BUSINESS_HOURS_MESSAGE` / `DUPLICATE_ATTENDEE_MESSAGE`)と `services/reservation_service.py`(`ATTENDEE_INVALID_MESSAGE`)に付記した |
| 12 | API-12・API-13 のクエリ検証エラー(`date_to < date_from`、31日超過、`room_id` が整数でない、`period` が不正)の文言・`field` 値がP002 5.7に無い | U003-T3、P002 5.7 | `field` はそれぞれ `date_to` / `date_to` / `room_id` / `period` とし、文言はAgentの想定で補って ★FIXME★ を `handlers/reservation_handlers.py` に付記した |
| 13 | 過去日の予約を**取消**したときのエラー文言がP002 3.4に無い(編集時の「過去の予約は編集できません。」のみ記載) | U003-T2、P002 3.4 | 編集時と同じ文言を流用し、★FIXME★ を `services/reservation_service.py`(`PAST_RESERVATION_MESSAGE`)に付記した |
| 14 | P003 5.3 は「ロック競合をログに `error_code=DB_LOCK_TIMEOUT` で記録する」と定めるが、実装上はロック競合も `ApiError(500, "INTERNAL_ERROR")` として送出されるため、`logging_middleware` が出すアクセスログの `error_code` は `INTERNAL_ERROR` になる | U003-T2、P003 5.3 | アクセスログの1行とは別に、`meeting_room.access` ロガーへ `error_code=DB_LOCK_TIMEOUT` の1行を追加出力する実装とした(`logging_middleware.py` を改造せずに要件を満たすため)。ログ形式をどちらに寄せるかは人間の判断を仰ぐ |
| 15 | S03/S04 の成功メッセージ(「予約を登録しました。」など)をS02へ引き渡す仕組みがP002に定義されていない(P002 3.3・3.4 は「S02へ戻り〜を表示」とだけ書かれている) | U004-T2、P002 3.3 / 3.4 | `views/s02-calendar.js` に1回限りの受け渡し口(`setFlash` / `takeFlash`)を設け、S03・S04がそこへ文言を渡す実装とした(`api.js` の `takePendingMessage` はセッション切れ専用のため流用しない)。共通部品として切り出すかは人間の判断を仰ぐ |
| 16 | S04の「キャンセル」の戻り先(遷移元=S02またはS05)を、ハッシュルーティングでどう伝えるかがP002 3.4に定義されていない | U004-T3、P002 3.4 | `#/reservations/{id}?from=#/my-reservations` のようにクエリで受け取り、未指定なら `#/calendar` へ戻す実装とした(★FIXME★ を `views/s04-reservation-detail.js` に付記)。S05側からの遷移でこのクエリを付けるかは人間の判断を仰ぐ |
| 17 | 参加者候補の「複数選択」UIの具体形(プルダウンかチェックボックスか)がP002 3.3に確定していない | U004-T2、P002 3.3 | `<select multiple>` + `<option>` として実装した(P008 T016 の「参加者候補のプルダウン」という記述に合わせた) |
| 18 | **参加予定人数の収容人数超過について、P002 3.3・U004-T2 が「クライアント側で送信前に検証し、フィールド直下に表示(APIを呼ばない)」と定める一方、P008 T016 手順7は「400 `CAPACITY_EXCEEDED` が返り、収容人数超過エラー領域に表示される」ことを期待しており、会議室が選択済みのケースでは両立しない** | P103 実行時(T016 手順7 がFAIL)、P002 3.3 / 2.4、U004-T2、T016 | 仕様(P002 3.3・U004-T2)どおりクライアント側検証を優先する実装のままとし、T016 手順7 のFAILは `docs/test-records/20260805-1226-test-record.md` に記録してReviewer Loop(P201〜)へ引き渡した(P103は失敗を修正しない)。想定される解消案は (a) クライアント側の収容人数超過メッセージも収容人数超過エラー領域に表示する、(b) T016 手順7 の期待結果をフィールド直下表示に改める、のいずれか。**→ 解決済み(Reviewer Loop の修正タスク F001)。(b) を採用し、`docs/P008-test-direction/T016-create-flow.md` 手順7 の期待結果を「POSTは呼ばれず、参加予定人数欄の直下に表示」に修正した。実装コードは変更していない。根拠: (1) T016 は自身の【参照テスト計画】でP002 3.3 を仕様の根拠として挙げており、V字モデル上P002が上流である。(2) P002 3.3「表示項目」は収容人数超過エラーメッセージ領域を「400 `CAPACITY_EXCEEDED` 時」の表示先と定めているため、(a) を採るとP002 3.3自身の記述と矛盾する。(3) P002 7.2 のシーケンス図も400の分岐を「収容人数超過(サーバー側検出)」と明記している。(4) サーバー側400の被覆は T013 手順1 が保持している。詳細は `docs/P202-fix-plan/fixed/F001-t016-capacity-expectation.md`** |
