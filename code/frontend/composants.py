"""
composants.py - Style global et composants Streamlit reutilises par toutes les vues.

Ce module existe pour garder une interface coherente : meme CSS (blanc ivoire, blanc pur, texte
noir ; la couleur sert uniquement a signaler un etat), memes cartes de publication, memes badges.
Il contient aussi les petits utilitaires d'affichage (dates, erreurs, messages de confirmation).
"""
import html
from datetime import datetime

import streamlit as st

from frontend.api_client import ApiErreur, appel

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ivoire:#FBF8F1; --blanc:#FFFFFF; --ligne:#E9E3D5; --encre:#111111; --gris:#6E695E;
        --pastille:#EFE9DA; --ok:#1E7B4F; --alerte:#B3261E; --info:#2B5C8A; }
html, body, .stApp, .stApp p, .stApp label, .stApp span, .stApp li, .stApp div { font-family:'Manrope', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp, .stApp p, .stApp label, .stMarkdown, h1, h2, h3, h4 { color: var(--encre); }
.stApp { background: var(--ivoire); }
header[data-testid="stHeader"], footer, #MainMenu { display:none; }
.block-container { padding-top: 1.6rem; max-width: 1100px; }
h1 { font-weight:800; letter-spacing:-0.02em; font-size:1.9rem; }
h2, h3 { font-weight:700; letter-spacing:-0.01em; }
[data-testid="stSidebar"] { background: var(--blanc); border-right:1px solid var(--ligne); }
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--blanc); border-color: var(--ligne) !important; border-radius:14px; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius:10px; border:1px solid var(--ligne); background:var(--blanc); color:var(--encre); font-weight:600; transition:background .15s; }
.stButton > button:hover { background:var(--pastille); border-color:#cfc7b3; color:var(--encre); }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] { background:var(--encre); color:#fff; border-color:var(--encre); }
.stButton > button[kind="primary"]:hover { background:#2a2a2a; color:#fff; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div { background:#fff; border-color:var(--ligne); color:var(--encre); border-radius:10px; }
button:focus-visible, input:focus-visible, textarea:focus-visible { outline:2px solid var(--encre) !important; outline-offset:2px; }
.avatar { display:inline-flex; align-items:center; justify-content:center; border-radius:50%; background:var(--pastille); color:var(--encre);
          font-weight:700; border:1px solid var(--ligne); flex:none; }
.entete { display:flex; gap:.7rem; align-items:center; }
.entete .nom { font-weight:700; line-height:1.2; }
.entete .meta { color:var(--gris); font-size:.82rem; line-height:1.3; }
.puce { display:inline-block; padding:.12rem .55rem; border-radius:999px; border:1px solid var(--ligne); background:var(--ivoire); font-size:.76rem; font-weight:600; margin-right:.3rem; }
.puce.tag { background:var(--pastille); }
.etat-nonlu { display:inline-block; padding:.12rem .6rem; border-radius:999px; background:var(--ok); color:#fff; font-size:.74rem; font-weight:700; }
.etat-lu { display:inline-block; padding:.12rem .6rem; border-radius:999px; background:var(--pastille); color:var(--gris); font-size:.74rem; font-weight:600; }
.etat-alerte { display:inline-block; padding:.12rem .6rem; border-radius:999px; background:var(--alerte); color:#fff; font-size:.74rem; font-weight:700; }
.raison { color:var(--info); font-size:.8rem; font-weight:600; margin:.2rem 0 .4rem; }
.discret { color:var(--gris); font-size:.85rem; }
.fil-bulles { display:flex; flex-direction:column; gap:.35rem; padding:.2rem 0; }
.bulle { max-width:78%; padding:.5rem .8rem; border-radius:14px; border:1px solid var(--ligne); background:#fff; width:fit-content; }
.bulle.moi { align-self:flex-end; background:var(--pastille); }
.bulle .qui { font-size:.74rem; font-weight:700; color:var(--gris); }
.bulle .quand { font-size:.7rem; color:var(--gris); margin-top:.15rem; }
.bulle .nouveau { color:var(--ok); font-weight:800; }
.notif-nonlue { border-left:4px solid var(--ok); }
.chiffre { font-size:1.7rem; font-weight:800; line-height:1.1; }
.etiquette { color:var(--gris); font-size:.82rem; font-weight:600; }
@media (max-width: 700px) { .bulle { max-width:92%; } .block-container { padding-left:.8rem; padding-right:.8rem; } }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
</style>
"""


def appliquer_style():
    st.markdown(CSS, unsafe_allow_html=True)


def e(texte):
    """Echappe le HTML des textes saisis par les utilisateurs (evite l'injection dans unsafe_allow_html)."""
    return html.escape(str(texte if texte is not None else ""))


def fdate(iso):
    """'2026-10-04T20:00:00' -> '04/10/2026 20:00'."""
    if not iso:
        return ""
    return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")


def fjour(iso):
    return datetime.fromisoformat(iso).strftime("%d/%m/%Y") if iso else ""


def avatar(prenom, nom, taille=40):
    initiales = ((prenom or "?")[:1] + (nom or "")[:1]).upper()
    return '<span class="avatar" style="width:%dpx;height:%dpx;font-size:%dpx">%s</span>' % (taille, taille, taille * 0.38, e(initiales))


def entete_utilisateur(u, meta="", taille=40):
    """Bloc HTML : avatar + nom complet + ligne de meta (pseudo, date...)."""
    if not u:
        return '<div class="entete"><span class="discret">Utilisateur indisponible</span></div>'
    return ('<div class="entete">%s<div><div class="nom">%s %s</div><div class="meta">@%s%s</div></div></div>'
            % (avatar(u.get("prenom"), u.get("nom"), taille), e(u.get("prenom")), e(u.get("nom")), e(u.get("pseudo")),
               (" - " + meta) if meta else ""))


def puces(valeurs, classe="puce"):
    return "".join('<span class="%s">%s</span>' % (classe, e(v)) for v in valeurs)


def message_flash(texte):
    """Memorise un message de confirmation affiche apres le prochain rerun (toast)."""
    st.session_state["flash"] = texte


def afficher_flash():
    if st.session_state.get("flash"):
        st.toast(st.session_state.pop("flash"))


def essayer(action, succes=None, **params):
    """
    Appelle l'API et gere l'erreur proprement : affiche le message sans planter la page.
    Renvoie (ok, resultat). Si 'succes' est fourni, il est affiche en toast apres rerun.
    """
    try:
        resultat = appel(action, **params)
    except ApiErreur as err:
        st.error(str(err))
        return False, None
    if succes:
        message_flash(succes)
    return True, resultat


VISIBILITES = {"public": "Public", "amis": "Amis", "prive": "Privé"}


def carte_publication(p, moi, prefixe, rerun=True):
    """
    Carte d'une publication : auteur, texte, image, hashtags, raison d'affichage, j'aime,
    commentaires (affiches a la demande pour limiter les appels), modification et suppression
    reservees a l'auteur. 'prefixe' rend les cles des widgets uniques entre les vues.
    """
    pid, cle = p["_id"], "%s_%s" % (prefixe, p["_id"])
    est_auteur = p["auteur_id"] == moi["_id"]
    with st.container(border=True):
        meta = fdate(p["date"]) + " - " + VISIBILITES.get(p["visibilite"], p["visibilite"])
        if p.get("groupe_nom"):
            meta += " - dans " + e(p["groupe_nom"])
        if p.get("historique_modifs"):
            meta += " - modifiée"
        st.markdown(entete_utilisateur(p.get("auteur"), meta), unsafe_allow_html=True)
        if p.get("raisons"):
            st.markdown('<div class="raison">%s</div>' % e(" / ".join(p["raisons"])), unsafe_allow_html=True)
        if p["texte"]:
            st.markdown(e(p["texte"]))
        for media in p.get("medias", []):
            st.image(media["url"], caption=media.get("description"), width="stretch")
        if p.get("hashtags"):
            st.markdown(puces(["#" + t for t in p["hashtags"]], "puce tag"), unsafe_allow_html=True)

        c = p["compteurs"]
        colonnes = st.columns([1, 1, 1, 1, 1] if est_auteur else [1, 1, 1, 2])
        if colonnes[0].button("%s %d" % ("Retirer j'aime" if p.get("a_aime") else "J'aime", c["aimes"]), key="like_" + cle,
                              type="primary" if p.get("a_aime") else "secondary", width="stretch"):
            ok, _ = essayer("aimer", pub_id=pid, user_id=moi["_id"])
            if ok and rerun:
                st.rerun()
        if colonnes[1].button("Commentaires %d" % c["commentaires"], key="comtog_" + cle, width="stretch"):
            st.session_state["com_" + cle] = not st.session_state.get("com_" + cle, False)
            st.rerun()
        if colonnes[2].button("Partager %d" % c["partages"], key="part_" + cle, width="stretch"):
            ok, _ = essayer("partager", succes="Publication partagée.", pub_id=pid)
            if ok and rerun:
                st.rerun()
        if est_auteur:
            if colonnes[3].button("Modifier", key="edit_" + cle, width="stretch"):
                st.session_state["edit_" + cle] = not st.session_state.get("edit_" + cle, False)
                st.rerun()
            with colonnes[4].popover("Supprimer", width="stretch"):
                st.caption("La publication et ses commentaires seront archivés (récupérables dans la base).")
                if st.button("Confirmer la suppression", key="del_" + cle, type="primary"):
                    ok, r = essayer("supprimer_publication", pub_id=pid, user_id=moi["_id"],
                                    succes="Publication supprimée (archivée).")
                    if ok:
                        st.rerun()

        if est_auteur and st.session_state.get("edit_" + cle):
            with st.form("form_edit_" + cle):
                texte = st.text_area("Texte", value=p["texte"], max_chars=1000)
                tags = st.text_input("Hashtags (séparés par des espaces)", value=" ".join(p.get("hashtags", [])))
                vis = st.selectbox("Visibilité", list(VISIBILITES), index=list(VISIBILITES).index(p["visibilite"]),
                                   format_func=VISIBILITES.get)
                if st.form_submit_button("Enregistrer les modifications", type="primary"):
                    ok, _ = essayer("modifier_publication", succes="Publication modifiée.", pub_id=pid, user_id=moi["_id"],
                                    texte=texte, hashtags=tags.split(), visibilite=vis)
                    if ok:
                        st.session_state["edit_" + cle] = False
                        st.rerun()

        if st.session_state.get("com_" + cle):
            _bloc_commentaires(p, moi, cle)


def _bloc_commentaires(p, moi, cle):
    """Liste des commentaires (chargee a la demande), reponses incluses, avec ajout et suppression."""
    ok, commentaires = essayer("commentaires", pub_id=p["_id"])
    if not ok:
        return
    st.markdown("---")
    if not commentaires:
        st.caption("Aucun commentaire pour le moment. Écrivez le premier.")
    for com in commentaires:
        _ligne_commentaire(com, moi, cle, p["_id"], parent=None)
        for rep in com.get("reponses", []):
            _ligne_commentaire(rep, moi, cle, p["_id"], parent=com["_id"], decalage=True)
        with st.popover("Répondre", width="content"):
            texte = st.text_input("Votre réponse", key="rep_txt_%s_%s" % (cle, com["_id"]))
            if st.button("Répondre", key="rep_ok_%s_%s" % (cle, com["_id"])):
                ok, _ = essayer("ajouter_commentaire", succes="Réponse publiée.", pub_id=p["_id"], user_id=moi["_id"],
                                contenu=texte, parent_id=com["_id"])
                if ok:
                    st.rerun()
    with st.form("form_com_" + cle, clear_on_submit=True):
        texte = st.text_input("Ajouter un commentaire", placeholder="Écrivez un commentaire...")
        if st.form_submit_button("Commenter"):
            ok, _ = essayer("ajouter_commentaire", succes="Commentaire publié.", pub_id=p["_id"], user_id=moi["_id"], contenu=texte)
            if ok:
                st.rerun()


def _ligne_commentaire(com, moi, cle, pub_id, parent, decalage=False):
    colonnes = st.columns([0.06, 0.94] if decalage else [1])
    zone = colonnes[-1]
    with zone:
        a = com.get("auteur")
        c1, c2 = st.columns([5, 1])
        c1.markdown('<div style="margin-bottom:.1rem"><b>@%s</b> <span class="discret">%s</span></div>%s'
                    % (e(a["pseudo"] if a else "?"), fdate(com["date"]), e(com["contenu"])), unsafe_allow_html=True)
        if com["auteur_id"] == moi["_id"]:
            if c2.button("Effacer", key="comdel_%s_%s" % (cle, com["_id"])):
                ok, _ = essayer("supprimer_commentaire", succes="Commentaire effacé (archivé).", commentaire_id=com["_id"], user_id=moi["_id"])
                if ok:
                    st.rerun()


def pagination(cle, total, par_page):
    """Boutons Precedent / Suivant ; renvoie la page courante (stockee dans session_state)."""
    pages = max(1, -(-total // par_page))
    page = min(st.session_state.get(cle, 1), pages)
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("Précédent", key=cle + "_prec", disabled=page <= 1, width="stretch"):
        st.session_state[cle] = page - 1
        st.rerun()
    c2.markdown('<div style="text-align:center;padding-top:.45rem" class="discret">Page %d sur %d - %d résultat(s)</div>' % (page, pages, total),
                unsafe_allow_html=True)
    if c3.button("Suivant", key=cle + "_suiv", disabled=page >= pages, width="stretch"):
        st.session_state[cle] = page + 1
        st.rerun()
    return page
