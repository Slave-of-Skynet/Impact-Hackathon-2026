/* Child achievement notices: transient presentation, never alters permanent grants (#83). */
(function () {
  "use strict";
  if (window.__GUSTUL_ACHIEVEMENT_NOTICES_INITIALIZED) return;
  window.__GUSTUL_ACHIEVEMENT_NOTICES_INITIALIZED = true;

  function init() {
    const root = document.getElementById("child-grant-notices");
    if (!root) return;
    const readerId = root.getAttribute("data-reader-id");
    if (!readerId || !/^[0-9a-f-]{36}$/i.test(readerId)) return;

    // Browser-only presentation memory; never access credentials or modify grants.
    const key = "gustul:seen-achievements:v1:" + readerId;
    const seen = new Set();
    try {
      const value = JSON.parse(window.localStorage.getItem(key) || "[]");
      if (Array.isArray(value)) {
        value.forEach((code) => {
          if (typeof code === "string" && code.length <= 80) seen.add(code);
        });
      }
    } catch (_) {
      // Storage disabled or invalid: dismissal and auto-hide still work.
    }

    function remember(code) {
      seen.add(code);
      try {
        window.localStorage.setItem(key, JSON.stringify(Array.from(seen).slice(-100)));
      } catch (_) {
        // Storage is optional; do not break the page.
      }
    }

    root.querySelectorAll(".child-grant-banner[data-grant-code]").forEach((banner) => {
      const code = banner.getAttribute("data-grant-code");
      if (!code) return;
      if (seen.has(code)) {
        banner.remove();
        return;
      }

      const close = banner.querySelector(".child-grant-dismiss");
      let timeoutId;
      function dismiss() {
        window.clearTimeout(timeoutId);
        remember(code);
        banner.remove();
      }
      if (close) close.addEventListener("click", dismiss);
      timeoutId = window.setTimeout(dismiss, 7000);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();