# COPIE GÉNÉRÉE depuis lib/calendrier.py par outils/synchroniser.py : ne pas modifier ici.
"""Jours fériés français et jours ouvrés.

Jours fériés légaux : article L3133-1 du Code du travail.
Alsace-Moselle : Vendredi saint et 26 décembre en plus (article L3134-13 du Code du travail).
Voir references/sources.md du skill pour les liens.
"""
from __future__ import annotations

from datetime import date, timedelta


def paques(annee: int) -> date:
    """Dimanche de Pâques (algorithme de Meeus/Jones/Butcher, calendrier grégorien)."""
    a = annee % 19
    b, c = divmod(annee, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois, jour = divmod(h + l - 7 * m + 114, 31)
    return date(annee, mois, jour + 1)


def jours_feries(annee: int, alsace_moselle: bool = False) -> dict[date, str]:
    """Dictionnaire {date: nom} des jours fériés de l'année."""
    dimanche_paques = paques(annee)
    feries = {
        date(annee, 1, 1): "Jour de l'an",
        dimanche_paques + timedelta(days=1): "Lundi de Pâques",
        date(annee, 5, 1): "Fête du travail",
        date(annee, 5, 8): "Victoire 1945",
        dimanche_paques + timedelta(days=39): "Ascension",
        dimanche_paques + timedelta(days=50): "Lundi de Pentecôte",
        date(annee, 7, 14): "Fête nationale",
        date(annee, 8, 15): "Assomption",
        date(annee, 11, 1): "Toussaint",
        date(annee, 11, 11): "Armistice 1918",
        date(annee, 12, 25): "Noël",
    }
    if alsace_moselle:
        feries[dimanche_paques - timedelta(days=2)] = "Vendredi saint (Alsace-Moselle)"
        feries[date(annee, 12, 26)] = "Saint-Étienne (Alsace-Moselle)"
    return feries


def nom_ferie(jour: date, alsace_moselle: bool = False) -> str | None:
    """Nom du jour férié, ou None."""
    return jours_feries(jour.year, alsace_moselle).get(jour)


def est_week_end(jour: date) -> bool:
    return jour.weekday() >= 5


def est_jour_ouvre(jour: date, alsace_moselle: bool = False) -> bool:
    """Ni samedi, ni dimanche, ni jour férié."""
    return not est_week_end(jour) and nom_ferie(jour, alsace_moselle) is None


def jour_ouvre_suivant(jour: date, alsace_moselle: bool = False) -> date:
    """Le jour lui-même s'il est ouvré, sinon le premier jour ouvré qui suit."""
    while not est_jour_ouvre(jour, alsace_moselle):
        jour += timedelta(days=1)
    return jour


def nieme_jour_ouvre(
    annee: int, mois: int, jour_depart: int, rang: int, alsace_moselle: bool = False
) -> date:
    """Le rang-ième jour ouvré à partir du jour_depart exclu.

    Exemple : 2e jour ouvré qui suit le 1er mai -> nieme_jour_ouvre(a, 5, 1, 2).
    """
    jour = date(annee, mois, jour_depart)
    compte = 0
    while compte < rang:
        jour += timedelta(days=1)
        if est_jour_ouvre(jour, alsace_moselle):
            compte += 1
    return jour
