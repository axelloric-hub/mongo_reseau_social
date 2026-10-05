"""
main.py - Menu principal en console : appelle crud.py et agregations.py.

Ce fichier existe parce que le PDF impose un menu qui "appelle tout le reste". Il permet de
demontrer chaque operation sans interface graphique (utile pendant la soutenance ou la video).
Fonctionnement : connexion avec un pseudo, puis menu a numeros ; chaque choix appelle une
fonction de crud.py ou agregations.py et affiche le resultat. Les erreurs metier sont attrapees
et affichees en clair (document introuvable, doublon, saisie invalide).
Usage : python main.py
"""
import agregations
import config
import crud


def afficher_tableau(lignes, colonnes):
    """Affiche une liste de dictionnaires en colonnes alignees."""
    if not lignes:
        print("  (aucun resultat)")
        return
    largeurs = [max(len(c), *(len(str(l.get(c, ""))) for l in lignes)) for c in colonnes]
    print("  " + "  ".join(c.ljust(w) for c, w in zip(colonnes, largeurs)))
    print("  " + "  ".join("-" * w for w in largeurs))
    for l in lignes:
        print("  " + "  ".join(str(l.get(c, "")).ljust(w) for c, w in zip(colonnes, largeurs)))


def lire(invite, defaut=""):
    saisie = input(invite).strip()
    return saisie or defaut


def date_courte(d):
    return d.strftime("%d/%m/%Y %H:%M") if d else ""


# --- Actions du menu ------------------------------------------------------------------------


def action_fil(moi):
    mode = lire("Mode (pour_moi / amis / preferences) [pour_moi] : ", "pour_moi")
    page = int(lire("Page [1] : ", "1"))
    r = crud.fil_actualite(moi["_id"], page, 5, mode)
    print("  %d publications au total, page %d" % (r["total"], r["page"]))
    for p in r["items"]:
        auteur = p["auteur"]["pseudo"] if p["auteur"] else "?"
        print("  - [%s] @%s : %s  #%s  (%d j'aime, %d com.)" % (date_courte(p["date"]), auteur, p["texte"], " #".join(p["hashtags"]) or "-",
                                                             p["compteurs"]["aimes"], p["compteurs"]["commentaires"]))
        print("      raison : " + " ; ".join(p["raisons"]))


def action_amis(moi):
    tri = lire("Tri (anciennete / frequence) [anciennete] : ", "anciennete")
    amis = crud.lister_amis(moi["_id"], tri)
    for a in amis:
        a["depuis"] = date_courte(a["depuis"])
    afficher_tableau(amis[:20], ["pseudo", "prenom", "nom", "ville", "depuis", "nb_messages"])


def action_groupe(moi):
    afficher_tableau(crud.lister_groupes(moi["_id"], True), ["nom", "type", "popularite", "nb_membres"])
    code = lire("Code du groupe pour voir ses publications (ex. GRP-01, vide = passer) : ")
    if code:
        g = config.get_db().groupes.find_one({"code": code.upper()})
        if not g:
            raise crud.DocumentIntrouvable("Groupe introuvable.")
        for p in crud.publications_groupe(g["_id"], moi["_id"], 1, 5)["items"]:
            print("  - @%s : %s" % (p["auteur"]["pseudo"], p["texte"]))


def action_non_lus(moi):
    r = crud.messages_non_lus(moi["_id"], 1, 10)
    print("  %d message(s) non lu(s) au total" % r["total"])
    for m in r["items"]:
        print("  - [%s] %s de @%s : %s" % (date_courte(m["date"]), m["type"], m["expediteur"]["pseudo"], m["contenu"]))


def action_notifications(moi):
    c = crud.compter_notifications(moi["_id"])
    print("  Non lues : %d (groupes %d, prives %d, autres %d)" % (c["total"], c["groupes"], c["prives"], c["autres"]))
    for n in crud.lister_notifications(moi["_id"], "tous", False, 1, 8)["items"]:
        de = n["de"]["pseudo"] if n["de"] else "?"
        print("  - [%s] %-8s de @%s  %s : %s" % (date_courte(n["date"]), n["statut"], de, n["type"], n["apercu"][:50]))
    if lire("Marquer toutes comme lues ? (o/n) [n] : ", "n").lower() == "o":
        print("  %d notification(s) marquee(s) comme lue(s)." % crud.marquer_notifications_lues(moi["_id"]))


def action_hashtag(moi):
    tag = lire("Hashtag (ex. nature) : ")
    r = crud.publications_par_hashtag(tag, moi["_id"], 1, 5)
    print("  %d publication(s) pour #%s" % (r["total"], tag.lstrip("#")))
    for p in r["items"]:
        print("  - @%s : %s" % (p["auteur"]["pseudo"], p["texte"]))


