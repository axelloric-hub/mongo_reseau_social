"""
notifications.py - Page 'Notifications' : de la plus recente a la plus ancienne, par categorie.

L'etat lu / non lu est stocke dans MongoDB (champ statut). 'Pas encore vue' signale une
notification non lue. Marquer comme lu met aussi a jour le message source.
"""
import streamlit as st

from frontend.components.avatar import avatar_utilisateur
from frontend.components.badges import badge_lu
from frontend.components.buttons import bouton_icone
from frontend.components.cards import carte, en_tete
from frontend.components.empty_state import etat_vide
from frontend.components.helpers import e, essayer, fdate, pagination, pills
from frontend.components.icons import icone

PAR_PAGE = 12
CATEGORIES = {"tous": "Tout", "groupes": "Groupes", "prives": "Conversations privées", "autres": "Autres"}


def _texte(n):
    de = "@" + e(n["de"]["pseudo"]) if n.get("de") else "Quelqu'un"
    apercu = "« %s »" % e(n["apercu"][:140]) if n.get("apercu") else ""
    kind = n["source"]["kind"]
    if kind == "message_prive":
        return "<b>%s</b> vous a écrit en privé<br>%s" % (de, apercu)
    if kind == "message_groupe":
        return "<b>%s</b> dans <b>%s</b><br>%s" % (de, e(n.get("groupe_nom") or "un groupe archivé"), apercu)
    if kind == "commentaire":
        return "<b>%s</b> a commenté votre publication<br>%s" % (de, apercu)
    if kind == "publication":
        return "<b>%s</b> a aimé votre publication" % de
    return "<b>%s</b> vous a envoyé une demande d'ami" % de


def _liste(moi, categorie, non_lues_seulement):
    page = st.session_state.get("notif_page", 1)
    ok, r = essayer("notifications", user_id=moi["_id"], categorie=categorie, non_lues_seulement=non_lues_seulement, page=page, par_page=PAR_PAGE)
    if not ok:
        return
    if not r["items"]:
        etat_vide("check-check", "Tout est à jour" if non_lues_seulement else "Aucune notification", "Rien à afficher dans cette catégorie.", compact=True)
    for n in r["items"]:
        nonlue = n["statut"] == "non_lue"
        with carte("notif_%s" % n["_id"], "nonlue" if nonlue else "flat"):
            c1, c2 = st.columns([6, 1.7])
            c1.markdown('<div class="notif">%s<div class="corps">%s<div class="quand">%s%s</div></div></div>'
                        % (avatar_utilisateur(n.get("de"), 40), _texte(n), icone("clock", 13), fdate(n["date"])), unsafe_allow_html=True)
            with c2:
                st.markdown('<div style="text-align:right">%s</div>' % badge_lu(nonlue), unsafe_allow_html=True)
                if n["type"] == "demande_ami" and nonlue:
                    if bouton_icone("Accepter", "user-plus", "acc_%s_%s" % (categorie, n["_id"]), variante="bord", width="stretch"):
                        ok, _ = essayer("accepter_ami", succes="Vous êtes maintenant amis.", user_id=moi["_id"], notification_id=n["_id"])
                        if ok:
                            st.rerun()
                elif nonlue and bouton_icone("Marquer lue", "check", "lue_%s_%s" % (categorie, n["_id"]), variante="bord", width="stretch"):
                    ok, _ = essayer("marquer_lues", user_id=moi["_id"], ids=[n["_id"]])
                    if ok:
                        st.rerun()
    pagination("notif_page", r["total"], PAR_PAGE)


def afficher(moi):
    ok, c = essayer("compter_notifications", user_id=moi["_id"])
    if not ok:
        return
    gauche, droite = st.columns([3, 1.3], vertical_alignment="center")
    with gauche:
        en_tete("Notifications", "%d non lues - groupes : %d, conversations privées : %d, autres : %d" % (c["total"], c["groupes"], c["prives"], c["autres"]))
    with droite:
        if bouton_icone("Tout marquer comme lu", "check-check", "toutlu", variante="plein", disabled=c["total"] == 0, width="stretch"):
            ok, _ = essayer("marquer_lues", succes="Toutes les notifications sont marquées comme lues.", user_id=moi["_id"])
            if ok:
                st.rerun()
    nombres = {"tous": c["total"], "groupes": c["groupes"], "prives": c["prives"], "autres": c["autres"]}
    f1, f2 = st.columns([3, 2], vertical_alignment="center")
    with f1:
        categorie = pills("notif_cat", list(CATEGORIES), "tous", lambda k: "%s (%d)" % (CATEGORIES[k], nombres[k]))
    with f2:
        seulement = st.toggle("Afficher uniquement les non lues", key="notif_nonlues")
    ctx = (categorie, seulement)
    if st.session_state.get("notif_ctx") != ctx:
        st.session_state["notif_ctx"], st.session_state["notif_page"] = ctx, 1
    if categorie != "tous" and nombres[categorie]:
        if bouton_icone("Marquer « %s » comme lu" % CATEGORIES[categorie], "check", "cat_" + categorie, variante="bord"):
            ok, _ = essayer("marquer_lues", succes="Catégorie marquée comme lue.", user_id=moi["_id"], categorie=categorie)
            if ok:
                st.rerun()
    _liste(moi, categorie, seulement)
