"""
generer_donnees.py - Genere et insere le jeu de donnees artificiel mais coherent du reseau social.

Ce script est execute UNE SEULE FOIS pour initialiser la base. Il existe pour fournir un volume
realiste (150 utilisateurs, 30 groupes, ~600 publications, ~1300 commentaires, ~2500 messages,
~3050 notifications) respectant les proportions du cahier des charges. Il fonctionne par etapes :
les entites independantes d'abord (utilisateurs, groupes), puis celles qui les referencent
(publications, commentaires, messages), enfin les notifications derivees des evenements.
Les identifiants sont deterministes (graine fixe) : memes donnees a chaque generation.
Usage : python generer_donnees.py [--sans-export]
"""
import random
import sys
import unicodedata
from datetime import datetime, timedelta

from bson import ObjectId

import config
import crud
from data.catalogue_images import HASHTAGS, IMAGES, TONS, construire_url
from data.noms_camerounais import NOMS, POIDS_VILLES, PRENOMS_F, PRENOMS_M, VILLES
from data.textes import BIOS, COMMENTAIRES_GENERIQUES, GROUPES, MESSAGES_GROUPE, MESSAGES_PRIVES

# --- Parametres du jeu de donnees (tout est modifiable ici) -------------------------------------
REF = datetime(2026, 10, 4, 20, 0, 0)    # "maintenant" fige de la base initiale
NB_UTILISATEURS = 150
NB_INFLUENCEURS, NB_NORMAUX = 15, 60      # le reste (75) sont des timides
VOLUME_PUBLICATIONS = {"influenceur": 420, "normal": 150, "timide_reseau": 30}   # 70 / 25 / 5 %
NB_PUBLICATIONS_VALDEZ = 10
NB_COMMENTAIRES = 1150                    # commentaires de premier niveau (+ reponses imbriquees)
NB_MESSAGES_PRIVES = 1500
NB_MESSAGES_GROUPE = 950
NB_NOTIFICATIONS = 3050
# Groupes : (taille, popularite, type) -> 15 populaires, 11 moins populaires, 4 restreints (prives)
SPEC_GROUPES = ([(85, "populaire", "public")] * 4 + [(35, "populaire", "public")] * 8 + [(25, "populaire", "public")] * 3
                + [(25, "moins_populaire", "public")] * 5 + [(10, "moins_populaire", "public")] * 6
                + [(10, "restreint", "prive")] * 4)

rng = random.Random(config.SEED)

# Prefixes d'ObjectId : rend les identifiants deterministes et lisibles dans Compass
PREFIXES = {"utilisateurs": 1, "groupes": 2, "publications": 3, "commentaires": 4, "messages": 5, "notifications": 6}


def nouvel_id(collection, numero):
    return ObjectId("%04x%020x" % (PREFIXES[collection], numero))


def date_entre(debut, fin):
    """Date aleatoire (a la minute) entre deux dates."""
    secondes = int((fin - debut).total_seconds())
    return (debut + timedelta(seconds=rng.randint(0, max(secondes, 0)))).replace(second=0, microsecond=0)


def sans_accent(texte):
    return unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode().lower().replace(" ", "")


def choisir_pondere(elements, poids, k):
    """Tirage sans remise pondere (algorithme d'Efraimidis-Spirakis) : cle = random ** (1 / poids)."""
    cles = sorted(((rng.random() ** (1.0 / max(poids[e], 1e-9)), e) for e in elements), reverse=True)
    return [e for _, e in cles[:k]]


# ---------------------------------------------------------------------------
# 1. Utilisateurs
# ---------------------------------------------------------------------------


