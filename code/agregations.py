"""
agregations.py - Requetes d'agregation et statistiques du reseau social.

Les 5 agregations du PDF (Projet 5) sont en tete, puis les agregations supplementaires qui
alimentent les graphiques de l'espace superviseur. Chaque fonction renvoie une liste de
dictionnaires simples, prets a etre affiches en tableau ou en graphique.
Les pipelines sont volontairement lisibles : un etage par ligne, commente.
"""
from datetime import timedelta

import config


def db():
    return config.get_db()


# ---------------------------------------------------------------------------
# Les 5 agregations demandees par le PDF
# ---------------------------------------------------------------------------


def top_hashtags(limite=10):
    """
    1. Les 10 hashtags les plus utilises.
    $unwind eclate le tableau 'hashtags' (une ligne par hashtag et par publication),
    $group compte les occurrences, $sort + $limit gardent le top.
    """
    pipeline = [
        {"$unwind": "$hashtags"},
        {"$group": {"_id": "$hashtags", "utilisations": {"$sum": 1}}},
        {"$sort": {"utilisations": -1, "_id": 1}},
        {"$limit": int(limite)},
        {"$project": {"_id": 0, "hashtag": "$_id", "utilisations": 1}},
    ]
    return list(db().publications.aggregate(pipeline))


def utilisateurs_les_plus_actifs(limite=10):
    """
    2. Utilisateurs les plus actifs = publications + commentaires.
    Deux $lookup (publications puis commentaires de chaque utilisateur), $size pour compter,
    $add pour totaliser. Les reponses imbriquees ne sont pas comptees (commentaires de 1er niveau).
    """
    pipeline = [
        {"$lookup": {"from": "publications", "localField": "_id", "foreignField": "auteur_id", "as": "pubs"}},
        {"$lookup": {"from": "commentaires", "localField": "_id", "foreignField": "auteur_id", "as": "coms"}},
        {"$project": {"_id": 0, "pseudo": 1, "categorie_activite": 1, "publications": {"$size": "$pubs"},
                      "commentaires": {"$size": "$coms"}}},
        {"$addFields": {"activite": {"$add": ["$publications", "$commentaires"]}}},
        {"$sort": {"activite": -1, "pseudo": 1}},
        {"$limit": int(limite)},
    ]
    return list(db().utilisateurs.aggregate(pipeline))


def engagement_par_ville():
    """
    3. Taux d'engagement moyen par publication selon la ville de l'auteur.
    Engagement d'une publication = j'aime + commentaires + partages (compteurs deja stockes,
    donc aucun recalcul). $lookup vers l'auteur pour connaitre sa ville, puis $avg par ville.
    """
    pipeline = [
        {"$lookup": {"from": "utilisateurs", "localField": "auteur_id", "foreignField": "_id", "as": "auteur"}},
        {"$unwind": "$auteur"},
        {"$addFields": {"engagement": {"$add": ["$compteurs.aimes", "$compteurs.commentaires", "$compteurs.partages"]}}},
        {"$group": {"_id": "$auteur.ville", "engagement_moyen": {"$avg": "$engagement"}, "publications": {"$sum": 1}}},
        {"$sort": {"engagement_moyen": -1}},
        {"$project": {"_id": 0, "ville": "$_id", "engagement_moyen": 1, "publications": 1}},
    ]
    lignes = list(db().publications.aggregate(pipeline))
    for ligne in lignes:                      # arrondi cote Python (affichage a 2 decimales)
        ligne["engagement_moyen"] = round(ligne["engagement_moyen"], 2)
    return lignes


def date_reference_messages():
    """
    Date du message le plus recent. Sert de 'aujourd'hui' pour l'agregation 4 : sans cela, une
    base generee il y a plusieurs semaines n'aurait plus aucun message dans les 7 derniers jours.
    """
    dernier = db().messages.find_one({}, {"date": 1}, sort=[("date", -1)])
    return dernier["date"] if dernier else None


def messages_par_jour(jours=7):
    """
    4. Nombre de messages echanges par jour sur la derniere semaine.
    $match limite la periode (7 jours avant la date de reference), $dateToString tronque a la
    journee, $group compte, avec la repartition prive / groupe.
    """
    ref = date_reference_messages()
    if ref is None:
        return []
    debut = (ref - timedelta(days=jours - 1)).replace(hour=0, minute=0, second=0)
    pipeline = [
        {"$match": {"date": {"$gte": debut}}},
        {"$group": {"_id": {"jour": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "type": "$type"},
                    "n": {"$sum": 1}}},
        {"$sort": {"_id.jour": 1}},
        {"$project": {"_id": 0, "jour": "$_id.jour", "type": "$_id.type", "messages": "$n"}},
    ]
    return list(db().messages.aggregate(pipeline))


def groupes_les_plus_peuples(limite=10):
    """
    5. Groupes ayant le plus de membres, avec le nom du createur.
    $size compte les membres imbriques, $lookup va chercher le createur dans utilisateurs.
    """
    pipeline = [
        {"$addFields": {"nb_membres": {"$size": "$membres"}}},
        {"$sort": {"nb_membres": -1, "nom": 1}},
        {"$limit": int(limite)},
        {"$lookup": {"from": "utilisateurs", "localField": "createur_id", "foreignField": "_id", "as": "createur"}},
        {"$unwind": "$createur"},
        {"$project": {"_id": 0, "groupe": "$nom", "nb_membres": 1, "popularite": 1,
                      "createur": {"$concat": ["$createur.prenom", " ", "$createur.nom"]},
                      "pseudo_createur": "$createur.pseudo"}},
    ]
    return list(db().groupes.aggregate(pipeline))


