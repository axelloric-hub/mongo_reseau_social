"""Utilitaire de test : remplace la connexion MongoDB par mongomock (aucun serveur requis)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mongomock
import config

_client = mongomock.MongoClient()
_base = _client["test_reseau"]


def installer():
    config.get_db = lambda: _base
    return _base
