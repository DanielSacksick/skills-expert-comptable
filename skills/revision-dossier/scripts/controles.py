"""Contrôles de révision avant clôture sur un FEC.

Chaque contrôle renvoie une liste de Constat. Un constat n'est jamais une erreur
certaine : c'est un point que l'expert-comptable doit justifier ou corriger.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from benford import ECHANTILLON_MINIMUM, NON_CONFORME, analyser
from calendrier import est_week_end, nom_ferie
from cycles import commentaire_sens, cycle_du_compte, sens_normal
from fec import LigneFec, libelles_comptes, soldes_par_compte, soldes_par_tiers
from montants import ZERO, formater_euros, pourcentage

FORT, MOYEN, FAIBLE = "fort", "moyen", "faible"
COMPTES_ATTENTE = ("471", "472", "473", "474", "475")
COMPTES_TIERS = ("40", "41")


@dataclass(frozen=True)
class Constat:
    controle: str
    cycle: str
    importance: str
    compte: str
    libelle: str
    montant: Decimal
    detail: str
    a_faire: str


def _journaux_a_nouveaux(lignes: list[LigneFec]) -> set[str]:
    return {l.journal_code for l in lignes
            if l.journal_code.upper() in ("AN", "RAN") or "nouveau" in l.journal_lib.lower()}


def controle_equilibre(lignes: list[LigneFec]) -> list[Constat]:
    constats = []
    par_journal: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for l in lignes:
        par_journal[l.journal_code] += l.solde
    for journal, ecart in sorted(par_journal.items()):
        if ecart:
            constats.append(Constat("equilibre", "Tous cycles", FORT, journal, f"Journal {journal}", ecart,
                                    f"Le journal {journal} n'est pas équilibré : écart de {formater_euros(ecart)}.",
                                    "Retrouver l'écriture déséquilibrée avant toute autre analyse."))
    return constats


def controle_comptes_attente(lignes: list[LigneFec]) -> list[Constat]:
    libelles = libelles_comptes(lignes)
    return [Constat("comptes_attente", cycle_du_compte(compte), FORT, compte, libelles[compte], solde,
                    f"Compte d'attente non soldé à la clôture : {formater_euros(solde)}.",
                    "Identifier chaque mouvement, le reclasser sur le bon compte, demander la pièce au client.")
            for compte, solde in sorted(soldes_par_compte(lignes).items())
            if compte.startswith(COMPTES_ATTENTE) and solde]


def _rang(numero: str) -> int | None:
    trouve = re.search(r"(\d+)\D*$", numero)
    return int(trouve.group(1)) if trouve else None


def controle_numerotation(lignes: list[LigneFec]) -> list[Constat]:
    """Trous dans la suite des numéros d'écriture, journal par journal."""
    par_journal: dict[str, dict[int, str]] = defaultdict(dict)
    for l in lignes:
        rang = _rang(l.ecriture_num)
        if rang is not None:
            par_journal[l.journal_code][rang] = l.ecriture_num
    constats = []
    for journal, numeros in sorted(par_journal.items()):
        rangs = sorted(numeros)
        manquants = [r for r in range(rangs[0], rangs[-1] + 1) if r not in numeros]
        if manquants:
            modele = numeros[rangs[0]]
            chiffres = re.search(r"(\d+)\D*$", modele)
            largeur = len(chiffres.group(1))
            noms = [f"{modele[:chiffres.start(1)]}{r:0{largeur}d}{modele[chiffres.end(1):]}" for r in manquants[:10]]
            constats.append(Constat("numerotation", "Tous cycles", FORT, journal, f"Journal {journal}", ZERO,
                                    f"{len(manquants)} numéro(s) d'écriture manquant(s) : {', '.join(noms)}.",
                                    "Demander pourquoi ces écritures ont disparu (suppression, renumérotation, export partiel)."))
    return constats


def controle_dates_atypiques(lignes: list[LigneFec], alsace_moselle: bool = False) -> list[Constat]:
    exclus = _journaux_a_nouveaux(lignes)
    ecritures: dict[tuple[str, str], list[LigneFec]] = defaultdict(list)
    for l in lignes:
        if l.ecriture_date and l.journal_code not in exclus:
            ecritures[(l.journal_code, l.ecriture_num)].append(l)
    constats = []
    for (journal, numero), groupe in sorted(ecritures.items()):
        jour = groupe[0].ecriture_date
        ferie = nom_ferie(jour, alsace_moselle)
        if not (ferie or est_week_end(jour)):
            continue
        quand = ferie or ("samedi" if jour.weekday() == 5 else "dimanche")
        total = sum((l.debit for l in groupe), ZERO)
        constats.append(Constat("dates_atypiques", cycle_du_compte(groupe[0].compte_num), MOYEN, groupe[0].compte_num,
                                groupe[0].ecriture_lib, total,
                                f"Écriture {numero} du {jour:%d/%m/%Y} ({quand}), journal {journal}.",
                                "Vérifier la pièce et qui a passé l'écriture. Normal pour un paiement carte, suspect pour une OD manuelle."))
    return constats


