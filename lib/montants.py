"""Montants en euros : lecture des formats français et affichage lisible.

Tout passe par Decimal. Jamais de float pour un montant.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ZERO = Decimal("0")
CENTIME = Decimal("0.01")

_ESPACES = (" ", " ", " ", "'")


def lire_montant(texte: object) -> Decimal:
    """Convertit '1 234,56', '1234.56', '-12,5' ou '' en Decimal.

    Une chaîne vide vaut zéro (cas normal dans un FEC : Debit vide si Credit rempli).
    Lève ValueError si le texte n'est pas un nombre.
    """
    if texte is None:
        return ZERO
    brut = str(texte).strip()
    if brut == "":
        return ZERO
    for espace in _ESPACES:
        brut = brut.replace(espace, "")
    brut = brut.replace("€", "")
    if "," in brut and "." in brut:
        # 1.234,56 (séparateur de milliers point) : on retire les points
        brut = brut.replace(".", "")
    brut = brut.replace(",", ".")
    try:
        return Decimal(brut)
    except InvalidOperation as erreur:
        raise ValueError(f"Montant illisible : {texte!r}") from erreur


def arrondir(montant: Decimal | int | str, pas: Decimal | int | str = CENTIME) -> Decimal:
    """Arrondi commercial (demi supérieur) au pas donné : 0.01, 1, 100..."""
    pas = Decimal(pas)
    return (Decimal(montant) / pas).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * pas


def formater_euros(montant: Decimal | int, decimales: int = 2) -> str:
    """Decimal('4200') -> '4 200,00 €' ; decimales=0 -> '4 200 €'."""
    valeur = arrondir(montant, Decimal(1).scaleb(-decimales))
    signe = "-" if valeur < 0 else ""
    valeur = abs(valeur)
    entier, _, fraction = f"{valeur:.{decimales}f}".partition(".")
    groupes = []
    while len(entier) > 3:
        groupes.insert(0, entier[-3:])
        entier = entier[:-3]
    groupes.insert(0, entier)
    texte = " ".join(groupes)
    if decimales:
        texte = f"{texte},{fraction}"
    return f"{signe}{texte} €"


def pourcentage(part: Decimal | int, total: Decimal | int, decimales: int = 1) -> Decimal | None:
    """Part en % de total, None si total nul."""
    if total == 0:
        return None
    return arrondir(Decimal(part) * 100 / Decimal(total), Decimal(1).scaleb(-decimales))