def generer_utilisateurs():
    """
    Cree les 150 utilisateurs : noms camerounais distincts, pseudos uniques (suffixes _237, _enspd,
    _dla), informations personnelles coherentes (age selon la fonction) et categorie d'activite.
    """
    assert len(set(NOMS)) >= NB_UTILISATEURS, "Il faut au moins 150 noms distincts."
    noms = NOMS[:NB_UTILISATEURS]
    indices = list(range(1, NB_UTILISATEURS))
    rng.shuffle(indices)
    categories = {0: "normal"}                       # le compte du professeur est un utilisateur normal
    for i in indices[:NB_INFLUENCEURS]:
        categories[i] = "influenceur"
    for i in indices[NB_INFLUENCEURS:NB_INFLUENCEURS + NB_NORMAUX - 1]:
        categories[i] = "normal"
    for i in indices[NB_INFLUENCEURS + NB_NORMAUX - 1:]:
        categories[i] = "timide_reseau"

    villes = list(VILLES)
    pseudos, utilisateurs = set(), []
    for i, nom in enumerate(noms):
        if i == 0:
            prenom, sexe, pseudo, fonction, age, ville = "Valdez", "M", config.PSEUDO_DEMO, "employe", 38, "Douala"
        else:
            sexe = rng.choice(["F", "M"])
            prenom = rng.choice(PRENOMS_F if sexe == "F" else PRENOMS_M)
            fonction = rng.choices(["ecolier / etudiant", "employe", "retraite"], [40, 48, 12])[0]
            age = {"ecolier / etudiant": lambda: rng.randint(14, 27), "employe": lambda: rng.randint(22, 58),
                   "retraite": lambda: rng.randint(58, 80)}[fonction]()
            ville = rng.choices(villes, POIDS_VILLES)[0]
            base = sans_accent(nom)
            racine = base if len(base) <= 5 else base[:rng.choice([3, 4, len(base)])]
            while True:
                pseudo = racine + rng.choice(["_237", "_enspd", "_dla"])
                if pseudo not in pseudos:
                    break
                racine = base
                if pseudo in pseudos:
                    pseudo = base + "_%d" % rng.randint(10, 99)
                    if pseudo not in pseudos:
                        break
        pseudos.add(pseudo)
        utilisateurs.append({
            "_id": nouvel_id("utilisateurs", i + 1), "code": "USR-%04d" % (i + 1), "pseudo": pseudo,
            "mot_de_passe_demo": config.MOT_DE_PASSE_DEMO if i == 0 else None,
            "nom": nom, "prenom": prenom, "photo": None,
            "bio": "Enseignant de la matiere Du SQL au NoSQL." if i == 0 else rng.choice(BIOS),
            "ville": ville, "region": VILLES[ville],
            "date_inscription": date_entre(datetime(2023, 1, 1), datetime(2026, 5, 15)),
            "infos": {"age": age, "sexe": sexe, "fonction": fonction},
            "categorie_activite": categories[i],
            "preferences": rng.sample(config.CATEGORIES_PREFERENCES, rng.randint(1, 3)),
            "amis": [], "groupes_ids": [],
            "confidentialite": {"messages_inconnus": True if i == 0 else rng.random() < 0.6,
                                "ajout_groupe_inconnus": False if i == 0 else rng.random() < 0.5},
            "role": "superviseur" if i == 0 else "membre", "historique_profil": [],
        })
    return utilisateurs


# ---------------------------------------------------------------------------
# 2. Amis
# ---------------------------------------------------------------------------


