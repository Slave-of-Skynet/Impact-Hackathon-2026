import json
import struct
from pathlib import Path
import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Account, ChildProfile, Reader


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def child_session(db):
    """Real database-backed child session without mocking."""
    guardian = Account.objects.create_user(email="pwa_guardian@test.local", password="password123")
    guardian.pin_hash = "mock_hash"
    guardian.save()
    child = ChildProfile.objects.create(
        guardian=guardian,
        nickname="Matei",
        avatar="fox",
        age_band="7-8",
    )
    Reader.objects.create(account=None, child=child, kind=Reader.CHILD)
    client = Client()
    client.force_login(guardian)
    session = client.session
    session["mode"] = "child"
    session["active_child"] = str(child.public_id)
    session.save()
    return client, guardian, child


def test_pwa_url_reverses():
    """Verify URL names match CHILD_ALLOWED contract in apps/accounts/middleware.py."""
    assert reverse("manifest") == "/manifest.webmanifest"
    assert reverse("sw") == "/sw.js"
    assert reverse("offline") == "/offline/"
    assert reverse("pwa_launch") == "/app/"


def test_manifest_endpoint(client):
    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert "application/manifest+json" in response["Content-Type"]
    manifest = json.loads(response.content.decode("utf-8"))
    assert manifest["name"] == "Gustul Cărților"
    # Identity stays /copil/ (existing installs); launch goes through the dispatcher.
    assert manifest["id"] == "/copil/"
    assert manifest["start_url"] == "/app/"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    assert len(manifest["icons"]) >= 2


def test_service_worker_endpoint(client):
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert "application/javascript" in response["Content-Type"]
    assert response.get("Service-Worker-Allowed") == "/"
    assert "no-cache" in response.get("Cache-Control", "")
    content = response.content.decode("utf-8")
    assert "gustul-cartilor-static-" in content
    # Ensure cache cleanup is scoped to gustul-cartilor only
    assert "startsWith(CACHE_PREFIX)" in content
    # Ensure offline route and assets are precached
    assert "/offline/" in content
    assert "/static/js/child.js" in content


def test_offline_view_no_private_data(client):
    response = client.get("/offline/")
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    content = response.content.decode("utf-8")
    assert "Nu am internet acum" in content
    # Verify no private data leaked in offline view
    for forbidden in ["email", "csrfmiddlewaretoken", "guardian", "child_id", "password"]:
        assert forbidden not in content.lower()


def test_pwa_accessible_in_child_mode(child_session):
    """Critical regression: in real child mode, middleware must allow manifest, sw, offline."""
    client, guardian, child = child_session

    resp_manifest = client.get("/manifest.webmanifest")
    assert resp_manifest.status_code == 200
    assert "application/manifest+json" in resp_manifest["Content-Type"]

    resp_sw = client.get("/sw.js")
    assert resp_sw.status_code == 200
    assert "application/javascript" in resp_sw["Content-Type"]
    assert resp_sw.get("Service-Worker-Allowed") == "/"

    resp_offline = client.get("/offline/")
    assert resp_offline.status_code == 200
    assert "text/html" in resp_offline["Content-Type"]


def test_pwa_fails_closed_when_child_is_invalid(child_session):
    """When active child is tampered with or deleted, ChildModeMiddleware fails closed to pin gate."""
    client, guardian, child = child_session

    session = client.session
    session["active_child"] = "00000000-0000-0000-0000-000000000000"
    session.save()

    response = client.get("/manifest.webmanifest")
    assert response.status_code == 302
    assert response["Location"] == "/parinte/"


def test_icon_dimensions_verified():
    """Ensure icons in staticfiles have exact expected dimensions 192x192 and 512x512."""
    def get_png_dimensions(path):
        with open(path, "rb") as f:
            data = f.read(24)
            assert data[:8] == b"\x89PNG\r\n\x1a\n", "Not a valid PNG file"
            w, h = struct.unpack(">LL", data[16:24])
            return w, h

    icon_192 = Path(settings.BASE_DIR) / "static" / "img" / "icons" / "icon-192.png"
    icon_512 = Path(settings.BASE_DIR) / "static" / "img" / "icons" / "icon-512.png"

    assert get_png_dimensions(icon_192) == (192, 192)
    assert get_png_dimensions(icon_512) == (512, 512)


def test_precache_assets_all_resolve_and_exist():
    # Verify every static asset in the SW precache list is resolvable by Django finders and non-empty
    static_assets = [
        "css/app.css",
        "fonts/literata-normal-latin.woff2",
        "fonts/atkinson-hyperlegible-next-normal-latin.woff2",
        "img/logo-gustul-cartilor.png",
        "js/child.js",
        "js/htmx.min.js",
        "img/icons/icon-192.png",
        "img/icons/icon-512.png",
        "img/mascot/mascot-happy.svg",
        "img/mascot/mascot-cheer.svg",
        "img/mascot/mascot-think.svg",
        "img/mascot/mascot-oops.svg",
        "img/avatars/fox.svg",
        "img/avatars/owl.svg",
        "img/avatars/cat.svg",
        "img/avatars/bear.svg",
        "img/avatars/rabbit.svg",
        "img/avatars/hedgehog.svg",
        "img/avatars/squirrel.svg",
        "img/avatars/turtle.svg",
    ]
    for rel_path in static_assets:
        found_path = finders.find(rel_path)
        assert found_path is not None, f"Static asset missing from staticfiles finders: {rel_path}"
        p = Path(found_path)
        assert p.is_file(), f"Asset path is not a file: {found_path}"
        assert p.stat().st_size > 0, f"Asset is empty (0 bytes): {found_path}"


