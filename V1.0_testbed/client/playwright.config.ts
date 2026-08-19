import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.resolve(__dirname, "..", "server", "data", "e2e-test.db");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
  },
  webServer: [
    {
      command: `uv --directory ../server run uvicorn app.main:app --port 8000`,
      url: "http://localhost:8000/openapi.json",
      reuseExistingServer: false,
      env: { DATABASE_PATH: dbPath },
      timeout: 30_000,
    },
    {
      command: "npm run dev -- --port 5173 --strictPort",
      url: "http://localhost:5173",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
