import { expect, test } from "@playwright/test";


test("launchpad contains every named activity and no board", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Play a Friend" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Challenge Sifu" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Analyze a Position" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Review a Record" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tournament Library" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Xiangqi board" })).toHaveCount(0);
});


test("friend move persists and can be resumed after reload", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 });
  await page.goto("/");
  await page.getByRole("button", { name: "Play a Friend" }).click();
  const dialog = page.getByRole("dialog", { name: "Play a Friend" });
  await dialog.getByLabel("Red player").fill("Mei");
  await dialog.getByLabel("Black player").fill("Lin");
  await dialog.getByRole("button", { name: "Play a Friend" }).click();

  const boardBeforeMove = await page.locator(".board-frame").boundingBox();
  await page.getByTestId("square-h2").click();
  await page.getByTestId("square-e2").click();
  await expect(page.getByText("BLACK TO MOVE")).toBeVisible();
  await expect(page.getByTestId("last-move-origin-h2")).toBeVisible();
  await expect(page.getByTestId("last-move-destination-e2")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollHeight <= window.innerHeight)).toBe(true);
  const boardAfterMove = await page.locator(".board-frame").boundingBox();
  expect(boardBeforeMove).not.toBeNull();
  expect(boardAfterMove?.x).toBeCloseTo(boardBeforeMove!.x, 1);
  expect(boardAfterMove?.y).toBeCloseTo(boardBeforeMove!.y, 1);

  await page.reload();
  await page.getByRole("button", { name: /Mei — Lin.*Continue/ }).click();
  await expect(page.getByText("1 / 1 moves")).toBeVisible();
  await expect(page.getByText("BLACK TO MOVE")).toBeVisible();
});


test("position analysis exposes metadata and grounded chat", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto("/");
  await page.getByRole("button", { name: "Analyze a Position" }).click();
  await page.getByRole("button", { name: "Confirm and analyze" }).click();

  await expect(page.getByRole("region", { name: "Position analysis" })).toBeVisible();
  await expect(page.getByText("h2e2", { exact: true })).toBeVisible();
  const boardWithAnalysis = await page.locator(".board-frame").boundingBox();
  await page.getByRole("button", { name: "Analysis on" }).click();
  const boardWithoutAnalysis = await page.locator(".board-frame").boundingBox();
  expect(boardWithAnalysis).not.toBeNull();
  expect(boardWithoutAnalysis?.x).toBeCloseTo(boardWithAnalysis!.x, 1);
  expect(boardWithoutAnalysis?.y).toBeCloseTo(boardWithAnalysis!.y, 1);
  await page.getByRole("button", { name: "Show the threat" }).click();
  await expect(page.getByText(/Pikafish's first choice is `h2e2`/)).toBeVisible();
});
