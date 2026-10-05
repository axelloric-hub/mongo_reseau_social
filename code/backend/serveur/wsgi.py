"""wsgi.py - Point d'entree WSGI (deploiement eventuel)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "serveur.settings")
application = get_wsgi_application()
