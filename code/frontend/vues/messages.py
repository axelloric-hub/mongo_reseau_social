"""
messages.py - Page 'Messages' : liste de conversations a gauche, discussion ou etat vide a droite.

Ouvrir une conversation marque ses messages comme lus dans MongoDB (statut 'lu' pour un message
prive, retrait de 'non_lu_par' pour un message de groupe). Les messages encore non lus a
l'ouverture sont signales 'Nouveau' avant d'etre marques. Rien n'est ouvert (donc rien n'est
marque lu) tant que l'utilisateur n'a pas choisi une conversation.
"""
import streamlit as st

from frontend.components.avatar import avatar, avatar_utilisateur
from frontend.components.buttons import popover_icone
from frontend.components.cards import carte, en_tete
from frontend.components.empty_state import etat_vide
from frontend.components.helpers import e, essayer, fcourt, pills
from frontend.components.messages import bulles_groupe, bulles_prives, en_tete_conversation, ligne_conversation
from frontend.components.icons import icone


def discussion_groupe(gid, moi):
    """Discussion d'un groupe (reutilisee par la page Groupes)."""
    ok, r = essayer("messages_groupe", groupe_id=gid, user_id=moi["_id"], par_page=40)
    if not ok:
        return
    if not r["items"]:
        st.markdown('<div class="small">Aucun message dans ce groupe pour le moment.</div>', unsafe_allow_html=True)
    elif r["total"] > len(r["items"]):
        st.markdown('<div class="small">Les %d messages les plus récents sur %d.</div>' % (len(r["items"]), r["total"]), unsafe_allow_html=True)
    bulles_groupe(r["items"], moi)
    texte = st.chat_input("Écrire au groupe", key="chat_groupe_" + gid)
    if texte:
        ok, _ = essayer("envoyer_groupe", user_id=moi["_id"], groupe_id=gid, contenu=texte)
        if ok:
            st.rerun()


def _nouvelle_conversation():
    with popover_icone("Nouvelle conversation", "plus", "nvconv", variante="plein", width="stretch"):
        pseudo = st.text_input("Pseudo du destinataire", key="conv_pseudo", placeholder="ex. kotto_enspd")
        if pseudo.strip():
            ok, trouves = essayer("rechercher", texte=pseudo)
            if ok and not trouves:
                st.markdown('<div class="small">Aucun membre trouvé.</div>', unsafe_allow_html=True)
            for t in (trouves or [])[:5]:
                if st.button("@%s - %s %s" % (t["pseudo"], t["prenom"], t["nom"]), key="nv_" + t["_id"], width="stretch"):
                    st.session_state["conv_cible"], st.session_state["tabs_msg_section"] = t["_id"], "Privées"
                    st.rerun()


def _liste_privees(moi):
    ok, convs = essayer("conversations", user_id=moi["_id"])
    if not ok:
        return
    recherche = st.session_state.get("champ-recherche_conv", "").strip().lower()
    if recherche:
        convs = [c for c in convs if recherche in ("%s %s %s" % (c["prenom"], c["nom"], c["pseudo"])).lower()]
    if not convs:
        etat_vide("search" if recherche else "inbox", "Aucun résultat" if recherche else "Aucune conversation", compact=True)
    with st.container(height=520, border=False):
        for c in convs[:60]:
            if ligne_conversation("p_" + c["_id"], st.session_state.get("conv_cible") == c["_id"], avatar_utilisateur(c, 44),
                                  "%s %s" % (c["prenom"], c["nom"]), c["dernier_message"], fcourt(c["derniere_date"]), c["non_lus"]):
                st.session_state["conv_cible"] = c["_id"]
                st.rerun()


def _liste_groupes(moi):
    ok, groupes = essayer("groupes", user_id=moi["_id"], miens=True)
    if not ok:
        return
    recherche = st.session_state.get("champ-recherche_conv", "").strip().lower()
    groupes = [g for g in groupes if recherche in g["nom"].lower()]
    if not groupes:
        etat_vide("users-round", "Aucun groupe", "Rejoignez un groupe pour discuter avec ses membres.", compact=True)
    with st.container(height=520, border=False):
        for g in groupes:
            if ligne_conversation("g_" + g["_id"], st.session_state.get("msg_groupe") == g["_id"], avatar(g["nom"], "", 44, g["nom"]),
                                  g["nom"], "%d membres" % g["nb_membres"], ""):
                st.session_state["msg_groupe"] = g["_id"]
                st.rerun()


def _panneau_prive(moi):
    cible = st.session_state.get("conv_cible")
    if not cible:
        etat_vide("message-circle", "Aucune conversation sélectionnée",
                  "Sélectionnez une conversation pour commencer à échanger avec un membre, ou démarrez-en une nouvelle.", hauteur=560)
        return
    ok, profil = essayer("profil", user_id=cible)
    if not ok:
        return
    with carte("thread"):
        en_tete_conversation(avatar_utilisateur(profil, 40), "%s %s" % (profil["prenom"], profil["nom"]), "@%s - %s" % (profil["pseudo"], profil["ville"]))
        ok, conv = essayer("conversation", user_id=moi["_id"], autre_id=cible, par_page=40)
        if not ok:
            return
        if not conv["items"]:
            st.markdown('<div class="small">Aucun message pour le moment. Dites bonjour.</div>', unsafe_allow_html=True)
        bulles_prives(conv["items"], moi)
        texte = st.chat_input("Écrire un message", key="chat_prive")
        if texte:
            ok, _ = essayer("envoyer_prive", user_id=moi["_id"], dest_id=cible, contenu=texte)
            if ok:
                st.rerun()


def _panneau_groupe(moi):
    gid = st.session_state.get("msg_groupe")
    if not gid:
        etat_vide("users-round", "Aucun groupe sélectionné", "Choisissez un groupe dans la liste pour lire et écrire dans sa discussion.", hauteur=560)
        return
    ok, g = essayer("groupe", groupe_id=gid, user_id=moi["_id"])
    if not ok:
        return
    with carte("thread_groupe"):
        en_tete_conversation(avatar(g["nom"], "", 40, g["nom"]), g["nom"], "%d membres" % len(g["membres"]))
        discussion_groupe(gid, moi)


def afficher(moi):
    titre, action = st.columns([2, 1.3], vertical_alignment="center")
    with titre:
        en_tete("Messages", "Conversations privées et discussions de groupe.")
    with action:
        _nouvelle_conversation()
    gauche, droite = st.columns([1, 2], gap="large")
    with gauche:
        st.text_input("Rechercher une conversation", key="champ-recherche_conv", placeholder="Rechercher une conversation", label_visibility="collapsed")
        section = pills("msg_section", ["Privées", "Groupes"], "Privées", onglets=True)
        (_liste_privees if section == "Privées" else _liste_groupes)(moi)
    with droite:
        (_panneau_prive if section == "Privées" else _panneau_groupe)(moi)
