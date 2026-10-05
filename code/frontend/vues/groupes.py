"""
groupes.py - Page 'Groupes' : liste, creation, publications, discussion et gestion des membres.

Rappel du modele : chaque groupe a un createur (administrateur d'office), une liste 'admins'
(le createur peut en nommer d'autres) et une liste 'membres'.
"""
import streamlit as st

from frontend.components.avatar import avatar, avatar_utilisateur
from frontend.components.badges import puces
from frontend.components.buttons import bouton_icone, popover_icone
from frontend.components.cards import carte, en_tete
from frontend.components.empty_state import etat_vide
from frontend.components.helpers import e, essayer, fjour, pagination, pills
from frontend.components.icons import icone
from frontend.components.post import carte_publication
from frontend.vues.messages import discussion_groupe

POPULARITE = {"populaire": "Populaire", "moins_populaire": "Moins populaire", "restreint": "Privé / restreint"}
PAR_PAGE = 5


def _ouvrir(gid):
    st.session_state["grp_ouvert"] = gid


def _liste(moi):
    c1, c2 = st.columns([3, 2], vertical_alignment="center")
    with c1:
        portee = pills("grp_portee", ["miens", "tous"], "miens", lambda v: "Mes groupes" if v == "miens" else "Tous les groupes")
    with c2:
        with popover_icone("Créer un groupe", "plus", "grp_nouveau", variante="plein", width="stretch"):
            nom = st.text_input("Nom du groupe", key="grp_nom")
            desc = st.text_input("Description", key="grp_desc")
            prive = st.checkbox("Groupe privé", key="grp_prive")
            if st.button("Créer le groupe", type="primary", key="grp_creer", width="stretch"):
                ok, r = essayer("creer_groupe", succes="Groupe créé : vous en êtes l'administrateur.", user_id=moi["_id"], nom=nom,
                                description=desc, type="prive" if prive else "public")
                if ok:
                    st.session_state["grp_ouvert"] = r["_id"]
                    st.rerun()
    ok, groupes = essayer("groupes", user_id=moi["_id"], miens=(portee == "miens"))
    if not ok:
        return
    st.markdown('<div class="small">%d groupe(s)</div>' % len(groupes), unsafe_allow_html=True)
    if not groupes:
        etat_vide("users-round", "Aucun groupe", "Créez un groupe ou affichez tous les groupes pour en découvrir.", compact=True)
    for g in groupes:
        with carte("flat_groupe_" + g["_id"]):
            a, b = st.columns([6, 1.4], vertical_alignment="center")
            a.markdown('<div class="post-head">%s<div class="who"><div class="card-title">%s</div><div class="small">%s</div></div></div>%s'
                       % (avatar(g["nom"], "", 44, g["nom"]), e(g["nom"]), e(g["description"]),
                          puces(["%d membres" % g["nb_membres"], POPULARITE.get(g["popularite"], g["popularite"]),
                                 "Privé" if g["type"] == "prive" else "Public"] + (["Membre"] if g.get("est_membre") else []))), unsafe_allow_html=True)
            with b:
                st.button("Ouvrir", key="ouvrir_" + g["_id"], type="secondary", width="stretch", on_click=_ouvrir, args=(g["_id"],))


