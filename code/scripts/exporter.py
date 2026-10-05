"""
exporter.py - Export de la base en JSON (toutes les collections) et CSV (collections principales).

Ce module existe pour produire exports/json et exports/csv exiges par le devoir, et pour
fournir l'etat initial utilise par restore_database.bat. Le JSON est ecrit en JSON etendu
(bson.json_util) : les ObjectId et les dates gardent leur type a la reimportation, avec
restaurer.py comme avec mongoimport --jsonArray.
"""
import csv
import sys
from pathlib import Path

from bson import json_util

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

COLLECTIONS_CSV = ["utilisateurs", "groupes", "publications", "commentaires", "messages", "notifications"]


def _aplatir(doc, prefixe=""):
    """Transforme un document en dictionnaire plat : sous-documents en 'a.b', listes en texte."""
    plat = {}
    for cle, val in doc.items():
        nom = prefixe + cle
        if isinstance(val, dict):
            plat.update(_aplatir(val, nom + "."))
        elif isinstance(val, list):
            if all(not isinstance(v, (dict, list)) for v in val):
                plat[nom] = ";".join(str(v) for v in val)
            else:
                plat[nom] = json_util.dumps(val, ensure_ascii=False)
        else:
            plat[nom] = str(val) if val is not None else ""
    return plat


def exporter(dossier=None, base=None):
    """Ecrit un .json par collection non vide et un .csv par collection principale. Renvoie les comptes."""
    dossier = Path(dossier or config.DOSSIER_EXPORTS)
    (dossier / "json").mkdir(parents=True, exist_ok=True)
    (dossier / "csv").mkdir(parents=True, exist_ok=True)
    base = base if base is not None else config.get_db()
    comptes = {}
    for nom in sorted(base.list_collection_names()):
        docs = list(base[nom].find({}).sort("_id", 1))
        if not docs:
            continue
        lignes = ",\n".join(json_util.dumps(d, ensure_ascii=False) for d in docs)
        (dossier / "json" / (nom + ".json")).write_text("[\n" + lignes + "\n]\n", encoding="utf-8")
        comptes[nom] = len(docs)
        if nom in COLLECTIONS_CSV:
            plats = [_aplatir(d) for d in docs]
            colonnes = list(dict.fromkeys(c for p in plats for c in p))
            with open(dossier / "csv" / (nom + ".csv"), "w", newline="", encoding="utf-8-sig") as f:
                ecrivain = csv.DictWriter(f, fieldnames=colonnes, delimiter=";", extrasaction="ignore")
                ecrivain.writeheader()
                ecrivain.writerows(plats)
    return comptes
