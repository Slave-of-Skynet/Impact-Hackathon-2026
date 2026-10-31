import pytest
from django.test import Client
from .conftest import make_guardian, make_child

pytestmark = pytest.mark.django_db


def test_brand_logo_rendered_on_landing(client: Client):
    response = client.get("/")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "img/brand/logo.png" in content
    assert 'alt="Gustul Cărților"' in content
    assert "landing-hero-logo" in content


def test_brand_logo_rendered_on_login_and_signup(client: Client):
    resp_login = client.get("/cont/intrare/")
    assert resp_login.status_code == 200
    content_login = resp_login.content.decode("utf-8")
    assert "img/brand/logo.png" in content_login
    assert "auth-logo-img" in content_login

    resp_signup = client.get("/cont/inregistrare/")
    assert resp_signup.status_code == 200
    content_signup = resp_signup.content.decode("utf-8")
    assert "img/brand/logo.png" in content_signup
    assert "auth-logo-img" in content_signup


def test_child_mode_unbroken_with_brand_logo(client: Client):
    parent = make_guardian("test_logo_parent@demo.local")
    child = make_child(parent, nickname="Radu")
    client.force_login(parent)

    resp_switch = client.post(f"/familie/{child.public_id}/mod-copil/")
    assert resp_switch.status_code == 302

    resp_child = client.get("/copil/")
    assert resp_child.status_code == 200
    content_child = resp_child.content.decode("utf-8")
    assert "Radu" in content_child
    assert "fox.svg" in content_child
