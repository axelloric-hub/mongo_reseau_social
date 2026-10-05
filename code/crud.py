"""
crud.py - Fonctions Creer / Lire / Modifier / Supprimer (archiver) du reseau social.

Ce module existe parce que le devoir demande que toute operation passe par du code Python.
Il contient la logique metier ; il est appele a la fois par main.py (menu console) et par
l'API Django (backend/), elle-meme consommee par l'interface Streamlit.
Toutes les fonctions acceptent des identifiants en str ou en ObjectId et renvoient des
documents Python bruts (la conversion en JSON est faite par la couche API).

Principe cle : aucune suppression n'est physique. On copie dans <collection>_archives
(methode du chapitre 2 du PDF) et l'etat initial peut etre restaure par restore_database.bat.
"""
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

import config

# ---------------------------------------------------------------------------
# Erreurs metier : l'API les transforme en reponses HTTP propres (404, 409, ...)
# ---------------------------------------------------------------------------


class ErreurMetier(Exception):
    code_http = 400


class DocumentIntrouvable(ErreurMetier):
    code_http = 404


class SaisieInvalide(ErreurMetier):
    code_http = 400


class DoublonErreur(ErreurMetier):
    code_http = 409


class ActionInterdite(ErreurMetier):
    code_http = 403


def db():
    """Raccourci vers la base ; passe par config pour permettre de la remplacer dans les tests."""
    return config.get_db()


def oid(valeur):
    """Convertit str -> ObjectId et leve SaisieInvalide si l'identifiant est mal forme."""
    if isinstance(valeur, ObjectId):
        return valeur
    try:
        return ObjectId(str(valeur))
    except (InvalidId, TypeError):
        raise SaisieInvalide("Identifiant invalide : %r" % (valeur,))


def maintenant():
    return datetime.now().replace(microsecond=0)


def _page(page, par_page):
    """Normalise la pagination et renvoie (skip, limit)."""
    page = max(1, int(page or 1))
    par_page = min(100, max(1, int(par_page or 10)))
    return (page - 1) * par_page, par_page


def _texte_valide(texte, maxi=2000, nom="Le contenu"):
    texte = (texte or "").strip()
    if not texte:
        raise SaisieInvalide("%s ne peut pas etre vide." % nom)
    if len(texte) > maxi:
        raise SaisieInvalide("%s depasse %d caracteres." % (nom, maxi))
    return texte


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


def creer_index():
    """
    Cree les index du projet. Pourquoi : le fil, les notifications et la messagerie sont des
    lectures tres frequentes. Chaque index correspond a une requete precise (voir README).
    """
    d = db()
    d.utilisateurs.create_index("pseudo", unique=True, name="uniq_pseudo")
    d.utilisateurs.create_index("code", unique=True, name="uniq_code")
    d.hashtags.create_index("tag", unique=True, name="uniq_tag")
    d.publications.create_index([("auteur_id", ASCENDING), ("date", DESCENDING)], name="pub_auteur_date")
    d.publications.create_index([("hashtags", ASCENDING), ("date", DESCENDING)], name="pub_hashtag_date")
    d.publications.create_index([("groupe_id", ASCENDING), ("date", DESCENDING)], name="pub_groupe_date")
    d.commentaires.create_index([("publication_id", ASCENDING), ("date", ASCENDING)], name="com_pub_date")
    d.messages.create_index([("destinataire_id", ASCENDING), ("statut", ASCENDING), ("date", DESCENDING)],
                            name="msg_dest_statut_date")
    d.messages.create_index([("groupe_id", ASCENDING), ("date", DESCENDING)], name="msg_groupe_date")
    d.messages.create_index([("non_lu_par", ASCENDING)], name="msg_non_lu_par")
    d.notifications.create_index([("utilisateur_id", ASCENDING), ("statut", ASCENDING), ("date", DESCENDING)],
                                 name="notif_user_statut_date")


# ---------------------------------------------------------------------------
# Archivage generique (methode du chapitre 2 du PDF)
# ---------------------------------------------------------------------------


def archiver(collection, filtre, raison="suppression"):
    """
    Deplace les documents qui respectent le filtre vers <collection>_archives.
    Pourquoi : ne jamais perdre une donnee. Comment : copie avec date_archivage et raison,
    puis suppression de la collection principale. Renvoie la liste des documents archives.
    """
    documents = list(db()[collection].find(filtre))
    if not documents:
        return []
    for doc in documents:
        doc["date_archivage"] = maintenant()
        doc["raison_archivage"] = raison
    db()[collection + "_archives"].insert_many(documents)
    db()[collection].delete_many({"_id": {"$in": [d["_id"] for d in documents]}})
    return documents


# ---------------------------------------------------------------------------
# Utilisateurs et authentification
# ---------------------------------------------------------------------------

_PROJECTION_PUBLIQUE = {"mot_de_passe_demo": 0}


def verifier_mot_de_passe(utilisateur, mot_de_passe):
    """
    Point d'extension : pour le devoir, la validation est volontairement permissive
    (tout mot de passe est accepte). Remplacer ce corps par un hash + comparaison
    suffira pour ajouter une vraie authentification plus tard.
    """
    return True


def get_utilisateur(user_id):
    u = db().utilisateurs.find_one({"_id": oid(user_id)}, _PROJECTION_PUBLIQUE)
    if not u:
        raise DocumentIntrouvable("Utilisateur introuvable.")
    return u


def get_utilisateur_par_pseudo(pseudo):
    u = db().utilisateurs.find_one({"pseudo": (pseudo or "").strip().lower()}, _PROJECTION_PUBLIQUE)
    if not u:
        raise DocumentIntrouvable("Aucun utilisateur avec le pseudo %r." % pseudo)
    return u


def authentifier(pseudo, mot_de_passe):
    """Connexion de demonstration : le pseudo doit exister, le mot de passe passe par le point d'extension."""
    if not (pseudo or "").strip():
        raise SaisieInvalide("Le pseudo est obligatoire.")
    u = get_utilisateur_par_pseudo(pseudo)
    if not verifier_mot_de_passe(u, mot_de_passe):
        raise ActionInterdite("Mot de passe incorrect.")
    return u


