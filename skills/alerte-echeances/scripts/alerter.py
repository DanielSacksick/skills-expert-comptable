"""Échéances du mois pour tout le portefeuille, contrôle de trésorerie et brouillons de messages clients.

Usage :
    python alerter.py portefeuille.csv --mois 2026-12 [--sortie echeances]

Le format du portefeuille est décrit dans references/format-portefeuille.md.
Écrit echeances-AAAA-MM.md (calendrier et messages) et echeances-AAAA-MM.json.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from echeances import Client, Echeance, echeances_du_mois
from montants import ZERO, arrondir, formater_euros, lire_montant

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
TENDU = Decimal("0.8")


def _oui(texte: str) -> bool:
    return texte.strip().lower() in ("oui", "o", "1", "true", "vrai", "x")


def lire_portefeuille(chemin: Path) -> list[Client]:
    texte = chemin.read_text(encoding="utf-8-sig")
    separateur = ";" if texte.splitlines()[0].count(";") else ","
    clients = []
    for ligne in csv.DictReader(texte.splitlines(), delimiter=separateur):
        jour, mois = (int(x) for x in ligne["cloture"].split("/"))
        clients.append(Client(
            nom=ligne["client"].strip(), contact=ligne["contact"].strip(), tutoiement=_oui(ligne["tutoiement"]),
            regime_tva=ligne["regime_tva"].strip().lower(), jour_tva=int(ligne["jour_tva"] or 15),
            tva_par_periode=lire_montant(ligne["tva_par_periode"]), tva_annuelle_n1=lire_montant(ligne["tva_annuelle_n1"]),
            cloture=(jour, mois), soumis_is=_oui(ligne["soumis_is"]),
            is_dernier_exercice=lire_montant(ligne["is_dernier_exercice"]), cfe_n1=lire_montant(ligne["cfe_n1"]),
            cfe_mensualisee=_oui(ligne["cfe_mensualisee"]), effectif=int(ligne["effectif"] or 0),
            cotisations_mensuelles=lire_montant(ligne["cotisations_mensuelles"]),
            tresorerie=lire_montant(ligne["tresorerie"]),
        ))
    return clients


def total_a_payer(echeances: list[Echeance]) -> Decimal:
    return sum((e.montant for e in echeances if e.paiement and e.montant), ZERO)


def etat_tresorerie(client: Client, total: Decimal) -> str:
    if total == 0:
        return "rien à payer"
    if total > client.tresorerie:
        return "insuffisante"
    if total > client.tresorerie * TENDU:
        return "tendue"
    return "suffisante"


def rediger_message(client: Client, echeances: list[Echeance], mois: int) -> str:
    total = total_a_payer(echeances)
    a_payer = [e for e in echeances if e.paiement and e.montant]
    tu = client.tutoiement
    if not a_payer:
        return ""
    prevoir = "prévois" if tu else "prévoyez"
    lignes = [f"Bonjour {client.contact},", "",
              f"Petit point sur {MOIS[mois - 1]} : {prevoir} environ {formater_euros(arrondir(total, 100), 0)} "
              f"sur le compte pour les échéances suivantes :", ""]
    for e in a_payer:
        nature = e.nature if e.nature[1:2].isupper() else e.nature[0].lower() + e.nature[1:]
        lignes.append(f"- le {e.jour:%d/%m} : {nature}, environ "
                      f"{formater_euros(arrondir(e.montant, 10), 0)}")
    lignes.append("")
    if etat_tresorerie(client, total) in ("insuffisante", "tendue"):
        lignes.append(("D'après les derniers chiffres que nous avons, ton solde risque d'être juste. "
                       "Appelle-moi si tu veux qu'on regarde ensemble comment étaler." if tu else
                       "D'après les derniers chiffres que nous avons, votre solde risque d'être juste. "
                       "N'hésitez pas à m'appeler pour voir ensemble comment étaler les paiements."))
        lignes.append("")
    lignes.append("Les montants sont des estimations : nous confirmons chaque montant au moment de la déclaration."
                  if not tu else "Ce sont des estimations, je te confirme chaque montant au moment de la déclaration.")
    lignes += ["", "Bien à toi," if tu else "Bien cordialement,", ""]
    return "\n".join(lignes)


def en_markdown(annee: int, mois: int, par_client: dict[str, tuple[Client, list[Echeance]]]) -> str:
    titre = f"{MOIS[mois - 1]} {annee}"
    lignes = [f"# Échéances de {titre}", "", "## Trésorerie", "",
              "| Client | À payer (estimé) | Trésorerie connue | État |", "|---|---|---|---|"]
    ordre = sorted(par_client.values(), key=lambda ce: (
        ["insuffisante", "tendue", "suffisante", "rien à payer"].index(etat_tresorerie(ce[0], total_a_payer(ce[1]))),
        -total_a_payer(ce[1])))
    for client, echeances in ordre:
        total = total_a_payer(echeances)
        etat = etat_tresorerie(client, total)
        marque = {"insuffisante": "🔴 ", "tendue": "🟠 "}.get(etat, "")
        lignes.append(f"| {client.nom} | {formater_euros(total, 0)} | {formater_euros(client.tresorerie, 0)} | {marque}{etat} |")
    lignes += ["", "## Calendrier", "", "| Date | Client | Échéance | Montant estimé | Note |", "|---|---|---|---|---|"]
    toutes = sorted((e for _, ech in par_client.values() for e in ech), key=lambda e: (e.jour is None, e.jour, e.client))
    for e in toutes:
        date_txt = f"{e.jour:%d/%m}" if e.jour else "dans le mois"
        montant = formater_euros(e.montant, 0) if e.montant is not None else ("déclaration" if not e.paiement else "à calculer")
        lignes.append(f"| {date_txt} | {e.client} | {e.nature} | {montant} | {e.note} |")
    lignes += ["", "## Brouillons de messages", "",
               "À relire avant tout envoi. Aucun message n'est envoyé automatiquement.", ""]
    for client, echeances in ordre:
        message = rediger_message(client, echeances, mois)
        if message:
            lignes += [f"### {client.nom}", "", "```text", message.rstrip(), "```", ""]
    return "\n".join(lignes) + "\n"


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("portefeuille", type=Path)
    parseur.add_argument("--mois", required=True, help="AAAA-MM")
    parseur.add_argument("--sortie", type=Path, default=Path("echeances"))
    args = parseur.parse_args()
    annee, mois = (int(x) for x in args.mois.split("-"))
    par_client = {c.nom: (c, echeances_du_mois(c, annee, mois)) for c in lire_portefeuille(args.portefeuille)}
    args.sortie.mkdir(parents=True, exist_ok=True)
    nom = f"echeances-{annee}-{mois:02d}"
    (args.sortie / f"{nom}.md").write_text(en_markdown(annee, mois, par_client), encoding="utf-8")
    donnees = [{"client": c.nom, "tresorerie": str(c.tresorerie), "total": str(total_a_payer(e)),
                "etat_tresorerie": etat_tresorerie(c, total_a_payer(e)),
                "echeances": [{**asdict(x), "jour": x.jour.isoformat() if x.jour else None,
                               "montant": None if x.montant is None else str(x.montant)} for x in e]}
               for c, e in par_client.values()]
    (args.sortie / f"{nom}.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    alertes = [d for d in donnees if d["etat_tresorerie"] in ("insuffisante", "tendue")]
    print(f"{sum(len(d['echeances']) for d in donnees)} échéances pour {len(donnees)} clients, "
          f"{len(alertes)} trésorerie(s) à surveiller. Fichiers : {args.sortie}/{nom}.md et .json")


if __name__ == "__main__":
    main()
