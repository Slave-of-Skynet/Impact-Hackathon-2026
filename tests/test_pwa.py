import json
import pytest
from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client


@pytest.fixture
def client():
    return Client()


def test_manifest_endpoint(client):
    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert "application/manifest+json" in response["Content-Type"]
    manifest = json.loads(response.content.decode("utf-8"))
    assert manifest["name"] == "Gustul Cărților"
    assert manifest["start_url"] == "/copil/"
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


def test_precache_assets_all_resolve_and_exist():
    # Verify every static asset in the SW precache list is resolvable by Django finders and non-empty
    static_assets = [
        "css/child.css",
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