def rechercher_utilisateurs(texte, limite=10):
    """Recherche par debut de pseudo (utilise l'index unique du pseudo)."""
    texte = (texte or "").strip().lower()
    if len(texte) < 2:
        return []
    import re
    motif = "^" + re.escape(texte)
    return list(db().utilisateurs.find({"pseudo": {"$regex": motif}}, {"pseudo": 1, "nom": 1, "prenom": 1, "ville": 1}).limit(limite))


def inscrire_utilisateur(pseudo, nom, prenom, ville, age, sexe, fonction):
    """Cree un utilisateur ; l'index unique sur le pseudo detecte les doublons."""
    pseudo = _texte_valide(pseudo, 30, "Le pseudo").lower()
    if sexe not in ("F", "M") or fonction not in ("employe", "ecolier / etudiant", "retraite"):
        raise SaisieInvalide("Sexe ou fonction invalide.")
    doc = {
        "code": "USR-N%s" % maintenant().strftime("%H%M%S"), "pseudo": pseudo,
        "nom": nom, "prenom": prenom, "photo": None, "bio": "", "ville": ville,
        "date_inscription": maintenant(),
        "infos": {"age": int(age), "sexe": sexe, "fonction": fonction},
        "categorie_activite": "timide_reseau", "preferences": [], "amis": [], "groupes_ids": [],
        "confidentialite": {"messages_inconnus": True, "ajout_groupe_inconnus": True},
        "role": "membre",
    }
    try:
        return db().utilisateurs.insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise DoublonErreur("Le pseudo %r est deja pris." % pseudo)


def mettre_a_jour_profil(user_id, bio=None, ville=None, photo=None, age=None):
    """
    Modifie le profil. Non destructif : l'ancienne version des champs modifies est conservee
    dans historique_profil (le $push et le $set se font dans la meme operation).
    """
    u = get_utilisateur(user_id)
    nouveau, avant = {}, {}
    if bio is not None:
        nouveau["bio"] = _texte_valide(bio, 280, "La bio") if bio.strip() else ""
    if ville is not None:
        nouveau["ville"] = _texte_valide(ville, 40, "La ville")
    if photo is not None:
        nouveau["photo"] = photo
    if age is not None:
        if not 10 <= int(age) <= 110:
            raise SaisieInvalide("Age invalide.")
        nouveau["infos.age"] = int(age)
    if not nouveau:
        raise SaisieInvalide("Aucune modification fournie.")
    for cle in nouveau:
        avant[cle] = u["infos"]["age"] if cle == "infos.age" else u.get(cle)
    db().utilisateurs.update_one({"_id": u["_id"]}, {
        "$set": nouveau,
        "$push": {"historique_profil": {"date": maintenant(), "avant": avant}},
    })
    return get_utilisateur(user_id)


_CLES_CONFIDENTIALITE = {"messages_inconnus", "ajout_groupe_inconnus"}


def changer_confidentialite(user_id, cle, valeur):
    """Modifie un parametre de confidentialite. Les cles autorisees sont listees ci-dessus (extensible)."""
    if cle not in _CLES_CONFIDENTIALITE:
        raise SaisieInvalide("Parametre de confidentialite inconnu : %r" % cle)
    if not isinstance(valeur, bool):
        raise SaisieInvalide("La valeur doit etre vrai ou faux.")
    r = db().utilisateurs.update_one({"_id": oid(user_id)}, {"$set": {"confidentialite." + cle: valeur}})
    if r.matched_count == 0:
        raise DocumentIntrouvable("Utilisateur introuvable.")
    return get_utilisateur(user_id)["confidentialite"]


def modifier_preferences(user_id, preferences):
    """Remplace les preferences (1 a 3 categories parmi les 10 du projet) ; elles pilotent le fil."""
    preferences = list(dict.fromkeys(preferences or []))
    if not 1 <= len(preferences) <= 3:
        raise SaisieInvalide("Choisissez entre 1 et 3 preferences.")
    if any(p not in config.CATEGORIES_PREFERENCES for p in preferences):
        raise SaisieInvalide("Preference inconnue.")
    db().utilisateurs.update_one({"_id": oid(user_id)}, {"$set": {"preferences": preferences}})
    return preferences


def _joindre_utilisateurs(documents, champ, cible="auteur"):
    """Ajoute a chaque document un mini-profil (pseudo, nom, prenom) en une seule requete ($in)."""
    ids = {d[champ] for d in documents if d.get(champ)}
    profils = {u["_id"]: u for u in db().utilisateurs.find(
        {"_id": {"$in": list(ids)}}, {"pseudo": 1, "nom": 1, "prenom": 1, "ville": 1})}
    for d in documents:
        d[cible] = profils.get(d.get(champ))
    return documents


# ---------------------------------------------------------------------------
# Amis
# ---------------------------------------------------------------------------


def lister_amis(user_id, tri="anciennete"):
    """
    Liste les amis avec deux tris possibles :
      - 'anciennete' : amitie la plus ancienne d'abord ;
      - 'frequence'  : plus grand nombre de messages echanges d'abord.
    Pipeline : $unwind de la liste imbriquee, $sort, puis $lookup pour obtenir le profil.
    """
    if tri not in ("anciennete", "frequence"):
        raise SaisieInvalide("Tri inconnu (anciennete ou frequence).")
    cle_tri = {"amis.depuis": 1} if tri == "anciennete" else {"amis.nb_messages": -1, "amis.depuis": 1}
    pipeline = [
        {"$match": {"_id": oid(user_id)}},
        {"$unwind": "$amis"},
        {"$sort": cle_tri},
        {"$lookup": {"from": "utilisateurs", "localField": "amis.ami_id", "foreignField": "_id", "as": "profil"}},
        {"$unwind": "$profil"},
        {"$project": {"_id": "$profil._id", "pseudo": "$profil.pseudo", "nom": "$profil.nom",
                      "prenom": "$profil.prenom", "ville": "$profil.ville",
                      "depuis": "$amis.depuis", "nb_messages": "$amis.nb_messages"}},
    ]
    return list(db().utilisateurs.aggregate(pipeline))