# ---------------------------------------------------------------------------
# Agregations supplementaires pour l'espace superviseur
# ---------------------------------------------------------------------------


def stats_globales():
    """Compteurs generaux de la communaute (affiches en tete de l'espace superviseur)."""
    d = db()
    return {
        "utilisateurs": d.utilisateurs.count_documents({}),
        "groupes": d.groupes.count_documents({}),
        "publications": d.publications.count_documents({}),
        "commentaires": d.commentaires.count_documents({}),
        "messages": d.messages.count_documents({}),
        "notifications": d.notifications.count_documents({}),
        "notifications_non_lues": d.notifications.count_documents({"statut": "non_lue"}),
        "archives": sum(d[c].count_documents({}) for c in d.list_collection_names() if c.endswith("_archives")),
    }


def _repartition(collection, champ):
    """Repartition simple : nombre de documents par valeur d'un champ (reutilisee par plusieurs stats)."""
    pipeline = [{"$group": {"_id": "$" + champ, "n": {"$sum": 1}}}, {"$sort": {"n": -1, "_id": 1}},
                {"$project": {"_id": 0, "valeur": "$_id", "n": 1}}]
    return list(db()[collection].aggregate(pipeline))


def repartition_sexe():
    return _repartition("utilisateurs", "infos.sexe")


def repartition_fonction():
    return _repartition("utilisateurs", "infos.fonction")


def repartition_ville():
    return _repartition("utilisateurs", "ville")


def repartition_age():
    """Tranches d'age avec $bucket (bornes inferieures incluses, borne superieure exclue)."""
    pipeline = [{"$bucket": {"groupBy": "$infos.age", "boundaries": [0, 18, 25, 35, 45, 60, 120],
                             "default": "autre", "output": {"n": {"$sum": 1}}}}]
    noms = {0: "moins de 18", 18: "18-24", 25: "25-34", 35: "35-44", 45: "45-59", 60: "60 et plus"}
    return [{"valeur": noms.get(r["_id"], str(r["_id"])), "n": r["n"], "ordre": r["_id"] if isinstance(r["_id"], int) else 999}
            for r in db().utilisateurs.aggregate(pipeline)]


def repartition_categorie_activite():
    """Nombre d'UTILISATEURS par categorie d'activite (influenceur / normal / timide_reseau)."""
    return _repartition("utilisateurs", "categorie_activite")


def volume_publications_par_categorie():
    """
    Nombre de PUBLICATIONS produites par chaque categorie d'utilisateurs, avec le pourcentage :
    c'est cette repartition qui doit valoir environ 70 / 25 / 5.
    """
    pipeline = [
        {"$lookup": {"from": "utilisateurs", "localField": "auteur_id", "foreignField": "_id", "as": "auteur"}},
        {"$unwind": "$auteur"},
        {"$group": {"_id": "$auteur.categorie_activite", "publications": {"$sum": 1}}},
        {"$sort": {"publications": -1}},
    ]
    lignes = list(db().publications.aggregate(pipeline))
    total = sum(r["publications"] for r in lignes) or 1
    return [{"categorie": r["_id"], "publications": r["publications"],
             "pourcentage": round(100 * r["publications"] / total, 1)} for r in lignes]


def repartition_popularite_groupes():
    return _repartition("groupes", "popularite")


def tailles_des_groupes():
    return list(db().groupes.aggregate([
        {"$project": {"_id": 0, "groupe": "$nom", "nb_membres": {"$size": "$membres"}}}, {"$sort": {"nb_membres": -1}}]))


def preferences_frequentes():
    """Preferences les plus choisies ($unwind du tableau 'preferences' des utilisateurs)."""
    pipeline = [{"$unwind": "$preferences"}, {"$group": {"_id": "$preferences", "n": {"$sum": 1}}},
                {"$sort": {"n": -1, "_id": 1}}, {"$project": {"_id": 0, "preference": "$_id", "n": 1}}]
    return list(db().utilisateurs.aggregate(pipeline))


def messages_par_type():
    return _repartition("messages", "type")


def notifications_par_type_et_statut():
    pipeline = [{"$group": {"_id": {"type": "$type", "statut": "$statut"}, "n": {"$sum": 1}}},
                {"$sort": {"_id.type": 1}}, {"$project": {"_id": 0, "type": "$_id.type", "statut": "$_id.statut", "n": 1}}]
    return list(db().notifications.aggregate(pipeline))


def groupes_par_utilisateur():
    """Combien d'utilisateurs appartiennent a 0, 1, 2... groupes (verifie le realisme de la repartition)."""
    pipeline = [{"$project": {"nb": {"$size": "$groupes_ids"}}}, {"$group": {"_id": "$nb", "utilisateurs": {"$sum": 1}}},
                {"$sort": {"_id": 1}}, {"$project": {"_id": 0, "nb_groupes": "$_id", "utilisateurs": 1}}]
    return list(db().utilisateurs.aggregate(pipeline))
