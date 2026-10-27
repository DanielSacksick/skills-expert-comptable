"""Calcule les chiffres du rendez-vous bilan à partir du FEC de clôture (et de N-1 si fourni).

Usage :
    python analyser_bilan.py FEC_N.txt [--n1 FEC_N-1.txt] [--client "Nom affiché"] [--sortie rdv]

Écrit rdv/chiffres.json. Les messages, questions et conseils sont écrits ensuite dans
rdv/messages.json, puis la page est produite par rendre_page.py.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from fec import lire_fec, soldes_par_compte
from montants import ZERO, formater_euros, pourcentage
from sig import calculer_bilan, calculer_sig, chiffre_affaires_par_mois, tresorerie_par_mois


def analyser(chemin: Path) -> dict:
    fichier = lire_fec(chemin)
    lignes = list(fichier.lignes)
    soldes = soldes_par_compte(lignes)
    sig = calculer_sig(soldes)
    bilan = calculer_bilan(soldes, sig)
    dates = [l.ecriture_date for l in lignes if l.ecriture_date]
    return {
        "fichier": chemin.name,
        "exercice": max(dates).year,
        "sig": asdict(sig),
        "bilan": asdict(bilan),
        "tresorerie_mensuelle": tresorerie_par_mois(lignes),
        "ca_mensuel": chiffre_affaires_par_mois(lignes),
        "controle_resultat": sum((-s for c, s in soldes.items() if c[0] in "67"), ZERO),
        "avertissements": list(fichier.avertissements[:10]) + (
            [f"Colonnes absentes : {', '.join(fichier.colonnes_manquantes)}"] if fichier.colonnes_manquantes else []),
    }


def variations(n: dict, n1: dict) -> dict:
    resultat = {}
    for bloc in ("sig", "bilan"):
        for cle, valeur in n[bloc].items():
            precedent = n1[bloc].get(cle)
            if isinstance(valeur, Decimal) and isinstance(precedent, Decimal):
                resultat[cle] = {"ecart": valeur - precedent, "pourcent": pourcentage(valeur - precedent, abs(precedent))}
    return resultat


def en_json(objet):
    if isinstance(objet, Decimal):
        return str(objet)
    raise TypeError(type(objet))


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("fec", type=Path)
    parseur.add_argument("--n1", type=Path)
    parseur.add_argument("--client", default="")
    parseur.add_argument("--sortie", type=Path, default=Path("rdv"))
    args = parseur.parse_args()
    n = analyser(args.fec)
    if n["controle_resultat"] != n["sig"]["resultat_net"]:
        n["avertissements"].append(
            f"Le résultat des SIG ({n['sig']['resultat_net']}) diffère de produits moins charges "
            f"({n['controle_resultat']}) : un compte de classe 6 ou 7 n'est pas rattaché, vérifier le plan comptable.")
    donnees = {"client": args.client or args.fec.stem, "n": n}
    if args.n1:
        donnees["n1"] = analyser(args.n1)
        donnees["variations"] = variations(n, donnees["n1"])
    args.sortie.mkdir(parents=True, exist_ok=True)
    (args.sortie / "chiffres.json").write_text(json.dumps(donnees, default=en_json, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    sig = n["sig"]
    print(f"Exercice {n['exercice']} : CA {formater_euros(sig['chiffre_affaires'], 0)}, "
          f"résultat net {formater_euros(sig['resultat_net'], 0)}, "
          f"trésorerie nette {formater_euros(n['bilan']['tresorerie_nette'], 0)}.")
    print(f"Chiffres écrits dans {args.sortie}/chiffres.json")
    for avertissement in n["avertissements"]:
        print("Attention :", avertissement)


if __name__ == "__main__":
    main()
