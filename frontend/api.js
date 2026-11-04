/**
 * StreakNudge Client API SDK & Configuration Manager
 * Connects frontend screens to API Gateway / Local Server.
 */

const StreakApi = (() => {
  const DEFAULT_CONFIG = {
    apiUrl: window.location.origin.includes("http") && !window.location.origin.includes("file") 
      ? (window.location.port === "3000" ? window.location.origin : "http://localhost:3000")
      : "http://localhost:3000",
    apiKey: "streaknudge-secret-key-12345",
    user: "student_demo",
    email: "student@example.com"
  };

  function getConfig() {
    return {
      apiUrl: localStorage.getItem("streaknudge_api_url") || DEFAULT_CONFIG.apiUrl,
      apiKey: localStorage.getItem("streaknudge_api_key") || DEFAULT_CONFIG.apiKey,
      user: localStorage.getItem("streaknudge_user") || DEFAULT_CONFIG.user,
      email: localStorage.getItem("streaknudge_email") || DEFAULT_CONFIG.email,
    };
  }

  function setConfig(newConfig) {
    if (newConfig.apiUrl !== undefined) localStorage.setItem("streaknudge_api_url", newConfig.apiUrl.replace(/\/+$/, ""));
    if (newConfig.apiKey !== undefined) localStorage.setItem("streaknudge_api_key", newConfig.apiKey.trim());
    if (newConfig.user !== undefined) localStorage.setItem("streaknudge_user", newConfig.user.trim());
    if (newConfig.email !== undefined) localStorage.setItem("streaknudge_email", newConfig.email.trim());
  }

  async function getStreak(customUser = null) {
    const config = getConfig();
    const user = customUser || config.user;
    const url = `${config.apiUrl}/streak/${encodeURIComponent(user)}`;

    try {
      const res = await fetch(url, {
        method: "GET",
        headers: {
          "x-api-key": config.apiKey,
        },
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}: Failed to retrieve streak`);
      }

      return data;
    } catch (err) {
      console.warn("StreakApi.getStreak error:", err.message);
      throw err;
    }
  }

  async function logSolve({ problem, difficulty, customUser = null, customEmail = null }) {
    const config = getConfig();
    const user = customUser || config.user;
    const email = customEmail || config.email;
    const url = `${config.apiUrl}/solves`;

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": config.apiKey,
        },
        body: JSON.stringify({
          user,
          problem,
          difficulty,
          email,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}: Failed to log solve`);
      }

      // Record in local history for UI persistence
      saveSolveToHistory({
        user,
        problem,
        difficulty,
        streak_count: data.streak_count,
        date: data.date || new Date().toISOString().slice(0, 10),
        timestamp: new Date().toISOString(),
      });

      return data;
    } catch (err) {
      console.error("StreakApi.logSolve error:", err.message);
      throw err;
    }
  }

  function getHistory() {
    try {
      const raw = localStorage.getItem("streaknudge_history");
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveSolveToHistory(item) {
    const history = getHistory();
    // Prepend new solve
    history.unshift(item);
    // Keep last 50 solves
    localStorage.setItem("streaknudge_history", JSON.stringify(history.slice(0, 50)));
  }

  // Calculate remaining time until 9:00 PM IST or midnight IST
  function getISTCountdown() {
    // Current time in IST (UTC + 5.5 hours)
    const now = new Date();
    const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
    const istMs = utcMs + (5.5 * 3600000);
    const istNow = new Date(istMs);

    // Today's 21:00 (9:00 PM) IST
    const ist9pm = new Date(istNow);
    ist9pm.setHours(21, 0, 0, 0);

    // Today's midnight (23:59:59) IST
    const istMidnight = new Date(istNow);
    istMidnight.setHours(23, 59, 59, 999);

    let diffMs = 0;
    let label = "";

    if (istNow < ist9pm) {
      diffMs = ist9pm - istNow;
      label = "9:00 PM IST Nudge";
    } else {
      diffMs = istMidnight - istNow;
      label = "Midnight Streak Deadline";
    }

    if (diffMs <= 0) {
      return { hours: "00", minutes: "00", seconds: "00", label: "Deadline passed" };
    }

    const hours = String(Math.floor(diffMs / 3600000)).padStart(2, "0");
    const minutes = String(Math.floor((diffMs % 3600000) / 60000)).padStart(2, "0");
    const seconds = String(Math.floor((diffMs % 60000) / 1000)).padStart(2, "0");

    return { hours, minutes, seconds, label };
  }

  // Mount floating Backend Settings button and modal
  function mountSettingsModal() {
    if (document.getElementById("streaknudge-settings-modal")) return;

    const modalHtml = `
      <!-- Floating Settings Trigger -->
      <button id="streaknudge-settings-btn" title="API Settings"
        class="fixed bottom-4 right-4 z-50 flex items-center gap-2 bg-surface-container-lowest text-on-surface px-4 py-2.5 rounded-full shadow-[0_4px_12px_rgba(0,0,0,0.15)] border border-outline-variant hover:bg-surface-container-high transition-all text-xs font-bold cursor-pointer">
        <span id="streaknudge-status-dot" class="w-2.5 h-2.5 rounded-full bg-secondary-container"></span>
        <span class="material-symbols-outlined text-[18px]">cloud</span>
        <span>Backend Config</span>
      </button>

      <!-- Settings Modal -->
      <div id="streaknudge-settings-modal" class="fixed inset-0 z-50 hidden flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
        <div class="bg-surface-container-lowest rounded-3xl p-6 max-w-md w-full shadow-2xl border border-outline-variant flex flex-col gap-4">
          <div class="flex items-center justify-between pb-2 border-b border-surface-container">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[24px]">cloud_sync</span>
              <h3 class="font-headline-sm text-lg font-bold text-on-surface">Backend API Settings</h3>
            </div>
            <button id="streaknudge-close-modal" class="text-on-surface-variant hover:text-on-surface p-1">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="flex flex-col gap-3 text-sm">
            <div>
              <label class="font-bold text-xs uppercase text-on-surface-variant">API Base URL</label>
              <input id="cfg-api-url" type="text"
                class="w-full mt-1 px-3 py-2 rounded-xl bg-surface-container text-on-surface border border-outline-variant focus:outline-none focus:border-primary text-xs"
                placeholder="http://localhost:3000 or https://xyz.execute-api..."/>
              <span class="text-[11px] text-on-surface-variant">Use http://localhost:3000 for local test or deployed AWS API Gateway URL.</span>
            </div>

            <div>
              <label class="font-bold text-xs uppercase text-on-surface-variant">API Key (x-api-key)</label>
              <input id="cfg-api-key" type="password"
                class="w-full mt-1 px-3 py-2 rounded-xl bg-surface-container text-on-surface border border-outline-variant focus:outline-none focus:border-primary text-xs"
                placeholder="streaknudge-secret-key-12345"/>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="font-bold text-xs uppercase text-on-surface-variant">Username</label>
                <input id="cfg-user" type="text"
                  class="w-full mt-1 px-3 py-2 rounded-xl bg-surface-container text-on-surface border border-outline-variant focus:outline-none focus:border-primary text-xs"
                  placeholder="student_demo"/>
              </div>
              <div>
                <label class="font-bold text-xs uppercase text-on-surface-variant">Notification Email</label>
                <input id="cfg-email" type="email"
                  class="w-full mt-1 px-3 py-2 rounded-xl bg-surface-container text-on-surface border border-outline-variant focus:outline-none focus:border-primary text-xs"
                  placeholder="student@example.com"/>
              </div>
            </div>

            <div id="cfg-test-result" class="hidden p-2.5 rounded-xl text-xs font-semibold"></div>
          </div>

          <div class="flex items-center justify-between pt-2 border-t border-surface-container">
            <button id="cfg-test-btn" type="button" class="px-4 py-2 rounded-xl bg-surface-container font-bold text-xs hover:bg-surface-container-high transition-all">
              Test Connection
            </button>
            <button id="cfg-save-btn" type="button" class="px-4 py-2 rounded-xl bg-primary-container text-on-primary font-bold text-xs shadow-[0_3px_0_#46a302] hover:bg-primary-container active:translate-y-0.5 transition-all">
              Save Settings
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHtml);

    const btn = document.getElementById("streaknudge-settings-btn");
    const modal = document.getElementById("streaknudge-settings-modal");
    const closeBtn = document.getElementById("streaknudge-close-modal");
    const saveBtn = document.getElementById("cfg-save-btn");
    const testBtn = document.getElementById("cfg-test-btn");
    const testResult = document.getElementById("cfg-test-result");

    function populateInputs() {
      const cfg = getConfig();
      document.getElementById("cfg-api-url").value = cfg.apiUrl;
      document.getElementById("cfg-api-key").value = cfg.apiKey;
      document.getElementById("cfg-user").value = cfg.user;
      document.getElementById("cfg-email").value = cfg.email;
    }

    btn.addEventListener("click", () => {
      populateInputs();
      testResult.classList.add("hidden");
      modal.classList.remove("hidden");
    });

    closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });

    saveBtn.addEventListener("click", () => {
      setConfig({
        apiUrl: document.getElementById("cfg-api-url").value,
        apiKey: document.getElementById("cfg-api-key").value,
        user: document.getElementById("cfg-user").value,
        email: document.getElementById("cfg-email").value,
      });
      modal.classList.add("hidden");
      // Trigger custom event so page re-fetches
      window.dispatchEvent(new CustomEvent("streaknudge:config-updated"));
    });

    testBtn.addEventListener("click", async () => {
      testResult.className = "p-2.5 rounded-xl text-xs font-semibold bg-surface-container text-on-surface";
      testResult.textContent = "Connecting to backend...";
      testResult.classList.remove("hidden");

      // Temporarily use values in inputs
      const tempUrl = document.getElementById("cfg-api-url").value.replace(/\/+$/, "");
      const tempKey = document.getElementById("cfg-api-key").value;
      const tempUser = document.getElementById("cfg-user").value;

      try {
        const start = performance.now();
        const res = await fetch(`${tempUrl}/streak/${encodeURIComponent(tempUser)}`, {
          headers: { "x-api-key": tempKey }
        });
        const elapsed = Math.round(performance.now() - start);

        if (res.ok || res.status === 404) {
          testResult.className = "p-2.5 rounded-xl text-xs font-semibold bg-primary-fixed text-on-primary-fixed";
          testResult.textContent = `🟢 Backend reachable! Status ${res.status} (${elapsed}ms).`;
          document.getElementById("streaknudge-status-dot").className = "w-2.5 h-2.5 rounded-full bg-primary-container";
        } else if (res.status === 401) {
          testResult.className = "p-2.5 rounded-xl text-xs font-semibold bg-error-container text-on-error-container";
          testResult.textContent = `🔴 401 Unauthorized: API Key does not match backend.`;
        } else {
          testResult.className = "p-2.5 rounded-xl text-xs font-semibold bg-error-container text-on-error-container";
          testResult.textContent = `⚠️ Backend returned status ${res.status}.`;
        }
      } catch (err) {
        testResult.className = "p-2.5 rounded-xl text-xs font-semibold bg-error-container text-on-error-container";
        testResult.textContent = `❌ Connection failed: ${err.message}. Ensure dev server or AWS API is running.`;
        document.getElementById("streaknudge-status-dot").className = "w-2.5 h-2.5 rounded-full bg-error";
      }
    });

    // Check status once in background
    setTimeout(async () => {
      try {
        const cfg = getConfig();
        const res = await fetch(`${cfg.apiUrl}/streak/${encodeURIComponent(cfg.user)}`, {
          headers: { "x-api-key": cfg.apiKey }
        });
        if (res.ok || res.status === 404) {
          document.getElementById("streaknudge-status-dot").className = "w-2.5 h-2.5 rounded-full bg-primary-container";
        } else {
          document.getElementById("streaknudge-status-dot").className = "w-2.5 h-2.5 rounded-full bg-error";
        }
      } catch {
        document.getElementById("streaknudge-status-dot").className = "w-2.5 h-2.5 rounded-full bg-error";
      }
    }, 500);
  }

  return {
    getConfig,
    setConfig,
    getStreak,
    logSolve,
    getHistory,
    getISTCountdown,
    mountSettingsModal,
  };
})();

// Auto-mount settings modal on all pages
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    StreakApi.mountSettingsModal();
  });
}
