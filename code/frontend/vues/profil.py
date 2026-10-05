"""profil.py - Page 'Mon profil' : en-tete, publications, informations et preferences."""
import streamlit as st

from frontend.components.avatar import avatar_utilisateur
from frontend.components.badges import puces
from frontend.components.cards import carte, en_tete, titre_carte
from frontend.components.empty_state import etat_vide
from frontend.components.helpers import e, essayer, fdate, fjour, pagination, pills
from frontend.components.post import carte_publication

PAR_PAGE = 5
FONCTIONS = {"employe": "Employé", "ecolier / etudiant": "Écolier / étudiant", "retraite": "Retraité"}


def afficher(moi):
    ok, profil = essayer("profil", user_id=moi["_id"])
    if not ok:
        return
    en_tete("Mon profil", "Vos informations, vos préférences et vos publications.")
    i = profil["infos"]
    with carte("profil_entete"):
        st.markdown('<div class="post-head">%s<div class="who"><div class="name" style="font-size:18px">%s %s</div>'
                    '<div class="meta">@%s - %s (%s) - inscrit le %s</div></div></div>'
                    % (avatar_utilisateur(profil, 64), e(profil["prenom"]), e(profil["nom"]), e(profil["pseudo"]), e(profil["ville"]),
                       e(profil["region"]), fjour(profil["date_inscription"])), unsafe_allow_html=True)
        st.markdown('<div class="post-body">%s</div>' % (e(profil["bio"]) or '<span class="muted">Aucune bio.</span>'), unsafe_allow_html=True)
        st.markdown(puces(["%d ans" % i["age"], "Femme" if i["sexe"] == "F" else "Homme", FONCTIONS.get(i["fonction"], i["fonction"]),
                           "%d amis" % len(profil["amis"]), "%d groupes" % len(profil["groupes_ids"])] +
                          ["Intérêt : " + p for p in profil["preferences"]]), unsafe_allow_html=True)

    section = pills("profil_section", ["Publications", "Paramètres"], "Publications", onglets=True)
    if section == "Publications":
        page = st.session_state.get("profil_page", 1)
        ok, r = essayer("publications_utilisateur", auteur_id=moi["_id"], user_id=moi["_id"], page=page, par_page=PAR_PAGE)
        if ok:
            if not r["items"]:
                etat_vide("file-text", "Vous n'avez encore rien publié", "Vos publications apparaîtront ici.", compact=True)
            for p in r["items"]:
                carte_publication(p, moi, "profil")
            pagination("profil_page", r["total"], PAR_PAGE)
        return

    with carte("profil_infos"):
        titre_carte("Informations personnelles", "Ces informations alimentent les statistiques de la communauté.")
        with st.form("form_profil", border=False):
            bio = st.text_area("Bio", value=profil["bio"], max_chars=280)
            c1, c2 = st.columns(2)
            ville = c1.text_input("Ville", value=profil["ville"])
            age = c2.number_input("Âge", 10, 110, value=i["age"])
            if st.form_submit_button("Enregistrer", type="primary"):
                ok, _ = essayer("maj_profil", succes="Profil mis à jour.", user_id=moi["_id"], bio=bio, ville=ville, age=int(age))
                if ok:
                    st.rerun()
    with carte("profil_prefs"):
        titre_carte("Centres d'intérêt", "Entre 1 et 3 choix : ils déterminent les publications proposées dans votre fil.")
        ok, categories = essayer("categories")
        if ok:
            choix = st.multiselect("Préférences", categories, default=profil["preferences"], max_selections=3, label_visibility="collapsed")
            if st.button("Enregistrer mes préférences", type="primary", key="prefs_ok"):
                ok, _ = essayer("preferences", succes="Préférences enregistrées.", user_id=moi["_id"], preferences=choix)
                if ok:
                    st.session_state["moi"]["preferences"] = choix
                    st.rerun()
    if profil.get("historique_profil"):
        with st.expander("Historique des modifications du profil (anciennes valeurs conservées)"):
            for h in reversed(profil["historique_profil"]):
                st.markdown('<div class="small">%s - %s</div>' % (fdate(h["date"]), e(", ".join("%s = %s" % (k, v) for k, v in h["avant"].items()))), unsafe_allow_html=True)
