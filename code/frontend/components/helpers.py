"""
helpers.py - Utilitaires partages : echappement HTML, dates, appels API surs, messages flash, pagination.

Ce module existe pour que les pages restent courtes : elles appellent essayer("action", ...)
(l'erreur est affichee proprement, la page ne plante jamais) et pagination(...) sans reecrire
la logique a chaque fois.
"""
import html
from datetime import datetime

import streamlit as st

from frontend.api_client import ApiErreur, appel
from frontend.components.icons import icone

MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def e(texte):
    """Echappe le HTML des textes saisis par les utilisateurs (evite l'injection via unsafe_allow_html)."""
    return html.escape(str(texte if texte is not None else ""))


def fdate(iso):
    """'2026-10-04T20:00:00' -> '4 oct. 2026, 20:00'."""
    if not iso:
        return ""
    d = datetime.fromisoformat(iso)
    return "%d %s %d, %s" % (d.day, MOIS[d.month - 1], d.year, d.strftime("%H:%M"))


def fjour(iso):
    if not iso:
        return ""
    d = datetime.fromisoformat(iso)
    return "%d %s %d" % (d.day, MOIS[d.month - 1], d.year)


def fcourt(iso):
    """Date compacte pour les listes : '4 oct.'."""
    if not iso:
        return ""
    d = datetime.fromisoformat(iso)
    return "%d %s" % (d.day, MOIS[d.month - 1])


def fheure(iso):
    return datetime.fromisoformat(iso).strftime("%H:%M") if iso else ""


def flash(texte, ton="succes"):
    """Memorise un message affiche en toast apres le prochain rerun."""
    st.session_state["flash"] = (texte, ton)


def afficher_flash():
    if st.session_state.get("flash"):
        texte, ton = st.session_state.pop("flash")
        st.toast(texte, icon=None)


def essayer(action, succes=None, **params):
    """
    Appelle l'API et gere l'erreur : le message est affiche dans un encadre, la page continue.
    Renvoie (ok, resultat). 'succes' est affiche en toast apres le rerun suivant.
    """
    try:
        resultat = appel(action, **params)
    except ApiErreur as err:
        st.error(str(err))
        return False, None
    if succes:
        flash(succes)
    return True, resultat


def aller(page, **etat):
    """Callback de navigation : change de page et pose d'eventuels etats (ex. section du profil)."""
    st.session_state["navigation"] = page
    for k, v in etat.items():
        st.session_state[k] = v


def pills(cle, options, defaut, format_func=str, onglets=False):
    """
    st.pills a selection unique qui ne peut pas etre 'vide' : cliquer l'option active la garde active.
    onglets=True utilise le style 'onglets soulignes' (la cle commence alors par tabs_).
    """
    cle_etat = ("tabs_" if onglets else "pills_") + cle

    def _garder():
        if st.session_state.get(cle_etat) is None:
            st.session_state[cle_etat] = st.session_state.get("_dernier_" + cle_etat, defaut)

    valeur = st.pills(cle, options, default=defaut, key=cle_etat, format_func=format_func, on_change=_garder,
                      label_visibility="collapsed") or defaut
    st.session_state["_dernier_" + cle_etat] = valeur
    return valeur


def pagination(cle, total, par_page):
    """Precedent / Suivant avec 'Page x sur y' ; la page courante est dans st.session_state[cle]."""
    pages = max(1, -(-total // par_page))
    page = min(st.session_state.get(cle, 1), pages)
    if pages == 1:
        return page
    c1, c2, c3 = st.columns([1, 2, 1], vertical_alignment="center")
    if c1.button("Précédent", key="ico-chevron-left__%s_prec" % cle, disabled=page <= 1, width="stretch"):
        st.session_state[cle] = page - 1
        st.rerun()
    c2.markdown('<div class="small" style="text-align:center">Page %d sur %d - %d résultat(s)</div>' % (page, pages, total), unsafe_allow_html=True)
    if c3.button("Suivant", key="ico-chevron-right__%s_suiv" % cle, disabled=page >= pages, width="stretch"):
        st.session_state[cle] = page + 1
        st.rerun()
    return page
