import { defineConfig } from "@playwright/test";

const port = 8877;
const dataDir = `/tmp/xiangqi-sifu-e2e-${process.pid}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    channel: "chrome",
    viewport: { width: 1280, height: 900 },
  },
  webServer: {
    command: `../../.venv/bin/python ../../scripts/run_app.py --no-open --port ${port} --data-dir ${dataDir}`,
    cwd: ".",
    url: `http://127.0.0.1:${port}/api/health`,
    reuseExistingServer: false,
    timeout: 20_000,
  },
});
