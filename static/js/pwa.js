/* PWA install support for the shared (adult/landing) layout — issue #58.
 * Privacy rules (same contract as static/sw.js):
 * - Only registers the existing root-scoped service worker; no caching logic here.
 * - The one-click button appears ONLY when the browser fires beforeinstallprompt;
 *   otherwise the footer shows the real menu path (⋮ → Install app), never a fake install.
 */
(function () {
  "use strict";

  // Same registration the child layout performs; the two layouts never share a page.
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" })
        .catch(function (err) { console.debug("SW registration note:", err); });
    });
  }

  var installEvent = null;
  var installBtn = document.getElementById("pwa-install-btn");
  var manualHint = document.getElementById("pwa-install-manual");
  if (!installBtn || !manualHint) return;

  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
  }

  function refresh() {
    if (isStandalone()) {
      // Already installed: hide the affordance entirely.
      installBtn.hidden = true;
      manualHint.hidden = true;
    } else if (installEvent) {
      installBtn.hidden = false;
      manualHint.hidden = true;
    } else {
      installBtn.hidden = true;
      manualHint.hidden = false;
    }
  }

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    installEvent = event;
    refresh();
  });

  window.addEventListener("appinstalled", function () {
    installEvent = null;
    refresh();
  });

  installBtn.addEventListener("click", function () {
    if (!installEvent) return;
    installEvent.prompt();
    installEvent.userChoice.then(function () {
      // Either accepted or dismissed, the native flow is finished for this visit.
      installEvent = null;
      refresh();
    });
  });

  refresh();
})();
