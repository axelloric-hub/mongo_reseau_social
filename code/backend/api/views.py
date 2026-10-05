"""
views.py - API JSON de l'application (couche Django).

Ce module existe pour separer le backend de l'interface Streamlit : Streamlit n'accede jamais a
MongoDB, il appelle uniquement cette API. Chaque action est declaree dans la table ACTIONS
(nom -> fonction qui prend les parametres et appelle crud.py / agregations.py). Une seule vue,
'dispatch', recoit la requete, execute l'action, convertit le resultat en JSON
(ObjectId -> texte, datetime -> ISO 8601) et traduit les erreurs metier en codes HTTP.
"""
import inspect
import json
import random
from datetime import date, datetime

from bson import ObjectId
from django.http import JsonResponse

import agregations
import config
import crud
from data.catalogue_images import HASHTAGS, IMAGES, construire_url


def en_json(valeur):
    """Convertit recursivement les types MongoDB/Python non serialisables en JSON."""
    if isinstance(valeur, ObjectId):
        return str(valeur)
    if isinstance(valeur, (datetime, date)):
        return valeur.isoformat()
    if isinstance(valeur, dict):
        return {k: en_json(v) for k, v in valeur.items()}
    if isinstance(valeur, (list, tuple)):
        return [en_json(v) for v in valeur]
    return valeur


def _creer_publication(p):
    """Construit le media a partir de l'id d'image du catalogue (MongoDB ne stocke que l'URL)."""
    medias = []
    if p.get("image_id") not in (None, ""):
        image_id = int(p["image_id"])
        if image_id not in IMAGES:
            raise crud.SaisieInvalide("Image inconnue.")
        variante = "grayscale" if p.get("variante") == "grayscale" else "principale"
        medias.append({"type": "image", "image_id": image_id, "variante": variante,
                       "description": IMAGES[image_id][0], "url": construire_url(image_id, variante, random.randint(1, 999))})
    return crud.creer_publication(p["user_id"], p.get("texte", ""), medias, p.get("hashtags", []),
                                  p.get("visibilite", "public"), p.get("groupe_id") or None)


# Agregations exposees a l'espace superviseur (nom -> fonction) ; 'source' renvoie leur code.
AGREGATIONS = {
    "top_hashtags": agregations.top_hashtags,
    "utilisateurs_actifs": agregations.utilisateurs_les_plus_actifs,
    "engagement_par_ville": agregations.engagement_par_ville,
    "messages_par_jour": agregations.messages_par_jour,
    "groupes_peuples": agregations.groupes_les_plus_peuples,
    "repartition_sexe": agregations.repartition_sexe,
    "repartition_age": agregations.repartition_age,
    "repartition_fonction": agregations.repartition_fonction,
    "repartition_ville": agregations.repartition_ville,
    "categories_utilisateurs": agregations.repartition_categorie_activite,
    "volume_publications": agregations.volume_publications_par_categorie,
    "popularite_groupes": agregations.repartition_popularite_groupes,
    "tailles_groupes": agregations.tailles_des_groupes,
    "preferences": agregations.preferences_frequentes,
    "messages_par_type": agregations.messages_par_type,
    "notifications_par_type": agregations.notifications_par_type_et_statut,
    "groupes_par_utilisateur": agregations.groupes_par_utilisateur,
}


def _agregation(p):
    nom = p.get("nom")
    if nom not in AGREGATIONS:
        raise crud.DocumentIntrouvable("Agregation inconnue.")
    return AGREGATIONS[nom]()


def _source_agregation(p):
    nom = p.get("nom")
    if nom not in AGREGATIONS:
        raise crud.DocumentIntrouvable("Agregation inconnue.")
    return {"source": inspect.getsource(AGREGATIONS[nom])}


def _superviseur(p):
    """Les statistiques globales sont reservees au compte superviseur."""
    if crud.get_utilisateur(p["user_id"])["role"] != "superviseur":
        raise crud.ActionInterdite("Espace reserve au superviseur.")


def _stats(p):
    _superviseur(p)
    return agregations.stats_globales()


