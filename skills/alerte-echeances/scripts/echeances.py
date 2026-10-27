"""Règles d'échéances fiscales et sociales d'un mois, pour un client du portefeuille.

Chaque règle est sourcée dans references/calendrier-fiscal.md (vérifié le 27/10/2026).
Les montants sont des estimations tirées des chiffres connus du portefeuille, jamais des calculs
de déclaration : l'expert-comptable valide.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from calendrier import jour_ouvre_suivant, nieme_jour_ouvre
from montants import ZERO, arrondir

SEUIL_DISPENSE_ACOMPTE_IS = Decimal("3000")     # BOI-IS-DECLA-20-10 §360 : IS de référence n'excédant pas 3 000 €
SEUIL_ACOMPTE_CFE = Decimal("3000")             # CFE N-1 supérieure ou égale à 3 000 €
SEUIL_DISPENSE_ACOMPTES_CA12 = Decimal("1000")  # TVA de l'année précédente inférieure à 1 000 €
TAUX_ACOMPTE_CA12 = {7: Decimal("0.55"), 12: Decimal("0.40")}
FIN_REGIME_SIMPLIFIE = date(2027, 1, 1)         # loi n° 2025-127, art. 38
MOIS_ACOMPTES_IS = (3, 6, 9, 12)


@dataclass(frozen=True)
class Client:
    nom: str
    contact: str
    tutoiement: bool
    regime_tva: str            # "mensuel", "trimestriel", "simplifie" ou "franchise"
    jour_tva: int              # jour limite affiché dans l'espace professionnel (15 à 24)
    tva_par_periode: Decimal   # TVA nette habituelle d'un mois (ou d'un trimestre)
    tva_annuelle_n1: Decimal   # régime simplifié : TVA due l'année précédente (ligne 57 de la CA12)
    cloture: tuple[int, int]   # (jour, mois) de clôture
    soumis_is: bool
    is_dernier_exercice: Decimal
    cfe_n1: Decimal
    cfe_mensualisee: bool
    effectif: int
    cotisations_mensuelles: Decimal
    tresorerie: Decimal


@dataclass(frozen=True)
class Echeance:
    client: str
    jour: date | None
    nature: str
    montant: Decimal | None
    paiement: bool
    note: str = ""


def _report(jour: date) -> date:
    """Art. 199-0 ann. IV CGI : un paiement dû un samedi, dimanche ou jour férié passe au jour ouvrable suivant."""
    return jour_ouvre_suivant(jour)


def echeances_tva(client: Client, annee: int, mois: int) -> list[Echeance]:
    jour = _report(date(annee, mois, client.jour_tva))
    if client.regime_tva == "mensuel":
        return [Echeance(client.nom, jour, "TVA (CA3) du mois précédent", client.tva_par_periode, True)]
    if client.regime_tva == "trimestriel" and mois in (1, 4, 7, 10):
        return [Echeance(client.nom, jour, "TVA (CA3) du trimestre précédent", client.tva_par_periode, True)]
    if client.regime_tva == "simplifie":
        return _echeances_regime_simplifie(client, annee, mois, jour)
    return []


def _echeances_regime_simplifie(client: Client, annee: int, mois: int, jour: date) -> list[Echeance]:
    if date(annee, mois, 1) >= FIN_REGIME_SIMPLIFIE:
        note = "Régime simplifié supprimé au 1er janvier 2027 : passage à la CA3. Vérifier la périodicité du client."
        if mois == 5:
            fin = nieme_jour_ouvre(annee, 5, 1, 2)
            return [Echeance(client.nom, fin, "Dernière déclaration annuelle de TVA (CA12) de 2026", None, False,
                             "Date à confirmer dans l'espace professionnel.")]
        return [Echeance(client.nom, None, "TVA : changement de régime", None, False, note)] if mois == 1 else []
    if mois not in TAUX_ACOMPTE_CA12:
        return []
    if client.tva_annuelle_n1 < SEUIL_DISPENSE_ACOMPTES_CA12:
        return [Echeance(client.nom, jour, "Acompte de TVA (CA12)", ZERO, True,
                         "Dispensé : TVA de l'année précédente inférieure à 1 000 €.")]
    montant = arrondir(client.tva_annuelle_n1 * TAUX_ACOMPTE_CA12[mois], 1)
    taux = "55 %" if mois == 7 else "40 %"
    return [Echeance(client.nom, jour, f"Acompte de TVA (CA12), {taux} de la TVA de l'an dernier", montant, True)]


def echeances_is(client: Client, annee: int, mois: int) -> list[Echeance]:
    if not client.soumis_is:
        return []
    resultat = []
    if mois in MOIS_ACOMPTES_IS:
        jour = _report(date(annee, mois, 15))
        if client.is_dernier_exercice <= SEUIL_DISPENSE_ACOMPTE_IS:
            resultat.append(Echeance(client.nom, jour, "Acompte d'impôt sur les sociétés", ZERO, True,
                                     "Dispensé : IS du dernier exercice n'excédant pas 3 000 €."))
        else:
            resultat.append(Echeance(client.nom, jour, "Acompte d'impôt sur les sociétés",
                                     arrondir(client.is_dernier_exercice / 4, 1), True,
                                     "Un quart de l'IS du dernier exercice clos (taux inchangés supposés)."))
    # solde : le 15 du 4e mois après la clôture, le 15 mai pour une clôture au 31/12 (art. 1668, 2 CGI)
    mois_solde = 5 if client.cloture == (31, 12) else (client.cloture[1] + 4 - 1) % 12 + 1
    if mois == mois_solde:
        resultat.append(Echeance(client.nom, _report(date(annee, mois, 15)), "Solde d'impôt sur les sociétés", None,
                                 True, "Montant à calculer à la clôture : IS de l'exercice moins les acomptes versés."))
    return resultat


def echeances_cfe(client: Client, annee: int, mois: int) -> list[Echeance]:
    if client.cfe_mensualisee or client.cfe_n1 <= 0:
        return []
    acompte_du = client.cfe_n1 >= SEUIL_ACOMPTE_CFE
    if mois == 6 and acompte_du:
        return [Echeance(client.nom, _report(date(annee, 6, 15)), "Acompte de CFE (50 % de la CFE de l'an dernier)",
                         arrondir(client.cfe_n1 / 2, 1), True)]
    if mois == 12:
        estime = client.cfe_n1 - (arrondir(client.cfe_n1 / 2, 1) if acompte_du else ZERO)
        return [Echeance(client.nom, _report(date(annee, 12, 15)), "Solde de CFE", estime, True,
                         "Estimé sur la CFE de l'an dernier : le montant exact est sur l'avis dans l'espace professionnel.")]
    return []


def echeances_sociales(client: Client, annee: int, mois: int) -> list[Echeance]:
    if client.effectif <= 0:
        return []
    jour = date(annee, mois, 5 if client.effectif >= 50 else 15)
    return [Echeance(client.nom, _report(jour), "DSN et cotisations sociales du mois précédent",
                     client.cotisations_mensuelles, True,
                     "50 salariés et plus : selon la date de paie, une partie peut être due le 15."
                     if client.effectif >= 50 else "")]


def echeances_declaratives(client: Client, annee: int, mois: int) -> list[Echeance]:
    resultat = []
    jour_cloture, mois_cloture = client.cloture
    if client.soumis_is and mois == 5 and (jour_cloture, mois_cloture) == (31, 12):
        resultat.append(Echeance(client.nom, nieme_jour_ouvre(annee, 5, 1, 2), "Liasse fiscale (2065)", None, False,
                                 "Délai supplémentaire de 15 jours accordé en cas de télédéclaration."))
    if mois == 1:
        resultat.append(Echeance(client.nom, None, "DAS2 (honoraires de plus de 2 400 € par bénéficiaire)", None,
                                 False, "Dans le courant de janvier, date exacte au calendrier fiscal."))
    return resultat


REGLES = (echeances_tva, echeances_is, echeances_cfe, echeances_sociales, echeances_declaratives)


def echeances_du_mois(client: Client, annee: int, mois: int) -> list[Echeance]:
    toutes = [e for regle in REGLES for e in regle(client, annee, mois)]
    return sorted(toutes, key=lambda e: (e.jour or date(annee, mois, 28), e.nature))
