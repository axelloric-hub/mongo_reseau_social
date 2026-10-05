"""cards.py - Cartes et en-tetes de page."""
import streamlit as st

from frontend.components.helpers import e


def carte(cle, variante=""):
    """
    Conteneur affiche comme une carte blanche (bordure 1px, rayon 16px, ombre legere).
    variante : '' | 'flat' (sans ombre) | 'nonlue' (liseré bleu) | 'info' (fond bleute) | 'dim'.
    La cle est obligatoire et doit etre unique : le CSS reconnait le prefixe 'card_'.
    """
    prefixe = "card_%s_" % variante if variante else "card_"
    return st.container(key=prefixe + str(cle))


def en_tete(titre, sous_titre=""):
    """Titre de page (32 px, 700) et sous-titre secondaire."""
    st.markdown('<div class="page-header"><h1 class="page-title">%s</h1>%s</div>'
                % (e(titre), '<div class="page-subtitle">%s</div>' % e(sous_titre) if sous_titre else ""), unsafe_allow_html=True)


def titre_section(texte):
    st.markdown('<div class="section-title">%s</div>' % e(texte), unsafe_allow_html=True)


def titre_carte(titre, texte=""):
    st.markdown('<div class="card-title">%s</div>%s' % (e(titre), '<div class="card-text">%s</div>' % e(texte) if texte else ""), unsafe_allow_html=True)
