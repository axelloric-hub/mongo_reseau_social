"""
post.py - Carte de publication : auteur, texte, image, hashtags, actions, commentaires, menu auteur.

Les commentaires ne sont charges qu'a la demande (un appel API par publication ouverte, pas par
publication affichee). Modifier et supprimer sont reserves a l'auteur, dans le menu '...'.
La suppression passe par une boite de dialogue de confirmation : la publication est archivee, pas detruite.
"""
import streamlit as st

from frontend.components.avatar import avatar_utilisateur
from frontend.components.badges import puces
from frontend.components.buttons import bouton_icone, popover_icone
from frontend.components.cards import carte
from frontend.components.helpers import e, essayer, fdate
from frontend.components.icons import icone

VISIBILITES = {"public": "Public", "amis": "Amis", "prive": "Privé"}


@st.dialog("Supprimer la publication ?")
def _dialogue_suppression(pid, user_id):
    st.markdown("La publication et ses commentaires seront **archivés** : ils quittent le fil mais restent récupérables dans la base.")
    c1, c2 = st.columns(2)
    if c1.button("Annuler", key="annuler_%s" % pid, width="stretch"):
        st.rerun()
    if c2.button("Supprimer", key="danger_confirmer_%s" % pid, type="primary", width="stretch"):
        ok, _ = essayer("supprimer_publication", succes="Publication supprimée (archivée).", pub_id=pid, user_id=user_id)
        if ok:
            st.rerun()


def _entete(p):
    meta = "@%s - %s - %s" % (e((p.get("auteur") or {}).get("pseudo", "?")), fdate(p["date"]), VISIBILITES.get(p["visibilite"], p["visibilite"]))
    if p.get("groupe_nom"):
        meta += " - dans %s" % e(p["groupe_nom"])
    if p.get("historique_modifs"):
        meta += " - modifiée"
    a = p.get("auteur") or {}
    return ('<div class="post-head">%s<div class="who"><div class="name">%s %s</div><div class="meta">%s</div></div></div>'
            % (avatar_utilisateur(a, 40), e(a.get("prenom", "")), e(a.get("nom", "")), meta))


def carte_publication(p, moi, prefixe):
    """Affiche une publication ; 'prefixe' rend les cles des widgets uniques d'une page a l'autre."""
    pid, cle = p["_id"], "%s_%s" % (prefixe, p["_id"])
    est_auteur = p["auteur_id"] == moi["_id"]
    c = p["compteurs"]
    with carte("post_" + cle):
        # --- en-tete : auteur + menu discret reserve a l'auteur
        if est_auteur:
            gauche, droite = st.columns([14, 1], vertical_alignment="center")
            gauche.markdown(_entete(p), unsafe_allow_html=True)
            with droite:
                with popover_icone("Options de la publication", "ellipsis", "menu_" + cle, width="content"):
                    if bouton_icone("Modifier", "pencil", "edit_" + cle, width="stretch"):
                        st.session_state["edit_" + cle] = not st.session_state.get("edit_" + cle, False)
                        st.rerun()
                    if bouton_icone("Supprimer", "trash-2", "suppr_" + cle, width="stretch"):
                        _dialogue_suppression(pid, moi["_id"])
        else:
            st.markdown(_entete(p), unsafe_allow_html=True)

        if p.get("raisons"):
            st.markdown('<div class="post-raison">%s%s</div>' % (icone("sparkles", 14), e(" - ".join(p["raisons"]))), unsafe_allow_html=True)
        if p["texte"]:
            st.markdown('<div class="post-body">%s</div>' % e(p["texte"]), unsafe_allow_html=True)
        for m in p.get("medias", []):
            st.markdown('<div><img class="post-media" src="%s" alt="%s" loading="lazy"><div class="post-media-legende">%s</div></div>'
                        % (e(m["url"]), e(m.get("description", "")), e(m.get("description", ""))), unsafe_allow_html=True)
        if p.get("hashtags"):
            st.markdown(puces(["#" + t for t in p["hashtags"]], "chip tag"), unsafe_allow_html=True)

        # --- actions : j'aime, commentaires, partager
        a1, a2, a3, _ = st.columns([0.9, 0.9, 1.5, 6])
        with a1:
            if bouton_icone(str(c["aimes"]), "thumbs-up", "like_" + cle, type="primary" if p.get("a_aime") else "tertiary",
                            help="Retirer mon j'aime" if p.get("a_aime") else "J'aime"):
                ok, _r = essayer("aimer", pub_id=pid, user_id=moi["_id"])
                if ok:
                    st.rerun()
        with a2:
            if bouton_icone(str(c["commentaires"]), "message-circle", "com_" + cle, type="primary" if st.session_state.get("com_" + cle) else "tertiary",
                            help="Afficher les commentaires"):
                st.session_state["com_" + cle] = not st.session_state.get("com_" + cle, False)
                st.rerun()
        with a3:
            if bouton_icone("Partager %d" % c["partages"] if c["partages"] else "Partager", "share-2", "part_" + cle, type="tertiary"):
                ok, _r = essayer("partager", succes="Publication partagée.", pub_id=pid)
                if ok:
                    st.rerun()

        if est_auteur and st.session_state.get("edit_" + cle):
            _formulaire_edition(p, moi, cle)
        if st.session_state.get("com_" + cle):
            _commentaires(p, moi, cle)


