"""
config.py - Seul fichier a modifier pour changer de base ou de parametres.

Ce module existe pour centraliser la connexion MongoDB et les constantes du projet
(exigence du devoir : aucune valeur de connexion en dur dans plusieurs fichiers).
Les valeurs sont lues dans le fichier .env (voir .env.example) puis dans l'environnement.
"""
import os
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

RACINE = Path(__file__).resolve().parent          # dossier code/
DOSSIER_EXPORTS = RACINE.parent / "exports"       # exports/json et exports/csv


def _charger_env():
    """Lit RACINE/.env ligne par ligne (CLE=valeur) sans ecraser l'environnement existant."""
    fichier = RACINE / ".env"
    if not fichier.exists():
        return
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip())


_charger_env()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
NOM_BASE = os.getenv("MONGODB_DATABASE", "reseau_social")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

# Compte de demonstration de l'enseignant (prerempli dans l'ecran de connexion)
PSEUDO_DEMO = "valdez_237"
MOT_DE_PASSE_DEMO = "1234"

SEED = 42  # graine fixe : memes donnees a chaque generation (conseil du PDF)

# Les 10 categories de preferences, deduites des images du fichier description_images.txt
CATEGORIES_PREFERENCES = [
    "productivite", "nature", "voyage", "aventure", "education",
    "mode", "philosophie", "foi", "histoire", "technologie",
]

_client = None


def get_db():
    """Ouvre (une seule fois) la connexion et renvoie la base, ou arrete proprement le programme."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        try:
            _client.admin.command("ping")
        except ServerSelectionTimeoutError:
            _client = None
            raise SystemExit("Impossible de joindre MongoDB : verifiez qu'il est demarre "
                             "et que MONGODB_URI est correct.")
    return _client[NOM_BASE]
