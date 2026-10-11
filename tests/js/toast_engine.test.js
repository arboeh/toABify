import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

const jsPath = resolve(__dirname, "../../custom_components/toabify/dist/toast_engine.js");
const jsCode = readFileSync(jsPath, "utf-8");

let wsCallbacks = [];
let toastifyInstances = [];
let callServiceMock;
let openSpy;

function setupWindow() {
  document.body.innerHTML = "";
  wsCallbacks = [];
  toastifyInstances = [];

  callServiceMock = vi.fn().mockResolvedValue(undefined);

  const hass = {
    connection: {
      subscribeMessage: vi.fn((cb, opts) => {
        wsCallbacks.push({ type: opts?.type, callback: cb });
        return Promise.resolve();
      }),
    },
    callService: callServiceMock,
  };

  const haEl = document.createElement("home-assistant");
  haEl.hass = hass;
  document.body.appendChild(haEl);

  const origQuerySelector = document.querySelector;
  document.querySelector = (sel) =>
    sel === "home-assistant" ? haEl : origQuerySelector.call(document, sel);

  window.Toastify = vi.fn((config) => {
    if (config?.node && config.node.parentNode !== document.body) {
      document.body.appendChild(config.node);
    }
    const instance = {
      showToast: vi.fn(() => {
        if (config?.node) document.body.appendChild(config.node);
      }),
      hideToast: vi.fn(),
    };
    toastifyInstances.push(instance);
    return instance;
  });

  openSpy = vi.spyOn(window, "open").mockImplementation(() => null);

  return { hass, haEl };
}

function loadEngine() {
  const origCreateElement = document.createElement.bind(document);
  document.createElement = (tag) => {
    const el = origCreateElement(tag);
    if (tag === "script") {
      Object.defineProperty(el, "onload", {
        set: (fn) => { if (fn) fn(); },
        configurable: true,
      });
    }
    return el;
  };

  try {
    eval(jsCode);
  } finally {
    document.createElement = origCreateElement;
  }
}

function setLocation(pathname) {
  Object.defineProperty(window, "location", {
    writable: true,
    value: { pathname },
  });
}

describe("toast_engine.js protocol identifiers", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("subscribes with type 'toastify/subscribe'", () => {
    setupWindow();
    loadEngine();

    vi.advanceTimersByTime(2000);

    expect(wsCallbacks.length).toBe(1);
    expect(wsCallbacks[0].type).toBe("toastify/subscribe");
  });
});

describe("toast_engine.js resource loading", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("loads toastify CSS stylesheet with correct id and href", () => {
    setupWindow();
    loadEngine();

    const cssLink = document.getElementById("toastify-css");
    expect(cssLink).not.toBeNull();
    expect(cssLink.tagName.toLowerCase()).toBe("link");
    expect(cssLink.rel).toBe("stylesheet");
    expect(cssLink.href).toContain("/toastify_lib/toastify.css");
  });

  it("loads toastify JS library with correct id and src", () => {
    setupWindow();
    loadEngine();

    const jsScript = document.getElementById("toastify-js");
    expect(jsScript).not.toBeNull();
    expect(jsScript.tagName.toLowerCase()).toBe("script");
    expect(jsScript.src).toContain("/toastify_lib/toastify.js");
  });

  it("injects keyframe pulse style into document head", () => {
    setupWindow();
    loadEngine();

    const styles = document.head.querySelectorAll("style");
    const allStyles = Array.from(styles).map((s) => s.innerHTML).join("");
    expect(allStyles).toContain("toast-label-pulse");
  });
});

