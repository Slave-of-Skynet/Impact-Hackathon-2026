"""PWA views for Gustul Cărților.

Owner: Denis (Antigravity).
Contracts: specs/001-reading-diary-mvp/contracts/routes.md § Route 18.
Provides:
- /manifest.webmanifest: Web App Manifest with correct MIME type
- /sw.js: Service Worker served at root scope with Service-Worker-Allowed: /
- /offline/: Static unauthenticated offline fallback page
- /app/: Installed-PWA launch dispatcher (P0 fix, review of issue #58)
"""

from pathlib import Path
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.accounts.authz import is_child_mode

from .mascot import get_mascot_line


_STATIC_DIR = Path(settings.BASE_DIR) / "static"


@require_GET
def manifest_view(request):
    """Serve the Web App Manifest with application/manifest+json MIME type."""
    manifest_path = _STATIC_DIR / "manifest.webmanifest"
    if manifest_path.exists():
        content = manifest_path.read_text(encoding="utf-8")
    else:
        content = "{}"

    response = HttpResponse(content, content_type="application/manifest+json; charset=utf-8")
    response["Cache-Control"] = "public, max-age=86400"
    return response


@require_GET
def service_worker_view(request):
    """Serve the root-scoped service worker with Service-Worker-Allowed: /."""
    sw_path = _STATIC_DIR / "sw.js"
    if sw_path.exists():
        content = sw_path.read_text(encoding="utf-8")
    else:
        content = "// sw missing"

    response = HttpResponse(content, content_type="application/javascript; charset=utf-8")
    # Crucial for PWA installation: allow the service worker to control all routes from /
    response["Service-Worker-Allowed"] = "/"
    # Always revalidate service worker script
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@require_GET
def offline_view(request):
    """Public unauthenticated offline fallback shell. Never exposes private child/family data."""
    context = {
        "mascot": get_mascot_line("offline"),
    }
    response = render(request, "child/offline.html", context)
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_GET
def pwa_launch(request):
    """Installed-PWA launch dispatcher (P0 fix for issue #58).

    The manifest start_url points here so a tapped app icon never lands on a
    route that would 403 or redirect-loop. Dispatch uses only existing session
    state; every authorization decision stays with ChildModeMiddleware:

    - anonymous -> public landing (login/registration CTAs);
    - authenticated adult in adult mode -> own dashboard /panou/;
    - child mode -> /copil/, which the middleware serves only for a valid owned
      active child and fails closed to the PIN gate for stale/deleted/foreign
      ones. No adult data can leak through this route.
    """
    if not request.user.is_authenticated:
        target = reverse("home")
    elif is_child_mode(request):
        target = reverse("child_home")
    else:
        target = reverse("adult_dashboard")
    response = redirect(target)
    # The redirect target depends on the session cookie: never cache it.
    response["Cache-Control"] = "private, no-store, must-revalidate"
    return response
