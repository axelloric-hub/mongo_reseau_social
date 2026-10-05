"""
verifier_mongo.py - Verifie la connexion MongoDB et l'etat de la base (utilise par run.bat).

Codes de sortie : 0 = base prete ; 2 = MongoDB joignable mais base vide (il faut generer les
donnees) ; 1 = MongoDB injoignable. Les messages sont volontairement courts et explicites.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def main():
    try:
        base = config.get_db()
    except SystemExit as e:
        print("ERREUR :", e)
        return 1
    n = base.utilisateurs.count_documents({}) if "utilisateurs" in base.list_collection_names() else 0
    print("MongoDB joignable (%s), base '%s'." % (config.MONGO_URI, config.NOM_BASE))
    if n == 0:
        print("La base est vide : les donnees initiales vont etre generees.")
        return 2
    print("Base prete : %d utilisateurs." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
