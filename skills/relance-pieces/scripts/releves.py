"""Lecture des relevés bancaires (CSV ou OFX) et de l'index des justificatifs reçus (CSV).

CSV bancaire : séparateur ; ou , détecté, en-têtes reconnus sans tenir compte des accents ni de la casse :
    date | date opération | date valeur ; libellé | label | description ; montant | amount
    ou deux colonnes débit / crédit.
OFX : blocs <STMTTRN> avec DTPOSTED, TRNAMT, NAME et MEMO (SGML ou XML).
Index des justificatifs (CSV) : fichier ; date ; tiers ; montant (TTC, positif).
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from montants import ZERO, lire_montant


@dataclass(frozen=True)
class Mouvement:
    jour: date
    libelle: str
    montant: Decimal  # négatif = sortie d'argent


@dataclass(frozen=True)
class Justificatif:
    fichier: str
    jour: date
    tiers: str
    montant: Decimal


def normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sans_accents).strip().lower()


def lire_date_souple(texte: str) -> date:
    brut = texte.strip()[:10]
    for motif in (r"(\d{4})-(\d{2})-(\d{2})", r"(\d{2})/(\d{2})/(\d{4})", r"(\d{4})(\d{2})(\d{2})"):
        trouve = re.fullmatch(motif, brut[: len(brut)])
        if trouve:
            a, b, c = trouve.groups()
            return date(int(a), int(b), int(c)) if len(a) == 4 else date(int(c), int(b), int(a))
    raise ValueError(f"Date illisible : {texte!r}")


def _lire_texte(chemin: Path) -> str:
    contenu = chemin.read_bytes()
    for encodage in ("utf-8-sig", "cp1252"):
        try:
            return contenu.decode(encodage)
        except UnicodeDecodeError:
            continue
    return contenu.decode("latin-1")


def _lignes_csv(texte: str) -> list[dict[str, str]]:
    separateur = ";" if texte.splitlines()[0].count(";") >= texte.splitlines()[0].count(",") else ","
    lecteur = csv.DictReader(io.StringIO(texte), delimiter=separateur)
    return [{normaliser(k or ""): (v or "") for k, v in ligne.items()} for ligne in lecteur]


def _colonne(ligne: dict[str, str], *noms: str) -> str | None:
    for nom in noms:
        if nom in ligne:
            return nom
    return None


def lire_releve_csv(chemin: Path) -> list[Mouvement]:
    lignes = _lignes_csv(_lire_texte(chemin))
    if not lignes:
        return []
    modele = lignes[0]
    col_date = _colonne(modele, "date", "date operation", "date de l'operation", "date valeur")
    col_libelle = _colonne(modele, "libelle", "label", "description", "libelle operation")
    col_montant = _colonne(modele, "montant", "amount", "montant (eur)")
    col_debit, col_credit = _colonne(modele, "debit"), _colonne(modele, "credit")
    if not col_date or not col_libelle or not (col_montant or (col_debit and col_credit)):
        raise ValueError(f"Colonnes non reconnues dans {chemin.name} : {list(modele)}")
    mouvements = []
    for ligne in lignes:
        if col_montant:
            montant = lire_montant(ligne[col_montant])
        else:
            montant = lire_montant(ligne[col_credit]) - abs(lire_montant(ligne[col_debit]))
        mouvements.append(Mouvement(lire_date_souple(ligne[col_date]), ligne[col_libelle].strip(), montant))
    return mouvements


def lire_releve_ofx(chemin: Path) -> list[Mouvement]:
    texte = _lire_texte(chemin)
    mouvements = []
    for bloc in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", texte, flags=re.S | re.I):
        champ = lambda nom: (re.search(rf"<{nom}>([^<\r\n]*)", bloc, flags=re.I) or [None, ""])[1].strip()  # noqa: E731
        libelle = " ".join(p for p in (champ("NAME"), champ("MEMO")) if p)
        mouvements.append(Mouvement(lire_date_souple(champ("DTPOSTED")[:8]), libelle, lire_montant(champ("TRNAMT"))))
    return mouvements


def lire_releve(chemin: Path) -> list[Mouvement]:
    if chemin.suffix.lower() in (".ofx", ".qfx"):
        return lire_releve_ofx(chemin)
    return lire_releve_csv(chemin)


def lire_justificatifs(chemin: Path) -> list[Justificatif]:
    justificatifs = []
    for ligne in _lignes_csv(_lire_texte(chemin)):
        montant = abs(lire_montant(ligne.get("montant", "")))
        if montant == ZERO:
            continue
        justificatifs.append(Justificatif(ligne.get("fichier", "").strip(), lire_date_souple(ligne["date"]),
                                          ligne.get("tiers", "").strip(), montant))
    return justificatifs