def _formulaire_edition(p, moi, cle):
    with st.form("form_edit_" + cle, border=False):
        texte = st.text_area("Texte", value=p["texte"], max_chars=1000)
        tags = st.text_input("Hashtags (séparés par des espaces)", value=" ".join(p.get("hashtags", [])))
        vis = st.selectbox("Visibilité", list(VISIBILITES), index=list(VISIBILITES).index(p["visibilite"]), format_func=VISIBILITES.get)
        if st.form_submit_button("Enregistrer les modifications", type="primary"):
            ok, _ = essayer("modifier_publication", succes="Publication modifiée.", pub_id=p["_id"], user_id=moi["_id"],
                            texte=texte, hashtags=tags.split(), visibilite=vis)
            if ok:
                st.session_state["edit_" + cle] = False
                st.rerun()


def _commentaires(p, moi, cle):
    ok, commentaires = essayer("commentaires", pub_id=p["_id"])
    if not ok:
        return
    st.markdown("<hr>", unsafe_allow_html=True)
    if not commentaires:
        st.markdown('<div class="small">Aucun commentaire pour le moment. Écrivez le premier.</div>', unsafe_allow_html=True)
    for com in commentaires:
        _ligne_commentaire(com, moi, cle, parent=None)
        for rep in com.get("reponses", []):
            _ligne_commentaire(rep, moi, cle, parent=com["_id"])
        with popover_icone("Répondre", "corner-down-right", "rep_%s_%s" % (cle, com["_id"]), width="content"):
            texte = st.text_input("Votre réponse", key="rep_txt_%s_%s" % (cle, com["_id"]))
            if st.button("Répondre", key="rep_ok_%s_%s" % (cle, com["_id"]), type="primary"):
                ok, _ = essayer("ajouter_commentaire", succes="Réponse publiée.", pub_id=p["_id"], user_id=moi["_id"], contenu=texte, parent_id=com["_id"])
                if ok:
                    st.rerun()
    with st.form("form_com_" + cle, clear_on_submit=True, border=False):
        texte = st.text_input("Ajouter un commentaire", placeholder="Écrivez un commentaire...", label_visibility="collapsed")
        if st.form_submit_button("Commenter", type="primary"):
            ok, _ = essayer("ajouter_commentaire", succes="Commentaire publié.", pub_id=p["_id"], user_id=moi["_id"], contenu=texte)
            if ok:
                st.rerun()


def _ligne_commentaire(com, moi, cle, parent):
    a = com.get("auteur") or {}
    taille = 28 if parent is None else 24
    st.markdown('<div class="comment%s">%s<div class="bulle-com"><div class="nom">@%s <span class="date">%s</span></div><div class="texte">%s</div></div></div>'
                % (" reponse" if parent else "", avatar_utilisateur(a, taille), e(a.get("pseudo", "?")), fdate(com["date"]), e(com["contenu"])), unsafe_allow_html=True)
    if com["auteur_id"] == moi["_id"]:
        if bouton_icone("Effacer", "trash-2", "comdel_%s_%s" % (cle, com["_id"]), type="tertiary"):
            ok, _ = essayer("supprimer_commentaire", succes="Commentaire effacé (archivé).", commentaire_id=com["_id"], user_id=moi["_id"])
            if ok:
                st.rerun()
