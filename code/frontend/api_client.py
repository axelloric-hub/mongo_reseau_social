"""
api_client.py - Client HTTP de l'API Django, seul point d'acces aux donnees pour Streamlit.

Ce module existe pour que l'interface ne contienne aucune logique MongoDB : elle appelle
simplement appel("nom_action", parametre=valeur). Les erreurs metier renvoyees par l'API
(404, 403, 409...) deviennent une exception ApiErreur dont le message est affichable tel quel.
"""
import requests

import config


class ApiErreur(Exception):
    """Erreur renvoyee par l'API (message deja lisible par l'utilisateur)."""


def appel(action, **params):
    """Appelle /api/<action>/ en POST JSON et renvoie le champ 'donnees' de la reponse."""
    try:
        r = requests.post("%s/%s/" % (config.API_URL.rstrip("/"), action), json=params, timeout=20)
    except requests.exceptions.ConnectionError:
        raise ApiErreur("Le serveur Django est injoignable (%s). Lancez run.bat." % config.API_URL)
    except requests.exceptions.Timeout:
        raise ApiErreur("Le serveur met trop de temps a repondre.")
    try:
        corps = r.json()
    except ValueError:
        raise ApiErreur("Reponse invalide du serveur (code %d)." % r.status_code)
    if r.status_code >= 400:
        raise ApiErreur(corps.get("erreur", "Erreur inconnue (code %d)." % r.status_code))
    return corps["donnees"]


def sante():
    """Renvoie (ok, message) : l'API et MongoDB repondent-ils ?"""
    try:
        r = requests.get(config.API_URL.rstrip("/") + "/", timeout=4)
        corps = r.json()
        return r.status_code == 200, "MongoDB : %s" % corps.get("mongodb")
    except Exception:
        return False, "API Django injoignable"
