"""
settings.py - Configuration minimale de Django.

Django sert ici uniquement d'API JSON : pas d'ORM, pas de base SQL, pas de sessions.
MongoDB est la seule base, accedee par pymongo dans crud.py. C'est pourquoi DATABASES est vide
et INSTALLED_APPS ne contient rien.
"""
SECRET_KEY = "cle-de-demonstration-a-changer-en-production"   # projet universitaire, pas de donnees sensibles
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = []
MIDDLEWARE = ["api.middleware.CorsMiddleware"]    # autorise Streamlit (autre port) a appeler l'API
ROOT_URLCONF = "serveur.urls"
DATABASES = {}
USE_TZ = False
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
LANGUAGE_CODE = "fr-fr"
