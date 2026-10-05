# Projet 5 - Réseau social et messagerie (MongoDB, Python, Django, Streamlit)

Projet de la matière « Du SQL au NoSQL » (enseignant : FOTSO T. Valdez W.).
Application de démonstration d'un réseau social : publications, commentaires, amis, groupes,
messagerie privée et de groupe, notifications, confidentialité et statistiques, entièrement
adossée à MongoDB.

Compte de démonstration (prérempli dans l'écran de connexion) :

```
Pseudo       : valdez_237
Mot de passe : 1234
```

## 1. Installation (Windows)

1. **Python 3.10 ou plus récent** : installer depuis python.org en cochant « Add python.exe to PATH ».
   (Le PDF exige Python 3.8 minimum ; Streamlit récent demande une version plus récente.)
2. **MongoDB Community Server** (service démarré sur `localhost:27017`) et, si possible, **MongoDB Compass**.
3. **MongoDB Database Tools** (pour `mongoexport`, `mongoimport`, `mongodump`, `mongorestore`).
4. Rien d'autre : `run.bat` crée l'environnement virtuel `code\.venv` et installe `requirements.txt` au premier lancement.

Installation manuelle (si vous ne voulez pas utiliser `run.bat`) :

```bat
cd code
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Variables d'environnement (`code\.env`)

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `MONGODB_URI` | adresse de MongoDB (local ou Atlas) | `mongodb://localhost:27017/` |
| `MONGODB_DATABASE` | nom de la base | `reseau_social` |
| `API_URL` | adresse de l'API Django utilisée par Streamlit | `http://127.0.0.1:8000/api` |

Aucune valeur de connexion n'est écrite en dur ailleurs que dans `config.py` (qui lit `.env`).
Pour MongoDB Atlas, mettre l'URI `mongodb+srv://...` dans `MONGODB_URI`.

## 2. Lancement : `run.bat`

Double-cliquer sur `run.bat` (à la racine du projet). Il :

1. vérifie que Python est installé ;
2. crée l'environnement virtuel et installe les dépendances (première fois seulement) ;
3. vérifie la connexion à MongoDB (`scripts\verifier_mongo.py`) ;
4. **génère le jeu de données si la base est vide** (`generer_donnees.py`, une seule fois) ;
5. démarre l'API Django (fenêtre séparée, port 8000) puis l'interface Streamlit (le navigateur s'ouvre).

Console (exigence du PDF) : `code\.venv\Scripts\python main.py` ouvre un menu qui appelle `crud.py` et `agregations.py`.

## 3. Restauration : `restore_database.bat`

Après une démonstration (notifications lues, publication supprimée, groupe créé...), exécuter
`restore_database.bat`. Le script vide toutes les collections puis réimporte `exports\json\`
avec `scripts\restaurer.py` : mêmes `ObjectId`, mêmes dates, mêmes index. Les collections
`*_archives` créées pendant la démo disparaissent. La base redevient **exactement** l'état initial
(3 050 notifications, 10 publications de `valdez_237`, etc.).

Pourquoi ce choix ? Le fichier `exports\json` est à la fois le livrable demandé par le PDF et
l'état initial de référence : un seul jeu de fichiers à maintenir. Le PDF impose d'« archiver au lieu
de supprimer » : toute suppression de l'application copie les documents dans `<collection>_archives`
(voir section 6), donc rien n'est jamais détruit physiquement, même avant restauration.

## 4. Architecture

```
Projet/
|-- run.bat                      lance l'application
|-- restore_database.bat         restaure l'etat initial
|-- exports/
|   |-- json/                    un .json par collection (etat initial, reimportable)
|   `-- csv/                     un .csv par collection principale
|-- captures/                    captures d'ecran du rapport (a remplir)
`-- code/
    |-- README.md  requirements.txt  .env.example
    |-- config.py                connexion MongoDB + constantes (seul fichier de configuration)
    |-- generer_donnees.py       genere et insere le jeu de donnees (une seule fois)
    |-- crud.py                  Creer / Lire / Modifier / Supprimer (archiver) + index
    |-- agregations.py           les 5 agregations du PDF + statistiques
    |-- main.py                  menu console
    |-- backend/                 API Django (JSON) : manage.py, serveur/, api/views.py
    |-- frontend/                interface Streamlit : app.py, api_client.py, components/ (design system), vues/ (8 pages)
    |-- scripts/                 valider_donnees.py, restaurer.py, exporter.py, tests_fonctionnels.py, tests_interface.py
    `-- data/                    noms camerounais, catalogue d'images, textes, rapport_validation.txt
```

Les sept fichiers exigés par le PDF (`README.md`, `requirements.txt`, `config.py`, `generer_donnees.py`,
`crud.py`, `agregations.py`, `main.py`) sont à la racine de `code/`, aux noms demandés. Les dossiers
`backend/`, `frontend/`, `scripts/` et `data/` sont des ajouts. Les dossiers `exports/` et `captures/` (13 captures de l'interface deja presentes)
suivent l'arborescence de la clé USB (le dossier racine `Filière-Niveau-Groupe` et la clé sont à composer
au moment de la remise).

### Interface et design system (`frontend/`)

L'interface vise un rendu de produit SaaS : barre laterale marine (`#0F172A`), fond `#F8FAFC`, cartes blanches a bord `#E2E8F0`
(rayon 16 px, ombre tres legere), couleur primaire `#3B82F6`, police Inter (repli sur la police systeme hors ligne), icones Lucide.
Streamlit n'est qu'un moteur : son habillage par defaut est masque.

| Fichier | Role |
|---|---|
| `components/styles.py` | **seul endroit contenant du CSS** : jetons (couleurs, rayons), styles globaux, regles generees (icones, etat actif, badge) |
| `components/icons.py` | 40 icones Lucide en SVG (en ligne pour le HTML, en `mask-image` pour les boutons) |
| `components/sidebar.py` | carte utilisateur, navigation sans `st.radio`, Parametres, deconnexion |
| `components/post.py`, `messages.py`, `kpi.py`, `cards.py`, `empty_state.py`, `avatar.py`, `badges.py`, `buttons.py`, `helpers.py` | composants reutilisables |
| `vues/*.py` | une page par fichier : fil, profil, amis, groupes, messages, notifications, confidentialite, supervision |

Convention de **cles de widgets** (le CSS s'appuie dessus) : `card_*` = carte ; `nav_<page>` = entree du menu ; `ico-<icone>__*` = bouton avec
icone Lucide ; `tabs_*` = `st.pills` affiche en onglets soulignes ; `conv_*` / `convbtn_*` = ligne de conversation cliquable.
Pour ajouter une page : creer `vues/ma_page.py` (fonction `afficher(moi)`), l'ajouter a `NAVIGATION` (`sidebar.py`), a `ICONES_NAV` (`styles.py`) et a `VUES` (`app.py`).

Chaîne d'appel : `Streamlit (frontend)  ->  API Django (backend)  ->  crud.py / agregations.py  ->  MongoDB`.
Streamlit n'accède jamais à MongoDB. Django n'utilise pas son ORM (pas de base SQL) : c'est une
couche HTTP mince. `main.py` appelle directement `crud.py` et `agregations.py`.

## 5. MongoDB : collections, modélisation, index

### Embedding ou referencing : choix et justifications

| Lien | Choix | Pourquoi |
|---|---|---|
| utilisateur -> **amis** | **imbriqué** (`amis: [{ami_id, depuis, nb_messages}]`) | liste bornée (quelques dizaines), toujours lue avec l'utilisateur pour construire le fil ; l'amitié porte ses propres attributs (date, fréquence). |
| utilisateur -> préférences, confidentialité | imbriqué | petits tableaux/sous-documents lus à chaque connexion. |
| publication -> **commentaires** | **référencé** (collection `commentaires`) | nombre non borné et très variable (document de 16 Mo, réécritures coûteuses) ; on les charge à la demande. |
| commentaire -> réponses | imbriqué | toujours lues avec leur parent, peu nombreuses. |
| publication -> compteurs (j'aime, commentaires, partages) | **dénormalisé** et mis à jour par `$inc` | le fil est lu bien plus souvent qu'il n'est écrit : on évite un `count` par publication à chaque affichage. |
| groupe -> membres, admins, créateur | imbriqué (`membres`) + références (`createur_id`, `admins`) | un groupe compte au plus quelques centaines de membres ; `$size` donne le nombre de membres. |
| message -> expéditeur / destinataire / groupe | référencé | les messages sont très nombreux et croissent sans limite. |
| notification -> source | référencé (`source: {kind, id, de_user_id, groupe_id}`) | une notification pointe vers un événement existant (message, commentaire, publication, utilisateur). |
| hashtags | collection à part | fait le pont entre préférences, hashtags et publications. |

### Collections

| Collection | Rôle et champs principaux |
|---|---|
| `utilisateurs` | `pseudo` (unique), `code` (USR-0001), `nom`, `prenom`, `ville`, `region`, `bio`, `photo`, `date_inscription`, `infos` {`age`, `sexe`, `fonction`}, `categorie_activite` (influenceur / normal / timide_reseau), `preferences` (1 à 3), `amis`, `groupes_ids`, `confidentialite` {`messages_inconnus`, `ajout_groupe_inconnus`}, `role` (membre / superviseur), `historique_profil` |
| `publications` | `auteur_id`, `texte`, `medias` [{`image_id`, `variante`, `url`, `description`}], `date`, `visibilite` (public / amis / prive), `compteurs` {`aimes`, `commentaires`, `partages`}, `aimes` (ids), `hashtags`, `groupe_id`, `historique_modifs` |
| `commentaires` | `publication_id`, `auteur_id`, `contenu`, `date`, `aimes`, `reponses` [{`_id`, `auteur_id`, `contenu`, `date`}] |
| `messages` | `type` (prive / groupe), `expediteur_id`, `destinataire_id` ou `groupe_id`, `contenu`, `date`, `statut` (envoye / recu / lu), `non_lu_par` (groupes : membres qui ne l'ont pas lu), `pieces_jointes` |
| `groupes` | `nom`, `description`, `createur_id`, `admins`, `membres` [{`user_id`, `depuis`}], `type` (public / prive), `popularite` (populaire / moins_populaire / restreint), `date_creation` |
| `notifications` | `utilisateur_id`, `type` (jaime / commentaire / message / demande_ami), `source` {`kind`, `id`, `de_user_id`, `groupe_id`, `publication_id`}, `date`, `statut` (lue / non_lue), `date_lecture` |
| `hashtags` | `tag` (unique), `categories` (1 à 3 des 10 préférences) |
| `*_archives` | copies des documents « supprimés », avec `date_archivage` et `raison_archivage` |

Les images ne sont **jamais** stockées dans MongoDB : seulement leur URL Lorem Picsum
(`https://picsum.photos/id/{id}/640/480.jpg?random=N`, variante `?grayscale&blur=2&random=N`).

### Index (créés par `crud.creer_index()`)

| Index | Type | Requête servie |
|---|---|---|
| `utilisateurs.pseudo` | **unique** | connexion, détection des doublons de pseudo |
| `utilisateurs.code`, `hashtags.tag` | unique | identifiants lisibles, unicité des hashtags |
| `publications (auteur_id, date)` | **composé** | publications d'un auteur, de la plus récente |
| `publications (hashtags, date)` | composé multikey | publications par hashtag, fil par préférences |
| `publications (groupe_id, date)` | composé | publications d'un groupe |
| `commentaires (publication_id, date)` | composé | commentaires d'une publication |
| `messages (destinataire_id, statut, date)` | composé | messages non lus |
| `messages (groupe_id, date)` | composé | discussion d'un groupe |
| `messages (non_lu_par)` | multikey | messages de groupe non lus |
| `notifications (utilisateur_id, statut, date)` | composé | notifications triées, compteur de non lues |

Pour montrer l'utilisation d'un index (diapositive « Index » du rapport), dans Compass ou mongosh :

```js
db.notifications.find({utilisateur_id: ObjectId("000100000000000000000001"), statut: "non_lue"}).sort({date: -1}).explain("executionStats")
```
(`winningPlan` doit contenir `IXSCAN` sur `notif_user_statut_date`.)

### Agrégations (`agregations.py`)

| # | Agrégation | Étages clés |
|---|---|---|
| 1 | Top 10 des hashtags | `$unwind`, `$group`, `$sort`, `$limit` |
| 2 | Utilisateurs les plus actifs (publications + commentaires) | 2 x `$lookup`, `$size`, `$add` |
| 3 | Engagement moyen par publication selon la ville de l'auteur | `$lookup`, `$unwind`, `$add`, `$avg` |
| 4 | Messages par jour sur la dernière semaine | `$match`, `$dateToString`, `$group` |
| 5 | Groupes les plus peuplés avec le nom du créateur | `$size`, `$lookup`, `$unwind`, `$concat` |

Agrégations supplémentaires (graphiques) : sexe, tranches d'âge (`$bucket`), fonction, ville, catégorie d'activité,
volume de publications par catégorie (70/25/5), popularité des groupes (50/35/15), préférences (`$unwind`),
messages par type, notifications par type et statut, groupes par utilisateur. Tri des amis : `$unwind` + `$sort` + `$lookup`.
Suggestions d'amis (bonus) : amis d'amis par nombre d'amis communs.

**Date de référence de l'agrégation 4** : « la dernière semaine » est comptée à partir de la date du message le plus
récent (`agregations.date_reference_messages`), et non de la date du jour. Sans cela, une base générée il y a plusieurs
semaines n'afficherait plus rien.

## 6. Fonctionnement

- **Authentification** : `crud.authentifier` cherche le pseudo en base ; la vérification du mot de passe passe par
  `crud.verifier_mot_de_passe`, volontairement permissive pour la démo. Remplacer ce corps par un hash suffira pour une vraie authentification.
- **Publications** : texte + image du catalogue + hashtags + visibilité. Modifier une publication conserve l'ancienne version dans
  `historique_modifs` (`$set` et `$push` dans la même opération). Le « j'aime » utilise `$addToSet` + `$inc` (un seul j'aime par personne).
- **Fil** : publications des amis (public ou amis) + publications publiques dont les hashtags correspondent aux préférences + les siennes.
  Chaque publication affiche pourquoi elle est là (« Publiée par un ami » ou « Correspond à vos préférences : #nature »).
  Changer ses préférences (Mon profil) change immédiatement le fil. Pagination `skip/limit`, tri par date décroissante.
- **Amis** : tri par ancienneté de l'amitié ou par fréquence des conversations (`nb_messages`, incrémenté par `$inc` à chaque message).
- **Groupes** : le créateur est administrateur d'office, peut nommer d'autres administrateurs ; un admin peut retirer un membre
  (le retrait est tracé dans `groupes_archives`). Ajouter un inconnu à un groupe respecte `confidentialite.ajout_groupe_inconnus`.
- **Messagerie** : messages privés et de groupe dans la même collection. Un message privé d'un inconnu est refusé si le destinataire a désactivé
  `messages_inconnus`.
- **Notifications** : un message non lu produit une notification non lue ; elles sont triées de la plus récente à la plus ancienne,
  regroupées en Tout / Groupes / Conversations privées / Autres, avec « Pas encore vue » pour les non lues. « Tout marquer comme lu » met
  à jour les notifications **et** les messages sources (état stocké dans MongoDB, jamais simulé).
- **Confidentialité** : deux paramètres aujourd'hui, extensibles (ajouter une clé dans `crud._CLES_CONFIDENTIALITE` et dans la vue).
- **Suppressions** : publication (avec ses commentaires et les notifications liées), commentaire, retrait de membre : tout est copié dans
  `*_archives` avant retrait. Aucun commentaire orphelin ne reste dans `commentaires`.
- **Statistiques** : l'espace « Supervision » (rôle `superviseur`, réservé à `valdez_237`) affiche les compteurs globaux et les graphiques
  (barres et camemberts) ; chaque graphique montre le code de l'agrégation qui le produit.

### Scénario de démonstration conseillé

1. Connexion `valdez_237 / 1234`. Fil d'actualité : comparer « Mes amis » et « Mes préférences », lire les raisons d'affichage.
2. Mon profil : changer les préférences, revenir au fil et constater la différence. Voir ses 10 publications ; en modifier une, en supprimer une.
3. Amis : alterner les deux tris. Messages : ouvrir une conversation (les messages « Nouveau » passent à « Lu »).
4. Notifications : comparer les onglets, « Tout marquer comme lu », puis vérifier dans Compass `notifications.statut`.
5. Confidentialité : désactiver les messages des inconnus. Groupes : ouvrir un groupe, gérer les membres.
6. Supervision : compteurs, graphiques, code des agrégations.
7. Fin : `restore_database.bat`, puis relancer `run.bat` : tout est revenu à l'état initial.

## 7. Jeu de données et validation

Généré par `generer_donnees.py` (graine 42, donc reproductible) : 150 utilisateurs (150 noms camerounais distincts, pseudos
`nom_237`, `nom_enspd`, `nom_dla`), 30 groupes, 600 publications, 1 150 commentaires (+ réponses), ~2 450 messages,
3 050 notifications, 32 hashtags, 10 préférences. Le professeur `valdez_237` a 28 amis, 5 groupes et 10 publications.

- **70 / 25 / 5 %** : ce sont des parts du **volume de publications** (420 / 150 / 30 sur 600) : 15 influenceurs, 60 normaux, 75 timides.
- **50 / 35 / 15 %** : 15 groupes populaires, 11 moins populaires, 4 restreints (privés) ; 4,5 groupes privés étant impossible, 4/30 = 13,3 %.
- Tailles de groupes 85 / 35 / 25 / 10 ; des utilisateurs sont dans 0, 1 ou plusieurs groupes.

`python scripts\valider_donnees.py` vérifie les volumes, les proportions et la cohérence (aucune référence orpheline, états lu/non lu
identiques entre messages et notifications, compteurs exacts) et écrit `data\rapport_validation.txt`.
`generer_donnees.py` refuse d'exporter si une vérification échoue.

Tests de l'interface : `python scripts\tests_interface.py` (25 tests : connexion, 8 pages, notifications, j'aime, commentaires, publication,
messagerie, confidentialite, groupes, droits du superviseur ; simule les clics avec Streamlit AppTest, sans navigateur ni MongoDB).

Tests : `python scripts\tests_fonctionnels.py` (72 tests : CRUD, erreurs, messagerie, notifications, agrégations, restauration) ;
option `--mock` pour s'exécuter sans serveur MongoDB. **En mode réel, ce script régénère la base.**

## 8. Exporter la base pour la remise

Le PDF demande : **un fichier JSON par collection** et **un CSV par collection principale**, réimportables.
`generer_donnees.py` produit déjà ces fichiers dans `exports\`. Pour les refaire à partir de la base actuelle
(après avoir lancé `restore_database.bat`, pour exporter l'état initial) :

```bat
cd Projet
mongoexport --db=reseau_social --collection=utilisateurs  --jsonArray --out=exports\json\utilisateurs.json
mongoexport --db=reseau_social --collection=groupes       --jsonArray --out=exports\json\groupes.json
mongoexport --db=reseau_social --collection=publications  --jsonArray --out=exports\json\publications.json
mongoexport --db=reseau_social --collection=commentaires  --jsonArray --out=exports\json\commentaires.json
mongoexport --db=reseau_social --collection=messages      --jsonArray --out=exports\json\messages.json
mongoexport --db=reseau_social --collection=notifications --jsonArray --out=exports\json\notifications.json
mongoexport --db=reseau_social --collection=hashtags      --jsonArray --out=exports\json\hashtags.json

mongoexport --db=reseau_social --collection=groupes --type=csv --fields=code,nom,type,popularite,date_creation --out=exports\csv\groupes.csv
```

**Quand utiliser quoi**

| Outil | Format | À utiliser pour |
|---|---|---|
| `mongoexport` / `mongoimport` | JSON ou CSV (texte lisible) | **le rendu** : l'enseignant ouvre les fichiers et réimporte avec `mongoimport --db=reseau_social --collection=utilisateurs --jsonArray --file=exports\json\utilisateurs.json` |
| `mongodump` / `mongorestore` | BSON (binaire, tous les types et index) | une **sauvegarde fidèle** : `mongodump --db=reseau_social --out=sauvegarde` puis `mongorestore --drop --db=reseau_social sauvegarde\reseau_social` |

Le CSV est plat : listes et sous-documents y sont mal représentés (normal, cf. PDF) ; le JSON contient toutes les données.
Les exports de ce projet sont en JSON étendu (`{"$oid": ...}`, `{"$date": ...}`) : `mongoimport` et `scripts\restaurer.py` les lisent tous deux.
Si vous réimportez avec `mongoimport`, recréez les index en lançant `python -c "import crud; crud.creer_index()"` depuis `code\`.

## 9. Limites connues et choix à signaler

- Les données de démonstration (noms, légendes, commentaires) sont écrites **sans accents** ; l'interface, elle, est accentuée.
- Les images viennent de Lorem Picsum : l'affichage des publications nécessite une connexion Internet.
- Responsive : sous 1100 px la liste de messages passe au-dessus de la discussion ; sous 640 px les KPI passent sur 2 colonnes. Sur mobile,
  le menu lateral (natif Streamlit) reste ouvert apres un clic : le refermer avec la fleche en haut.
- L'interface n'a pas de bouton emoji dans le composer (aucune fonction associee) ; les indicateurs de supervision n'affichent aucune
  « evolution » inventee : leurs notes sont calculees sur les donnees reelles.
- Les rubriques de confidentialite non gerees par le backend (visibilite du profil, des activites, donnees personnelles) sont affichees « A venir ».
- Les photos de profil ne sont pas utilisées (avatars à initiales) : le champ `photo` existe dans le modèle.
- Le blocage d'un utilisateur (bonus du PDF) n'est pas implémenté ; suggestions d'amis et conversation chronologique le sont.
- Le fichier `description_images.txt` écrit l'URL de variante avec deux `?` ; le code utilise `&random=` (URL valide).
  Les images 8 et 31 reçoivent des légendes neutres.
- Livrables hors code (rapport PowerPoint, vidéo, captures, clé USB) : à produire par le groupe ; `exports/` et `captures/` sont prêts.
