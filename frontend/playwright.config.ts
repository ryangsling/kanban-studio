import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "bash -lc 'export PATH=\"$HOME/.local/bin:$PATH\" && cd /home/alif/projects/pm/frontend && npm run build && cd /home/alif/projects/pm/backend && rm -f /tmp/pm-e2e.db && DB_PATH=/tmp/pm-e2e.db uv sync --dev && DB_PATH=/tmp/pm-e2e.db uv run uvicorn app.main:app --host 127.0.0.1 --port 3000'",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 240_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
