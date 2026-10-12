import { expect } from "@playwright/test";
import { open_page, push_toast, test } from "./fixtures.js";

// Text button created by the engine for onClick (not the Toastify X).
const CLICK_BUTTON = ".toastify button:not(.toast-close)";

const DEFAULT_PATH = "/dashboard-home/default_view";

test("renders_message_with_theme_color", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page, { color: "success" });

  const toast = page.locator(".toastify");
  await expect(toast).toHaveCount(1);
  await expect(toast).toContainText("Test");
  await expect(toast).toHaveCSS("background-color", "rgb(0, 176, 155)");
});

test("no_button_without_on_click", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page); // close: false, onClick: null

  await expect(page.locator(".toastify")).toHaveCount(1);
  await expect(page.locator(".toastify button")).toHaveCount(0);

  await push_toast(page, { close: true });
  await expect(page.locator(".toastify .toast-close")).toHaveCount(1);
  // The X is not a text button.
  await expect(page.locator(CLICK_BUTTON)).toHaveCount(0);
});

test("on_click_empty_object_shows_close_button", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page, { onClick: {} });

  await expect(page.locator(CLICK_BUTTON)).toHaveText("CLOSE");
});

test("on_click_label_is_shown", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page, { onClick: { action: "/x", label: "Open" } });

  await expect(page.locator(CLICK_BUTTON)).toHaveText("Open");
});

test("on_click_path_opens_new_tab", async ({ context, page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page, { onClick: { action: "/x", label: "Open" } });

  const [popup] = await Promise.all([
    context.waitForEvent("page"),
    page.locator(CLICK_BUTTON).click(),
  ]);
  await popup.waitForLoadState();

  expect(popup.url()).toMatch(/\/x$/);
});

test("on_click_service_calls_call_service", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page, {
    onClick: { action: "light.turn_on", action_data: { entity_id: "light.test" } },
  });

  await page.locator(CLICK_BUTTON).click();
  await expect
    .poll(() => page.evaluate(() => window.__service_calls))
    .toEqual([["light", "turn_on", { entity_id: "light.test" }]]);
});

test("on_click_unknown_key_does_nothing", async ({ context, page }) => {
  await open_page(page, DEFAULT_PATH);
  const pages_before = context.pages().length;
  await push_toast(page, { onClick: { URL: "/x" } });

  await page.locator(CLICK_BUTTON).click();
  await page.waitForTimeout(1200);

  // No popup, no service call, toast dismissed - documented behavior for
  // action objects that carry no actionable "action" key.
  expect(context.pages().length).toBe(pages_before);
  expect(await page.evaluate(() => window.__service_calls)).toEqual([]);
  await expect(page.locator(".toastify")).toHaveCount(0);
});

test("contrast_text_color", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  // The server expands #rgb to #rrggbb; the engine only sees the long form.
  await push_toast(page, { color: "#ffffff" });
  await push_toast(page, { color: "#000000" });

  // Toastify ignores oldestFirst and prepends the newest toast, so the DOM
  // order is the reverse of the push order - assert pairs, not positions.
  const colors = await page.locator(".toastify").evaluateAll((els) =>
    els.map((el) => [
      getComputedStyle(el).backgroundColor,
      getComputedStyle(el).color,
    ]),
  );
  expect(colors).toContainEqual(["rgb(255, 255, 255)", "rgb(0, 0, 0)"]);
  expect(colors).toContainEqual(["rgb(0, 0, 0)", "rgb(255, 255, 255)"]);
});

test("visibility_depends_on_path", async ({ page }) => {
  await open_page(page, "/developer-tools/action");
  await push_toast(page, { visibility: "dashboard" });
  await page.waitForTimeout(2000);
  await expect(page.locator(".toastify")).toHaveCount(0);

  await push_toast(page, { visibility: "all" });
  await expect(page.locator(".toastify")).toHaveCount(1);

  await open_page(page, DEFAULT_PATH);
  await push_toast(page, { visibility: "dashboard" });
  await expect(page.locator(".toastify")).toHaveCount(1);
});

test("gravity_center_renders_top", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  await push_toast(page, { gravity: "center" });
  await push_toast(page, { gravity: "bottom" });

  // Position-independent: Toastify appends each new toast at the top of the
  // container, so gravity mapping is checked per class, not per order.
  await expect(page.locator(".toastify.toastify-top")).toHaveCount(1);
  await expect(page.locator(".toastify.toastify-bottom")).toHaveCount(1);
});

test("label_is_rendered_as_text", async ({ page }) => {
  await open_page(page, DEFAULT_PATH);
  // Exactly what the server sends after _sanitize_label.
  await push_toast(page, {
    onClick: { action: "/x", label: "a &amp; b &lt;b&gt;x&lt;/b&gt;" },
  });

  const button = page.locator(CLICK_BUTTON);
  await expect(button).toHaveText("a & b <b>x</b>");
  expect(await button.locator("b").count()).toBe(0);
});
