"""
tests_fonctionnels.py - Teste le CRUD, la messagerie, les notifications, les agregations et la restauration.

Usage :
    python scripts/tests_fonctionnels.py          -> contre la vraie base MongoDB configuree (.env)
    python scripts/tests_fonctionnels.py --mock   -> contre mongomock (aucun serveur requis)
ATTENTION en mode reel : la base est regeneree (donnees initiales) au debut et a la fin.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import agregations  # noqa: E402
import config  # noqa: E402

if "--mock" in sys.argv:
    from scripts import tests_mock
    tests_mock.installer()

import crud  # noqa: E402
import generer_donnees  # noqa: E402
from scripts import exporter, restaurer, valider_donnees  # noqa: E402

RESULTATS = []


def test(libelle, condition):
    RESULTATS.append(condition)
    print("[%s] %s" % ("OK    " if condition else "ECHEC ", libelle))


def leve(exception, fonction, *args, **kw):
    """Renvoie True si la fonction leve bien l'exception attendue (test des cas d'erreur)."""
    try:
        fonction(*args, **kw)
    except exception:
        return True
    except Exception:
        return False
    return False


def main():
    d = config.get_db()
    generer_donnees.generer(base=d, exporter_fichiers=False)
    tmp = Path(tempfile.mkdtemp())
    exporter.exporter(dossier=tmp, base=d)           # etat initial de reference pour le test de restauration
    moi = crud.get_utilisateur_par_pseudo(config.PSEUDO_DEMO)
    mid = moi["_id"]

    print("\n--- Authentification et profil")
    test("connexion valdez_237 / 1234", crud.authentifier("valdez_237", "1234")["_id"] == mid)
    test("pseudo inconnu -> DocumentIntrouvable", leve(crud.DocumentIntrouvable, crud.authentifier, "inconnu_999", "x"))
    test("pseudo vide -> SaisieInvalide", leve(crud.SaisieInvalide, crud.authentifier, "", "x"))
    test("doublon de pseudo -> DoublonErreur", leve(crud.DoublonErreur, crud.inscrire_utilisateur, "valdez_237", "A", "B", "Douala", 20, "M", "employe"))
    p = crud.mettre_a_jour_profil(mid, bio="Nouvelle bio", ville="Yaounde")
    test("mise a jour du profil + historique conserve", p["bio"] == "Nouvelle bio" and len(p["historique_profil"]) == 1)
    test("age invalide refuse", leve(crud.SaisieInvalide, crud.mettre_a_jour_profil, mid, age=5))
    test("confidentialite modifiee", crud.changer_confidentialite(mid, "messages_inconnus", False)["messages_inconnus"] is False)
    test("cle de confidentialite inconnue refusee", leve(crud.SaisieInvalide, crud.changer_confidentialite, mid, "x", True))

    print("\n--- Amis")
    par_anc = crud.lister_amis(mid, "anciennete")
    par_freq = crud.lister_amis(mid, "frequence")
    test("28 amis pour le professeur", len(par_anc) == 28 == len(par_freq))
    test("tri anciennete croissant", [a["depuis"] for a in par_anc] == sorted(a["depuis"] for a in par_anc))
    test("tri frequence decroissant", [a["nb_messages"] for a in par_freq] == sorted((a["nb_messages"] for a in par_freq), reverse=True))
    test("suggestions d'amis (amis d'amis)", len(crud.suggestions_amis(mid)) > 0)

    print("\n--- Publications et fil")
    fil = crud.fil_actualite(mid, 1, 10)
    test("fil pagine de 10 publications, recentes d'abord", len(fil["items"]) == 10 and [x["date"] for x in fil["items"]] == sorted((x["date"] for x in fil["items"]), reverse=True))
    test("chaque publication du fil a une raison d'affichage", all(x["raisons"] for x in fil["items"]))
    test("page 2 differente de la page 1", crud.fil_actualite(mid, 2, 10)["items"][0]["_id"] != fil["items"][0]["_id"])
    fil_pref = crud.fil_actualite(mid, 1, 50, "preferences")
    test("mode preferences : hashtags en lien avec les preferences",
         all(any("preferences" in r for r in x["raisons"]) for x in fil_pref["items"]))
    mes = crud.publications_utilisateur(mid, mid, 1, 50)
    test("10 publications du professeur", mes["total"] == 10)
    pid = crud.creer_publication(mid, "Test de publication", hashtags=["#Test"])
    test("creation d'une publication", crud.get_publication(pid)["hashtags"] == ["test"])
    test("publication vide refusee", leve(crud.SaisieInvalide, crud.creer_publication, mid, "  "))
    crud.modifier_publication(pid, mid, texte="Texte modifie")
    pub = crud.get_publication(pid)
    test("modification + historique", pub["texte"] == "Texte modifie" and pub["historique_modifs"][0]["texte"] == "Test de publication")
    autre = next(a for a in par_anc)["_id"]
    test("modifier la publication d'un autre refuse", leve(crud.ActionInterdite, crud.modifier_publication, pid, autre, texte="x"))
    crud.aimer_publication(pid, autre)
    test("j'aime : compteur incremente et notification creee", crud.get_publication(pid)["compteurs"]["aimes"] == 1
         and d.notifications.count_documents({"source.id": pid, "type": "jaime"}) == 1)
    crud.aimer_publication(pid, autre)
    test("deuxieme j'aime = retrait", crud.get_publication(pid)["compteurs"]["aimes"] == 0)
    test("publications par hashtag", crud.publications_par_hashtag("test", mid)["total"] == 1)
    cid = crud.ajouter_commentaire(pid, autre, "Bravo")
    rid = crud.ajouter_commentaire(pid, mid, "Merci", parent_id=cid)
    test("commentaire + reponse : compteur = 2", crud.get_publication(pid)["compteurs"]["commentaires"] == 2)
    crud.supprimer_commentaire(rid, mid)
    test("reponse effacee : compteur = 1 et archivee", crud.get_publication(pid)["compteurs"]["commentaires"] == 1 and d.commentaires_archives.count_documents({}) == 1)
    test("effacer le commentaire d'un autre refuse", leve(crud.ActionInterdite, crud.supprimer_commentaire, cid, mid))
    crud.ajouter_commentaire(pid, autre, "Deuxieme")
    res = crud.supprimer_publication(pid, mid)
    test("suppression : publication et commentaires archives", d.publications.count_documents({"_id": pid}) == 0
         and d.commentaires.count_documents({"publication_id": pid}) == 0 and res["commentaires_archives"] == 2)
    test("aucun commentaire orphelin", d.commentaires.count_documents({"publication_id": pid}) == 0
         and d.publications_archives.count_documents({"_id": pid}) == 1)
    test("publication supprimee introuvable", leve(crud.DocumentIntrouvable, crud.get_publication, pid))

    print("\n--- Groupes")
    mes_groupes = crud.lister_groupes(mid, seulement_miens=True)
    test("professeur membre de 5 groupes", len(mes_groupes) == 5)
    gid = mes_groupes[0]["_id"]
    det = crud.detail_groupe(gid, mid)
    test("detail : createur et administrateurs", det["createur"] and len(det["admins_profils"]) >= 1)
    test("publications d'un groupe", crud.publications_groupe(gid, mid)["total"] >= 0)
    prive = next(g for g in d.groupes.find({"type": "prive"}) if mid not in [m["user_id"] for m in g["membres"]])
    test("groupe prive : acces refuse aux non-membres", leve(crud.ActionInterdite, crud.publications_groupe, prive["_id"], mid))
    ng = crud.creer_groupe(mid, "Groupe de test", "Description")
    test("createur = admin automatique", crud.get_groupe(ng)["admins"] == [mid])
    refus = d.utilisateurs.find_one({"confidentialite.ajout_groupe_inconnus": False, "_id": {"$ne": mid}, "amis.ami_id": {"$ne": mid}})
    test("ajout refuse si confidentialite l'interdit (inconnu)", leve(crud.ActionInterdite, crud.ajouter_membre, ng, refus["_id"], mid))
    accepte = d.utilisateurs.find_one({"confidentialite.ajout_groupe_inconnus": True, "_id": {"$ne": mid}, "amis.ami_id": {"$ne": mid}})
    crud.ajouter_membre(ng, accepte["_id"], mid)
    test("membre ajoute", len(crud.get_groupe(ng)["membres"]) == 2)
    crud.promouvoir_admin(ng, accepte["_id"], mid)
    test("createur designe un autre administrateur", len(crud.get_groupe(ng)["admins"]) == 2)
    test("seul le createur nomme un admin", leve(crud.ActionInterdite, crud.promouvoir_admin, ng, mid, accepte["_id"]))
    crud.retirer_membre(ng, accepte["_id"], mid)
    test("retrait d'un membre archive l'evenement", len(crud.get_groupe(ng)["membres"]) == 1 and d.groupes_archives.count_documents({}) == 1)
    test("le createur ne peut pas etre retire", leve(crud.ActionInterdite, crud.retirer_membre, ng, mid, mid))

    print("\n--- Messagerie")
    ami = par_freq[0]["_id"]
    avant = crud.lister_amis(mid, "frequence")[0]["nb_messages"]
    crud.envoyer_message_prive(mid, ami, "Salut, test de message")
    test("message prive + compteur de frequence $inc", crud.lister_amis(mid, "frequence")[0]["nb_messages"] == avant + 1)
    conv = crud.conversation(mid, ami)
    test("conversation chronologique", [m["date"] for m in conv["items"]] == sorted(m["date"] for m in conv["items"]))
    inconnu = d.utilisateurs.find_one({"confidentialite.messages_inconnus": False, "_id": {"$ne": mid}, "amis.ami_id": {"$ne": mid}})
    test("message refuse : destinataire n'accepte pas les inconnus", leve(crud.ActionInterdite, crud.envoyer_message_prive, mid, inconnu["_id"], "Coucou"))
    test("message vide refuse", leve(crud.SaisieInvalide, crud.envoyer_message_prive, mid, ami, " "))
    non_lus = crud.messages_non_lus(mid)
    test("messages non lus du professeur", non_lus["total"] > 0)
    test("liste de conversations avec non-lus", len(crud.conversations(mid)) > 0)
    mg = [g for g in crud.lister_groupes(mid, True)][0]["_id"]
    crud.envoyer_message_groupe(mid, mg, "Message de groupe")
    test("message de groupe cree des notifications pour les autres membres",
         d.notifications.count_documents({"source.kind": "message_groupe", "source.groupe_id": mg, "utilisateur_id": {"$ne": mid}}) > 0)
    test("non-membre ne peut pas ecrire", leve(crud.ActionInterdite, crud.envoyer_message_groupe, mid, prive["_id"], "x"))

    print("\n--- Notifications")
    compte = crud.compter_notifications(mid)
    test("notifications non lues presentes (groupes, prives, autres)", compte["groupes"] > 0 and compte["prives"] > 0 and compte["autres"] > 0)
    liste = crud.lister_notifications(mid, "tous", page=1, par_page=50)["items"]
    test("notifications de la plus recente a la plus ancienne", [n["date"] for n in liste] == sorted((n["date"] for n in liste), reverse=True))
    test("categorie groupes", all(n["source"]["kind"] == "message_groupe" for n in crud.lister_notifications(mid, "groupes")["items"]))
    test("categorie prives", all(n["source"]["kind"] == "message_prive" for n in crud.lister_notifications(mid, "prives")["items"]))
    nb = crud.marquer_notifications_lues(mid, "groupes")
    apres = crud.compter_notifications(mid)
    test("marquer la categorie groupes comme lue", nb == compte["groupes"] and apres["groupes"] == 0 and apres["prives"] == compte["prives"])
    nb = crud.marquer_notifications_lues(mid)
    test("marquer toutes les notifications comme lues", crud.compter_notifications(mid)["total"] == 0)
    test("messages correspondants marques lus", crud.messages_non_lus(mid)["total"] == 0)
    test("etat lue/non_lue stocke en base", d.notifications.count_documents({"utilisateur_id": mid, "statut": "non_lue"}) == 0)
    demande = d.notifications.find_one({"type": "demande_ami", "statut": "non_lue"})
    crud.accepter_demande_ami(demande["utilisateur_id"], demande["_id"])
    test("accepter une demande d'ami cree l'amitie des deux cotes",
         any(a["ami_id"] == demande["source"]["de_user_id"] for a in crud.get_utilisateur(demande["utilisateur_id"])["amis"])
         and any(a["ami_id"] == demande["utilisateur_id"] for a in crud.get_utilisateur(demande["source"]["de_user_id"])["amis"]))

    print("\n--- Agregations")
    h = agregations.top_hashtags()
    test("top 10 hashtags ($unwind)", len(h) == 10 and h[0]["utilisations"] >= h[-1]["utilisations"])
    a = agregations.utilisateurs_les_plus_actifs()
    test("utilisateurs les plus actifs", len(a) == 10 and a[0]["activite"] == a[0]["publications"] + a[0]["commentaires"])
    e = agregations.engagement_par_ville()
    test("engagement moyen par ville ($lookup)", len(e) >= 5 and e[0]["engagement_moyen"] >= e[-1]["engagement_moyen"])
    j = agregations.messages_par_jour()
    test("messages par jour sur 7 jours", 1 <= len({x["jour"] for x in j}) <= 7)
    g = agregations.groupes_les_plus_peuples()
    test("groupes les plus peuples avec createur ($lookup)", g[0]["nb_membres"] == 85 and g[0]["createur"])
    s = agregations.stats_globales()
    test("statistiques globales", s["utilisateurs"] == 150 and s["groupes"] == 31 and s["archives"] > 0)
    test("repartition par age ($bucket)", sum(x["n"] for x in agregations.repartition_age()) == 150)
    test("repartitions sexe / fonction / popularite", all(len(f()) >= 2 for f in (agregations.repartition_sexe, agregations.repartition_fonction, agregations.repartition_popularite_groupes)))
    test("preferences et notifications par type", len(agregations.preferences_frequentes()) == 10 and len(agregations.notifications_par_type_et_statut()) >= 4)

    print("\n--- Index")
    noms = set(d.publications.index_information()) | set(d.utilisateurs.index_information())
    test("index unique pseudo et index composes crees", {"uniq_pseudo", "pub_auteur_date", "pub_hashtag_date"} <= noms)

    print("\n--- Restauration (exports -> base)")
    restaurer.restaurer(dossier_json=tmp / "json", base=d)
    test("apres restauration : 10 publications du professeur",
         d.publications.count_documents({"auteur_id": mid}) == 10)
    test("apres restauration : plus d'archives ni de groupe de test", "publications_archives" not in d.list_collection_names()
         and d.groupes.count_documents({}) == 30)
    test("apres restauration : notifications initiales revenues", d.notifications.count_documents({}) == 3050
         and crud.compter_notifications(mid)["total"] > 0)
    rapport = valider_donnees.valider(d)
    test("apres restauration : base 100 % coherente", rapport.echecs == 0)

    echecs = RESULTATS.count(False)
    print("\n%d tests, %d echec(s)" % (len(RESULTATS), echecs))
    return echecs


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
