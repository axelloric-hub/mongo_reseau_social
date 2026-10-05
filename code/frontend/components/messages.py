"""messages.py - Composants de messagerie : ligne de conversation cliquable et bulles de discussion."""
import streamlit as st

from frontend.components.avatar import avatar, avatar_utilisateur
from frontend.components.badges import compteur
from frontend.components.helpers import e, fdate, fheure
from frontend.components.icons import icone

STATUTS = {"envoye": "Envoyé", "recu": "Reçu", "lu": "Lu"}


def ligne_conversation(cle, actif, avatar_html, nom, apercu, heure, non_lus=0):
    """
    Ligne de la liste : avatar, nom, dernier message, heure, badge de non-lus.
    Technique : le HTML est affiche tel quel et un st.button invisible (convbtn_*) le recouvre,
    ce qui rend toute la ligne cliquable. Renvoie True si la ligne a ete cliquee.
    """
    with st.container(key=("conv_actif_%s" if actif else "conv_%s") % cle):
        st.markdown('<div class="conv-row%s">%s<div class="corps"><div class="haut"><span class="nom">%s</span><span class="heure">%s</span></div>'
                    '<div class="bas"><span class="apercu">%s</span>%s</div></div></div>'
                    % (" nonlu" if non_lus else "", avatar_html, e(nom), e(heure), e(apercu), compteur(non_lus, "primaire")), unsafe_allow_html=True)
        return st.button("Ouvrir la conversation avec %s" % nom, key="convbtn_%s" % cle)


def en_tete_conversation(avatar_html, nom, sous_titre):
    st.markdown('<div class="thread-head">%s<div><div class="nom">%s</div><div class="small">%s</div></div></div>'
                % (avatar_html, e(nom), e(sous_titre)), unsafe_allow_html=True)


def bulles_prives(messages, moi):
    html = ['<div class="fil-bulles">']          # column-reverse : on emet du plus recent au plus ancien, l'affichage reste chronologique
    for m in reversed(messages):
        mien = m["expediteur_id"] == moi["_id"]
        nouveau = (not mien) and m["statut"] != "lu"
        pied = fheure(m["date"]) + " - " + fdate(m["date"]).split(",")[0] + ((" - " + STATUTS.get(m["statut"], m["statut"])) if mien else "")
        if nouveau:
            pied += ' - <span class="nouveau">Nouveau</span>'
        html.append('<div class="bulle%s">%s<div class="quand">%s</div></div>' % (" moi" if mien else "", e(m["contenu"]), pied))
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def bulles_groupe(messages, moi):
    html = ['<div class="fil-bulles">']
    for m in reversed(messages):
        mien = m["expediteur_id"] == moi["_id"]
        nouveau = moi["_id"] in m.get("non_lu_par", [])
        auteur = m.get("expediteur") or {}
        pied = fheure(m["date"]) + " - " + fdate(m["date"]).split(",")[0] + (' - <span class="nouveau">Nouveau</span>' if nouveau else "")
        html.append('<div class="bulle%s">%s%s<div class="quand">%s</div></div>'
                    % (" moi" if mien else "", "" if mien else '<div class="qui">@%s</div>' % e(auteur.get("pseudo", "?")), e(m["contenu"]), pied))
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)
