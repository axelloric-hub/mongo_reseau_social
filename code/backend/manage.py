#!/usr/bin/env python
"""
manage.py - Point d'entree Django (python manage.py runserver 8000).

Il ajoute le dossier code/ au chemin Python pour que le backend puisse importer
config, crud et agregations, qui contiennent toute la logique MongoDB.
"""
import os
import sys
from pathlib import Path


def main():
    racine_code = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(racine_code))          # config.py, crud.py, agregations.py
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "serveur.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