def suggestions_amis(user_id, limite=8):
    """Bonus du PDF : amis d'amis, classes par nombre d'amis communs."""
    u = get_utilisateur(user_id)
    exclus = [u["_id"]] + [a["ami_id"] for a in u["amis"]]
    pipeline = [
        {"$match": {"_id": u["_id"]}}, {"$unwind": "$amis"},
        {"$lookup": {"from": "utilisateurs", "localField": "amis.ami_id", "foreignField": "_id", "as": "ami"}},
        {"$unwind": "$ami"}, {"$unwind": "$ami.amis"},
        {"$match": {"ami.amis.ami_id": {"$nin": exclus}}},
        {"$group": {"_id": "$ami.amis.ami_id", "amis_communs": {"$sum": 1}}},
        {"$sort": {"amis_communs": -1, "_id": 1}}, {"$limit": int(limite)},
        {"$lookup": {"from": "utilisateurs", "localField": "_id", "foreignField": "_id", "as": "profil"}},
        {"$unwind": "$profil"},
        {"$project": {"pseudo": "$profil.pseudo", "nom": "$profil.nom", "prenom": "$profil.prenom",
                      "ville": "$profil.ville", "amis_communs": 1}},
    ]
    return list(db().utilisateurs.aggregate(pipeline))


def envoyer_demande_ami(de_id, a_id):
    """Cree une notification 'demande_ami' ; l'amitie n'existe qu'apres acceptation."""
    de, a = get_utilisateur(de_id), get_utilisateur(a_id)
    if de["_id"] == a["_id"]:
        raise SaisieInvalide("Vous ne pouvez pas vous ajouter vous-meme.")
    if any(x["ami_id"] == a["_id"] for x in de["amis"]):
        raise DoublonErreur("Vous etes deja amis.")
    if db().notifications.find_one({"utilisateur_id": a["_id"], "type": "demande_ami",
                                    "source.de_user_id": de["_id"], "statut": "non_lue"}):
        raise DoublonErreur("Une demande est deja en attente.")
    notif = {"utilisateur_id": a["_id"], "type": "demande_ami",
             "source": {"kind": "utilisateur", "id": de["_id"], "de_user_id": de["_id"]},
             "date": maintenant(), "statut": "non_lue", "date_lecture": None}
    return db().notifications.insert_one(notif).inserted_id


def accepter_demande_ami(user_id, notification_id):
    """Cree l'amitie des deux cotes ($push conditionnel pour eviter un doublon) et lit la notification."""
    notif = db().notifications.find_one({"_id": oid(notification_id), "utilisateur_id": oid(user_id),
                                         "type": "demande_ami"})
    if not notif:
        raise DocumentIntrouvable("Demande d'ami introuvable.")
    moi, lui = oid(user_id), notif["source"]["de_user_id"]
    maintenant_ = maintenant()
    for a, b in ((moi, lui), (lui, moi)):
        db().utilisateurs.update_one({"_id": a, "amis.ami_id": {"$ne": b}},
                                     {"$push": {"amis": {"ami_id": b, "depuis": maintenant_, "nb_messages": 0}}})
    db().notifications.update_one({"_id": notif["_id"]}, {"$set": {"statut": "lue", "date_lecture": maintenant_}})
    return True


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------


def lister_hashtags():
    return list(db().hashtags.find({}, {"_id": 0}).sort("tag", 1))


def creer_publication(auteur_id, texte, medias=None, hashtags=None, visibilite="public", groupe_id=None):
    """Cree une publication avec ses compteurs a zero (mis a jour ensuite avec $inc)."""
    auteur = get_utilisateur(auteur_id)
    if visibilite not in ("public", "amis", "prive"):
        raise SaisieInvalide("Visibilite invalide.")
    texte = (texte or "").strip()
    if not texte and not medias:
        raise SaisieInvalide("Une publication doit contenir un texte ou un media.")
    if len(texte) > 1000:
        raise SaisieInvalide("Le texte depasse 1000 caracteres.")
    if groupe_id:
        groupe = get_groupe(groupe_id)
        if not any(m["user_id"] == auteur["_id"] for m in groupe["membres"]):
            raise ActionInterdite("Vous devez etre membre du groupe pour y publier.")
    tags = [t.strip().lstrip("#").lower() for t in (hashtags or []) if t.strip()]
    doc = {
        "code": "PUB-N%s" % maintenant().strftime("%H%M%S%f")[:9],
        "auteur_id": auteur["_id"], "texte": texte, "medias": medias or [], "date": maintenant(),
        "visibilite": visibilite, "compteurs": {"aimes": 0, "commentaires": 0, "partages": 0},
        "aimes": [], "hashtags": list(dict.fromkeys(tags)),
        "groupe_id": oid(groupe_id) if groupe_id else None, "historique_modifs": [],
    }
    return db().publications.insert_one(doc).inserted_id


def get_publication(pub_id):
    p = db().publications.find_one({"_id": oid(pub_id)})
    if not p:
        raise DocumentIntrouvable("Publication introuvable (supprimee ?).")
    return p


def _enrichir_publications(docs, user_id=None):
    """Ajoute l'auteur, l'etat 'j'aime' de l'utilisateur et le nom du groupe a chaque publication."""
    _joindre_utilisateurs(docs, "auteur_id", "auteur")
    noms_groupes = {g["_id"]: g["nom"] for g in db().groupes.find(
        {"_id": {"$in": [d["groupe_id"] for d in docs if d.get("groupe_id")]}}, {"nom": 1})}
    for d in docs:
        d["a_aime"] = bool(user_id) and oid(user_id) in d.get("aimes", [])
        d["groupe_nom"] = noms_groupes.get(d.get("groupe_id"))
        d.pop("aimes", None)  # la liste complete des likers n'est pas utile a l'affichage
    return docs


