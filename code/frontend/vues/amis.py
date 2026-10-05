"""amis.py - Page 'Amis' : liste triable (anciennete ou frequence des conversations) et suggestions."""
import streamlit as st

from frontend.components.avatar import avatar_utilisateur
from frontend.components.buttons import bouton_icone
from frontend.components.cards import carte, en_tete, titre_section
from frontend.components.empty_state import etat_vide
from frontend.components.helpers import e, essayer, fjour, pills

TRIS = {"anciennete": "Ancienneté de l'amitié", "frequence": "Fréquence des conversations"}


def _ecrire(ami_id):
    """Callback : ouvre la messagerie sur la conversation avec cet ami."""
    st.session_state["conv_cible"] = ami_id
    st.session_state["navigation"] = "messages"
    st.session_state["tabs_msg_section"] = "Privées"


def _ligne(a, cle, details, bouton):
    with carte("flat_ami_" + cle, ):
        c1, c2, c3 = st.columns([5, 4, 2], vertical_alignment="center")
        c1.markdown('<div class="post-head">%s<div class="who"><div class="name">%s %s</div><div class="meta">@%s - %s</div></div></div>'
                    % (avatar_utilisateur(a, 40), e(a["prenom"]), e(a["nom"]), e(a["pseudo"]), e(a["ville"])), unsafe_allow_html=True)
        c2.markdown('<div class="small">%s</div>' % details, unsafe_allow_html=True)
        with c3:
            bouton()


def afficher(moi):
    en_tete("Amis", "Retrouvez vos amis, écrivez-leur et découvrez de nouvelles personnes.")
    tri = pills("amis_tri", list(TRIS), "anciennete", TRIS.get)
    ok, amis = essayer("amis", user_id=moi["_id"], tri=tri)
    if not ok:
        return
    st.markdown('<div class="small">%d amis - %s</div>' % (len(amis), "les amitiés les plus anciennes d'abord" if tri == "anciennete"
                else "les plus grands nombres de messages échangés d'abord"), unsafe_allow_html=True)
    if not amis:
        etat_vide("users", "Pas encore d'amis", "Les suggestions ci-dessous peuvent vous aider à démarrer.", compact=True)
    for a in amis:
        _ligne(a, "l_" + a["_id"], "Amis depuis le %s<br>%d messages échangés" % (fjour(a["depuis"]), a["nb_messages"]),
               lambda a=a: bouton_icone("Écrire", "message-circle", "ecrire_" + a["_id"], variante="bord", width="stretch", on_click=_ecrire, args=(a["_id"],)))

    titre_section("Suggestions d'amis")
    st.markdown('<div class="small">Amis de vos amis, classés par nombre d\'amis en commun.</div>', unsafe_allow_html=True)
    ok, sugg = essayer("suggestions", user_id=moi["_id"])
    if ok:
        if not sugg:
            etat_vide("user-plus", "Aucune suggestion pour le moment", compact=True)
        for s in sugg:
            def demander(s=s):
                if bouton_icone("Demander", "user-plus", "dem_" + s["_id"], variante="bord", width="stretch"):
                    ok, _ = essayer("demande_ami", succes="Demande d'ami envoyée.", user_id=moi["_id"], cible_id=s["_id"])
                    if ok:
                        st.rerun()
            _ligne(s, "s_" + s["_id"], "%d ami(s) en commun" % s["amis_communs"], demander)