def test_manifest_link_on_public_pages(client):
    """Issue #58: PWA metadata must be discoverable from the landing and login pages too."""
    for url in ("/", "/cont/intrare/"):
        response = client.get(url)
        assert response.status_code == 200
        html = response.content.decode()
        assert '<link rel="manifest" href="/manifest.webmanifest">' in html
        assert 'name="theme-color" content="#F7F5EE"' in html
        assert 'id="pwa-install-btn"' in html
        assert 'id="pwa-install-manual"' in html


def test_manifest_link_on_adult_dashboard(adult_client):
    """Issue #58: the shared adult layout exposes the same manifest and install affordance."""
    response = adult_client.get("/panou/")
    assert response.status_code == 200
    html = response.content.decode()
    assert '<link rel="manifest" href="/manifest.webmanifest">' in html
    assert 'id="pwa-install-btn"' in html
    assert 'id="pwa-install-manual"' in html


def test_manifest_link_in_child_mode(child_session):
    """Child mode keeps its manifest link and SW registration (no regression)."""
    client, guardian, child = child_session
    response = client.get("/copil/")
    assert response.status_code == 200
    html = response.content.decode()
    assert '<link rel="manifest" href="/manifest.webmanifest">' in html
    assert "navigator.serviceWorker.register" in html


def test_manifest_installability_fields(client):
    """Chrome installability contract: stable identity, standalone display, PNG 192/512 any+maskable."""
    response = client.get("/manifest.webmanifest")
    manifest = json.loads(response.content.decode("utf-8"))
    # Identity must not drift (existing installs key on it); start_url is the
    # session-aware launch dispatcher, never a route that can 403 a signed-in adult.
    assert manifest["id"] == "/copil/"
    assert manifest["start_url"] == "/app/"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    assert manifest["theme_color"] == "#F7F5EE"
    entries = {(icon["sizes"], icon["type"], icon["purpose"]) for icon in manifest["icons"]}
    assert ("192x192", "image/png", "any") in entries
    assert ("512x512", "image/png", "any") in entries
    assert ("512x512", "image/png", "maskable") in entries


def test_launch_anonymous_gets_public_landing(client):
    """P0 acceptance: the manifest start_url must open a usable public entry, not 403/500/loop."""
    resp = client.get("/app/")
    assert resp.status_code == 302
    assert resp["Location"] == "/"
    landing = client.get(resp["Location"])
    assert landing.status_code == 200


def test_launch_adult_mode_gets_own_dashboard(adult_client):
    """Signed-in adult launching the app lands on /panou/, never the forbidden child home."""
    resp = adult_client.get("/app/")
    assert resp.status_code == 302
    assert resp["Location"] == "/panou/"
    dashboard = adult_client.get(resp["Location"])
    assert dashboard.status_code == 200


def test_launch_child_mode_gets_child_home(child_session):
    """Valid owned child session launches straight into real child content."""
    client, guardian, child = child_session
    resp = client.get("/app/")
    assert resp.status_code == 302
    assert resp["Location"] == "/copil/"
    home = client.get(resp["Location"])
    assert home.status_code == 200
    assert "Matei" in home.content.decode()  # real child content, not the adult dashboard


def test_launch_with_stale_child_fails_closed_to_pin_gate(child_session):
    """Stale/deleted active child: middleware PIN gate, no adult dashboard and no leakage."""
    client, guardian, child = child_session
    session = client.session
    session["active_child"] = "00000000-0000-0000-0000-000000000000"
    session.save()
    resp = client.get("/app/")
    assert resp.status_code == 302
    assert resp["Location"] == "/parinte/"
    gate = client.get(resp["Location"])
    assert gate.status_code == 200
    gate_html = gate.content.decode()
    assert "Zonă pentru părinți" in gate_html  # the PIN gate renders, recovery path intact
    assert "Raftul meu" not in gate_html  # no adult-only navigation or data leaks


def test_launch_response_is_no_store(client):
    """The dispatch depends on the session cookie: the redirect itself must never be cached."""
    resp = client.get("/app/")
    assert "no-store" in resp["Cache-Control"]
    assert "private" in resp["Cache-Control"]


def test_direct_child_home_stays_403_for_adult_mode(adult_client):
    """Fail-closed invariant kept untouched: /copil/ directly still forbids adult-mode sessions."""
    resp = adult_client.get("/copil/")
    assert resp.status_code == 403


def test_sw_never_caches_private_html(client):
    """Privacy invariant: the worker passes through non-GET and never writes to the cache at runtime."""
    content = client.get("/sw.js").content.decode()
    assert 'request.method !== "GET"' in content
    assert "fetch(request).catch" in content  # navigations: network-first, no cache.put
    assert "caches.put" not in content  # no runtime cache writes, so private HTML can never be stored


def test_install_button_hidden_rule_in_css():
    """Regression: .btn sets its own display, so a bare hidden attribute would not hide it.

    Without `.pwa-install .btn[hidden] { display: none; }` the install button renders
    even when pwa.js marks it hidden — a broken, non-functional button (issue #58).
    """
    css_path = Path(settings.BASE_DIR) / "static" / "css" / "app.css"
    css = css_path.read_text(encoding="utf-8")
    assert ".pwa-install .btn[hidden]" in css
    assert "display: none" in css