def fil_actualite(user_id, page=1, par_page=10, mode="pour_moi"):
    """
    Fil d'actualite pagine, du plus recent au plus ancien.
    Modes : 'amis' (publications des amis), 'preferences' (publications publiques dont les
    hashtags correspondent aux preferences), 'pour_moi' (les deux + les miennes).
    Chaque publication recoit 'raisons' : pourquoi elle apparait (demonstration de l'effet des preferences).
    """
    if mode not in ("pour_moi", "amis", "preferences"):
        raise SaisieInvalide("Mode de fil inconnu.")
    u = get_utilisateur(user_id)
    amis_ids = [a["ami_id"] for a in u["amis"]]
    hashtags_pref = {h["tag"]: h["categories"] for h in db().hashtags.find(
        {"categories": {"$in": u["preferences"]}})}
    branche_amis = {"auteur_id": {"$in": amis_ids}, "visibilite": {"$in": ["public", "amis"]}}
    branche_pref = {"visibilite": "public", "hashtags": {"$in": list(hashtags_pref)}, "auteur_id": {"$ne": u["_id"]}}
    branche_moi = {"auteur_id": u["_id"]}
    branches = {"amis": [branche_amis], "preferences": [branche_pref],
                "pour_moi": [branche_amis, branche_pref, branche_moi]}[mode]
    acces_groupe = {"$or": [{"groupe_id": None}, {"groupe_id": {"$in": u["groupes_ids"]}}]}
    filtre = {"$and": [acces_groupe, {"$or": branches}]}
    skip, limite = _page(page, par_page)
    total = db().publications.count_documents(filtre)
    docs = list(db().publications.find(filtre).sort([("date", DESCENDING), ("_id", DESCENDING)]).skip(skip).limit(limite))
    amis_set = set(amis_ids)
    for d in docs:
        raisons = []
        if d["auteur_id"] == u["_id"]:
            raisons.append("Votre publication")
        if d["auteur_id"] in amis_set:
            raisons.append("Publiee par un ami")
        communs = [t for t in d.get("hashtags", []) if t in hashtags_pref]
        if communs and d["auteur_id"] != u["_id"]:
            raisons.append("Correspond a vos preferences : " + ", ".join("#" + t for t in communs))
        d["raisons"] = raisons
    return {"items": _enrichir_publications(docs, user_id), "total": total, "page": int(page), "par_page": limite}


def publications_utilisateur(auteur_id, voyeur_id, page=1, par_page=10):
    """Publications d'un auteur ; un autre utilisateur ne voit que ce que la visibilite autorise."""
    auteur = get_utilisateur(auteur_id)
    filtre = {"auteur_id": auteur["_id"]}
    if str(voyeur_id) != str(auteur["_id"]):
        ami = any(str(a["ami_id"]) == str(voyeur_id) for a in auteur["amis"])
        filtre["visibilite"] = {"$in": ["public", "amis"] if ami else ["public"]}
        filtre["groupe_id"] = None
    skip, limite = _page(page, par_page)
    total = db().publications.count_documents(filtre)
    docs = list(db().publications.find(filtre).sort("date", DESCENDING).skip(skip).limit(limite))
    return {"items": _enrichir_publications(docs, voyeur_id), "total": total, "page": int(page), "par_page": limite}


def publications_groupe(groupe_id, user_id, page=1, par_page=10):
    """Publications d'un groupe ; reservees aux membres si le groupe est prive."""
    g = get_groupe(groupe_id)
    est_membre = any(str(m["user_id"]) == str(user_id) for m in g["membres"])
    if g["type"] == "prive" and not est_membre:
        raise ActionInterdite("Groupe prive : reserve aux membres.")
    skip, limite = _page(page, par_page)
    filtre = {"groupe_id": g["_id"]}
    total = db().publications.count_documents(filtre)
    docs = list(db().publications.find(filtre).sort("date", DESCENDING).skip(skip).limit(limite))
    return {"items": _enrichir_publications(docs, user_id), "total": total, "page": int(page), "par_page": limite}


def publications_par_hashtag(tag, user_id=None, page=1, par_page=10):
    """Publications publiques portant un hashtag (index multikey publications.hashtags + date)."""
    tag = (tag or "").strip().lstrip("#").lower()
    if not tag:
        raise SaisieInvalide("Hashtag vide.")
    skip, limite = _page(page, par_page)
    filtre = {"hashtags": tag, "visibilite": "public", "groupe_id": None}
    total = db().publications.count_documents(filtre)
    docs = list(db().publications.find(filtre).sort("date", DESCENDING).skip(skip).limit(limite))
    return {"items": _enrichir_publications(docs, user_id), "total": total, "page": int(page), "par_page": limite}


def modifier_publication(pub_id, user_id, texte=None, hashtags=None, visibilite=None):
    """
    Modifie une publication de l'utilisateur. Non destructif : l'ancienne version du texte,
    des hashtags et de la visibilite est poussee dans historique_modifs ($push) en meme temps
    que le $set, dans une seule operation atomique.
    """
    p = get_publication(pub_id)
    if p["auteur_id"] != oid(user_id):
        raise ActionInterdite("Vous ne pouvez modifier que vos publications.")
    nouveau = {}
    if texte is not None:
        nouveau["texte"] = _texte_valide(texte, 1000, "Le texte")
    if hashtags is not None:
        nouveau["hashtags"] = list(dict.fromkeys(t.strip().lstrip("#").lower() for t in hashtags if t.strip()))
    if visibilite is not None:
        if visibilite not in ("public", "amis", "prive"):
            raise SaisieInvalide("Visibilite invalide.")
        nouveau["visibilite"] = visibilite
    if not nouveau:
        raise SaisieInvalide("Aucune modification fournie.")
    nouveau["date_modification"] = maintenant()
    avant = {"date": maintenant(), "texte": p["texte"], "hashtags": p["hashtags"], "visibilite": p["visibilite"]}
    db().publications.update_one({"_id": p["_id"]}, {"$set": nouveau, "$push": {"historique_modifs": avant}})
    return get_publication(pub_id)


