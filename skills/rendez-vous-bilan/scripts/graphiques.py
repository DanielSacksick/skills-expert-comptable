"""Graphiques SVG autonomes (sans bibliothèque) pour la page du rendez-vous bilan.

Deux séries au plus : l'exercice N (couleur pleine) et N-1 (gris). Une seule échelle par graphique.
Survol : chaque marque porte un <title>, lu par le navigateur comme info-bulle.
"""
from __future__ import annotations

from decimal import Decimal
from html import escape

from montants import formater_euros

MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def _echelle(valeurs: list[Decimal]) -> tuple[Decimal, Decimal]:
    """Bornes arrondies qui incluent zéro."""
    bas, haut = min(min(valeurs), Decimal(0)), max(max(valeurs), Decimal(0))
    if haut == bas:
        haut = bas + 1
    pas = Decimal(10) ** max(len(str(int(max(abs(bas), abs(haut))))) - 2, 0)
    return (bas / pas).to_integral_value(rounding="ROUND_FLOOR") * pas, \
        (haut / pas).to_integral_value(rounding="ROUND_CEILING") * pas


def _court(montant: Decimal) -> str:
    """1 234 567 -> '1,2 M€' ; 45 300 -> '45 k€'."""
    valeur = abs(montant)
    signe = "-" if montant < 0 else ""
    if valeur >= 1_000_000:
        return f"{signe}{str(round(valeur / 1_000_000, 1)).replace('.', ',')} M€"
    if valeur >= 1_000:
        return f"{signe}{round(valeur / 1_000)} k€"
    return f"{signe}{round(valeur)} €"


def barres_n_n1(postes: list[tuple[str, Decimal, Decimal | None]], largeur: int = 640, hauteur: int = 260) -> str:
    """Barres groupées : un groupe par poste, N-1 à gauche (gris), N à droite (couleur)."""
    valeurs = [v for _, n, n1 in postes for v in (n, n1) if v is not None]
    bas, haut = _echelle(valeurs)
    marge_g, marge_b, marge_h = 8, 34, 24
    zone_h = hauteur - marge_b - marge_h
    y = lambda v: marge_h + float((haut - v) / (haut - bas)) * zone_h  # noqa: E731
    groupe = (largeur - marge_g * 2) / len(postes)
    barre = min(44.0, groupe / 3.2)
    elements = [f'<line x1="{marge_g}" x2="{largeur - marge_g}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axe"/>']
    for i, (nom, n, n1) in enumerate(postes):
        centre = marge_g + groupe * (i + 0.5)
        for decalage, valeur, classe, annee in ((-barre / 2 - 1, n1, "n1", "N-1"), (barre / 2 + 1, n, "n", "N")):
            if valeur is None:
                continue
            haut_barre, bas_barre = sorted((y(valeur), y(0)))
            elements.append(
                f'<rect x="{centre + decalage - barre / 2:.1f}" y="{haut_barre:.1f}" width="{barre:.1f}" '
                f'height="{max(bas_barre - haut_barre, 1):.1f}" rx="4" class="{classe}">'
                f'<title>{escape(nom)} {annee} : {escape(formater_euros(valeur, 0))}</title></rect>')
        etiquette_y = y(n) - 6 if n >= 0 else y(n) + 14
        elements.append(f'<text x="{centre + barre / 2 + 1:.1f}" y="{etiquette_y:.1f}" class="valeur">{_court(n)}</text>')
        elements.append(f'<text x="{centre:.1f}" y="{hauteur - 12}" class="poste">{escape(nom)}</text>')
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" aria-label="Comparaison N et N-1">'
            + "".join(elements) + "</svg>")


def courbe_tresorerie(serie_n: list[tuple[str, Decimal]], serie_n1: list[tuple[str, Decimal]] | None,
                      largeur: int = 640, hauteur: int = 220) -> str:
    """Trésorerie en fin de mois : N en trait plein, N-1 en pointillé gris."""
    par_mois = lambda serie: {int(m[5:7]): v for m, v in serie}  # noqa: E731
    n, n1 = par_mois(serie_n), par_mois(serie_n1 or [])
    valeurs = list(n.values()) + list(n1.values())
    bas, haut = _echelle(valeurs)
    marge_g, marge_d, marge_b, marge_h = 24, 56, 26, 16
    x = lambda mois: marge_g + (mois - 1) * (largeur - marge_g - marge_d) / 11  # noqa: E731
    y = lambda v: marge_h + float((haut - v) / (haut - bas)) * (hauteur - marge_b - marge_h)  # noqa: E731
    elements = [f'<line x1="{marge_g}" x2="{largeur - marge_d}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axe"/>']
    for mois in range(1, 13):
        elements.append(f'<text x="{x(mois):.1f}" y="{hauteur - 6}" class="poste">{MOIS[mois - 1]}</text>')
    for serie, classe, annee in ((n1, "ligne-n1", "N-1"), (n, "ligne-n", "N")):
        if not serie:
            continue
        points = " ".join(f"{x(m):.1f},{y(v):.1f}" for m, v in sorted(serie.items()))
        elements.append(f'<polyline points="{points}" class="{classe}"/>')
        for mois, valeur in sorted(serie.items()):
            elements.append(f'<circle cx="{x(mois):.1f}" cy="{y(valeur):.1f}" r="7" class="cible">'
                            f'<title>Fin {MOIS[mois - 1]} {annee} : {escape(formater_euros(valeur, 0))}</title></circle>')
    if n1:
        dernier = max(n1)
        elements.append(f'<text x="{x(dernier) + 8:.1f}" y="{y(n1[dernier]) + 4:.1f}" class="poste fin">'
                        f'{_court(n1[dernier])}</text>')
    if n:
        dernier = max(n)
        elements.append(f'<text x="{x(dernier) + 8:.1f}" y="{y(n[dernier]) + 4:.1f}" class="valeur fin">'
                        f'{_court(n[dernier])}</text>')
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" aria-label="Trésorerie fin de mois">'
            + "".join(elements) + "</svg>")