def generer_amis(utilisateurs):
    """
    Construit un graphe d'amities symetrique. Les influenceurs ont beaucoup d'amis, les timides
    peu. Le compte du professeur recoit exactement 28 amis pour que le tri soit demonstratif.
    """
    par_id = {u["_id"]: u for u in utilisateurs}
    cible = {u["_id"]: {"influenceur": rng.randint(28, 45), "normal": rng.randint(8, 24), "timide_reseau": rng.randint(3, 9)}[u["categorie_activite"]]
             for u in utilisateurs}
    cible[utilisateurs[0]["_id"]] = 28

    def lier(a, b):
        ua, ub = par_id[a], par_id[b]
        depuis = date_entre(max(ua["date_inscription"], ub["date_inscription"]) + timedelta(days=1), REF - timedelta(days=3))
        ua["amis"].append({"ami_id": b, "depuis": depuis, "nb_messages": 0})
        ub["amis"].append({"ami_id": a, "depuis": depuis, "nb_messages": 0})

    ids = [u["_id"] for u in utilisateurs]
    # le professeur d'abord, pour garantir ses 28 amis meme si les autres ont deja de la place
    for b in rng.sample(ids[1:], 28):
        lier(ids[0], b)
    for _ in range(40):                       # plusieurs passes : chacun cherche des amis disponibles
        for a in rng.sample(ids, len(ids)):
            ua = par_id[a]
            if len(ua["amis"]) >= cible[a]:
                continue
            deja = {x["ami_id"] for x in ua["amis"]} | {a, ids[0]}
            libres = [b for b in ids if b not in deja and len(par_id[b]["amis"]) < cible[b]]
            if libres:
                lier(a, rng.choice(libres))
    for u in utilisateurs:
        u["amis"].sort(key=lambda x: x["depuis"])


# ---------------------------------------------------------------------------
# 3. Groupes
# ---------------------------------------------------------------------------


def generer_groupes(utilisateurs):
    """
    Cree 30 groupes de tailles 85 / 35 / 25 / 10. Certains utilisateurs n'appartiennent a aucun
    groupe, d'autres a beaucoup (tirage pondere). Le createur est administrateur d'office ; un
    ou deux autres administrateurs sont designes parmi les membres.
    """
    ids = [u["_id"] for u in utilisateurs]
    par_id = {u["_id"]: u for u in utilisateurs}
    sans_groupe = set(rng.sample(ids[1:], 20))
    poids = {i: rng.choice([0.3, 1, 1, 1.5, 2]) for i in ids}
    candidats = [i for i in ids[1:] if i not in sans_groupe]   # le professeur est ajoute a part (voir 'forces')
    specs = list(SPEC_GROUPES)
    rng.shuffle(specs)
    groupes = []
    for k, (taille, popularite, type_groupe) in enumerate(specs):
        nom, description = GROUPES[k]
        membres_ids = choisir_pondere(candidats, poids, taille)
        groupes.append({"_id": nouvel_id("groupes", k + 1), "code": "GRP-%02d" % (k + 1), "nom": nom,
                        "description": description, "taille": taille, "popularite": popularite,
                        "type": type_groupe, "membres_ids": membres_ids})
    # le professeur appartient a 5 groupes varies : un tres grand, un moyen, un petit populaire,
    # un restreint et un moins populaire dont il est administrateur (mais pas createur)
    def premier(pred):
        return next(g for g in groupes if pred(g))
    forces = [premier(lambda g: g["taille"] == 85), premier(lambda g: g["taille"] == 35),
              premier(lambda g: g["taille"] == 25 and g["popularite"] == "populaire"),
              premier(lambda g: g["popularite"] == "restreint"),
              premier(lambda g: g["taille"] == 25 and g["popularite"] == "moins_populaire")]
    for g in forces:
        g["membres_ids"][rng.randrange(len(g["membres_ids"]))] = ids[0]   # remplace un membre : la taille reste exacte
    docs = []
    for g in groupes:
        membres_ids = g["membres_ids"]
        candidats_createur = [m for m in membres_ids if m != ids[0]]
        createur = rng.choice(candidats_createur)
        date_creation = date_entre(max(par_id[createur]["date_inscription"], datetime(2023, 6, 1)) + timedelta(days=1), datetime(2026, 6, 30))
        admins = [createur] + rng.sample([m for m in candidats_createur if m != createur], rng.randint(0, 2))
        if g is forces[4]:
            admins.append(ids[0])
        membres = []
        for m in membres_ids:
            debut = max(date_creation, par_id[m]["date_inscription"])
            membres.append({"user_id": m, "depuis": date_creation if m == createur else date_entre(debut, REF - timedelta(days=50))})
            par_id[m]["groupes_ids"].append(g["_id"])
        docs.append({"_id": g["_id"], "code": g["code"], "nom": g["nom"], "description": g["description"],
                     "createur_id": createur, "admins": admins, "membres": membres, "type": g["type"],
                     "popularite": g["popularite"], "date_creation": date_creation})
    return docs