def aimer_publication(pub_id, user_id):
    """
    Bascule le j'aime. $addToSet + filtre '$ne' garantit un seul j'aime par utilisateur ;
    le compteur denormalise est mis a jour avec $inc au lieu d'etre recalcule (exigence du PDF).
    """
    p, uid = get_publication(pub_id), oid(user_id)
    if uid in p.get("aimes", []):
        db().publications.update_one({"_id": p["_id"], "aimes": uid},
                                     {"$pull": {"aimes": uid}, "$inc": {"compteurs.aimes": -1}})
        return {"aime": False}
    r = db().publications.update_one({"_id": p["_id"], "aimes": {"$ne": uid}},
                                     {"$addToSet": {"aimes": uid}, "$inc": {"compteurs.aimes": 1}})
    if r.modified_count and p["auteur_id"] != uid:
        db().notifications.insert_one({
            "utilisateur_id": p["auteur_id"], "type": "jaime",
            "source": {"kind": "publication", "id": p["_id"], "de_user_id": uid, "publication_id": p["_id"]},
            "date": maintenant(), "statut": "non_lue", "date_lecture": None})
    return {"aime": True}


def partager_publication(pub_id):
    """Incremente le compteur de partages."""
    r = db().publications.update_one({"_id": oid(pub_id)}, {"$inc": {"compteurs.partages": 1}})
    if r.matched_count == 0:
        raise DocumentIntrouvable("Publication introuvable.")
    return True


def supprimer_publication(pub_id, user_id):
    """
    Archive une publication, ses commentaires et les notifications qui y renvoient.
    Ainsi aucun commentaire ni notification orphelin ne reste dans les collections actives,
    et tout est recuperable dans les collections *_archives.
    """
    p = get_publication(pub_id)
    if p["auteur_id"] != oid(user_id):
        raise ActionInterdite("Vous ne pouvez supprimer que vos publications.")
    raison = "publication supprimee par son auteur"
    nb_com = len(archiver("commentaires", {"publication_id": p["_id"]}, raison))
    nb_notif = len(archiver("notifications", {"source.publication_id": p["_id"]}, raison))
    archiver("publications", {"_id": p["_id"]}, raison)
    return {"commentaires_archives": nb_com, "notifications_archivees": nb_notif}


# ---------------------------------------------------------------------------
# Commentaires
# ---------------------------------------------------------------------------


def lister_commentaires(pub_id, page=1, par_page=20):
    """Commentaires d'une publication (index publication_id + date), reponses imbriquees incluses."""
    skip, limite = _page(page, par_page)
    docs = list(db().commentaires.find({"publication_id": oid(pub_id)}).sort("date", ASCENDING).skip(skip).limit(limite))
    _joindre_utilisateurs(docs, "auteur_id", "auteur")
    tous = [r for d in docs for r in d.get("reponses", [])]
    _joindre_utilisateurs(tous, "auteur_id", "auteur")
    return docs


def ajouter_commentaire(pub_id, auteur_id, contenu, parent_id=None):
    """
    Ajoute un commentaire (ou une reponse imbriquee si parent_id est fourni), incremente le
    compteur de la publication avec $inc et notifie l'auteur de la publication.
    """
    p, auteur = get_publication(pub_id), oid(auteur_id)
    get_utilisateur(auteur)
    contenu = _texte_valide(contenu, 500, "Le commentaire")
    if parent_id:
        reponse = {"_id": ObjectId(), "auteur_id": auteur, "contenu": contenu, "date": maintenant(), "aimes": []}
        r = db().commentaires.update_one({"_id": oid(parent_id), "publication_id": p["_id"]},
                                         {"$push": {"reponses": reponse}})
        if r.matched_count == 0:
            raise DocumentIntrouvable("Commentaire parent introuvable.")
        cid = reponse["_id"]
    else:
        cid = db().commentaires.insert_one({
            "publication_id": p["_id"], "auteur_id": auteur, "contenu": contenu,
            "date": maintenant(), "aimes": [], "reponses": []}).inserted_id
    db().publications.update_one({"_id": p["_id"]}, {"$inc": {"compteurs.commentaires": 1}})
    if p["auteur_id"] != auteur:
        db().notifications.insert_one({
            "utilisateur_id": p["auteur_id"], "type": "commentaire",
            "source": {"kind": "commentaire", "id": cid, "de_user_id": auteur, "publication_id": p["_id"]},
            "date": maintenant(), "statut": "non_lue", "date_lecture": None})
    return cid


def supprimer_commentaire(commentaire_id, user_id):
    """
    Efface un commentaire (ou une reponse) de l'utilisateur. Le commentaire est archive avec
    ses reponses, le compteur de la publication est decremente avec $inc.
    """
    cid, uid = oid(commentaire_id), oid(user_id)
    c = db().commentaires.find_one({"_id": cid})
    if c:  # commentaire de premier niveau
        if c["auteur_id"] != uid:
            raise ActionInterdite("Vous ne pouvez effacer que vos commentaires.")
        retire = 1 + len(c.get("reponses", []))
        archiver("commentaires", {"_id": cid}, "commentaire efface par son auteur")
        pub_id = c["publication_id"]
    else:  # reponse imbriquee
        parent = db().commentaires.find_one({"reponses._id": cid})
        if not parent:
            raise DocumentIntrouvable("Commentaire introuvable.")
        reponse = next(r for r in parent["reponses"] if r["_id"] == cid)
        if reponse["auteur_id"] != uid:
            raise ActionInterdite("Vous ne pouvez effacer que vos commentaires.")
        db().commentaires_archives.insert_one({**reponse, "parent_id": parent["_id"], "publication_id": parent["publication_id"],
                                               "date_archivage": maintenant(), "raison_archivage": "reponse effacee"})
        db().commentaires.update_one({"_id": parent["_id"]}, {"$pull": {"reponses": {"_id": cid}}})
        retire, pub_id = 1, parent["publication_id"]
    db().publications.update_one({"_id": pub_id}, {"$inc": {"compteurs.commentaires": -retire}})
    archiver("notifications", {"source.id": cid}, "commentaire efface")
    return {"retires": retire}


# ---------------------------------------------------------------------------
# Groupes
# ---------------------------------------------------------------------------


def get_groupe(groupe_id):
    g = db().groupes.find_one({"_id": oid(groupe_id)})
    if not g:
        raise DocumentIntrouvable("Groupe introuvable.")
    return g


