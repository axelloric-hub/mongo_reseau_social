"""
app.py - Point d'entree Streamlit : connexion, coque de l'application (barre laterale + contenu) et routage.

Lancement : streamlit run frontend/app.py (fait par run.bat). Ce fichier ne contient aucune logique
metier ni aucun CSS : il identifie l'utilisateur via l'API Django, injecte le design system
(components/styles.py), affiche la barre laterale puis la page choisie.
L'identite de l'utilisateur est gardee dans st.session_state["moi"], la page courante dans
st.session_state["navigation"] (cle de page : fil, profil, amis, ...).
"""
import sys
from pathlib import Path

# Rend importables config.py, data/ et le package frontend, quel que soit le dossier de lancement
RACINE_CODE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE_CODE))

import streamlit as st  # noqa: E402

import config  # noqa: E402
from frontend.api_client import ApiErreur, appel, sante  # noqa: E402
from frontend.components import styles  # noqa: E402
from frontend.components.cards import carte  # noqa: E402
from frontend.components.helpers import afficher_flash, e  # noqa: E402
from frontend.components.icons import icone  # noqa: E402
from frontend.components.sidebar import barre_laterale, entree_active, pages_visibles  # noqa: E402
from frontend.vues import amis, confidentialite, fil, groupes, messages, notifications, profil, supervision  # noqa: E402

st.set_page_config(page_title="Réseau social - démonstration MongoDB", page_icon=None, layout="wide")

VUES = {"fil": fil.afficher, "profil": profil.afficher, "amis": amis.afficher, "groupes": groupes.afficher,
        "messages": messages.afficher, "notifications": notifications.afficher,
        "confidentialite": confidentialite.afficher, "supervision": supervision.afficher}


def ecran_connexion():
    """
    Connexion de demonstration : pseudo et mot de passe de l'enseignant sont preremplis.
    L'API accepte tout mot de passe tant que le pseudo existe (crud.verifier_mot_de_passe est le
    point d'extension pour une vraie authentification).
    """
    styles.injecter()
    _, centre, _ = st.columns([1, 1.1, 1])
    with centre:
        st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
        st.markdown('<div style="display:flex;align-items:center;gap:12px"><span class="avatar" style="width:44px;height:44px;border-radius:12px;'
                    'background:#3B82F6;color:#fff">%s</span><div><div class="card-title" style="font-size:18px">Réseau social</div>'
                    '<div class="small">Démonstration MongoDB</div></div></div>' % icone("message-circle", 22), unsafe_allow_html=True)
        st.markdown('<h1 class="page-title" style="font-size:28px;margin-top:8px">Connexion</h1>'
                    '<div class="page-subtitle">Publications, groupes, messagerie, notifications et statistiques.</div>', unsafe_allow_html=True)
        ok, etat = sante()
        if not ok:
            st.error("%s. Lancez l'application avec run.bat (MongoDB et Django doivent être démarrés)." % etat)
        with carte("connexion"):
            with st.form("connexion", border=False):
                pseudo = st.text_input("Pseudo", value=config.PSEUDO_DEMO)
                mdp = st.text_input("Mot de passe", value=config.MOT_DE_PASSE_DEMO, type="password")
                if st.form_submit_button("Se connecter", type="primary", width="stretch"):
                    try:
                        st.session_state["moi"] = appel("login", pseudo=pseudo, mot_de_passe=mdp)
                        st.session_state["navigation"] = "fil"
                        st.rerun()
                    except ApiErreur as err:
                        st.error(str(err))
        st.markdown('<div class="small" style="text-align:center">Compte de démonstration : <b>%s</b> / <b>%s</b></div>'
                    % (e(config.PSEUDO_DEMO), e(config.MOT_DE_PASSE_DEMO)), unsafe_allow_html=True)


def main():
    moi = st.session_state.get("moi")
    if not moi:
        ecran_connexion()
        return
    afficher_flash()
    pages = dict(pages_visibles(moi))
    if st.session_state.get("navigation") not in pages:
        st.session_state["navigation"] = "fil"
    try:
        non_lues = appel("compter_notifications", user_id=moi["_id"])["total"]
    except ApiErreur:
        non_lues = 0
    styles.injecter(entree_active(), non_lues)      # design system + etat actif + badge de notifications
    barre_laterale(moi)
    page = st.session_state["navigation"]
    # Fermer le groupe ouvert quand on quitte la page Groupes
    if st.session_state.get("page_precedente") != page:
        st.session_state.pop("grp_ouvert", None)
        st.session_state["page_precedente"] = page
    VUES[page](moi)


main()
