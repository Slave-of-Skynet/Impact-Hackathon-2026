import os

from django.core.wsgi import get_wsgi_application

# Hosts set DJANGO_SETTINGS_MODULE=config.settings.prod explicitly.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
