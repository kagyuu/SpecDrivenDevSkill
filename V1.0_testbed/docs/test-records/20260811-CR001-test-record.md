# テスト記録 2026-08-11(CR-001対応)

> P903(Refactor実行)〜P205(結合テスト再実施)相当。CR-001(予約への「備考(社内向けメモ)」欄追加)にともなう実装・テストの結果を記録する。

## 実行環境共通

* サーバー: `server/.venv`(既存の仮想環境をそのまま使用)。`uv`コマンド自体はローカル実行環境のPATHに存在しなかったため、`server/.venv/Scripts/python.exe`を直接使用した(`docs/P101-impl-context.md`のネットワーク制約にもとづく代替とは別種の、ローカル実行環境固有のツール可用性の差異。恒久的な仕様変更は行っていない)。
* フロントエンド: `client/`の既存`node_modules`をそのまま使用(Node.js v24.12.0)。

## 実行結果一覧

| コマンド | 件数 | 結果 |
| --- | --- | --- |
| `cd server && <venv>/python.exe -m pytest tests/ -v` | 121件 | **全PASS** |
| `cd client && npx vitest run` | 25件 | **全PASS** |
| `cd client && npx tsc -b` | — | **成功**(型エラー0件) |
| `cd client && npx playwright test tests/integration/` | 9件(T001〜T010) | **全PASS** |
| `cd client && npx playwright test tests/acceptance/` | 5件(A001・A002・A004・A005・A007) | **全PASS** |
| `cd client && npm run build`(`vite build`) | — | **失敗(環境要因、下記参照)** |

## `npm run build` の失敗について

* `tsc -b`(型検査)は成功したのち、`vite build`(rollupによるバンドル)が「46 modules transformed.」の直後に、ソースコードの内容によらずネイティブクラッシュ(プロセス終了コード `0xC0000409` = `STATUS_STACK_BUFFER_OVERRUN`、Windows版rollupネイティブバインディング内)で異常終了することを確認した。
* 切り分けのため以下を実施し、いずれもCR-001のソースコード変更に起因しないと判断した。
  * `--minify false` を付けても同じ箇所でクラッシュする(minifyの問題ではない)。
  * `node_modules/@rollup/*`・`node_modules/@esbuild/*` を削除して`npm install`で再インストールしても再現する(ネイティブバイナリの破損ではない)。
  * `esbuild.exe --version` は単体で正常動作する。
  * 最小限のrollup単体呼び出し(`rollup({input}) → bundle.generate()`)はエラーなく成功する(rollup自体が全面的に壊れているわけではなく、vite特有のビルドパイプラインの中でのみクラッシュする)。
  * `vite`(開発サーバー)は正常に起動・応答する(`curl`で200を確認)。
  * `npx playwright test`(`npm run dev`経由、本番ビルド不使用)はT001〜T010・A001・A002・A004・A005・A007のすべてでPASSしている。
* 以上より、Node.js v24.12.0とrollup 4.62.4のWindowsネイティブバインディングの組み合わせに起因するローカル実行環境固有の問題である可能性が高いと判断し、これ以上のツールチェイン側の追跡調査(依存関係のダウングレード等)は本ラウンドのCR-001スコープ外として保留し、人間に報告する。
* この完了条件については、`tsc -b`の型検査・`npx vitest run`の単体テスト・`npx playwright test`のE2Eテスト(dev-mode、production buildを経由しない)がいずれも全PASSであることをもって代替確認とした。`docs/P007-impl-direction/U002-reservation-core.md`(U002-T7)・`docs/P007-impl-direction/U003-reservation-management-and-rooms.md`(U003-T7)の完了条件欄に同内容を記録済み。

## `docs/P901-cr-direction/CR-001.md` の各「期待する振る舞い」との対応(P904相当の一次確認)

| # | 期待する振る舞い | 確認方法 | 結果 |
| --- | --- | --- | --- |
| 1 | 所有者・管理者はS03/S04で「備考(社内向けメモ)」を入力・閲覧できる | T010手順1〜3 | PASS |
| 2 | 所有者・管理者以外にはAPIレスポンスの`internal_memo`が`null`になる(詳細・一覧の双方) | T010手順4、`test_get_reservation_non_owner_non_admin_gets_null_internal_memo`・`test_list_reservations_non_owner_non_admin_gets_null_internal_memo` | PASS |
| 3 | 300文字を超える入力は拒否される | `test_reservation_create_request_rejects_internal_memo_over_300_chars`・`test_post_reservation_internal_memo_over_300_chars_is_rejected` | PASS(ただし実際のエラー形式は既存の欠陥により422/`detail`。上記「`npm run build`の失敗について」に隣接する未解決事項参照) |
| 4 | 既存の`notes`(公開の備考)の閲覧範囲・文字数制限は変更されない | 既存の`test_reservation_*`群(500文字制限・全ユーザー閲覧可)がすべてPASSのまま | PASS |
| 5 | マイグレーションは2回連続実行しても失敗しない | `test_run_migrations_applies_004_as_a_pure_diff_on_top_of_001_002_003` | PASS |

## サーバーログ確認

* `migrations_applied` イベントで `versions: [1, 2, 3, 4]` を確認し、004が正しく適用されていることを確認した(T010実行時のWebServerログ)。

## 判定

* Unit Test 121件・vitest 25件・Playwright(integration/acceptance)14件、いずれも全PASS。`npm run build`のみ環境要因により未検証(上記参照)。
* P904(CR反映確認)へ進む。
