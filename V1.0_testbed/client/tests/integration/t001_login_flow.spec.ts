import { expect, test } from "@playwright/test";
import { createRoomViaApi, loginViaApi, loginViaUi, logoutViaApi, uniqueName } from "./helpers";

// docs/P008-test-direction/T001-login-me-rooms-flow.md
test("T001: ログイン〜自分情報〜会議室一覧の結合確認", async ({ page, context }) => {
  // 事前準備: admin001でAPI経由ログインし、会議室を1件用意してからログアウトする。
  await loginViaApi(context, "admin001");
  const room = await createRoomViaApi(context, uniqueName("T001会議室"));
  await logoutViaApi(context);

  await loginViaUi(page, "user001");

  // ユーザー名がGET /api/meの結果と一致して画面に表示されること。
  await expect(page.getByText("一般花子")).toBeVisible();

  // 会議室一覧(会議室フィルタの選択肢)がGET /api/roomsの結果と一致すること。
  const roomFilter = page.getByLabel("会議室フィルタ");
  await expect(roomFilter.locator(`option[value="${room.id}"]`)).toHaveText(room.name);
});
