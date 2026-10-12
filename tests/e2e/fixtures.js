import { test as base } from "@playwright/test";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const DIST_DIR = new URL("../../custom_components/toabify/dist/", import.meta.url);

const read_dist_file = (name) =>
  fs.readFileSync(fileURLToPath(new URL(name, DIST_DIR)));

const LIB_FILES = {
  "/toastify_lib/toastify.js": {
    body: read_dist_file("toastify.js"),
    content_type: "application/javascript",
  },
  "/toastify_lib/toastify.css": {
    body: read_dist_file("toastify.css"),
    content_type: "text/css",
  },
  "/toastify_lib/toast_engine.js": {
    body: read_dist_file("toast_engine.js"),
    content_type: "application/javascript",
  },
};

// The engine reads the hass object off <home-assistant> and subscribes via
// hass.connection.subscribeMessage. This page mocks both, without a server:
// it records service calls and hands the toast push callback to the test.
const TEST_PAGE = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>toabify e2e</title></head>
<body>
<home-assistant></home-assistant>
<script>
window.__service_calls = [];
window.__popups = [];
document.querySelector("home-assistant").hass = {
  connection: { subscribeMessage: (cb) => { window.__toast_push = cb; return Promise.resolve(); } },
  callService: (d, s, data) => { window.__service_calls.push([d, s, data]); return Promise.resolve(); },
};
</script>
<script src="/toastify_lib/toast_engine.js"></script>
</body>
</html>`;

const BASE_URL = "http://toabify.test";

export const test = base.extend({
  context: async ({ context }, use) => {
    // Routed on the context, not the page, so popups are served too.
    await context.route(`${BASE_URL}/**`, async (route) => {
      const file = LIB_FILES[new URL(route.request().url()).pathname];

      if (file) {
        await route.fulfill({
          status: 200,
          contentType: file.content_type,
          body: file.body,
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "text/html; charset=utf-8",
          body: TEST_PAGE,
        });
      }
    });

    await use(context);
  },
});

// Opens a test page and waits until the engine has subscribed. The engine
// polls for the hass object once per second, so this normally takes ~1-2s.
export const open_page = async (page, path) => {
  await page.goto(BASE_URL + path);
  await page.waitForFunction(() => typeof window.__toast_push === "function");
};

// Server defaults (notify.py NOTIFY_SERVICE_FIELDS + const.py defaults).
// visibility is "all" here so only the visibility tests exercise that path.
const TOAST_DEFAULTS = {
  message: "Test",
  duration: 5000,
  close: false,
  position: "right",
  gravity: "top",
  icon: "",
  color: "info",
  visibility: "all",
  button_label: "CLOSE",
  oldestFirst: true,
  onClick: null,
  callback: null,
};

export const push_toast = (page, overrides = {}) =>
  page.evaluate(
    (payload) => window.__toast_push(payload),
    { ...TOAST_DEFAULTS, ...overrides },
  );