# ---------------------------------------------------------------------------
# 4. Hashtags, publications, likes
# ---------------------------------------------------------------------------


def generer_hashtags():
    return [{"_id": ObjectId("%04x%020x" % (7, i + 1)), "tag": tag, "categories": cats}
            for i, (tag, cats) in enumerate(sorted(HASHTAGS.items()))]


def repartir_volume(total, ids, poids):
    """Repartit exactement 'total' publications entre des auteurs selon des poids (methode du plus fort reste)."""
    somme = sum(poids[i] for i in ids)
    brut = {i: total * poids[i] / somme for i in ids}
    comptes = {i: int(brut[i]) for i in ids}
    reste = total - sum(comptes.values())
    for i in sorted(ids, key=lambda i: brut[i] - comptes[i], reverse=True)[:reste]:
        comptes[i] += 1
    return comptes


def generer_publications(utilisateurs, groupes):
    """
    Cree les publications : le VOLUME total de chaque categorie vaut 70 / 25 / 5 % (420 / 150 / 30
    sur 600). Les influenceurs sont peu nombreux mais prolifiques, les timides nombreux mais
    quasi muets. Le texte, le ton et les hashtags decoulent de l'image choisie.
    """
    par_cat = {c: [u["_id"] for u in utilisateurs if u["categorie_activite"] == c] for c in VOLUME_PUBLICATIONS}
    valdez = utilisateurs[0]["_id"]
    comptes = {}
    comptes.update(repartir_volume(VOLUME_PUBLICATIONS["influenceur"], par_cat["influenceur"], {i: rng.uniform(0.5, 1.6) for i in par_cat["influenceur"]}))
    autres_normaux = [i for i in par_cat["normal"] if i != valdez]
    comptes.update(repartir_volume(VOLUME_PUBLICATIONS["normal"] - NB_PUBLICATIONS_VALDEZ, autres_normaux, {i: rng.uniform(0.3, 2.0) for i in autres_normaux}))
    comptes[valdez] = NB_PUBLICATIONS_VALDEZ
    comptes.update(repartir_volume(VOLUME_PUBLICATIONS["timide_reseau"], par_cat["timide_reseau"], {i: rng.random() ** 3 + 0.01 for i in par_cat["timide_reseau"]}))

    par_id = {u["_id"]: u for u in utilisateurs}
    groupes_de = {u["_id"]: [g for g in groupes if u["_id"] in {m["user_id"] for m in g["membres"]}] for u in utilisateurs}
    tags_par_categorie = {}
    for tag, cats in HASHTAGS.items():
        for c in cats:
            tags_par_categorie.setdefault(c, []).append(tag)

    brouillons = []
    for auteur, n in comptes.items():
        for k in range(n):
            image_id = rng.choice(list(IMAGES))
            description, cats, tons = IMAGES[image_id]
            ton = rng.choice(tons)
            groupe = None
            if auteur != valdez and groupes_de[auteur] and rng.random() < 0.25:
                groupe = rng.choice(groupes_de[auteur])
            if auteur == valdez:
                date = date_entre(REF - timedelta(days=55), REF - timedelta(hours=6))
                visibilite = "amis" if k == 8 else "prive" if k == 9 else "public"
            else:
                date = date_entre(REF - timedelta(days=49 if groupe else 120), REF - timedelta(hours=1))
                visibilite = "public" if groupe else rng.choices(["public", "amis", "prive"], [80, 15, 5])[0]
            candidats = sorted({t for c in cats for t in tags_par_categorie.get(c, [])})
            nb_tags = rng.choices([0, 1, 2, 3], [15, 35, 35, 15])[0] if auteur != valdez or k % 3 else 2
            tags = rng.sample(candidats, min(nb_tags, len(candidats)))
            variante = "grayscale" if rng.random() < 0.25 else "principale"
            brouillons.append({
                "auteur_id": auteur, "date": date, "ton": ton, "visibilite": visibilite,
                "texte": rng.choice(TONS[ton][0]),
                "medias": [{"type": "image", "image_id": image_id, "variante": variante, "description": description,
                            "url": construire_url(image_id, variante, rng.randint(1, 999))}],
                "hashtags": tags, "groupe_id": groupe["_id"] if groupe else None})
    brouillons.sort(key=lambda b: b["date"])

    publications, tons = [], {}
    for k, b in enumerate(brouillons):
        pid = nouvel_id("publications", k + 1)
        tons[pid] = b.pop("ton")
        cat = par_id[b["auteur_id"]]["categorie_activite"]
        if b["auteur_id"] == valdez:
            nb_likes = rng.randint(6, 25)
        else:
            nb_likes = {"influenceur": rng.randint(8, 60), "normal": rng.randint(0, 25), "timide_reseau": rng.randint(0, 6)}[cat]
        if b["groupe_id"]:
            pool = [m["user_id"] for g in groupes if g["_id"] == b["groupe_id"] for m in g["membres"]]
        else:
            pool = list(par_id)
        pool = [x for x in pool if x != b["auteur_id"]]
        likers = rng.sample(pool, min(nb_likes, len(pool)))
        publications.append({"_id": pid, "code": "PUB-%04d" % (k + 1), **b, "aimes": likers,
                             "compteurs": {"aimes": len(likers), "commentaires": 0, "partages": rng.randint(0, max(1, len(likers) // 4))},
                             "historique_modifs": []})
    return publications, tons


# ---------------------------------------------------------------------------
# 5. Commentaires
# ---------------------------------------------------------------------------


def generer_commentaires(utilisateurs, groupes, publications, tons):
    """
    Cree les commentaires de premier niveau (leur ton suit celui de l'image) et quelques reponses
    imbriquees. Les publications d'influenceurs en recoivent davantage. Le compteur
    de chaque publication est calcule ici, au moment de l'insertion.
    """
    par_id = {u["_id"]: u for u in utilisateurs}
    valdez = utilisateurs[0]["_id"]
    visibles = [p for p in publications if p["visibilite"] != "prive" or p["auteur_id"] == valdez]
    poids = [{"influenceur": 5, "normal": 2, "timide_reseau": 1}[par_id[p["auteur_id"]]["categorie_activite"]] for p in visibles]
    cibles = [p for p in publications if p["auteur_id"] == valdez for _ in range(3)]       # 3 commentaires minimum chacune
    cibles += rng.choices(visibles, poids, k=NB_COMMENTAIRES - len(cibles))
    membres_de = {g["_id"]: [m["user_id"] for m in g["membres"]] for g in groupes}
    commentaires, totaux = [], {}
    for k, p in enumerate(cibles):
        pool = membres_de[p["groupe_id"]] if p["groupe_id"] else list(par_id)
        pool = [x for x in pool if x != p["auteur_id"]] or list(par_id)
        auteur = rng.choice(pool)
        date = date_entre(p["date"] + timedelta(minutes=2), min(REF, p["date"] + timedelta(days=10)))
        textes = TONS[tons[p["_id"]]][1] if tons[p["_id"]] in TONS else COMMENTAIRES_GENERIQUES
        reponses = []
        if rng.random() < 0.18:
            for _ in range(rng.randint(1, 2)):
                reponses.append({"_id": ObjectId(), "auteur_id": rng.choice([p["auteur_id"], rng.choice(list(par_id))]),
                                 "contenu": rng.choice(COMMENTAIRES_GENERIQUES + ["Merci !", "Avec plaisir."]),
                                 "date": date_entre(date + timedelta(minutes=1), min(REF, date + timedelta(days=3))), "aimes": []})
        commentaires.append({"_id": ObjectId("%04x%020x" % (4, k + 1)), "publication_id": p["_id"], "auteur_id": auteur,
                             "contenu": rng.choice(textes), "date": date, "aimes": rng.sample(list(par_id), rng.randint(0, 4)),
                             "reponses": sorted(reponses, key=lambda r: r["date"])})
        totaux[p["_id"]] = totaux.get(p["_id"], 0) + 1 + len(reponses)
    # identifiants de reponses deterministes (ObjectId() aleatoire remplace)
    compteur = 0
    for c in commentaires:
        for r in c["reponses"]:
            compteur += 1
            r["_id"] = ObjectId("%04x%020x" % (8, compteur))
    for p in publications:
        p["compteurs"]["commentaires"] = totaux.get(p["_id"], 0)
    commentaires.sort(key=lambda c: c["date"])
    return commentaires


# ---------------------------------------------------------------------------
# 6. Messages et notifications
# ---------------------------------------------------------------------------


def generer_messages(utilisateurs, groupes):
    """
    Cree des conversations privees (entre amis, et quelques inconnus si le destinataire l'accepte)
    et des messages de groupe. Les derniers messages d'un fil peuvent etre non lus ; pour un
    message de groupe, 'non_lu_par' liste les membres qui ne l'ont pas encore vu.
    """
    par_id = {u["_id"]: u for u in utilisateurs}
    valdez = utilisateurs[0]["_id"]
    messages = []

    def nouveau_message(**champs):
        messages.append({"type": "prive", "groupe_id": None, "destinataire_id": None, "non_lu_par": [],
                         "pieces_jointes": [], "statut": "lu", **champs})

    paires = [(valdez, a["ami_id"]) for a in par_id[valdez]["amis"]]
    autres = [(u["_id"], a["ami_id"]) for u in utilisateurs[1:] for a in u["amis"] if u["_id"] < a["ami_id"] and valdez not in (u["_id"], a["ami_id"])]
    rng.shuffle(autres)
    inconnus = []
    for _ in range(400):                      # paires d'inconnus acceptees par la confidentialite du destinataire
        a, b = rng.sample(list(par_id), 2)
        if valdez not in (a, b) and par_id[b]["confidentialite"]["messages_inconnus"] and not any(x["ami_id"] == b for x in par_id[a]["amis"]):
            inconnus.append((a, b))
        if len(inconnus) >= 25:
            break
    fils = [(p, rng.randint(8, 18)) for p in paires] + [(p, rng.randint(1, 3)) for p in inconnus] + [(p, rng.randint(2, 14)) for p in autres]
    total = 0
    for (a, b), longueur in fils:
        if total >= NB_MESSAGES_PRIVES:
            break
        ami = next((x for x in par_id[a]["amis"] if x["ami_id"] == b), None)
        borne = max(ami["depuis"], REF - timedelta(days=60)) if ami else REF - timedelta(days=30)
        ecarts = [timedelta(minutes=rng.randint(1, 90)) if rng.random() < 0.8 else timedelta(hours=rng.randint(3, 60)) for _ in range(longueur - 1)]
        duree = sum(ecarts, timedelta())
        marge = max(timedelta(), (REF - timedelta(minutes=5)) - borne - duree)
        if marge == timedelta() and duree > REF - borne:        # fil trop long pour la fenetre : on le compresse
            ecarts = [e * ((REF - borne).total_seconds() * 0.9 / duree.total_seconds()) for e in ecarts]
            duree = sum(ecarts, timedelta())
            marge = max(timedelta(), (REF - timedelta(minutes=5)) - borne - duree)
        debut = borne + timedelta(seconds=rng.randint(0, int(marge.total_seconds())))
        dates, courant = [debut], debut
        for e in ecarts:
            courant += e
            dates.append(courant)
        expediteurs = []
        for _ in range(longueur):
            expediteurs.append(rng.choice([a, b]) if not expediteurs or rng.random() < 0.4 else expediteurs[-1] if rng.random() < 0.35 else (b if expediteurs[-1] == a else a))
        # fil en attente de lecture : la derniere serie de messages du meme expediteur n'a pas ete lue
        nb_non_lus = 0
        if rng.random() < (0.8 if valdez in (a, b) else 0.3):
            serie = 1
            while serie < longueur and expediteurs[-1 - serie] == expediteurs[-1]:
                serie += 1
            nb_non_lus = rng.randint(1, min(serie, 4))
        for k in range(longueur):
            exp = expediteurs[k]
            dest = b if exp == a else a
            non_lu = k >= longueur - nb_non_lus
            nouveau_message(expediteur_id=exp, destinataire_id=dest, contenu=rng.choice(MESSAGES_PRIVES), date=dates[k],
                            statut=rng.choice(["envoye", "recu", "recu"]) if non_lu else "lu")
        total += longueur
        if ami:                                # frequence de conversation, utilisee par le tri des amis
            for x, y in ((a, b), (b, a)):
                next(f for f in par_id[x]["amis"] if f["ami_id"] == y)["nb_messages"] += longueur

    # messages de groupe : les plus recents sont les plus souvent non lus
    for _ in range(NB_MESSAGES_GROUPE):
        g = rng.choices(groupes, [len(x["membres"]) for x in groupes])[0]
        membres = [m["user_id"] for m in g["membres"]]
        age = 45 * rng.random() ** 1.5
        date = (REF - timedelta(days=age, minutes=rng.randint(0, 600))).replace(second=0, microsecond=0)
        exp = rng.choice(membres)
        autres_membres = [m for m in membres if m != exp]
        recent = age < 10
        nb = rng.randint(0, 4) if recent else (rng.randint(1, 2) if rng.random() < 0.2 else 0)
        non_lu_par = rng.sample(autres_membres, min(nb, len(autres_membres)))
        if valdez in autres_membres and valdez not in non_lu_par and age < 12 and rng.random() < 0.5:
            non_lu_par.append(valdez)
        messages.append({"type": "groupe", "expediteur_id": exp, "destinataire_id": None, "groupe_id": g["_id"],
                         "contenu": rng.choice(MESSAGES_GROUPE), "date": date, "statut": "envoye",
                         "non_lu_par": non_lu_par, "pieces_jointes": []})
    messages.sort(key=lambda m: m["date"])
    for k, m in enumerate(messages):
        m["_id"] = nouvel_id("messages", k + 1)
    return messages


def generer_notifications(utilisateurs, publications, commentaires, messages):
    """
    Notifications derivees d'evenements REELS : un message non lu = une notification non lue ;
    puis completees (jusqu'a ~3050) par des j'aime, commentaires et demandes d'ami existants,
    lus ou non. Chaque notification porte la date de l'evenement et reste coherente avec lui.
    """
    notifs = []

    def ajouter(user, type_, kind, source_id, de, date, statut, **extra):
        notifs.append({"utilisateur_id": user, "type": type_, "date": date, "statut": statut,
                       "date_lecture": min(REF, date + timedelta(hours=rng.randint(1, 48))) if statut == "lue" else None,
                       "source": {"kind": kind, "id": source_id, "de_user_id": de, **extra}})

    for m in messages:                          # 1) messages non lus
        if m["type"] == "prive" and m["statut"] != "lu":
            ajouter(m["destinataire_id"], "message", "message_prive", m["_id"], m["expediteur_id"], m["date"], "non_lue")
        elif m["type"] == "groupe":
            for uid in m["non_lu_par"]:
                ajouter(uid, "message", "message_groupe", m["_id"], m["expediteur_id"], m["date"], "non_lue", groupe_id=m["groupe_id"])
    manque = NB_NOTIFICATIONS - len(notifs)
    par_pub = {p["_id"]: p for p in publications}
    valdez = utilisateurs[0]["_id"]
    candidats = []
    for p in publications:                      # 2) j'aime reels
        for liker in p["aimes"]:
            candidats.append(("jaime", p["auteur_id"], "publication", p["_id"], liker, date_entre(p["date"], REF), p["_id"]))
    for c in commentaires:                      # 3) commentaires reels
        p = par_pub[c["publication_id"]]
        if c["auteur_id"] != p["auteur_id"]:
            candidats.append(("commentaire", p["auteur_id"], "commentaire", c["_id"], c["auteur_id"], c["date"], p["_id"]))
    rng.shuffle(candidats)
    # les interactions sur les publications du professeur sont privilegiees pour sa demonstration
    candidats.sort(key=lambda x: 0 if x[1] == valdez else 1)
    interactions = candidats[:int(manque * 0.85)]
    for type_, dest, kind, sid, de, date, pub_id in interactions:
        recent = date > REF - timedelta(days=14)
        ajouter(dest, type_, kind, sid, de, date, "non_lue" if rng.random() < (0.65 if recent else 0.15) else "lue", publication_id=pub_id)
    ids = [u["_id"] for u in utilisateurs]
    deja = set()
    while len(notifs) < NB_NOTIFICATIONS:       # 4) demandes d'ami (entre personnes qui ne sont pas amies)
        a, b = rng.sample(ids, 2)
        ua = next(u for u in utilisateurs if u["_id"] == a)
        if (a, b) in deja or any(x["ami_id"] == b for x in ua["amis"]):
            continue
        deja.add((a, b))
        date = date_entre(REF - timedelta(days=30), REF)
        ajouter(b, "demande_ami", "utilisateur", a, a, date, "non_lue" if rng.random() < 0.6 else "lue")
    notifs.sort(key=lambda n: n["date"])
    for k, n in enumerate(notifs):
        n["_id"] = nouvel_id("notifications", k + 1)
    return notifs


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------


def generer(base=None, exporter_fichiers=True):
    """Genere toutes les collections, les insere, cree les index, valide puis exporte."""
    base = base if base is not None else config.get_db()
    print("Generation des donnees (graine %d)..." % config.SEED)
    utilisateurs = generer_utilisateurs()
    generer_amis(utilisateurs)
    groupes = generer_groupes(utilisateurs)
    hashtags = generer_hashtags()
    publications, tons = generer_publications(utilisateurs, groupes)
    commentaires = generer_commentaires(utilisateurs, groupes, publications, tons)
    messages = generer_messages(utilisateurs, groupes)
    notifications = generer_notifications(utilisateurs, publications, commentaires, messages)

    for nom in base.list_collection_names():     # on repart d'une base vide
        base.drop_collection(nom)
    jeu = {"utilisateurs": utilisateurs, "groupes": groupes, "hashtags": hashtags, "publications": publications,
           "commentaires": commentaires, "messages": messages, "notifications": notifications}
    for nom, docs in jeu.items():
        base[nom].insert_many(docs, ordered=True)   # insert_many par lot, comme recommande dans le PDF
        print("  %-14s %5d documents" % (nom, len(docs)))
    crud.creer_index()
    from scripts import valider_donnees
    rapport = valider_donnees.valider(base)
    print("\n".join(rapport.lignes))
    if rapport.echecs:
        raise SystemExit("Validation en echec : le jeu de donnees n'est pas exporte.")
    (config.RACINE / "data" / "rapport_validation.txt").write_text("\n".join(rapport.lignes) + "\n", encoding="utf-8")
    if exporter_fichiers:
        from scripts import exporter
        comptes = exporter.exporter(base=base)
        print("\nExports JSON/CSV ecrits dans %s (%d collections)." % (config.DOSSIER_EXPORTS, len(comptes)))
    return jeu


if __name__ == "__main__":
    generer(exporter_fichiers="--sans-export" not in sys.argv)
