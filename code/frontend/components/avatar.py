"""avatar.py - Avatar a initiales, couleur stable par utilisateur (teintes douces, jamais de violet)."""
from frontend.components.helpers import e

# (fond, texte) : palette sobre alignee sur le design system
TEINTES = [("#DBEAFE", "#1D4ED8"), ("#CCFBF1", "#0F766E"), ("#FEF3C7", "#B45309"), ("#FCE7F3", "#BE185D"),
           ("#DCFCE7", "#15803D"), ("#E2E8F0", "#334155"), ("#FFEDD5", "#C2410C"), ("#CFFAFE", "#0E7490")]


def avatar(prenom, nom, taille=40, graine=None):
    """Renvoie le HTML d'un avatar rond. 'graine' (ex. le pseudo) fixe la couleur."""
    initiales = ((prenom or "?")[:1] + (nom or "")[:1]).upper()
    cle = graine if graine is not None else "%s%s" % (prenom, nom)
    fond, texte = TEINTES[sum(ord(c) for c in str(cle)) % len(TEINTES)]
    return ('<span class="avatar" style="width:%dpx;height:%dpx;font-size:%dpx;background:%s;color:%s">%s</span>'
            % (taille, taille, max(11, round(taille * 0.38)), fond, texte, e(initiales)))


def avatar_utilisateur(u, taille=40):
    if not u:
        return avatar("?", "", taille)
    return avatar(u.get("prenom"), u.get("nom"), taille, u.get("pseudo"))
