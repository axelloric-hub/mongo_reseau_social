"""
tests_interface.py - Teste l'interface Streamlit de bout en bout (sans navigateur ni serveur MongoDB).

Principe : on remplace l'appel HTTP de api_client par le client de test de Django, qui execute
la vraie API sur une base mongomock generee a la volee. Streamlit AppTest simule alors les clics :
on verifie qu'aucune page ne plante et que les interactions modifient bien les donnees.
Usage : python scripts/tests_interface.py
"""
import contextlib
import io
import json
import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "backend"))
os.environ["DJANGO_SETTINGS_MODULE"] = "serveur.settings"

from scripts import tests_mock  # noqa: E402

base = tests_mock.installer()
import generer_donnees  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    generer_donnees.generer(base=base, exporter_fichiers=False)

import django  # noqa: E402

django.setup()
from django.test import Client  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

import frontend.api_client as api_client  # noqa: E402

client = Client()


def appel_local(action, **params):
    """Meme contrat que api_client.appel, mais sans reseau : la requete va directement a la vue Django."""
    r = client.post("/api/%s/" % action, json.dumps(params), content_type="application/json")
    corps = r.json()
    if r.status_code >= 400:
        raise api_client.ApiErreur(corps.get("erreur", "erreur"))
    return corps["donnees"]


api_client.appel = appel_local
api_client.sante = lambda: (True, "MongoDB : ok")

RESULTATS = []


def test(libelle, condition):
    RESULTATS.append(bool(condition))
    print("[%s] %s" % ("OK    " if condition else "ECHEC ", libelle))


def bouton(at, prefixe_cle):
    """Premier bouton dont la cle commence par le prefixe donne."""
    return next((b for b in at.button if (b.key or "").startswith(prefixe_cle)), None)


def erreurs(at):
    return [str(x.value)[:200] for x in at.exception]


def main():
    at = AppTest.from_file(str(RACINE / "frontend" / "app.py"), default_timeout=90)
    at.run()
    test("ecran de connexion : champs preremplis valdez_237 / 1234", at.text_input[0].value == "valdez_237" and at.text_input[1].value == "1234" and not erreurs(at))
    at.button[0].click().run()
    moi = at.session_state["moi"]
    test("connexion reussie sans erreur", moi["pseudo"] == "valdez_237" and not erreurs(at))
    test("navigation personnalisee : aucun st.radio", len(at.radio) == 0)

    for page in ["fil", "profil", "amis", "groupes", "messages", "notifications", "confidentialite", "supervision"]:
        at.session_state["navigation"] = page
        at.run()
        test("page %s s'affiche sans exception" % page, not erreurs(at))

    # --- Notifications
    at.session_state["navigation"] = "notifications"
    at.run()
    avant = appel_local("compter_notifications", user_id=moi["_id"])["total"]
    test("notifications non lues presentes (%d)" % avant, avant > 100)
    bouton(at, "ico-check-check__toutlu").click().run()
    apres = appel_local("compter_notifications", user_id=moi["_id"])
    test("'Tout marquer comme lu' met tout a zero dans MongoDB", apres["total"] == 0 and not erreurs(at))
    test("messages sources marques lus aussi", appel_local("messages_non_lus", user_id=moi["_id"])["total"] == 0)

    # --- Fil, j'aime, commentaires
    at.session_state["navigation"] = "fil"
    at.run()
    b = bouton(at, "ico-thumbs-up__like_")
    avant_likes = int(b.label)
    b.click().run()
    test("j'aime : compteur modifie", not erreurs(at) and int(bouton(at, "ico-thumbs-up__like_").label) != avant_likes)
    bouton(at, "ico-message-circle__com_").click().run()
    test("commentaires affiches a la demande", not erreurs(at) and len(at.text_input) > 1)

    # --- Composer : publier
    nb_avant = appel_local("stats", user_id=moi["_id"])["publications"]
    at.text_area(key="nouv_texte").set_value("Publication de test depuis l'interface").run()
    bouton(at, "ico-send__publier").click().run()
    test("publication creee depuis le composer", appel_local("stats", user_id=moi["_id"])["publications"] == nb_avant + 1 and not erreurs(at))
    test("composer vide apres publication", at.text_area(key="nouv_texte").value == "")

    # --- Messages
    at.session_state["navigation"] = "messages"
    at.run()
    lignes = [x for x in at.button if (x.key or "").startswith("convbtn_p_")]
    test("liste des conversations affichee", len(lignes) > 0)
    nb_msg = appel_local("stats", user_id=moi["_id"])["messages"]
    lignes[0].click().run()
    at.chat_input[0].set_value("Bonjour depuis le test").run()
    test("message prive envoye", appel_local("stats", user_id=moi["_id"])["messages"] == nb_msg + 1 and not erreurs(at))

    # --- Confidentialite : enregistrement automatique
    at.session_state["navigation"] = "confidentialite"
    at.run()
    at.toggle(key="conf_messages_inconnus").set_value(False).run()
    test("toggle confidentialite enregistre dans MongoDB", appel_local("profil", user_id=moi["_id"])["confidentialite"]["messages_inconnus"] is False and not erreurs(at))
    at.toggle(key="conf_messages_inconnus").set_value(True).run()
    test("toggle reactive", appel_local("profil", user_id=moi["_id"])["confidentialite"]["messages_inconnus"] is True)

    # --- Groupes
    at.session_state["navigation"] = "groupes"
    at.run()
    bouton(at, "ouvrir_").click().run()
    test("detail d'un groupe affiche", not erreurs(at) and at.session_state["grp_ouvert"])

    # --- Supervision : droits
    at.session_state["navigation"] = "supervision"
    at.run()
    test("supervision : graphiques calcules par l'API", not erreurs(at) and len(at.markdown) > 8)
    test("acces refuse aux non-superviseurs", _refus_non_superviseur())

    echecs = RESULTATS.count(False)
    print("\n%d tests, %d echec(s)" % (len(RESULTATS), echecs))
    return echecs


def _refus_non_superviseur():
    autre = base.utilisateurs.find_one({"role": "membre"})
    try:
        appel_local("stats", user_id=str(autre["_id"]))
    except api_client.ApiErreur:
        return True
    return False


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
