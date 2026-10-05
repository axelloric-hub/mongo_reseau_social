"""badges.py - Badges d'etat, compteurs et puces (couleur = information, jamais decoration)."""
from frontend.components.helpers import e


def badge(texte, ton="neutre", point=False):
    """ton : neutre | primaire | succes | danger | alerte."""
    return '<span class="badge %s">%s%s</span>' % (ton, '<span class="point"></span>' if point else "", e(texte))


def badge_lu(non_lue):
    """Etat d'une notification : 'Pas encore vue' (vert, avec point) ou 'Lue' (neutre)."""
    return badge("Pas encore vue", "succes", point=True) if non_lue else badge("Lue", "neutre")


def compteur(n, ton=""):
    return '<span class="compteur %s">%d</span>' % (ton, n) if n else ""


def puces(valeurs, classe="chip"):
    return '<div class="chips">%s</div>' % "".join('<span class="%s">%s</span>' % (classe, e(v)) for v in valeurs)