def _membres(g, moi, gid):
    admins = set(g["admins"])
    for m in g["membres"]:
        p = m["profil"]
        with carte("flat_membre_" + m["user_id"]):
            c1, c2, c3 = st.columns([5, 2, 2], vertical_alignment="center")
            roles = ["Créateur"] if m["user_id"] == g["createur_id"] else (["Administrateur"] if m["user_id"] in admins else [])
            c1.markdown('<div class="post-head">%s<div class="who"><div class="name">%s %s</div><div class="meta">@%s - membre depuis le %s</div></div></div>%s'
                        % (avatar_utilisateur(p, 36), e((p or {}).get("prenom", "")), e((p or {}).get("nom", "")), e((p or {}).get("pseudo", "?")),
                           fjour(m["depuis"]), puces(roles) if roles else ""), unsafe_allow_html=True)
            if m["user_id"] != g["createur_id"]:
                if moi["_id"] == g["createur_id"] and m["user_id"] not in admins:
                    with c2:
                        if bouton_icone("Nommer admin", "lock", "adm_" + m["user_id"], variante="bord", width="stretch"):
                            ok, _ = essayer("promouvoir_admin", succes="Administrateur nommé.", groupe_id=gid, cible_id=m["user_id"], user_id=moi["_id"])
                            if ok:
                                st.rerun()
                if g["est_admin"] or m["user_id"] == moi["_id"]:
                    with c3:
                        if bouton_icone("Quitter" if m["user_id"] == moi["_id"] else "Retirer", "x", "ret_" + m["user_id"], variante="bord", width="stretch"):
                            ok, _ = essayer("retirer_membre", succes="Membre retiré du groupe.", groupe_id=gid, cible_id=m["user_id"], user_id=moi["_id"])
                            if ok:
                                st.rerun()
    if g["est_membre"]:
        with carte("ajout_membre"):
            st.markdown('<div class="card-title">Ajouter un membre</div>', unsafe_allow_html=True)
            pseudo = st.text_input("Pseudo (au moins 2 lettres)", key="champ-recherche_grp_ajout", placeholder="Rechercher un pseudo")
            if pseudo.strip():
                ok, trouves = essayer("rechercher", texte=pseudo)
                for t in (trouves or [])[:5]:
                    if bouton_icone("Ajouter @%s" % t["pseudo"], "user-plus", "ajout_" + t["_id"], variante="bord"):
                        ok, _ = essayer("ajouter_membre", succes="Membre ajouté.", groupe_id=gid, cible_id=t["_id"], user_id=moi["_id"])
                        if ok:
                            st.rerun()


def _detail(moi, gid):
    ok, g = essayer("groupe", groupe_id=gid, user_id=moi["_id"])
    if not ok:
        st.session_state.pop("grp_ouvert", None)
        return
    if bouton_icone("Tous les groupes", "arrow-left", "grp_retour", type="tertiary"):
        st.session_state.pop("grp_ouvert", None)
        st.rerun()
    en_tete(g["nom"], g["description"])
    createur = g["createur"] or {}
    st.markdown(puces(["%d membres" % len(g["membres"]), POPULARITE.get(g["popularite"], g["popularite"]), "Privé" if g["type"] == "prive" else "Public",
                       "Créé le " + fjour(g["date_creation"]), "Créateur : @" + createur.get("pseudo", "?")]), unsafe_allow_html=True)
    if g["type"] == "prive" and not g["est_membre"]:
        etat_vide("lock", "Ce groupe est privé", "Son contenu est réservé aux membres.")
        return
    section = pills("grp_section", ["Publications", "Discussion", "Membres"], "Publications", onglets=True)
    if section == "Publications":
        page = st.session_state.get("grp_page", 1)
        ok, r = essayer("publications_groupe", groupe_id=gid, user_id=moi["_id"], page=page, par_page=PAR_PAGE)
        if g["est_membre"]:
            with st.expander("Publier dans ce groupe"):
                texte = st.text_area("Texte", key="grp_pub_texte", max_chars=1000)
                if st.button("Publier dans le groupe", type="primary", key="grp_pub_ok"):
                    ok2, _ = essayer("creer_publication", succes="Publication ajoutée au groupe.", user_id=moi["_id"], texte=texte, groupe_id=gid)
                    if ok2:
                        st.rerun()
        if ok:
            if not r["items"]:
                etat_vide("file-text", "Aucune publication", "Soyez le premier à publier dans ce groupe.", compact=True)
            for p in r["items"]:
                carte_publication(p, moi, "grp")
            pagination("grp_page", r["total"], PAR_PAGE)
    elif section == "Discussion":
        if g["est_membre"]:
            with carte("discussion_groupe"):
                discussion_groupe(gid, moi)
        else:
            etat_vide("message-circle", "Réservé aux membres", "Rejoignez le groupe pour participer à la discussion.", compact=True)
    else:
        _membres(g, moi, gid)


def afficher(moi):
    gid = st.session_state.get("grp_ouvert")
    if gid:
        _detail(moi, gid)
    else:
        en_tete("Groupes", "Rejoignez des groupes, publiez et discutez avec leurs membres.")
        _liste(moi)
