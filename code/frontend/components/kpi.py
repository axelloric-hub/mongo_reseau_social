"""kpi.py - Carte d'indicateur : label, valeur, icone discrete et note (calculee a partir de donnees reelles)."""
import streamlit as st

from frontend.components.helpers import e
from frontend.components.icons import icone


def format_nombre(n):
    return format(n, ",").replace(",", "\u202f")


def kpi(label, valeur, icone_nom, note="", alerte=False):
    st.markdown('<div class="kpi%s"><div class="haut"><span class="label">%s</span><span class="icone">%s</span></div>'
                '<div class="valeur">%s</div>%s</div>'
                % (" alerte" if alerte else "", e(label), icone(icone_nom, 17), format_nombre(valeur),
                   '<div class="note">%s</div>' % e(note).replace(".", ",") if note else '<div class="note">&nbsp;</div>'), unsafe_allow_html=True)