def action_publier(moi):
    texte = lire("Texte : ")
    tags = lire("Hashtags separes par des espaces : ").split()
    pid = crud.creer_publication(moi["_id"], texte, hashtags=tags)
    print("  Publication creee : %s" % pid)
    if lire("La modifier ? (o/n) [n] : ", "n").lower() == "o":
        crud.modifier_publication(pid, moi["_id"], texte=lire("Nouveau texte : "))
        print("  Modifiee (ancienne version conservee dans historique_modifs).")
    if lire("La supprimer (archiver) ? (o/n) [n] : ", "n").lower() == "o":
        print("  Archivee :", crud.supprimer_publication(pid, moi["_id"]))


def action_profil(moi):
    bio = lire("Nouvelle bio (vide = inchangee) : ")
    ville = lire("Nouvelle ville (vide = inchangee) : ")
    crud.mettre_a_jour_profil(moi["_id"], bio=bio or None, ville=ville or None)
    print("  Profil mis a jour.")


def action_confidentialite(moi):
    cle = lire("Parametre (messages_inconnus / ajout_groupe_inconnus) : ")
    valeur = lire("Autoriser ? (o/n) : ").lower() == "o"
    print("  ", crud.changer_confidentialite(moi["_id"], cle, valeur))


def action_message(moi):
    pseudo = lire("Pseudo du destinataire : ")
    dest = crud.get_utilisateur_par_pseudo(pseudo)
    crud.envoyer_message_prive(moi["_id"], dest["_id"], lire("Message : "))
    print("  Message envoye.")
    for m in crud.conversation(moi["_id"], dest["_id"], 1, 5)["items"]:
        print("  [%s] %s : %s" % (date_courte(m["date"]), "moi" if m["expediteur_id"] == moi["_id"] else pseudo, m["contenu"]))


def menu_agregations():
    print("  1. Top 10 hashtags   2. Utilisateurs actifs   3. Engagement par ville")
    print("  4. Messages par jour 5. Groupes les plus peuples   6. Statistiques globales")
    choix = lire("Agregation : ")
    if choix == "1":
        afficher_tableau(agregations.top_hashtags(), ["hashtag", "utilisations"])
    elif choix == "2":
        afficher_tableau(agregations.utilisateurs_les_plus_actifs(), ["pseudo", "publications", "commentaires", "activite"])
    elif choix == "3":
        afficher_tableau(agregations.engagement_par_ville(), ["ville", "engagement_moyen", "publications"])
    elif choix == "4":
        afficher_tableau(agregations.messages_par_jour(), ["jour", "type", "messages"])
    elif choix == "5":
        afficher_tableau(agregations.groupes_les_plus_peuples(), ["groupe", "nb_membres", "popularite", "createur"])
    elif choix == "6":
        for k, v in agregations.stats_globales().items():
            print("  %-24s %s" % (k, v))


MENU = [
    ("Fil d'actualite (pagine)", action_fil), ("Mes amis (tri)", action_amis), ("Mes groupes et leurs publications", action_groupe),
    ("Messages non lus", action_non_lus), ("Notifications (lire / marquer lues)", action_notifications),
    ("Publications par hashtag", action_hashtag), ("Publier / modifier / supprimer", action_publier),
    ("Mettre a jour mon profil", action_profil), ("Changer la confidentialite", action_confidentialite),
    ("Envoyer un message prive", action_message), ("Agregations et statistiques", lambda moi: menu_agregations()),
]


def main():
    print("=== Reseau social - Console de demonstration ===")
    try:
        moi = crud.authentifier(lire("Pseudo [%s] : " % config.PSEUDO_DEMO, config.PSEUDO_DEMO),
                                lire("Mot de passe [%s] : " % config.MOT_DE_PASSE_DEMO, config.MOT_DE_PASSE_DEMO))
    except crud.ErreurMetier as e:
        print("Connexion impossible :", e)
        return
    print("Connecte : %s %s (@%s)" % (moi["prenom"], moi["nom"], moi["pseudo"]))
    while True:
        print("\n--- Menu ---")
        for i, (libelle, _) in enumerate(MENU, 1):
            print("  %2d. %s" % (i, libelle))
        print("   0. Quitter")
        choix = lire("Votre choix : ")
        if choix == "0":
            break
        if not choix.isdigit() or not 1 <= int(choix) <= len(MENU):
            print("Choix invalide.")
            continue
        try:
            MENU[int(choix) - 1][1](moi)
        except crud.ErreurMetier as e:       # erreurs prevues : message clair, le programme continue
            print("Erreur :", e)
        except ValueError:
            print("Erreur : saisie numerique attendue.")


if __name__ == "__main__":
    main()
