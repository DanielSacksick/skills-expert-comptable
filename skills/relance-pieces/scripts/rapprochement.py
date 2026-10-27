"""Rapprochement des mouvements bancaires avec les justificatifs reçus.

Règle : un justificatif couvre un mouvement s'il a le même montant (au centime) et une date
comprise entre 60 jours avant et 10 jours après le mouvement. Entre plusieurs candidats,
on garde celui dont le nom de tiers ressemble le plus au libellé bancaire, puis le plus proche en date.
Chaque justificatif ne sert qu'une fois.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from releves import Justificatif, Mouvement, normaliser

AVANT, APRES = timedelta(days=60), timedelta(days=10)
# mouvements qui n'appellent pas de pièce du client (le cabinet a déjà le document ou le produit)
SANS_PIECE_PAR_DEFAUT = ("frais bancaires", "commission", "cotisation carte", "urssaf", "dgfip", "impot",
                         "salaire", "virement interne", "vir interne", "agios", "interets debiteurs")
MOTS_VIDES = {"sarl", "sas", "sa", "eurl", "prlv", "sepa", "vir", "cb", "carte", "paiement", "de", "du", "la", "le",
              "les", "et", "des", "facture", "fac", "virement", "recu", "emis", "inst"}


@dataclass(frozen=True)
class Rapprochement:
    mouvement: Mouvement
    justificatif: Justificatif | None
    sans_piece: bool = False


def mots(texte: str) -> set[str]:
    return {m for m in re.findall(r"[a-z0-9]{3,}", normaliser(texte)) if m not in MOTS_VIDES}


def ressemblance(libelle: str, tiers: str) -> float:
    a, b = mots(libelle), mots(tiers)
    return len(a & b) / len(b) if b else 0.0


def ne_demande_pas_de_piece(mouvement: Mouvement, motifs: tuple[str, ...]) -> bool:
    libelle = normaliser(mouvement.libelle)
    return any(motif in libelle for motif in motifs)


def rapprocher(mouvements: list[Mouvement], justificatifs: list[Justificatif],
               sans_piece: tuple[str, ...] = SANS_PIECE_PAR_DEFAUT) -> tuple[list[Rapprochement], list[Justificatif]]:
    """Renvoie (un rapprochement par mouvement, justificatifs restés sans mouvement)."""
    candidats = []
    for i, mouvement in enumerate(mouvements):
        if ne_demande_pas_de_piece(mouvement, sans_piece):
            continue
        for j, justificatif in enumerate(justificatifs):
            if justificatif.montant != abs(mouvement.montant):
                continue
            if not (mouvement.jour - AVANT <= justificatif.jour <= mouvement.jour + APRES):
                continue
            ecart = abs((mouvement.jour - justificatif.jour).days)
            candidats.append((-ressemblance(mouvement.libelle, justificatif.tiers), ecart, i, j))
    pris_m, pris_j, trouves = set(), set(), {}
    for _, _, i, j in sorted(candidats):
        if i not in pris_m and j not in pris_j:
            pris_m.add(i)
            pris_j.add(j)
            trouves[i] = justificatifs[j]
    resultat = [Rapprochement(m, trouves.get(i), ne_demande_pas_de_piece(m, sans_piece))
                for i, m in enumerate(mouvements)]
    orphelins = [j for k, j in enumerate(justificatifs) if k not in pris_j]
    return resultat, orphelins


def pieces_manquantes(rapprochements: list[Rapprochement]) -> list[Mouvement]:
    """Mouvements sans justificatif, du plus gros montant au plus petit."""
    manquants = [r.mouvement for r in rapprochements if r.justificatif is None and not r.sans_piece]
    return sorted(manquants, key=lambda m: (-abs(m.montant), m.jour))
