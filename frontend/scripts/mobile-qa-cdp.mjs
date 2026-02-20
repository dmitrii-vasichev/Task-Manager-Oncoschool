import fs from "node:fs/promises";
import path from "node:path";

const DEVTOOLS_HTTP = "http://127.0.0.1:9222";
const API_BASE = "http://127.0.0.1:8000";
const APP_BASE = "http://127.0.0.1:3000";

const TELEGRAM_ID = Number(process.env.QA_TELEGRAM_ID || "");
if (!Number.isFinite(TELEGRAM_ID) || TELEGRAM_ID <= 0) {
  throw new Error("QA_TELEGRAM_ID is required and must be a positive number");
}

const VIEWPORTS = [
  { width: 320, height: 740, label: "320x740" },
  { width: 375, height: 812, label: "375x812" },
  { width: 390, height: 844, label: "390x844" },
];

const ROUTES = [
  { path: "/", name: "dashboard" },
  { path: "/tasks", name: "tasks" },
  { path: "/meetings", name: "meetings" },
  { path: "/analytics", name: "analytics" },
  { path: "/team", name: "team" },
  { path: "/settings", name: "settings" },
  { path: "/broadcasts", name: "broadcasts" },
];

const OUTPUT_DIR = path.resolve(process.cwd(), "frontend/qa/mobile");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function requestJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${url} -> HTTP ${res.status}: ${text.slice(0, 500)}`);
  }
  return res.json();
}

async function createTarget() {
  const res = await fetch(`${DEVTOOLS_HTTP}/json/new?about:blank`, {
    method: "PUT",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to create target: HTTP ${res.status} ${text}`);
  }
  return res.json();
}

