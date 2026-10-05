"""buttons.py - Boutons a icone Lucide : la cle encode l'icone, le CSS (styles.py) la dessine."""
import streamlit as st


def bouton_icone(libelle, icone_nom, cle, variante="", **kw):
    """
    Bouton avec icone Lucide devant le libelle. variante : '' (discret) | 'bord' (contour) | 'plein' (bleu).
    L'icone doit figurer dans styles.ICONES_BOUTONS.
    """
    suffixe = "__%s" % variante if variante else ""
    return st.button(libelle, key="ico-%s__%s%s" % (icone_nom, cle, suffixe), **kw)


def popover_icone(libelle, icone_nom, cle, variante="", **kw):
    suffixe = "__%s" % variante if variante else ""
    return st.popover(libelle, key="ico-%s__%s%s" % (icone_nom, cle, suffixe), **kw)