def controle_tiers(lignes: list[LigneFec], cloture: date, jours_anciennete: int = 180) -> list[Constat]:
    """Soldes de tiers anciens non lettrés et tiers soldés mais non lettrés."""
    par_tiers: dict[tuple[str, str], list[LigneFec]] = defaultdict(list)
    for l in lignes:
        if l.comp_aux_num and l.compte_num.startswith(COMPTES_TIERS):
            par_tiers[(l.compte_num, l.comp_aux_num)].append(l)
    constats = []
    for (compte, tiers), groupe in sorted(par_tiers.items()):
        ouvertes = [l for l in groupe if not l.ecriture_let]
        if not ouvertes:
            continue
        solde = sum((l.solde for l in groupe), ZERO)
        plus_ancienne = min(l.piece_date or l.ecriture_date for l in ouvertes)
        age = (cloture - plus_ancienne).days
        nom = groupe[0].comp_aux_lib or tiers
        if solde == 0:
            constats.append(Constat("tiers_non_lettres", cycle_du_compte(compte), FAIBLE, compte, nom, ZERO,
                                    f"{nom} ({tiers}) est soldé mais {len(ouvertes)} ligne(s) restent non lettrées.",
                                    "Lettrer le compte."))
        elif age > jours_anciennete:
            nature = "Créance" if compte.startswith("41") else "Dette"
            anciennes = sum((l.solde for l in ouvertes
                             if (cloture - (l.piece_date or l.ecriture_date)).days > jours_anciennete), ZERO)
            constats.append(Constat("tiers_non_lettres", cycle_du_compte(compte), FORT, compte, nom, anciennes,
                                    f"{nature} non lettrée depuis le {plus_ancienne:%d/%m/%Y} ({age} jours) sur {nom} ({tiers}) : {formater_euros(abs(anciennes))} ont plus de {jours_anciennete} jours, solde total {formater_euros(solde)}.",
                                    "Relancer ou justifier. Une créance de plus d'un an pose la question d'une dépréciation."))
    return constats


def _constat_sens(compte: str, libelle: str, solde: Decimal, tiers: str = "") -> Constat | None:
    regle = sens_normal(compte)
    if regle is None or solde == 0:
        return None
    prefixe, attendu, nature = regle
    observe = "D" if solde > 0 else "C"
    if observe == attendu:
        return None
    sens = "débiteur" if observe == "D" else "créditeur"
    qui = f"{libelle} ({tiers})" if tiers else f"compte {compte} {libelle}"
    importance = FORT if compte.startswith(("53", "455", "512")) or tiers else MOYEN
    return Constat("sens_anormal", cycle_du_compte(compte), importance, compte, libelle, solde,
                   f"{nature} : solde {sens} de {formater_euros(abs(solde))} sur {qui}.", commentaire_sens(prefixe))


def controle_sens(lignes: list[LigneFec]) -> list[Constat]:
    libelles = libelles_comptes(lignes)
    comptes_avec_tiers = {l.compte_num for l in lignes if l.comp_aux_num}
    constats = []
    for compte, solde in sorted(soldes_par_compte(lignes).items()):
        if compte not in comptes_avec_tiers:
            constat = _constat_sens(compte, libelles[compte], solde)
            if constat:
                constats.append(constat)
    for (compte, tiers), solde in sorted(soldes_par_tiers(lignes).items()):
        constat = _constat_sens(compte, libelles.get(tiers, tiers), solde, tiers)
        if constat:
            constats.append(constat)
    return constats


def controle_ecarts(lignes: list[LigneFec], lignes_n1: list[LigneFec], seuil_montant: Decimal,
                    seuil_pourcent: Decimal) -> list[Constat]:
    """Variations N contre N-1 par compte de charge ou de produit au-delà du seuil de signification."""
    def gestion(liste):
        return {c: s for c, s in soldes_par_compte(liste).items() if c[0] in "67"}
    n, n1 = gestion(lignes), gestion(lignes_n1)
    libelles = {**libelles_comptes(lignes_n1), **libelles_comptes(lignes)}
    constats = []
    for compte in sorted(set(n) | set(n1)):
        actuel, precedent = n.get(compte, ZERO), n1.get(compte, ZERO)
        ecart = actuel - precedent
        taux = pourcentage(ecart, abs(precedent))
        if abs(ecart) < seuil_montant or (taux is not None and abs(taux) < seuil_pourcent):
            continue
        evolution = (f"{'+' if taux > 0 else ''}{str(taux).replace('.', ',')} %"
                     if taux is not None else "nouveau compte")
        constats.append(Constat("ecarts_n_n1", cycle_du_compte(compte), MOYEN, compte, libelles[compte], ecart,
                                f"{compte} {libelles[compte]} : {formater_euros(abs(precedent), 0)} en N-1, "
                                f"{formater_euros(abs(actuel), 0)} en N ({evolution}).",
                                "Demander l'explication au client et vérifier les plus grosses pièces du compte."))
    return constats


def controle_benford(lignes: list[LigneFec]) -> list[Constat]:
    exclus = _journaux_a_nouveaux(lignes)
    utiles = [l for l in lignes if l.journal_code not in exclus]
    constats = []
    groupes = {"Tout le FEC": utiles}
    for journal in sorted({l.journal_code for l in utiles}):
        groupes[f"Journal {journal}"] = [l for l in utiles if l.journal_code == journal]
    for nom, groupe in groupes.items():
        resultat = analyser([l.montant for l in groupe])
        if resultat is None or resultat.verdict != NON_CONFORME or resultat.effectif < ECHANTILLON_MINIMUM:
            continue
        constats.append(Constat("benford", "Tous cycles", MOYEN, nom, "Loi de Benford", ZERO,
                                f"{nom} : {resultat.effectif} montants, écart moyen {format(resultat.mad, '.4f').replace('.', ',')} (non-conformité au-delà de 0,015). "
                                f"Le chiffre {resultat.chiffre_le_plus_en_exces} revient trop souvent en premier.",
                                f"Regarder les montants qui commencent par {resultat.chiffre_le_plus_en_exces} : seuils de validation contournés, montants ronds, saisies répétées ?"))
    return constats
