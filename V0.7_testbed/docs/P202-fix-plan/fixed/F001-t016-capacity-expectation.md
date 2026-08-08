あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F001 — T016 手順7 の期待結果(収容人数超過)を仕様に合わせる

## 【対応する失敗テスト】T016

* 1件のみ。`docs/P008-test-direction/T016-create-flow.md` 手順7。
* 本F001は **A001 とは根本原因が異なる**ため、まとめない(A001 は F002 で扱う)。

## 【障害記録】

* テスト記録: `docs/test-records/20260805-1226-test-record.md` の T016 ブロック(P103での初回検出)。
* 失敗コマンド: `cd client && node --test tests/integration/test_t016_create_flow.js`
* 失敗内容: 手順7(会議室A 収容人数10 / 参加予定人数11 / 14:00-15:00 で登録)で、テストは `POST /api/reservations` が呼ばれて 400 `CAPACITY_EXCEEDED` が返ることを期待しているが、実際には **POSTが1回も発行されない**(`1 !== 2`)。

```text
not ok 7 - 手順7: 14:00-15:00 / 参加予定人数11 は 400 CAPACITY_EXCEEDED になり所定領域に出る
    POST /api/reservations が呼ばれること
    1 !== 2
```

* 事象は「クライアント側の収容人数検証が送信前に成立し、APIに到達しない」ことによる。
* 既に `docs/P007-impl-direction.md` 5章「未解決事項」#18 として、仕様間の矛盾の疑いが記録されている。

## 【参照ファイル】

* `docs/P002-frontend-spec.md` 3.3(S03の項目表・「参加予定人数の検証タイミング」・表示項目)、2.4(クライアント側バリデーション違反ではAPIを呼ばない)、7.2(予約作成のシーケンス図)
* `docs/P007-impl-direction/U004-reservation-ui.md` U004-T2(実装内容)
* `docs/P008-test-direction/T016-create-flow.md` 手順7・期待結果
* `docs/P008-test-direction/T013-capacity-and-authz.md`(サーバー側 400 `CAPACITY_EXCEEDED` の担当テスト)
* `client/src/views/s03-reservation-new.js`、`client/src/components/reservation-form.js`、`client/src/lib/validation.js`
* `client/tests/integration/test_t016_create_flow.js`

## 【調査方針】

1. どちらが上流の仕様か(V字モデルでどちらが根拠か)を確定する。T016 は自身の【参照テスト計画】で「仕様: `docs/P002-frontend-spec.md` 3.3・2.4・4・5.7」を根拠として挙げている。すなわち T016 は P002 3.3 から**導出された**テストであり、両者が食い違う場合は P002 が上流である。
2. P002 3.3 の3つの記述を突き合わせる。
   * 項目表の「参加予定人数」行のエラーメッセージ列: 「参加予定人数が会議室の収容人数({capacity}名)を超えています。」— 他の全項目と同じく**フィールド単位のメッセージ**として定義されている。
   * 「参加予定人数の検証タイミング」: 「会議室選択の変更時と**送信時にクライアント側で検証する**。… サーバー側でも同じ検証を行い、超過時は 400 `CAPACITY_EXCEEDED` を返す。」
   * 「表示項目」: 「収容人数超過エラーメッセージ領域(**400 `CAPACITY_EXCEEDED` 時**)」— この領域は 400 応答を受けたときの表示先として定義されている。
3. P002 2.4 の「クライアント側バリデーション違反ではAPIを呼ばない」と、P002 7.2 のシーケンス図を確認する。図は `S03->>S03: クライアント側バリデーション(収容人数超過を含む)` を POST の**前**に置き、400 の分岐には `else 収容人数超過(**サーバー側検出**)` と明記している。つまり設計は「クライアント側検証で止まるのが通常経路、400 はサーバー側の二重防御」という構造である。
4. サーバー側 400 `CAPACITY_EXCEEDED` の被覆が失われないことを確認する(T013 手順1 が API レベルで 400 `CAPACITY_EXCEEDED` を PASS で確認済み)。

## 【修正方針】

