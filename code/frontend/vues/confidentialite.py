"""
confidentialite.py - Page 'Confidentialite' : permissions enregistrees automatiquement dans MongoDB.

Les parametres vivent dans utilisateurs.confidentialite (sous-document). Ajouter un parametre =
ajouter une entree dans PARAMETRES ici et dans crud._CLES_CONFIDENTIALITE. Les rubriques non
encore gerees par le backend sont listees 'A venir' (desactivees) : aucune fausse option.
"""
import streamlit as st

from frontend.api_client import ApiErreur, appel
from frontend.components.badges import badge
from frontend.components.cards import carte, en_tete, titre_carte
from frontend.components.helpers import e, essayer, fdate, flash
from frontend.components.icons import icone

# (cle, rubrique, titre, aide si active, aide si desactive)
PARAMETRES = [
    ("messages_inconnus", "Qui peut me contacter ?", "Accepter les messages des personnes qui ne sont pas mes amis",
     "Activé : n'importe quel membre peut vous écrire en privé.", "Désactivé : seuls vos amis peuvent vous écrire en privé."),
    ("ajout_groupe_inconnus", "Ajout à un groupe", "Autoriser un inconnu à m'ajouter à un groupe",
     "Activé : n'importe quel membre peut vous ajouter à un groupe.", "Désactivé : seuls vos amis peuvent vous ajouter à un groupe."),
]
A_VENIR = ["Visibilité du profil", "Visibilité de mes activités", "Préférences de notification", "Données personnelles"]


def _enregistrer(user_id, cle):
    """Callback du toggle : enregistre tout de suite la valeur dans MongoDB (pas de bouton Enregistrer)."""
    valeur = st.session_state["conf_" + cle]
    try:
        appel("confidentialite", user_id=user_id, cle=cle, valeur=valeur)
        flash("Paramètre enregistré.")
    except ApiErreur as err:
        flash(str(err), "erreur")


def afficher(moi):
    en_tete("Confidentialité", "Gérez qui peut vous contacter et interagir avec vous sur la plateforme.")
    ok, profil = essayer("profil", user_id=moi["_id"])
    if not ok:
        return
    for cle, rubrique, titre, aide_on, aide_off in PARAMETRES:
        with carte("reglage_" + cle):
            gauche, droite = st.columns([6, 1], vertical_alignment="center")
            if "conf_" + cle not in st.session_state:
                st.session_state["conf_" + cle] = profil["confidentialite"].get(cle, True)
            aide = aide_on if st.session_state["conf_" + cle] else aide_off
            gauche.markdown('<div class="small" style="font-weight:600">%s</div><div class="reglage-titre">%s</div><div class="reglage-texte">%s</div>'
                            % (e(rubrique), e(titre), e(aide)), unsafe_allow_html=True)
            droite.toggle(titre, key="conf_" + cle, on_change=_enregistrer, args=(moi["_id"], cle), label_visibility="collapsed")
    with carte("info_test", "info"):
        st.markdown('<div class="post-head"><span class="avatar" style="width:40px;height:40px;background:#3B82F6;color:#fff">%s</span>'
                    '<div class="who"><div class="card-title">Comment tester</div><div class="card-text">Les modifications sont enregistrées automatiquement, sans étape supplémentaire. '
                    'Désactivez les messages des inconnus : dans la base, <code>confidentialite.messages_inconnus</code> passe à <code>false</code> '
                    'et l\'envoi d\'un inconnu est refusé par <code>crud.envoyer_message_prive</code>.</div></div></div>' % icone("lightbulb", 20), unsafe_allow_html=True)
    with carte("avenir", "dim"):
        titre_carte("Autres paramètres", "Pas encore pris en charge par le backend : ils seront ajoutés sans changer la structure.")
        for nom in A_VENIR:
            st.markdown('<div class="a-venir"><span>%s</span>%s</div>' % (e(nom), badge("À venir", "neutre")), unsafe_allow_html=True)