describe("toast_engine.js toast creation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    setLocation("/lovelace/default_view");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("creates a toast with default duration 5000", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    expect(wsCallbacks.length).toBe(1);
    wsCallbacks[0].callback({ message: "Hello!" });

    expect(window.Toastify).toHaveBeenCalledOnce();
    const config = window.Toastify.mock.calls[0][0];
    expect(config.duration).toBe(5000);
  });

  it("uses custom duration from message", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Test", duration: 3000 });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.duration).toBe(3000);
  });

  it("does not create toast when message is empty", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "" });
    expect(window.Toastify).not.toHaveBeenCalled();
  });

  it("uses theme color for 'info' color", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Info", color: "info" });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.style.background).toBe("#03a9f4");
  });

  it("uses theme color for 'success' color", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Success", color: "success" });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.style.background).toBe("#00b09b");
  });

  it("uses theme color for 'warning' color", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Warning", color: "warning" });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.style.background).toBe("#ff9800");
  });

  it("uses theme color for 'error' color", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Error", color: "error" });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.style.background).toBe("#f44336");
  });

  it("uses direct hex color when not a theme name", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Custom", color: "#ff5733" });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.style.background).toBe("#ff5733");
  });

  it("defaults to 'right' position and 'top' gravity", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Position Test" });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.gravity).toBe("top");
    expect(config.position).toBe("right");
  });

  it("creates Mdi icon element for mdi: icon prefix", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "With Icon", icon: "mdi:bell" });
    const config = window.Toastify.mock.calls[0][0];
    const iconEl = config.node.querySelector("ha-icon");
    expect(iconEl).not.toBeNull();
    expect(iconEl.getAttribute("icon")).toBe("mdi:bell");
  });

  it("creates image element for non-mdi icons", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Img", icon: "https://example.com/img.png" });
    const config = window.Toastify.mock.calls[0][0];
    const imgEl = config.node.querySelector("img");
    expect(imgEl).not.toBeNull();
    expect(imgEl.src).toContain("img.png");
  });

  it("passes callback as string to Toastify config", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Callback Test",
      callback: "/local/service",
    });
    const config = window.Toastify.mock.calls[0][0];
    expect(config.callback).toBeInstanceOf(Function);
  });

  it("omits callback field when using server-side callback dict", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Dict Callback",
      callback: { action: "light.turn_on", action_data: {} },
    });
    const config = window.Toastify.mock.calls[0][0];
    expect(typeof config.callback).toBe("function");
  });
});

describe("toast_engine.js visibility filtering", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("shows 'dashboard' toast on lovelace page", () => {
    setLocation("/lovelace/default_view");
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Hi" });
    expect(window.Toastify).toHaveBeenCalledOnce();
  });

  it("shows 'all' visibility toast on any page", () => {
    setLocation("/history");
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Hi", visibility: "all" });
    expect(window.Toastify).toHaveBeenCalledOnce();
  });

  it("does not show 'dashboard' toast on non-dashboard page", () => {
    setLocation("/history");
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Hi", visibility: "dashboard" });
    expect(window.Toastify).not.toHaveBeenCalled();
  });

  it("shows 'dashboard' toast on /dashboard page", () => {
    setLocation("/dashboard/1");
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Hi" });
    expect(window.Toastify).toHaveBeenCalledOnce();
  });

  it("shows toast with explicit visibility='dashboard' on dashboard page", () => {
    setLocation("/lovelace/default_view");
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({ message: "Hi", visibility: "dashboard" });
    expect(window.Toastify).toHaveBeenCalledOnce();
  });
});

describe("toast_engine.js action execution", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    setLocation("/lovelace/default_view");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("opens URL for http actions via onClick button", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Hello",
      onClick: { action: "https://example.com" },
    });

    const btn = document.querySelector("button");
    expect(btn).not.toBeNull();
    btn.click();

    expect(openSpy).toHaveBeenCalledWith("https://example.com", "_blank");
  });

  it("opens relative URL for slash-prefixed actions", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Hello",
      onClick: { action: "/local/page" },
    });

    const btn = document.querySelector("button");
    btn.click();

    expect(openSpy).toHaveBeenCalledWith("/local/page", "_blank");
  });

  it("calls HA service for dot-separated actions via onClick", async () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Hello",
      onClick: {
        action: "light.turn_on",
        action_data: { entity_id: "light.test" },
      },
    });

    const btn = document.querySelector("button");
    expect(btn).not.toBeNull();
    btn.click();

    await vi.waitFor(() => {
      expect(callServiceMock).toHaveBeenCalled();
    }, { timeout: 3000 });

    expect(callServiceMock).toHaveBeenCalledWith("light", "turn_on", {
      entity_id: "light.test",
    });
  });

  it("uses custom button label when provided", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Hello",
      onClick: { label: "Click Me" },
    });

    const btnLabel = document.querySelector(".btn-label-text");
    expect(btnLabel).not.toBeNull();
    expect(btnLabel.textContent).toBe("Click Me");
  });

  it("defaults button label to CLOSE", () => {
    setupWindow();
    loadEngine();
    vi.advanceTimersByTime(2000);

    wsCallbacks[0].callback({
      message: "Hello",
      onClick: { action: "https://example.com" },
    });

    const btnLabel = document.querySelector(".btn-label-text");
    expect(btnLabel).not.toBeNull();
    expect(btnLabel.textContent).toBe("CLOSE");
  });
});
