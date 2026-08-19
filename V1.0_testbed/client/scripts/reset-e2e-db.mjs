// E2Eテスト用データストアを、ベースライン(マイグレーション適用直後)へ復元する。
//
// docs/P006-test-plan.md「テストデータのライフサイクル方針」にもとづく。
// ベースラインは「全行削除」ではなく「マイグレーション適用直後の状態」を指す。
// server/migrations/002_seed_initial_users.sql が admin001/user001 を投入するため、
// 全行削除ではログインできなくなる。ここではDBファイルを削除するだけとし、
// 復元はバックエンド起動時のマイグレーション自動適用(server/app/main.py)に任せる。
//
// 【この処理をwebServerの起動コマンドに置いている理由】
// Playwrightの globalSetup は webServer の起動「後」に実行される。そのため globalSetup で
// DBファイルを削除すると、起動済みのバックエンドが掴んでいるファイルを消すことになり、
// 実行が不安定になる(実際にネイティブクラッシュを再現した)。
// 復元は「テスト対象アプリの起動前」でなければならないため、起動コマンドの一部としている。
//
// 復元の単位は「テスト1件ごと」ではなく「スイートの実行ごと」である。
// テストごとに復元すると、先行するテストが用意したデータまで消してしまうため。
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// 呼び出し元のカレントディレクトリに依存しないよう、本スクリプト自身の位置から解決する。
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.resolve(scriptDir, "..", "..", "server", "data", "e2e-test.db");

// 注: fs.rmSync は本実行環境(Node.js v24.12.0/Windows)でネイティブクラッシュするため使用しない。
// 詳細は e2e-validation-report.md 参照。unlinkSync + try/catch で代替する。
for (const suffix of ["", "-wal", "-shm", "-journal"]) {
  try {
    fs.unlinkSync(`${dbPath}${suffix}`);
  } catch (err) {
    if (err.code !== "ENOENT") throw err;
  }
}

console.log(`[reset-e2e-db] E2Eデータストアをベースラインへ復元しました: ${dbPath}`);
