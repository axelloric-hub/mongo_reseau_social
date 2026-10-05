"""empty_state.py - Etats vides : jamais d'ecran blanc, toujours une explication et une direction."""
import streamlit as st

from frontend.components.helpers import e
from frontend.components.icons import icone


def etat_vide(icone_nom, titre, texte="", compact=False, hauteur=None):
    """Zone centree : pastille d'icone, titre, texte. 'compact' = version blanche pour les listes vides."""
    style = ' style="min-height:%dpx"' % hauteur if hauteur else ""
    st.markdown('<div class="empty%s"%s><span class="pastille">%s</span><div class="titre">%s</div>%s</div>'
                % (" compact" if compact else "", style, icone(icone_nom, 26), e(titre), '<div class="texte">%s</div>' % e(texte) if texte else ""),
                unsafe_allow_html=True)
