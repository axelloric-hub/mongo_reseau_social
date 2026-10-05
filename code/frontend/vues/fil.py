"""
fil.py - Page 'Fil d'actualite' : composer, filtrer le fil et recherche par hashtag.

Le fil vient de l'API (crud.fil_actualite) ; chaque publication indique pourquoi elle apparait
(ami, preferences), ce qui montre a l'enseignant l'effet des preferences sur le fil.
"""
import streamlit as st

from data.catalogue_images import construire_url
from frontend.api_client import ApiErreur, appel
from frontend.components.avatar import avatar_utilisateur
from frontend.components.buttons import bouton_icone, popover_icone
from frontend.components.cards import carte, en_tete
from frontend.components.empty_state import etat_vide
from frontend.components.helpers import essayer, flash, pagination, pills
from frontend.components.post import VISIBILITES, carte_publication

MODES = {"pour_moi": "Pour moi", "amis": "Mes amis", "preferences": "Mes préférences"}
PAR_PAGE = 8


def _publier(user_id):
    """Callback du bouton Publier : lit les champs du composer, appelle l'API, puis vide le formulaire."""
    s = st.session_state
    try:
        appel("creer_publication", user_id=user_id, texte=s.get("nouv_texte", ""), image_id=s.get("nouv_image"),
              variante="grayscale" if s.get("nouv_variante") else "principale", hashtags=s.get("nouv_tags", []),
              visibilite=s.get("nouv_vis", "public"))
    except ApiErreur as err:
        flash(str(err), "erreur")
        return
    for cle, vide in (("nouv_texte", ""), ("nouv_image", None), ("nouv_variante", False), ("nouv_tags", []), ("nouv_vis", "public")):
        s[cle] = vide
    s["fil_page"] = 1
    flash("Publication créée.")


def _composer(moi):
    ok, images = essayer("images")
    ok2, hashtags = essayer("hashtags")
    if not (ok and ok2):
        return
    with carte("composer"):
        c_av, c_txt = st.columns([1, 15], vertical_alignment="top")
        c_av.markdown(avatar_utilisateur(moi, 40), unsafe_allow_html=True)
        c_txt.text_area("Quoi de neuf ?", key="nouv_texte", placeholder="Quoi de neuf ?", max_chars=1000, height=84, label_visibility="collapsed")
        b1, b2, _, b4 = st.columns([1.1, 1.3, 4, 1.6], vertical_alignment="center")
        with b1:
            with popover_icone("Image", "image", "composer_image", variante="bord", width="stretch"):
                choix = st.selectbox("Image du catalogue (Lorem Picsum)", [None] + [i["id"] for i in images], key="nouv_image",
                                     format_func=lambda i: "Aucune image" if i is None else "%d - %s" % (i, next(x["description"] for x in images if x["id"] == i)))
                st.checkbox("Variante en niveaux de gris et floutée", key="nouv_variante")
                if choix is not None:
                    url = construire_url(choix, "grayscale" if st.session_state.get("nouv_variante") else "principale", 1, 400, 260)
                    st.markdown('<img class="post-media" src="%s" alt="Aperçu">' % url, unsafe_allow_html=True)
        with b2:
            with popover_icone("Hashtags", "hash", "composer_options", variante="bord", width="stretch"):
                st.multiselect("Hashtags", [h["tag"] for h in hashtags], key="nouv_tags",
                               help="Chaque hashtag est rattaché à 1 à 3 préférences et alimente le fil des autres membres.")
                st.selectbox("Visibilité", list(VISIBILITES), key="nouv_vis", format_func=VISIBILITES.get)
        with b4:
            bouton_icone("Publier", "send", "publier", variante="plein", width="stretch", on_click=_publier, args=(moi["_id"],))
        resume = []
        if st.session_state.get("nouv_image") is not None:
            resume.append("image %d" % st.session_state["nouv_image"])
        if st.session_state.get("nouv_tags"):
            resume.append(" ".join("#" + t for t in st.session_state["nouv_tags"]))
        if resume:
            st.markdown('<div class="small">Joint à la publication : %s</div>' % ", ".join(resume), unsafe_allow_html=True)


def afficher(moi):
    en_tete("Fil d'actualité", "Les publications de vos amis et celles qui correspondent à vos préférences.")
    _composer(moi)
    c1, c2 = st.columns([3, 2], vertical_alignment="center")
    with c1:
        mode = pills("fil_mode", list(MODES), "pour_moi", MODES.get)
    with c2:
        tag = st.text_input("Rechercher un hashtag", key="champ-recherche_fil", placeholder="Rechercher un hashtag, ex. nature",
                            label_visibility="collapsed").strip().lstrip("#")
    if st.session_state.get("fil_ctx") != (mode, tag):          # nouveau filtre : retour a la page 1
        st.session_state["fil_ctx"], st.session_state["fil_page"] = (mode, tag), 1
    page = st.session_state.get("fil_page", 1)
    if tag:
        st.markdown('<div class="small">Publications publiques portant #%s</div>' % tag.replace("<", ""), unsafe_allow_html=True)
        ok, r = essayer("publications_hashtag", tag=tag, user_id=moi["_id"], page=page, par_page=PAR_PAGE)
    else:
        prefs = ", ".join(moi["preferences"])
        explication = {"pour_moi": "Vos publications, celles de vos amis et celles qui correspondent à vos préférences (%s)." % prefs,
                       "amis": "Publications de vos amis, publiques ou réservées aux amis.",
                       "preferences": "Publications publiques dont les hashtags correspondent à vos préférences : %s." % prefs}[mode]
        st.markdown('<div class="small">%s</div>' % explication, unsafe_allow_html=True)
        ok, r = essayer("fil", user_id=moi["_id"], mode=mode, page=page, par_page=PAR_PAGE)
    if not ok:
        return
    if not r["items"]:
        etat_vide("inbox", "Aucune publication à afficher", "Essayez un autre filtre, ou publiez quelque chose pour lancer la conversation.", compact=True)
    for p in r["items"]:
        carte_publication(p, moi, "fil")
    pagination("fil_page", r["total"], PAR_PAGE)