* **結論: テスト指示(T016 手順7)の期待結果が誤り**である。`SKILL-P202-fix-plan.md` の「テスト指示や期待結果に誤りがあった → P008側を修正する」に該当する。**アプリケーションコードは変更しない。**
  * 採らない案: 「クライアント側の収容人数超過メッセージも `[data-role="capacity-error"]` 領域に表示する」(P007 #18 の案(a))。P002 3.3 が同領域を「400 `CAPACITY_EXCEEDED` 時」の表示先と明記しているため、コード側を変えるとP002 3.3の表示項目定義と矛盾する。加えて項目表はフィールド単位メッセージを定義しており、現実装はP002の記述に一致している。
* 具体的な修正内容:
  1. `docs/P008-test-direction/T016-create-flow.md` 手順7 の【期待結果】を、仕様どおりの挙動に書き換える。
     * 「`POST /api/reservations` は呼ばれず、参加予定人数欄の直下に『参加予定人数が会議室の収容人数(10名)を超えています。』が表示される。画面はS03のまま」。
     * あわせて、サーバー側の 400 `CAPACITY_EXCEEDED` は T013 手順1 が担当することを注記し、被覆の欠落がないことを明示する。
     * 修正理由と根拠(P002 3.3 / 2.4 / 7.2)を同ファイル内に1〜2行で残す。
  2. `client/tests/integration/test_t016_create_flow.js` の手順7 のアサーションを、上記の期待結果に合わせて書き換える。**期待値を緩めるのではなく、仕様どおりの期待値に置き換える**こと(POSTが増えないこと・フィールド直下のメッセージ文言が一致することの両方を検証する)。
  3. `docs/P007-impl-direction.md` 5章「未解決事項」#18 の「扱い」列に、Reviewer Loop(F001)で (b) 案を採って解決したことと、その根拠を追記する。
* 範囲を広げないこと。S03・S04の実装コード、`validation.js`、P002本体の記述はいずれも変更しない。

## 【試行錯誤してよい範囲】

* 上記【参照ファイル】の読み取り、`node --test` によるテスト再実行。
* 一時的にログを挿入して「POSTが発行されないこと」「どのDOM要素にメッセージが入るか」を確認すること(確認後に必ず除去する)。
* アプリケーションコード(`client/src/**`、`server/src/**`)の恒久的な変更は行わない。

## 【修正成功時に更新するdocs】

* `docs/P008-test-direction/T016-create-flow.md`(手順7 の期待結果。必須)
* `docs/P007-impl-direction.md` 5章 #18(扱いの追記。必須)
* `docs/P202-fix-plan/fixed/F001-t016-capacity-expectation.md`(修正内容の詳細)
* `docs/P202-fix-plan/P202-fix-resolved.md`(概要)

## 【ロールバック条件】

* 作業開始前に、資産一式を `meeting-room-YYYYMMDDHHMMSS.zip` として退避しておく(本プロジェクトはGit管理外)。
* T016 が PASS にならない場合、または他のクライアント側テスト(単体126件・結合)に退行が出た場合は、退避した資産から本タスクの変更のみを戻す。他の修正タスク(F002)の変更は戻さない。

## 【検証コマンド】

* `cd client && node --test tests/integration/test_t016_create_flow.js`(手順1〜8すべてPASS)
* `cd client && node --test 'tests/*.js'`(単体126件が退行していないこと)
* `cd client && node --test 'tests/integration/*.js'`(結合が退行していないこと)
* `cd server && python3 -m unittest tests.integration.test_t013_capacity_and_authz -v`(サーバー側 400 の被覆が残っていること)

## 【完了条件】

* T016 の8手順すべてが PASS。
* クライアント単体・結合、サーバー単体・結合に退行がない。
* `docs/P008-test-direction/T016-create-flow.md` と `docs/P007-impl-direction.md` #18 が更新されている。
* アプリケーションコードの差分が0であること。

## 重要:

* 作業開始前に現在の変更状態を確認してください。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

---

# 【修正結果】(P203で追記)

## 判定

* **RESOLVED**(2026/08/05)

## 実施した内容

1. **どちらが正か**の確定(【調査方針】1〜4を実施):
   * T016 は自身の【参照テスト計画】で「仕様: `docs/P002-frontend-spec.md` 3.3・2.4・4・5.7」を根拠に挙げている。V字モデル上、テストの期待結果は設計から導出されるため **P002 が上流であり authoritative** である。
   * P002 3.3 の3記述はすべて現実装と一致する。項目表はフィールド単位メッセージ「参加予定人数が会議室の収容人数({capacity}名)を超えています。」を定義し、「参加予定人数の検証タイミング」は送信時のクライアント側検証を義務づけ、「表示項目」は収容人数超過エラーメッセージ領域を **400 `CAPACITY_EXCEEDED` 時**の表示先と定めている。
   * P002 7.2 のシーケンス図も `S03->>S03: クライアント側バリデーション(収容人数超過を含む)` を POST の前に置き、400 の分岐に `else 収容人数超過(サーバー側検出)` と明記している。
   * 実装(`client/src/views/s03-reservation-new.js` の `submit`、`client/src/components/reservation-form.js` の `validate`/`showErrors`、`client/src/lib/validation.js` の `validateAttendeeCount`)は上記どおりであり、**コードは仕様に一致している**。
   * サーバー側 400 の被覆は `docs/P008-test-direction/T013-capacity-and-authz.md` 手順1 が担っており、実測でも PASS(`cd server && python3 -m unittest tests.integration.test_t013_capacity_and_authz` → 1 test / OK)。
2. **テスト指示の修正**: `docs/P008-test-direction/T016-create-flow.md`
   * 手順7 の記述に「(会議室Aの収容人数10を超える値)」を補足。
   * 【期待結果】手順7 を「`POST /api/reservations` は呼ばれず、参加予定人数欄の直下に『参加予定人数が会議室の収容人数(10名)を超えています。』が表示される。画面はS03のまま」に変更し、根拠(P002 3.3 / 2.4 / 7.2)・被覆の担当(T013 手順1)・修正経緯(F001)を併記した。
3. **テストコードの修正**: `client/tests/integration/test_t016_create_flow.js` 手順7
   * `postCalls().length` が **増えないこと**、`[data-error-for="attendee_count"]` の文言が仕様の文言と**完全一致**すること、`[data-role="capacity-error"]` が空であること、画面遷移が起きていないことを検証する形に置き換えた(アサーションの削除・緩和はしていない。検証項目は1→4に増えている)。
4. **`docs/P007-impl-direction.md` 5章 #18** の「扱い」列に、(b) 案を採用した旨と4点の根拠、参照先を追記した。

## 変更したソースコード

* **アプリケーションコードの変更は0件**(`client/src/**` / `server/src/**` に差分なし)。
* テストコード: `client/tests/integration/test_t016_create_flow.js`(手順7のみ)

## 更新したdocs

* `docs/P008-test-direction/T016-create-flow.md`
* `docs/P007-impl-direction.md`(5章 #18)

## 実行したテスト / テスト結果

| コマンド | 結果 |
| --- | --- |
| `cd client && node --test tests/integration/test_t016_create_flow.js` | 8 tests / **8 pass / 0 fail** |
| `cd client && node --test 'tests/*.js'` | 126 tests / **126 pass** |
| `cd client && node --test 'tests/integration/*.js'` | 41 tests / **41 pass** |
| `cd server && python3 -m unittest tests.integration.test_t013_capacity_and_authz` | 1 test / **OK** |

## 残課題

* なし。P002本体の記述は変更していないため、仕様側の追加判断は不要。
* 参考: 「クライアント側の収容人数超過も専用領域に出す」という別案(P007 #18 の (a))を将来採りたい場合は、P002 3.3 の「表示項目」の定義変更を伴うため、CR(P901)として起票するのが適切である。

## 修正経緯

* P103(2026/08/05 12:26)で T016 手順7 が初回FAIL。P103の規定により修正せず記録のみ。
* P201 第1回(2026/08/05 16:03)で未解決のFAILとして再確認し、P202 で F001 を起票。
* P203 で上記のとおり **テスト指示側の誤り**と確定し修正。`docs/P202-fix-plan/P202-fix-unresolved.md` への該当記載は存在しない(P103 の時点では未修整記録ファイル自体が未作成だったため、コピー・削除の対象なし)。
