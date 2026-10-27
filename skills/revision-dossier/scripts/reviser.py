"""Passe un FEC aux contrôles de révision et produit la feuille de travail.

Usage :
    python reviser.py FEC_N.txt [--n1 FEC_N-1.txt] [--seuil-montant 5000] [--seuil-pourcent 20]
                      [--alsace-moselle] [--sortie dossier]

Sorties dans le dossier de sortie : revision.json, feuille-de-travail.md, feuille-de-travail.html.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from controles import (Constat, controle_benford, controle_comptes_attente, controle_dates_atypiques,
                       controle_ecarts, controle_equilibre, controle_numerotation, controle_sens,
                       controle_tiers)
from feuille import en_html, en_markdown, resume
from fec import FichierFec, lire_fec
from montants import formater_euros


def date_de_cloture(chemin: Path, fichier: FichierFec) -> date:
    """Date de clôture lue dans le nom normé SIRENFECAAAAMMJJ, sinon dernière date d'écriture."""
    trouve = re.search(r"FEC(\d{8})", chemin.name, re.IGNORECASE)
    if trouve:
        texte = trouve.group(1)
        return date(int(texte[:4]), int(texte[4:6]), int(texte[6:]))
    return max(l.ecriture_date for l in fichier.lignes if l.ecriture_date)


def reviser(chemin: Path, chemin_n1: Path | None, seuil_montant: Decimal, seuil_pourcent: Decimal,
            alsace_moselle: bool = False) -> tuple[dict, list[Constat], list[str]]:
    fichier = lire_fec(chemin)
    lignes = list(fichier.lignes)
    cloture = date_de_cloture(chemin, fichier)
    constats = (controle_equilibre(lignes) + controle_comptes_attente(lignes) + controle_numerotation(lignes)
                + controle_dates_atypiques(lignes, alsace_moselle) + controle_tiers(lignes, cloture)
                + controle_sens(lignes) + controle_benford(lignes))
    passes = ["equilibre", "comptes_attente", "numerotation", "dates_atypiques", "tiers_non_lettres",
              "sens_anormal", "benford"]
    if chemin_n1:
        constats += controle_ecarts(lignes, list(lire_fec(chemin_n1).lignes), seuil_montant, seuil_pourcent)
        passes.append("ecarts_n_n1")
    entete = {
        "dossier": chemin.name,
        "cloture": f"{cloture:%d/%m/%Y}",
        "nb_lignes": len(lignes),
        "n1": chemin_n1.name if chemin_n1 else "non fourni",
        "seuil": f"{formater_euros(seuil_montant, 0)} et {seuil_pourcent} %",
        "colonnes_manquantes": list(fichier.colonnes_manquantes),
        "avertissements": list(fichier.avertissements[:20]),
    }
    return entete, constats, passes


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("fec", type=Path)
    parseur.add_argument("--n1", type=Path)
    parseur.add_argument("--seuil-montant", type=Decimal, default=Decimal("5000"))
    parseur.add_argument("--seuil-pourcent", type=Decimal, default=Decimal("20"))
    parseur.add_argument("--alsace-moselle", action="store_true")
    parseur.add_argument("--sortie", type=Path, default=Path("revision"))
    args = parseur.parse_args()
    entete, constats, passes = reviser(args.fec, args.n1, args.seuil_montant, args.seuil_pourcent,
                                       args.alsace_moselle)
    args.sortie.mkdir(parents=True, exist_ok=True)
    donnees = {"entete": entete, "resume": resume(constats),
               "constats": [{**asdict(c), "montant": str(c.montant)} for c in constats]}
    (args.sortie / "revision.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.sortie / "feuille-de-travail.md").write_text(en_markdown(entete, constats, passes), encoding="utf-8")
    (args.sortie / "feuille-de-travail.html").write_text(en_html(entete, constats, passes), encoding="utf-8")
    compte = resume(constats)
    print(f"{len(constats)} points à justifier ({compte['fort']} importants, {compte['moyen']} à vérifier, "
          f"{compte['faible']} mineurs). Fichiers écrits dans {args.sortie}/")
    for avertissement in entete["avertissements"]:
        print("Attention :", avertissement)
    if entete["colonnes_manquantes"]:
        print("Colonnes obligatoires absentes :", ", ".join(entete["colonnes_manquantes"]))


if __name__ == "__main__":
    main()
