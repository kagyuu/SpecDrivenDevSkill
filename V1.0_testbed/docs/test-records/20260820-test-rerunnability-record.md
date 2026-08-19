# テスト記録 — テストスイートの再実行可能性の是正と確認(2026-08-20)

## 対象

`V1.0_testbed` の実地検証で見つかった「生成されたテストスイートが再実行可能でない」問題(`e2e-validation-report.md` 3-1)の是正と、その確認。

Skill V1.0 に追加された次の規定にもとづく作業である。

* `SKILL.md` 共通指示「テストスイートは、続けて2回実行しても同じ結果になること(再実行可能であること)を確認する」
* `SKILL-P006-test-plan.md`「テストデータのライフサイクル方針を明記する」
* `SKILL-P008-test-direction.md`・`SKILL-P009-acceptance-direction.md` の事前準備に関する規定

## 是正前の事象

`client/playwright.config.ts` がE2E用テストDBを固定パス(`server/data/e2e-test.db`)で指定し、誰も復元しないため、実行のたびに予約データが累積していた。

| 実行 | 結合テスト(Playwright、9件) |
| --- | --- |
| DB削除直後の1回目 | **9 passed** |
| 同一DBのまま2回目 | **7 passed / 2 failed** |

失敗内容(いずれも累積データによる要素の重複):

```
T003: strict mode violation: getByText('一般花子 / テスト会議T003') resolved to 2 elements
T005: strict mode violation: getByText('T005未来の予約') resolved to 3 elements
```

## 是正内容

### 1. テストデータのライフサイクル方針の決定(P006相当)

`docs/P006-test-plan.md` §5 に方針を追記した。

* 復元の単位: **テストスイートの実行ごとに1回**(テスト1件ごとには復元しない)
* ベースラインの定義: 全行削除ではなく**マイグレーション適用直後の状態**。`server/migrations/002_seed_initial_users.sql` が `admin001`/`user001` を投入しているため、全行削除するとログインできなくなる
* 復元のタイミング: **バックエンド起動より前**

### 2. 復元処理の実装

* 新規: `client/scripts/reset-e2e-db.mjs` — E2E用DBファイル(および WAL/journal の副産物)を削除する。復元自体はバックエンド起動時のマイグレーション自動適用に任せる。
* 変更: `client/playwright.config.ts` — `webServer` のバックエンド起動コマンドの先頭で上記スクリプトを実行するようにした。

### 3. テスト指示書への反映

* `docs/P008-test-direction.md`・`docs/P009-acceptance-direction.md` に「テスト実行環境(全テスト共通)」節を設け、復元の方針と、**各テストの事前準備に復元手順を書かない**ことを明記した。

## 実装過程で判明した事項

### Playwrightの `globalSetup` はこの用途に使えない

当初、復元処理を Playwright の `globalSetup` に置いたが、実行ログから **`webServer` が `globalSetup` より先に起動する**ことが判明した。

```
[WebServer] INFO:     Started server process [30176]
[WebServer] {"event": "migrations_applied", "versions": []}
[WebServer] INFO:     Application startup complete.
...
[global-setup] E2Eデータストアをベースラインへ復元しました: ...
```

この順序では、起動済みのバックエンドが開いているDBファイルを削除することになり、実行が不安定になった(ネイティブクラッシュを再現)。したがって復元は **`webServer` の起動コマンドの一部**として実行する必要がある。この経緯は `client/playwright.config.ts` のコメントおよび `docs/P006-test-plan.md` に★ACCEPTED★付きで記録した。

### 本実行環境固有のNode.jsの不具合: `fs.rmSync` がネイティブクラッシュする

復元スクリプトの実装中、`fs.rmSync()` の呼び出しが Node.js v24.12.0(Windows)で**必ずネイティブクラッシュする**ことを特定した。

```
STATUS_STACK_BUFFER_OVERRUN (0xC0000409 / exit -1073740791)
```

最小再現:

```js
import fs from "node:fs";
fs.rmSync("nonexistent-xyz.db", { force: true });   // → クラッシュ
```

対象ファイルが存在する場合・しない場合のいずれでもクラッシュする。`fs.unlinkSync()` + `try/catch`(ENOENTを無視)は正常に動作するため、復元スクリプトはこちらを用いている。

**この不具合は、`V0.9_testbed` で「原因不明」として記録されていた `npm run build`(`vite build`)のネイティブクラッシュを説明する可能性が高い。** `vite build` は出力先ディレクトリの掃除に `fs.rmSync(outDir, { recursive: true, force: true })` を用いるため、同じ不具合を踏んでいると考えられる。`V0.9_testbed` では「ソース内容によらずクラッシュする」と記録されており、この説明と整合する。

これはアプリケーションの欠陥でも Skill の欠陥でもなく、**実行環境(Node.js v24.12.0/Windows)の問題**である。

## 確認結果

`SKILL.md` 共通指示「続けて2回実行しても同じ結果になること」にもとづき、実際に連続実行して確認した。

| スイート | 1回目 | 2回目 | 3回目 |
| --- | --- | --- | --- |
| 結合テスト(Playwright、`tests/integration/`) | ✅ 9 passed | ✅ 9 passed | ✅ 9 passed |
| 受け入れ結合テスト(Playwright、`tests/acceptance/`) | ✅ 5 passed | ✅ 5 passed | — |

**是正前は2回目で2件失敗していたが、是正後は連続実行でも全件PASSする。**

なお、サーバ側のpytestスイート(121件)は元々テストごとに一時DBを作る構成であり、この問題の対象外である(是正前から再実行可能)。

## 実行環境上の注記

本環境には `uv` が導入されていないため、`client/playwright.config.ts` の `webServer` 設定(`uv --directory ../server run uvicorn ...`)はそのままでは起動しない。上記の実行時のみ、この部分を `.venv/Scripts/python.exe -m uvicorn ...` に一時的に差し替えて実行し、**実行後に原状復帰した**。復元スクリプトの呼び出し部分(`node scripts/reset-e2e-db.mjs &&`)は原状復帰後の形でもパスが正しく解決されることを確認済み。
