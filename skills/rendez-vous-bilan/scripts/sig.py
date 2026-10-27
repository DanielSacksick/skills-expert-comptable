"""Soldes intermédiaires de gestion, trésorerie et BFR à partir des soldes d'un FEC.

SIG : tableau du système développé du plan comptable général (règlement ANC n° 2014-03).
Le BFR et la trésorerie sont une lecture simplifiée du bilan, détaillée dans references/formules.md.
Convention : produits et ressources en positif, charges et emplois en positif, puis on soustrait.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from fec import LigneFec
from montants import ZERO


def _somme(soldes: dict[str, Decimal], prefixes: tuple[str, ...], exclus: tuple[str, ...] = (),
           signe: int = 1) -> Decimal:
    """Somme des soldes (débit - crédit) des comptes commençant par un préfixe, multipliée par signe."""
    total = sum((s for c, s in soldes.items() if c.startswith(prefixes) and not c.startswith(exclus)), ZERO)
    return total * signe


def produits(soldes, prefixes, exclus=()):
    return _somme(soldes, prefixes, exclus, -1)


def charges(soldes, prefixes, exclus=()):
    return _somme(soldes, prefixes, exclus, 1)


@dataclass(frozen=True)
class Sig:
    ventes_marchandises: Decimal
    cout_marchandises: Decimal
    marge_commerciale: Decimal
    production_exercice: Decimal
    consommations_tiers: Decimal
    valeur_ajoutee: Decimal
    subventions: Decimal
    impots_taxes: Decimal
    charges_personnel: Decimal
    ebe: Decimal
    resultat_exploitation: Decimal
    resultat_financier: Decimal
    resultat_courant: Decimal
    resultat_exceptionnel: Decimal
    impot_participation: Decimal
    resultat_net: Decimal
    chiffre_affaires: Decimal


def calculer_sig(soldes: dict[str, Decimal]) -> Sig:
    ventes_m = produits(soldes, ("707", "7097"))
    cout_m = charges(soldes, ("607", "6037", "6087", "6097"))
    marge = ventes_m - cout_m
    production = produits(soldes, ("70", "71", "72"), exclus=("707", "7097"))
    consommations = charges(soldes, ("60", "61", "62"), exclus=("607", "6037", "6087", "6097"))
    va = marge + production - consommations
    subventions = produits(soldes, ("74",))
    impots = charges(soldes, ("63",))
    personnel = charges(soldes, ("64",))
    ebe = va + subventions - impots - personnel
    resultat_exploitation = (ebe + produits(soldes, ("75", "781", "791"), exclus=("755",))
                             - charges(soldes, ("65", "681"), exclus=("655",)))
    financier = (produits(soldes, ("76", "786", "796", "755")) - charges(soldes, ("66", "686", "655")))
    courant = resultat_exploitation + financier
    exceptionnel = produits(soldes, ("77", "787", "797")) - charges(soldes, ("67", "687"))
    impot = charges(soldes, ("69",))
    return Sig(
        ventes_marchandises=ventes_m, cout_marchandises=cout_m, marge_commerciale=marge,
        production_exercice=production, consommations_tiers=consommations, valeur_ajoutee=va,
        subventions=subventions, impots_taxes=impots, charges_personnel=personnel, ebe=ebe,
        resultat_exploitation=resultat_exploitation, resultat_financier=financier, resultat_courant=courant,
        resultat_exceptionnel=exceptionnel, impot_participation=impot,
        resultat_net=courant + exceptionnel - impot,
        chiffre_affaires=produits(soldes, ("70",)),
    )


@dataclass(frozen=True)
class Bilan:
    tresorerie_nette: Decimal
    disponibilites: Decimal
    concours_bancaires: Decimal
    creances_clients: Decimal
    dettes_fournisseurs: Decimal
    bfr: Decimal
    capitaux_propres: Decimal
    emprunts: Decimal
    delai_clients_jours: Decimal | None
    delai_fournisseurs_jours: Decimal | None


def _jours(encours: Decimal, flux_annuel: Decimal) -> Decimal | None:
    if flux_annuel <= 0:
        return None
    return (encours * 365 / flux_annuel).quantize(Decimal("1"))


def calculer_bilan(soldes: dict[str, Decimal], sig: Sig) -> Bilan:
    tresorerie = {c: s for c, s in soldes.items() if c.startswith(("50", "51", "53", "54"))}
    disponibilites = sum((s for s in tresorerie.values() if s > 0), ZERO)
    concours = -sum((s for s in tresorerie.values() if s < 0), ZERO)
    clients = _somme(soldes, ("41",), exclus=("419",)) - _somme(soldes, ("491",), signe=-1)
    fournisseurs = _somme(soldes, ("40",), exclus=("409",), signe=-1)
    # BFR simplifié : stocks, tiers (hors associés 45 et attente 47) et régularisations
    bfr = _somme(soldes, ("3", "4"), exclus=("45", "47"))
    # le résultat de l'exercice n'est pas encore viré au compte 12 dans un FEC : on l'ajoute
    capitaux = _somme(soldes, ("10", "11", "12", "13", "14"), signe=-1) + sig.resultat_net
    achats = charges(soldes, ("60", "61", "62"))
    return Bilan(
        tresorerie_nette=disponibilites - concours,
        disponibilites=disponibilites,
        concours_bancaires=concours,
        creances_clients=clients,
        dettes_fournisseurs=fournisseurs,
        bfr=bfr,
        capitaux_propres=capitaux,
        emprunts=_somme(soldes, ("16",), signe=-1),
        delai_clients_jours=_jours(clients, sig.chiffre_affaires * Decimal("1.2")),
        delai_fournisseurs_jours=_jours(fournisseurs, achats * Decimal("1.2")),
    )


def tresorerie_par_mois(lignes: list[LigneFec]) -> list[tuple[str, Decimal]]:
    """Solde de trésorerie cumulé (comptes 50 à 54) à la fin de chaque mois."""
    mouvements: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for ligne in lignes:
        if ligne.compte_num.startswith(("50", "51", "53", "54")) and ligne.ecriture_date:
            mouvements[f"{ligne.ecriture_date:%Y-%m}"] += ligne.solde
    cumul, serie = ZERO, []
    for mois in sorted(mouvements):
        cumul += mouvements[mois]
        serie.append((mois, cumul))
    return serie


def chiffre_affaires_par_mois(lignes: list[LigneFec]) -> dict[int, Decimal]:
    """Chiffre d'affaires (comptes 70) par numéro de mois."""
    ca: dict[int, Decimal] = defaultdict(lambda: ZERO)
    for ligne in lignes:
        if ligne.compte_num.startswith("70") and ligne.ecriture_date:
            ca[ligne.ecriture_date.month] -= ligne.solde
    return dict(ca)
