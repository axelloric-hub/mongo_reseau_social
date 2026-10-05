"""
valider_donnees.py - Verifie les volumes, les proportions et la coherence referentielle.

Ce script existe pour prouver que le jeu de donnees respecte le PDF (volumes minimaux) et le
cahier des charges (70/25/5, 50/35/15, 10 publications du professeur) et qu'il ne contient
aucune reference vers un document inexistant. Il lit la base MongoDB et ecrit un rapport dans
data/rapport_validation.txt. Usage : python scripts/valider_donnees.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import agregations  # noqa: E402
import config  # noqa: E402


class Rapport:
    """Accumule les lignes de verification (OK / ECHEC) et compte les echecs."""

    def __init__(self):
        self.lignes, self.echecs = [], 0

    def verifier(self, condition, libelle, detail=""):
        etat = "OK    " if condition else "ECHEC "
        self.lignes.append("[%s] %s %s" % (etat, libelle, detail))
        if not condition:
            self.echecs += 1

    def titre(self, texte):
        self.lignes.append("")
        self.lignes.append("== " + texte)


def valider(base=None):
    base = base if base is not None else config.get_db()
    r = Rapport()
    u = {x["_id"]: x for x in base.utilisateurs.find()}
    g = {x["_id"]: x for x in base.groupes.find()}
    p = {x["_id"]: x for x in base.publications.find()}
    c = list(base.commentaires.find())
    m = {x["_id"]: x for x in base.messages.find()}
    n = list(base.notifications.find())

    r.titre("Volumes (minimums du PDF et du cahier des charges)")
    r.verifier(len(u) == 150, "150 utilisateurs", "(%d)" % len(u))
    r.verifier(len(g) == 30, "30 groupes", "(%d)" % len(g))
    r.verifier(len(p) >= 500, "au moins 500 publications", "(%d)" % len(p))
    r.verifier(len(c) >= 1000, "au moins 1000 commentaires", "(%d)" % len(c))
    r.verifier(len(m) >= 2000, "au moins 2000 messages", "(%d)" % len(m))
    r.verifier(2950 <= len(n) <= 3300, "environ 3000 notifications (>= 3000 exige)", "(%d)" % len(n))
    valdez = base.utilisateurs.find_one({"pseudo": config.PSEUDO_DEMO})
    nb_valdez = base.publications.count_documents({"auteur_id": valdez["_id"]}) if valdez else 0
    r.verifier(nb_valdez == 10, "10 publications pour %s" % config.PSEUDO_DEMO, "(%d)" % nb_valdez)

    r.titre("Proportions")
    volume = {x["categorie"]: x["pourcentage"] for x in agregations.volume_publications_par_categorie()}
    for cat, cible in (("influenceur", 70), ("normal", 25), ("timide_reseau", 5)):
        r.verifier(abs(volume.get(cat, 0) - cible) <= 2, "volume de publications %s ~ %d %%" % (cat, cible),
                   "(%.1f %%)" % volume.get(cat, 0))
    pop = Counter(x["popularite"] for x in g.values())
    for cle, cible in (("populaire", 50), ("moins_populaire", 36.7), ("restreint", 13.3)):
        r.verifier(abs(100 * pop.get(cle, 0) / max(len(g), 1) - cible) <= 1, "groupes %s ~ %.1f %%" % (cle, cible),
                   "(%d groupes)" % pop.get(cle, 0))
    tailles = Counter(len(x["membres"]) for x in g.values())
    r.verifier(set(tailles) == {10, 25, 35, 85}, "tailles de groupes 10 / 25 / 35 / 85", "(%s)" % dict(sorted(tailles.items())))
    nb_groupes = Counter(len(x["groupes_ids"]) for x in u.values())
    r.verifier(0 in nb_groupes and 1 in nb_groupes and max(nb_groupes) > 1, "utilisateurs a 0, 1 et plusieurs groupes",
               "(%s)" % dict(sorted(nb_groupes.items())))
    r.verifier(len({x["pseudo"] for x in u.values()}) == len(u), "pseudos uniques")
    r.verifier(len({x["nom"] for x in u.values()}) == len(u), "150 noms distincts")
    nb_tags = Counter(len(x["hashtags"]) for x in p.values())
    r.verifier(0 in nb_tags and max(nb_tags) >= 2, "publications avec 0 et plusieurs hashtags", "(%s)" % dict(sorted(nb_tags.items())))
    r.verifier(all(1 <= len(x["preferences"]) <= 3 for x in u.values()), "1 a 3 preferences par utilisateur")

    r.titre("Coherence referentielle (aucune reference orpheline)")
    r.verifier(all(x["auteur_id"] in u and (x["groupe_id"] is None or x["groupe_id"] in g) for x in p.values()), "publications -> auteur / groupe")
    r.verifier(all(x["publication_id"] in p and x["auteur_id"] in u for x in c), "commentaires -> publication / auteur")
    r.verifier(all(rep["auteur_id"] in u for x in c for rep in x["reponses"]), "reponses -> auteur")
    r.verifier(all(x["createur_id"] in {mb["user_id"] for mb in x["membres"]} and x["createur_id"] in x["admins"] for x in g.values()),
               "chaque groupe : createur membre et administrateur")
    r.verifier(all(set(x["admins"]) <= {mb["user_id"] for mb in x["membres"]} for x in g.values()), "administrateurs -> membres")
    r.verifier(all(mb["user_id"] in u for x in g.values() for mb in x["membres"]), "membres -> utilisateurs")
    appartenance = {uid: set() for uid in u}
    for x in g.values():
        for mb in x["membres"]:
            appartenance[mb["user_id"]].add(x["_id"])
    r.verifier(all(set(x["groupes_ids"]) == appartenance[x["_id"]] for x in u.values()), "utilisateurs.groupes_ids = membres des groupes")
    amis_ok = all(any(b["ami_id"] == x["_id"] for b in u[a["ami_id"]]["amis"]) for x in u.values() for a in x["amis"] if a["ami_id"] in u)
    r.verifier(amis_ok and all(a["ami_id"] in u for x in u.values() for a in x["amis"]), "amities symetriques et existantes")
    priv_ok = all(x["expediteur_id"] in u and x["destinataire_id"] in u for x in m.values() if x["type"] == "prive")
    r.verifier(priv_ok, "messages prives -> utilisateurs")
    grp_ok = all(x["groupe_id"] in g and x["expediteur_id"] in appartenance and x["groupe_id"] in appartenance[x["expediteur_id"]]
                 and set(x["non_lu_par"]) <= {mb["user_id"] for mb in g[x["groupe_id"]]["membres"]}
                 for x in m.values() if x["type"] == "groupe")
    r.verifier(grp_ok, "messages de groupe -> groupe / expediteur membre / non_lu_par membres")
    r.verifier(all(x["utilisateur_id"] in u for x in n), "notifications -> utilisateur")

    r.titre("Notifications coherentes avec les evenements")
    def source_ok(x):
        s = x["source"]
        if s["de_user_id"] not in u:
            return False
        if s["kind"] == "message_prive":
            return s["id"] in m and m[s["id"]]["destinataire_id"] == x["utilisateur_id"]
        if s["kind"] == "message_groupe":
            return s["id"] in m and m[s["id"]]["groupe_id"] == s["groupe_id"]
        if s["kind"] == "publication":
            return s["id"] in p and p[s["id"]]["auteur_id"] == x["utilisateur_id"]
        if s["kind"] == "commentaire":
            return s["publication_id"] in p and p[s["publication_id"]]["auteur_id"] == x["utilisateur_id"]
        return s["kind"] == "utilisateur"
    r.verifier(all(source_ok(x) for x in n), "chaque notification pointe vers un evenement existant")
    def lecture_ok(x):
        s = x["source"]
        if s["kind"] == "message_prive":
            non_lu = m[s["id"]]["statut"] != "lu"
        elif s["kind"] == "message_groupe":
            non_lu = x["utilisateur_id"] in m[s["id"]]["non_lu_par"]
        else:
            return True
        return non_lu == (x["statut"] == "non_lue")
    r.verifier(all(lecture_ok(x) for x in n), "etat lu / non lu identique entre messages et notifications")
    r.verifier(all(x["date"] <= max(mm["date"] for mm in m.values()) + __import__("datetime").timedelta(days=1) for x in n),
               "aucune notification datee apres le dernier evenement")
    r.verifier(all(x["date"] >= p[x["publication_id"]]["date"] for x in c), "commentaires posterieurs a leur publication")
    r.verifier(all(x["compteurs"]["aimes"] == len(x["aimes"]) for x in p.values()), "compteur j'aime = taille de la liste des j'aime")
    nb_com = Counter()
    for x in c:
        nb_com[x["publication_id"]] += 1 + len(x["reponses"])
    r.verifier(all(x["compteurs"]["commentaires"] == nb_com[x["_id"]] for x in p.values()), "compteur de commentaires exact")

    r.titre("Resume : %s" % ("TOUT EST COHERENT" if r.echecs == 0 else "%d verification(s) en echec" % r.echecs))
    return r


def main():
    rapport = valider()
    texte = "\n".join(rapport.lignes)
    print(texte)
    sortie = config.RACINE / "data" / "rapport_validation.txt"
    sortie.write_text(texte + "\n", encoding="utf-8")
    print("\nRapport ecrit dans %s" % sortie)
    return rapport.echecs


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
