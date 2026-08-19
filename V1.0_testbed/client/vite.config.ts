/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 開発サーバー・E2Eテスト実行時、フロントエンド(Vite)とバックエンド(FastAPI)を
    // ブラウザから見て同一オリジンにするためのプロキシ。
    // ※P103(結合テスト実行)実施中に発見: Cookieセッション(ADR-005、SameSite=Lax)は
    // クロスオリジンのfetch/XHRには送出されない仕様のため、フロントエンドとバックエンドを
    // 別オリジン(別ポート)のまま連携させるとログイン後のCookieがAPI呼び出しに付与されず
    // 認証が機能しない。本番環境ではリバースプロキシ配下でSPA静的配信とAPIを同一オリジンに
    // 統合する前提(docs/P003-backend-spec.md §7のTLS終端前提と整合)だが、開発・E2Eテスト時に
    // 同じ前提を再現するため、このプロキシ設定を追加した。
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/tests/setup.ts"],
    // include を src/tests/ 配下に限定する。tests/integration/ はPlaywright(E2E)専用のスペックであり
    // (P103で追加)、Vitestの既定パターン(**/tests/**)に含まれてしまうと `test()` の呼び出し元が
    // 異なるフレームワークであるとして収集エラーになるため、明示的に除外する。
    include: ["src/tests/**/*.test.{ts,tsx}"],
  },
});
