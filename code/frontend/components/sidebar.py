"""
sidebar.py - Barre laterale : carte utilisateur, navigation personnalisee, parametres et deconnexion.

La navigation n'utilise pas st.radio : chaque entree est un st.button 'tertiary' dont la cle
(nav_<page>) permet au CSS d'ajouter l'icone Lucide, l'etat actif et le badge de notifications.
"""
import streamlit as st

from frontend.components.avatar import avatar_utilisateur
from frontend.components.helpers import aller, e

# (cle de page, libelle) dans l'ordre d'affichage ; 'supervision' est reservee au role superviseur
NAVIGATION = [("fil", "Fil d'actualité"), ("profil", "Mon profil"), ("amis", "Amis"), ("groupes", "Groupes"),
              ("messages", "Messages"), ("notifications", "Notifications"), ("confidentialite", "Confidentialité"),
              ("supervision", "Supervision")]


def pages_visibles(moi):
    return [(k, l) for k, l in NAVIGATION if k != "supervision" or moi["role"] == "superviseur"]


def entree_active():
    """Cle de l'entree surlignee : 'Paramètres' est un raccourci vers la section Paramètres du profil."""
    page = st.session_state.get("navigation", "fil")
    if page == "profil" and st.session_state.get("tabs_profil_section") == "Paramètres":
        return "parametres"
    return page


def barre_laterale(moi):
    with st.sidebar:
        role = "Superviseur" if moi["role"] == "superviseur" else "Membre"
        st.markdown('<div class="user-card">%s<div class="txt"><div class="name">%s %s</div><div class="meta">@%s</div><div class="meta">%s</div></div></div>'
                    % (avatar_utilisateur(moi, 40), e(moi["prenom"]), e(moi["nom"]), e(moi["pseudo"]), role), unsafe_allow_html=True)
        for cle, libelle in pages_visibles(moi):
            st.button(libelle, key="nav_" + cle, type="tertiary", width="stretch", on_click=aller, args=(cle,),
                      kwargs={"tabs_profil_section": "Publications"} if cle == "profil" else {})
        st.markdown('<div class="nav-sep"></div>', unsafe_allow_html=True)
        st.button("Paramètres", key="nav_parametres", type="tertiary", width="stretch", on_click=aller, args=("profil",),
                  kwargs={"tabs_profil_section": "Paramètres"})
        if st.button("Se déconnecter", key="nav_deconnexion", type="tertiary", width="stretch"):
            st.session_state.clear()
            st.rerun()