def lister_groupes(user_id=None, seulement_miens=False):
    """Liste les groupes avec leur nombre de membres ; 'seulement_miens' filtre sur l'utilisateur."""
    filtre = {"membres.user_id": oid(user_id)} if seulement_miens and user_id else {}
    pipeline = [{"$match": filtre},
                {"$project": {"nom": 1, "description": 1, "type": 1, "popularite": 1, "createur_id": 1,
                              "date_creation": 1, "nb_membres": {"$size": "$membres"}}},
                {"$sort": {"nb_membres": -1, "nom": 1}}]
    docs = list(db().groupes.aggregate(pipeline))
    if user_id:
        mes_groupes = set(get_utilisateur(user_id)["groupes_ids"])
        for d in docs:
            d["est_membre"] = d["_id"] in mes_groupes
    return docs


def detail_groupe(groupe_id, user_id=None):
    """Groupe complet avec createur, administrateurs et membres enrichis (profils)."""
    g = get_groupe(groupe_id)
    membres = _joindre_utilisateurs(list(g["membres"]), "user_id", "profil")
    g["membres"] = membres
    g["createur"] = db().utilisateurs.find_one({"_id": g["createur_id"]}, {"pseudo": 1, "nom": 1, "prenom": 1})
    g["admins_profils"] = list(db().utilisateurs.find({"_id": {"$in": g["admins"]}}, {"pseudo": 1, "nom": 1, "prenom": 1}))
    g["est_membre"] = bool(user_id) and any(str(m["user_id"]) == str(user_id) for m in membres)
    g["est_admin"] = bool(user_id) and oid(user_id) in g["admins"]
    return g


def creer_groupe(createur_id, nom, description, type_groupe="public"):
    """Cree un groupe : le createur devient automatiquement administrateur et premier membre."""
    if type_groupe not in ("public", "prive"):
        raise SaisieInvalide("Type de groupe invalide.")
    nom = _texte_valide(nom, 60, "Le nom du groupe")
    cid = get_utilisateur(createur_id)["_id"]
    doc = {"code": "GRP-N%s" % maintenant().strftime("%H%M%S"), "nom": nom,
           "description": (description or "").strip()[:300], "createur_id": cid, "admins": [cid],
           "membres": [{"user_id": cid, "depuis": maintenant()}], "type": type_groupe,
           "popularite": "restreint" if type_groupe == "prive" else "moins_populaire",
           "date_creation": maintenant()}
    gid = db().groupes.insert_one(doc).inserted_id
    db().utilisateurs.update_one({"_id": cid}, {"$addToSet": {"groupes_ids": gid}})
    return gid


def ajouter_membre(groupe_id, cible_id, par_id):
    """
    Ajoute un membre. Un membre du groupe peut ajouter n'importe qui, mais si l'auteur n'est pas
    ami de la cible, la confidentialite 'ajout_groupe_inconnus' de la cible doit l'autoriser.
    """
    g, cible, par = get_groupe(groupe_id), get_utilisateur(cible_id), get_utilisateur(par_id)
    if not any(m["user_id"] == par["_id"] for m in g["membres"]):
        raise ActionInterdite("Seuls les membres peuvent ajouter quelqu'un.")
    if any(m["user_id"] == cible["_id"] for m in g["membres"]):
        raise DoublonErreur("Cette personne est deja membre.")
    sont_amis = any(a["ami_id"] == par["_id"] for a in cible["amis"])
    if not sont_amis and not cible["confidentialite"]["ajout_groupe_inconnus"]:
        raise ActionInterdite("Cette personne n'accepte pas d'etre ajoutee a un groupe par un inconnu.")
    db().groupes.update_one({"_id": g["_id"]}, {"$push": {"membres": {"user_id": cible["_id"], "depuis": maintenant()}}})
    db().utilisateurs.update_one({"_id": cible["_id"]}, {"$addToSet": {"groupes_ids": g["_id"]}})
    return True


def promouvoir_admin(groupe_id, cible_id, par_id):
    """Seul le createur peut designer d'autres administrateurs (la cible doit etre membre)."""
    g = get_groupe(groupe_id)
    if g["createur_id"] != oid(par_id):
        raise ActionInterdite("Seul le createur du groupe peut nommer des administrateurs.")
    if not any(m["user_id"] == oid(cible_id) for m in g["membres"]):
        raise SaisieInvalide("La cible n'est pas membre du groupe.")
    db().groupes.update_one({"_id": g["_id"]}, {"$addToSet": {"admins": oid(cible_id)}})
    return True


def retirer_membre(groupe_id, cible_id, par_id):
    """
    Retire un membre (par un admin, ou lui-meme). Le createur ne peut pas etre retire.
    L'evenement est conserve dans groupes_archives (type 'membre_retire').
    """
    g, cible, par = get_groupe(groupe_id), oid(cible_id), oid(par_id)
    if cible == g["createur_id"]:
        raise ActionInterdite("Le createur ne peut pas etre retire du groupe.")
    if par != cible and par not in g["admins"]:
        raise ActionInterdite("Seul un administrateur peut retirer un autre membre.")
    membre = next((m for m in g["membres"] if m["user_id"] == cible), None)
    if not membre:
        raise DocumentIntrouvable("Cette personne n'est pas membre du groupe.")
    db().groupes.update_one({"_id": g["_id"]}, {"$pull": {"membres": {"user_id": cible}, "admins": cible}})
    db().utilisateurs.update_one({"_id": cible}, {"$pull": {"groupes_ids": g["_id"]}})
    db().groupes_archives.insert_one({"type": "membre_retire", "groupe_id": g["_id"], "membre": membre,
                                      "retire_par": par, "date_archivage": maintenant(),
                                      "raison_archivage": "membre retire"})
    return True


# ---------------------------------------------------------------------------
# Messagerie
# ---------------------------------------------------------------------------


