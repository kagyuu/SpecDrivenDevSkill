import type { BrowserContext, Page } from "@playwright/test";

export const TEST_PASSWORD = "TestPassw0rd!";

export async function loginViaUi(page: Page, employeeId: string, password = TEST_PASSWORD) {
  await page.goto("/");
  await page.getByLabel("社員ID").fill(employeeId);
  await page.getByLabel("パスワード").fill(password);
  await page.getByRole("button", { name: "ログイン" }).click();
  await page.waitForURL("**/calendar");
}

export async function logoutViaApi(context: BrowserContext) {
  await context.request.post("/api/auth/logout");
  await context.clearCookies();
}

export async function createRoomViaApi(context: BrowserContext, name: string, capacity = 10) {
  // 事前にadmin001としてログイン済みのcontextであることを前提とする。
  const resp = await context.request.post("/api/rooms", {
    data: { name, capacity },
  });
  if (!resp.ok()) {
    throw new Error(`会議室作成に失敗: ${resp.status()} ${await resp.text()}`);
  }
  return resp.json();
}

export async function loginViaApi(context: BrowserContext, employeeId: string, password = TEST_PASSWORD) {
  const resp = await context.request.post("/api/auth/login", {
    data: { employee_id: employeeId, password },
  });
  if (!resp.ok()) {
    throw new Error(`ログインに失敗: ${resp.status()} ${await resp.text()}`);
  }
  return resp.json();
}

export function uniqueName(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
}

// ※P202 F002にもとづき追加: アプリ側(CalendarPage.tsx)がローカルタイムゾーン基準の
// 日付文字列を使うようになったため(toISOString()=UTC基準は使わない)、テスト側の
// 日付計算もローカル基準に統一する。
export function localDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function todayDateString(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return localDateString(d);
}