# Table des actions : nom -> fonction(parametres) -> resultat
ACTIONS = {
    # authentification et profil
    "login": lambda p: crud.authentifier(p.get("pseudo"), p.get("mot_de_passe")),
    "profil": lambda p: crud.get_utilisateur(p["user_id"]),
    "maj_profil": lambda p: crud.mettre_a_jour_profil(p["user_id"], p.get("bio"), p.get("ville"), None, p.get("age")),
    "confidentialite": lambda p: crud.changer_confidentialite(p["user_id"], p["cle"], p["valeur"]),
    "preferences": lambda p: crud.modifier_preferences(p["user_id"], p["preferences"]),
    "categories": lambda p: config.CATEGORIES_PREFERENCES,
    "rechercher": lambda p: crud.rechercher_utilisateurs(p.get("texte")),
    # publications
    "fil": lambda p: crud.fil_actualite(p["user_id"], p.get("page", 1), p.get("par_page", 10), p.get("mode", "pour_moi")),
    "publications_utilisateur": lambda p: crud.publications_utilisateur(p["auteur_id"], p["user_id"], p.get("page", 1), p.get("par_page", 10)),
    "publications_groupe": lambda p: crud.publications_groupe(p["groupe_id"], p["user_id"], p.get("page", 1), p.get("par_page", 10)),
    "publications_hashtag": lambda p: crud.publications_par_hashtag(p["tag"], p.get("user_id"), p.get("page", 1), p.get("par_page", 10)),
    "hashtags": lambda p: crud.lister_hashtags(),
    "images": lambda p: [{"id": i, "description": v[0], "categories": v[1]} for i, v in IMAGES.items()],
    "creer_publication": lambda p: {"_id": _creer_publication(p)},
    "modifier_publication": lambda p: crud.modifier_publication(p["pub_id"], p["user_id"], p.get("texte"), p.get("hashtags"), p.get("visibilite")),
    "supprimer_publication": lambda p: crud.supprimer_publication(p["pub_id"], p["user_id"]),
    "aimer": lambda p: crud.aimer_publication(p["pub_id"], p["user_id"]),
    "partager": lambda p: {"ok": crud.partager_publication(p["pub_id"])},
    # commentaires
    "commentaires": lambda p: crud.lister_commentaires(p["pub_id"]),
    "ajouter_commentaire": lambda p: {"_id": crud.ajouter_commentaire(p["pub_id"], p["user_id"], p.get("contenu"), p.get("parent_id"))},
    "supprimer_commentaire": lambda p: crud.supprimer_commentaire(p["commentaire_id"], p["user_id"]),
    # amis
    "amis": lambda p: crud.lister_amis(p["user_id"], p.get("tri", "anciennete")),
    "suggestions": lambda p: crud.suggestions_amis(p["user_id"]),
    "demande_ami": lambda p: {"_id": crud.envoyer_demande_ami(p["user_id"], p["cible_id"])},
    "accepter_ami": lambda p: {"ok": crud.accepter_demande_ami(p["user_id"], p["notification_id"])},
    # groupes
    "groupes": lambda p: crud.lister_groupes(p.get("user_id"), p.get("miens", False)),
    "groupe": lambda p: crud.detail_groupe(p["groupe_id"], p.get("user_id")),
    "creer_groupe": lambda p: {"_id": crud.creer_groupe(p["user_id"], p.get("nom"), p.get("description"), p.get("type", "public"))},
    "ajouter_membre": lambda p: {"ok": crud.ajouter_membre(p["groupe_id"], p["cible_id"], p["user_id"])},
    "promouvoir_admin": lambda p: {"ok": crud.promouvoir_admin(p["groupe_id"], p["cible_id"], p["user_id"])},
    "retirer_membre": lambda p: {"ok": crud.retirer_membre(p["groupe_id"], p["cible_id"], p["user_id"])},
    # messagerie
    "conversations": lambda p: crud.conversations(p["user_id"]),
    "conversation": lambda p: crud.conversation(p["user_id"], p["autre_id"], p.get("page", 1), p.get("par_page", 30)),
    "envoyer_prive": lambda p: {"_id": crud.envoyer_message_prive(p["user_id"], p["dest_id"], p.get("contenu"))},
    "messages_groupe": lambda p: crud.messages_groupe(p["groupe_id"], p["user_id"], p.get("page", 1), p.get("par_page", 30)),
    "envoyer_groupe": lambda p: {"_id": crud.envoyer_message_groupe(p["user_id"], p["groupe_id"], p.get("contenu"))},
    "messages_non_lus": lambda p: crud.messages_non_lus(p["user_id"], p.get("page", 1), p.get("par_page", 20)),
    # notifications
    "notifications": lambda p: crud.lister_notifications(p["user_id"], p.get("categorie", "tous"), p.get("non_lues_seulement", False), p.get("page", 1), p.get("par_page", 15)),
    "compter_notifications": lambda p: crud.compter_notifications(p["user_id"]),
    "marquer_lues": lambda p: {"modifiees": crud.marquer_notifications_lues(p["user_id"], p.get("categorie", "tous"), p.get("ids"))},
    # supervision
    "stats": _stats,
    "agregation": _agregation,
    "source_agregation": _source_agregation,
}


def sante(request):
    """Verifie que l'API et MongoDB repondent (utilise par run.bat et par l'ecran de connexion)."""
    try:
        config.get_db().command("ping")
        return JsonResponse({"api": "ok", "mongodb": "ok", "base": config.NOM_BASE})
    except BaseException as e:
        return JsonResponse({"api": "ok", "mongodb": "indisponible", "detail": str(e)}, status=503)


def dispatch(request, action):
    """Execute l'action demandee ; GET (query string) ou POST (corps JSON) sont acceptes."""
    if action not in ACTIONS:
        return JsonResponse({"erreur": "Action inconnue : %s" % action}, status=404)
    try:
        params = dict(request.GET.items())
        if request.method == "POST" and request.body:
            params.update(json.loads(request.body.decode("utf-8")))
        resultat = ACTIONS[action](params)
        return JsonResponse({"donnees": en_json(resultat)})
    except crud.ErreurMetier as e:
        return JsonResponse({"erreur": str(e)}, status=e.code_http)
    except KeyError as e:
        return JsonResponse({"erreur": "Parametre manquant : %s" % e}, status=400)
    except (ValueError, TypeError) as e:
        return JsonResponse({"erreur": "Saisie invalide : %s" % e}, status=400)
    except SystemExit as e:                      # MongoDB injoignable (leve par config.get_db)
        return JsonResponse({"erreur": str(e)}, status=503)
