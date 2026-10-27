"""Liste des pièces manquantes et brouillon de mail de relance, client par client.

Usage :
    python relancer.py DOSSIER_PORTEFEUILLE [--sortie relances]

DOSSIER_PORTEFEUILLE contient un sous-dossier par client avec :
    releve.csv ou releve.ofx    le relevé bancaire de la période
    justificatifs.csv           l'index des pièces reçues : fichier ; date ; tiers ; montant
    client.json (facultatif)    {"nom": "...", "prenom_contact": "...", "periode": "septembre 2026",
                                 "sans_piece": ["mots du libellé à ignorer"]}
Écrit pour chaque client : <client>-manquants.csv et <client>-relance.md, plus synthese.json.
"""
from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path

from montants import ZERO, formater_euros
from rapprochement import SANS_PIECE_PAR_DEFAUT, pieces_manquantes, rapprocher
from releves import Mouvement, lire_justificatifs, lire_releve

LIGNES_DANS_LE_MAIL = 15


def trouver_releve(dossier: Path) -> Path:
    for nom in ("releve.csv", "releve.ofx", "releve.qfx"):
        if (dossier / nom).exists():
            return dossier / nom
    raise FileNotFoundError(f"Aucun relevé (releve.csv ou releve.ofx) dans {dossier}")


def nature(mouvement: Mouvement) -> str:
    return "facture d'achat ou ticket" if mouvement.montant < 0 else "facture de vente"


def ligne_relance(mouvement: Mouvement) -> str:
    sens = "payé" if mouvement.montant < 0 else "reçu"
    return (f"- le {mouvement.jour:%d/%m/%Y}, {formater_euros(abs(mouvement.montant))} {sens}, "
            f"libellé « {mouvement.libelle} » : {nature(mouvement)}")


def rediger_mail(client: dict, manquants: list[Mouvement]) -> str:
    prenom = client.get("prenom_contact") or "Madame, Monsieur"
    periode = client.get("periode", "la période")
    total = sum((abs(m.montant) for m in manquants), ZERO)
    if not manquants:
        return (f"Objet : Pièces de {periode} : tout est complet\n\nBonjour {prenom},\n\n"
                f"Nous avons bien toutes les pièces de {periode}. Merci !\n\nBien cordialement,\n")
    lignes = [ligne_relance(m) for m in manquants[:LIGNES_DANS_LE_MAIL]]
    reste = len(manquants) - LIGNES_DANS_LE_MAIL
    if reste > 0:
        lignes.append(f"- et {reste} autre(s) opération(s) plus petite(s), listées dans le fichier joint")
    pluriel = "s" if len(manquants) > 1 else ""
    return "\n".join([
        f"Objet : {len(manquants)} justificatif{pluriel} à nous transmettre pour {periode}",
        "",
        f"Bonjour {prenom},",
        "",
        f"Pour avancer sur votre comptabilité de {periode}, il nous manque {len(manquants)} justificatif{pluriel}, "
        f"pour un total de {formater_euros(total)}. Les voici, du plus important au plus petit :",
        "",
        *lignes,
        "",
        "Une photo ou un PDF suffit. Vous pouvez répondre directement à ce mail ou les déposer dans votre espace.",
        "Si une opération est personnelle ou a été passée par erreur sur le compte de la société, dites-le-nous : "
        "nous la traiterons autrement.",
        "",
        "Merci d'avance,",
        "",
        "Bien cordialement,",
        "",
    ])


def traiter_client(dossier: Path, sortie: Path) -> dict:
    client = {"nom": dossier.name}
    if (dossier / "client.json").exists():
        client.update(json.loads((dossier / "client.json").read_text(encoding="utf-8")))
    sans_piece = SANS_PIECE_PAR_DEFAUT + tuple(m.lower() for m in client.get("sans_piece", []))
    mouvements = lire_releve(trouver_releve(dossier))
    justificatifs = lire_justificatifs(dossier / "justificatifs.csv") if (dossier / "justificatifs.csv").exists() else []
    rapprochements, orphelins = rapprocher(mouvements, justificatifs, sans_piece)
    manquants = pieces_manquantes(rapprochements)
    with (sortie / f"{dossier.name}-manquants.csv").open("w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.writer(fichier, delimiter=";")
        ecrivain.writerow(["date", "montant", "libelle", "piece_attendue"])
        for m in manquants:
            ecrivain.writerow([f"{m.jour:%d/%m/%Y}", str(m.montant).replace(".", ","), m.libelle, nature(m)])
    (sortie / f"{dossier.name}-relance.md").write_text(rediger_mail(client, manquants), encoding="utf-8")
    return {
        "client": client.get("nom", dossier.name),
        "mouvements": len(mouvements),
        "sans_piece_attendue": sum(1 for r in rapprochements if r.sans_piece),
        "rapproches": sum(1 for r in rapprochements if r.justificatif),
        "manquants": [{"date": f"{m.jour:%Y-%m-%d}", "montant": str(m.montant), "libelle": m.libelle}
                      for m in manquants],
        "total_manquant": str(sum((abs(m.montant) for m in manquants), ZERO)),
        "justificatifs_sans_mouvement": [{"fichier": j.fichier, "date": f"{j.jour:%Y-%m-%d}", "tiers": j.tiers,
                                          "montant": str(j.montant)} for j in orphelins],
    }


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("portefeuille", type=Path)
    parseur.add_argument("--sortie", type=Path, default=Path("relances"))
    args = parseur.parse_args()
    args.sortie.mkdir(parents=True, exist_ok=True)
    a_un_releve = lambda d: any((d / n).exists() for n in ("releve.csv", "releve.ofx", "releve.qfx"))  # noqa: E731
    dossiers = sorted(d for d in args.portefeuille.iterdir() if d.is_dir() and a_un_releve(d))
    if not dossiers and (args.portefeuille / "justificatifs.csv").exists():
        dossiers = [args.portefeuille]
    synthese = [traiter_client(d, args.sortie) for d in dossiers]
    synthese.sort(key=lambda s: -Decimal(s["total_manquant"]))
    (args.sortie / "synthese.json").write_text(json.dumps(synthese, ensure_ascii=False, indent=2), encoding="utf-8")
    for s in synthese:
        print(f"{s['client']} : {len(s['manquants'])} pièce(s) manquante(s), "
              f"{formater_euros(Decimal(s['total_manquant']))}, "
              f"{len(s['justificatifs_sans_mouvement'])} pièce(s) reçue(s) sans mouvement")
    print(f"Brouillons et listes dans {args.sortie}/")


if __name__ == "__main__":
    main()
