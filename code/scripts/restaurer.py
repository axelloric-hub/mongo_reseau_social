"""
restaurer.py - Remet la base dans son etat initial (appele par restore_database.bat).

Principe : l'etat initial est le contenu de exports/json/ (cree par generer_donnees.py).
Le script vide toutes les collections de la base puis reinsere chaque fichier JSON, avec les
memes ObjectId et les memes dates, avant de recreer les index. Les collections *_archives
creees pendant la demonstration disparaissent car elles n'existent pas dans l'etat initial.
"""
import sys
from pathlib import Path

from bson import json_util

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
import crud  # noqa: E402


def restaurer(dossier_json=None, base=None):
    dossier_json = Path(dossier_json or config.DOSSIER_EXPORTS / "json")
    fichiers = sorted(dossier_json.glob("*.json"))
    if not fichiers:
        raise SystemExit("Aucun fichier JSON dans %s : lancez d'abord generer_donnees.py." % dossier_json)
    base = base if base is not None else config.get_db()
    for nom in base.list_collection_names():
        base.drop_collection(nom)
    total = 0
    for f in fichiers:
        docs = json_util.loads(f.read_text(encoding="utf-8"))
        if docs:
            base[f.stem].insert_many(docs)
        total += len(docs)
        print("  %-28s %6d documents" % (f.stem, len(docs)))
    crud.creer_index()
    print("Restauration terminee : %d documents dans la base %s." % (total, config.NOM_BASE))
    return total


if __name__ == "__main__":
    restaurer()