async function loginAndGetToken() {
  const payload = await requestJson(`${API_BASE}/api/auth/dev-login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ telegram_id: TELEGRAM_ID }),
  });

  if (!payload?.access_token) {
    throw new Error("No access_token from dev-login");
  }
  return payload.access_token;
}

class CDP {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.seq = 0;
    this.pending = new Map();
    this.listeners = new Map();

    this.opened = new Promise((resolve, reject) => {
      this.ws.addEventListener("open", () => resolve());
      this.ws.addEventListener("error", (event) => reject(event.error || new Error("WS error")));
    });

    this.ws.addEventListener("message", (event) => {
      const msg = JSON.parse(String(event.data));
      if (msg.id) {
        const pending = this.pending.get(msg.id);
        if (!pending) return;
        this.pending.delete(msg.id);
        if (msg.error) {
          pending.reject(new Error(msg.error.message || "CDP error"));
        } else {
          pending.resolve(msg.result || {});
        }
        return;
      }

      if (!msg.method) return;
      const listeners = this.listeners.get(msg.method);
      if (!listeners || listeners.length === 0) return;
      for (const listener of listeners) {
        listener(msg.params || {});
      }
    });

    this.ws.addEventListener("close", () => {
      for (const [, pending] of this.pending) {
        pending.reject(new Error("CDP socket closed"));
      }
      this.pending.clear();
    });
  }

  async ready() {
    await this.opened;
  }

  send(method, params = {}) {
    const id = ++this.seq;
    const payload = JSON.stringify({ id, method, params });
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(payload);
    });
  }

  on(method, handler) {
    const arr = this.listeners.get(method) || [];
    arr.push(handler);
    this.listeners.set(method, arr);
    return () => {
      const current = this.listeners.get(method) || [];
      const next = current.filter((item) => item !== handler);
      this.listeners.set(method, next);
    };
  }

  waitForEvent(method, timeoutMs = 15000) {
    return new Promise((resolve, reject) => {
      let done = false;
      const timer = setTimeout(() => {
        if (done) return;
        done = true;
        off();
        reject(new Error(`Timeout waiting for ${method}`));
      }, timeoutMs);

      const off = this.on(method, (params) => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        off();
        resolve(params);
      });
    });
  }

  async close() {
    try {
      this.ws.close();
    } catch {
      // ignore
    }
  }
}

async function setup(cdp) {
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("DOM.enable");
  await cdp.send("Network.enable");
}

async function setViewport(cdp, width, height) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 2,
    mobile: true,
    screenWidth: width,
    screenHeight: height,
  });
  await cdp.send("Emulation.setTouchEmulationEnabled", {
    enabled: true,
    maxTouchPoints: 5,
  });
}

async function navigate(cdp, url) {
  const loadEvent = cdp.waitForEvent("Page.loadEventFired", 20000);
  await cdp.send("Page.navigate", { url });
  await loadEvent;
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  return result.result?.value;
}

async function waitForCondition(cdp, expression, timeoutMs = 10000, intervalMs = 250) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const value = await evaluate(cdp, expression);
    if (value) return true;
    await sleep(intervalMs);
  }
  return false;
}

async function screenshot(cdp, outPath, width, height) {
  const metrics = await cdp.send("Page.getLayoutMetrics");
  const cssContentSize = metrics.cssContentSize || { width, height };
  const clip = {
    x: 0,
    y: 0,
    width: Math.max(width, Math.ceil(cssContentSize.width || width)),
    height: Math.max(height, Math.ceil(cssContentSize.height || height)),
    scale: 1,
  };

  const data = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: true,
    clip,
  });

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, Buffer.from(data.data, "base64"));
}

function overflowProbeExpr() {
  return `(() => {
    const viewportWidth = window.innerWidth;
    const scrollWidth = document.documentElement.scrollWidth;
    const bodyScrollWidth = document.body ? document.body.scrollWidth : 0;
    const nodes = Array.from(document.querySelectorAll('body *'));
    const offenders = [];

    for (const el of nodes) {
      const rect = el.getBoundingClientRect();
      if (!rect || rect.width < 1 || rect.height < 1) continue;
      const style = window.getComputedStyle(el);
      if (style.position === 'fixed' && rect.left >= -1 && rect.right <= viewportWidth + 1) continue;
      if (rect.right > viewportWidth + 1 || rect.left < -1) {
        offenders.push({
          tag: el.tagName.toLowerCase(),
          className: (el.className || '').toString().slice(0, 180),
          text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80),
          left: Number(rect.left.toFixed(1)),
          right: Number(rect.right.toFixed(1)),
          width: Number(rect.width.toFixed(1)),
        });
      }
      if (offenders.length >= 25) break;
    }

    return {
      url: location.pathname + location.search,
      title: document.title,
      viewportWidth,
      scrollWidth,
      bodyScrollWidth,
      hasHorizontalOverflow: scrollWidth > viewportWidth + 1,
      offenders,
    };
  })();`;
}

async function run() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const token = await loginAndGetToken();
  const target = await createTarget();
  const cdp = new CDP(target.webSocketDebuggerUrl);

  try {
    await cdp.ready();
    await setup(cdp);

    await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
      source: `(() => { localStorage.setItem('token', ${JSON.stringify(token)}); })();`,
    });

    await setViewport(cdp, 390, 844);
    await navigate(cdp, `${APP_BASE}/`);
    const loggedIn = await waitForCondition(
      cdp,
      "location.pathname !== '/login'",
      20000,
      300
    );
    const currentPath = await evaluate(cdp, "location.pathname");
    console.log(`logged in: ${loggedIn}, currentPath: ${currentPath}`);
    if (!loggedIn) {
      throw new Error("Login did not complete within timeout");
    }

    const report = {
      generatedAt: new Date().toISOString(),
      routes: ROUTES.map((r) => r.path),
      viewports: VIEWPORTS.map((v) => v.label),
      results: [],
    };

    for (const viewport of VIEWPORTS) {
      for (const route of ROUTES) {
        console.log(`Running ${viewport.label} ${route.path}`);
        await setViewport(cdp, viewport.width, viewport.height);
        await navigate(cdp, `${APP_BASE}${route.path}`);
        await waitForCondition(
          cdp,
          "document.readyState === 'complete' && document.querySelectorAll('.animate-pulse').length === 0",
          15000,
          300
        );
        await sleep(400);

        const probe = await evaluate(cdp, overflowProbeExpr());

        const screenshotPath = path.join(
          OUTPUT_DIR,
          viewport.label,
          `${route.name}.png`
        );
        await screenshot(cdp, screenshotPath, viewport.width, viewport.height);

        report.results.push({
          viewport: viewport.label,
          route: route.path,
          screenshot: screenshotPath,
          probe,
        });
      }
    }

    const reportPath = path.join(OUTPUT_DIR, "report.json");
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

    console.log(JSON.stringify({ ok: true, reportPath, outputDir: OUTPUT_DIR }, null, 2));
  } finally {
    await cdp.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