def envoyer_message_prive(exp_id, dest_id, contenu, pieces_jointes=None):
    """
    Envoie un message prive. Refuse si le destinataire n'accepte pas les inconnus et n'est pas ami.
    Cree la notification du destinataire et incremente nb_messages dans la liste d'amis des deux
    cotes ($inc positionnel), ce qui alimente le tri des amis par frequence.
    """
    contenu = _texte_valide(contenu, 2000, "Le message")
    exp, dest = get_utilisateur(exp_id), get_utilisateur(dest_id)
    if exp["_id"] == dest["_id"]:
        raise SaisieInvalide("Vous ne pouvez pas vous ecrire a vous-meme.")
    sont_amis = any(a["ami_id"] == dest["_id"] for a in exp["amis"])
    if not sont_amis and not dest["confidentialite"]["messages_inconnus"]:
        raise ActionInterdite("%s n'accepte pas les messages des personnes qui ne sont pas ses amis." % dest["pseudo"])
    msg = {"type": "prive", "expediteur_id": exp["_id"], "destinataire_id": dest["_id"], "groupe_id": None,
           "contenu": contenu, "date": maintenant(), "statut": "envoye", "non_lu_par": [],
           "pieces_jointes": pieces_jointes or []}
    mid = db().messages.insert_one(msg).inserted_id
    db().notifications.insert_one({
        "utilisateur_id": dest["_id"], "type": "message",
        "source": {"kind": "message_prive", "id": mid, "de_user_id": exp["_id"]},
        "date": msg["date"], "statut": "non_lue", "date_lecture": None})
    if sont_amis:
        db().utilisateurs.update_one({"_id": exp["_id"], "amis.ami_id": dest["_id"]}, {"$inc": {"amis.$.nb_messages": 1}})
        db().utilisateurs.update_one({"_id": dest["_id"], "amis.ami_id": exp["_id"]}, {"$inc": {"amis.$.nb_messages": 1}})
    return mid


def envoyer_message_groupe(exp_id, groupe_id, contenu):
    """
    Envoie un message dans un groupe. 'non_lu_par' liste les membres qui ne l'ont pas encore lu ;
    une notification est creee pour chacun d'eux (insert_many).
    """
    contenu = _texte_valide(contenu, 2000, "Le message")
    g, exp = get_groupe(groupe_id), oid(exp_id)
    if not any(m["user_id"] == exp for m in g["membres"]):
        raise ActionInterdite("Vous devez etre membre du groupe pour y ecrire.")
    autres = [m["user_id"] for m in g["membres"] if m["user_id"] != exp]
    date = maintenant()
    mid = db().messages.insert_one({
        "type": "groupe", "expediteur_id": exp, "destinataire_id": None, "groupe_id": g["_id"],
        "contenu": contenu, "date": date, "statut": "envoye", "non_lu_par": autres,
        "pieces_jointes": []}).inserted_id
    if autres:
        db().notifications.insert_many([{
            "utilisateur_id": m, "type": "message",
            "source": {"kind": "message_groupe", "id": mid, "de_user_id": exp, "groupe_id": g["_id"]},
            "date": date, "statut": "non_lue", "date_lecture": None} for m in autres])
    return mid


def _marquer_messages_lus(user_id, filtre_messages):
    """
    Marque des messages comme lus pour un utilisateur ET lit les notifications associees.
    Prive : statut -> 'lu'. Groupe : l'utilisateur est retire de non_lu_par ($pull).
    """
    uid, date = oid(user_id), maintenant()
    prives = {**filtre_messages, "type": "prive", "destinataire_id": uid, "statut": {"$ne": "lu"}}
    groupes = {**filtre_messages, "type": "groupe", "non_lu_par": uid}
    ids = [m["_id"] for m in db().messages.find(prives, {"_id": 1})] + \
          [m["_id"] for m in db().messages.find(groupes, {"_id": 1})]
    if not ids:
        return 0
    db().messages.update_many({"_id": {"$in": ids}, "type": "prive"}, {"$set": {"statut": "lu"}})
    db().messages.update_many({"_id": {"$in": ids}, "type": "groupe"}, {"$pull": {"non_lu_par": uid}})
    db().notifications.update_many({"utilisateur_id": uid, "source.id": {"$in": ids}, "statut": "non_lue"},
                                   {"$set": {"statut": "lue", "date_lecture": date}})
    return len(ids)


def conversation(user_id, autre_id, page=1, par_page=30, marquer_lu=True):
    """Conversation privee entre deux utilisateurs, renvoyee dans l'ordre chronologique."""
    a, b = oid(user_id), oid(autre_id)
    filtre = {"type": "prive", "$or": [{"expediteur_id": a, "destinataire_id": b},
                                       {"expediteur_id": b, "destinataire_id": a}]}
    skip, limite = _page(page, par_page)
    total = db().messages.count_documents(filtre)
    docs = list(db().messages.find(filtre).sort("date", DESCENDING).skip(skip).limit(limite))
    docs.reverse()
    if marquer_lu:
        _marquer_messages_lus(a, {"expediteur_id": b})
    return {"items": docs, "total": total}


def conversations(user_id):
    """
    Liste des conversations privees : une ligne par interlocuteur avec dernier message et nombre
    de non-lus. Pipeline $group sur l'interlocuteur (calcule avec $cond), puis $lookup du profil.
    """
    uid = oid(user_id)
    autre = {"$cond": [{"$eq": ["$expediteur_id", uid]}, "$destinataire_id", "$expediteur_id"]}
    non_lu = {"$cond": [{"$and": [{"$eq": ["$destinataire_id", uid]}, {"$ne": ["$statut", "lu"]}]}, 1, 0]}
    pipeline = [
        {"$match": {"type": "prive", "$or": [{"expediteur_id": uid}, {"destinataire_id": uid}]}},
        {"$sort": {"date": -1}},
        {"$group": {"_id": autre, "dernier_message": {"$first": "$contenu"}, "derniere_date": {"$first": "$date"},
                    "nb_messages": {"$sum": 1}, "non_lus": {"$sum": non_lu}}},
        {"$sort": {"derniere_date": -1}},
        {"$lookup": {"from": "utilisateurs", "localField": "_id", "foreignField": "_id", "as": "profil"}},
        {"$unwind": "$profil"},
        {"$project": {"pseudo": "$profil.pseudo", "nom": "$profil.nom", "prenom": "$profil.prenom",
                      "dernier_message": 1, "derniere_date": 1, "nb_messages": 1, "non_lus": 1}},
    ]
    return list(db().messages.aggregate(pipeline))


