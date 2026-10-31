import pytest
from django.contrib.staticfiles import finders

LOGO = "img/logo-gustul-cartilor.png"


def test_logo_file_is_a_real_static_asset():
    # A missing name would 500 under the prod manifest storage (#56).
    assert finders.find(LOGO)


@pytest.mark.parametrize("url", ["/cont/intrare/", "/cont/inregistrare/"])
def test_auth_pages_show_brand_logo(client, db, url):
    body = client.get(url).content.decode()
    assert f'src="/static/{LOGO}"' in body
    assert 'alt="Gustul Cărților"' in body