def messages_groupe(groupe_id, user_id, page=1, par_page=30, marquer_lu=True):
    """Discussion d'un groupe (chronologique), reservee aux membres."""
    g = get_groupe(groupe_id)
    if not any(str(m["user_id"]) == str(user_id) for m in g["membres"]):
        raise ActionInterdite("Reserve aux membres du groupe.")
    skip, limite = _page(page, par_page)
    filtre = {"type": "groupe", "groupe_id": g["_id"]}
    total = db().messages.count_documents(filtre)
    docs = list(db().messages.find(filtre).sort("date", DESCENDING).skip(skip).limit(limite))
    docs.reverse()
    _joindre_utilisateurs(docs, "expediteur_id", "expediteur")
    if marquer_lu:
        _marquer_messages_lus(user_id, {"groupe_id": g["_id"]})
    return {"items": docs, "total": total}


def messages_non_lus(user_id, page=1, par_page=20):
    """Messages non lus de l'utilisateur (prives non lus + messages de groupe dont il est dans non_lu_par)."""
    uid = oid(user_id)
    filtre = {"$or": [{"type": "prive", "destinataire_id": uid, "statut": {"$ne": "lu"}}, {"type": "groupe", "non_lu_par": uid}]}
    skip, limite = _page(page, par_page)
    total = db().messages.count_documents(filtre)
    docs = list(db().messages.find(filtre).sort("date", DESCENDING).skip(skip).limit(limite))
    _joindre_utilisateurs(docs, "expediteur_id", "expediteur")
    # Un message prive 'envoye' devient 'recu' des qu'il est presente au destinataire
    db().messages.update_many({"_id": {"$in": [d["_id"] for d in docs]}, "type": "prive", "statut": "envoye"},
                              {"$set": {"statut": "recu"}})
    return {"items": docs, "total": total}


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

_FILTRES_NOTIF = {
    "tous": {},
    "groupes": {"source.kind": "message_groupe"},
    "prives": {"source.kind": "message_prive"},
    "autres": {"source.kind": {"$nin": ["message_groupe", "message_prive"]}},
}


def lister_notifications(user_id, categorie="tous", non_lues_seulement=False, page=1, par_page=15):
    """
    Notifications de la plus recente a la plus ancienne (date d'envoi du message / de l'evenement).
    categorie : tous | groupes | prives | autres. Index utilise : utilisateur_id + statut + date.
    """
    if categorie not in _FILTRES_NOTIF:
        raise SaisieInvalide("Categorie de notification inconnue.")
    filtre = {"utilisateur_id": oid(user_id), **_FILTRES_NOTIF[categorie]}
    if non_lues_seulement:
        filtre["statut"] = "non_lue"
    skip, limite = _page(page, par_page)
    total = db().notifications.count_documents(filtre)
    docs = list(db().notifications.find(filtre).sort([("date", DESCENDING), ("_id", DESCENDING)]).skip(skip).limit(limite))
    for d in docs:
        d["de_user_id"] = d["source"].get("de_user_id")
    _joindre_utilisateurs(docs, "de_user_id", "de")
    msgs = {m["_id"]: m["contenu"] for m in db().messages.find(
        {"_id": {"$in": [d["source"]["id"] for d in docs if d["source"]["kind"].startswith("message")]}}, {"contenu": 1})}
    comms = {c["_id"]: c["contenu"] for c in db().commentaires.find(
        {"_id": {"$in": [d["source"]["id"] for d in docs if d["source"]["kind"] == "commentaire"]}}, {"contenu": 1})}
    groupes = {g["_id"]: g["nom"] for g in db().groupes.find(
        {"_id": {"$in": [d["source"]["groupe_id"] for d in docs if d["source"].get("groupe_id")]}}, {"nom": 1})}
    for d in docs:
        d["apercu"] = msgs.get(d["source"]["id"]) or comms.get(d["source"]["id"]) or ""
        d["groupe_nom"] = groupes.get(d["source"].get("groupe_id"))
    return {"items": docs, "total": total}


def compter_notifications(user_id):
    """Compte les notifications non lues par categorie avec une seule agregation ($group sur source.kind)."""
    pipeline = [{"$match": {"utilisateur_id": oid(user_id), "statut": "non_lue"}},
                {"$group": {"_id": "$source.kind", "n": {"$sum": 1}}}]
    par_kind = {r["_id"]: r["n"] for r in db().notifications.aggregate(pipeline)}
    groupes, prives = par_kind.get("message_groupe", 0), par_kind.get("message_prive", 0)
    autres = sum(n for k, n in par_kind.items() if k not in ("message_groupe", "message_prive"))
    return {"groupes": groupes, "prives": prives, "autres": autres, "total": groupes + prives + autres}


def marquer_notifications_lues(user_id, categorie="tous", ids=None):
    """
    Marque comme lues les notifications (toutes, d'une categorie, ou une liste d'ids). Pour les
    notifications de messages, le message lui-meme est aussi marque lu : l'etat est donc
    coherent entre les deux collections. Renvoie le nombre de notifications modifiees.
    """
    if categorie not in _FILTRES_NOTIF:
        raise SaisieInvalide("Categorie de notification inconnue.")
    uid = oid(user_id)
    filtre = {"utilisateur_id": uid, "statut": "non_lue", **_FILTRES_NOTIF[categorie]}
    if ids:
        filtre["_id"] = {"$in": [oid(i) for i in ids]}
    notifs = list(db().notifications.find(filtre, {"source": 1}))
    if not notifs:
        return 0
    ids_msg = [n["source"]["id"] for n in notifs if n["source"]["kind"].startswith("message")]
    if ids_msg:
        db().messages.update_many({"_id": {"$in": ids_msg}, "type": "prive", "destinataire_id": uid}, {"$set": {"statut": "lu"}})
        db().messages.update_many({"_id": {"$in": ids_msg}, "type": "groupe"}, {"$pull": {"non_lu_par": uid}})
    r = db().notifications.update_many({"_id": {"$in": [n["_id"] for n in notifs]}},
                                       {"$set": {"statut": "lue", "date_lecture": maintenant()}})
    return r.modified_count
