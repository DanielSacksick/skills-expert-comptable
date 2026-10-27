"""Test du premier chiffre (loi de Benford) sur les montants d'un FEC.

Statistiques :
- MAD (écart absolu moyen) comparé aux seuils empiriques de Nigrini (2012, table 7.1) ;
- khi-deux à 8 degrés de liberté, avec sa probabilité exacte (degrés pairs : formule fermée).

Limites : la loi ne s'applique qu'à des montants issus de nombreuses transactions de tailles
variées. Un loyer fixe, des abonnements ou un petit échantillon s'en écartent sans fraude.
Un écart est une piste à regarder, jamais une preuve.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

ATTENDU = {chiffre: math.log10(1 + 1 / chiffre) for chiffre in range(1, 10)}
# Nigrini, Benford's Law (2012), table 7.1, premier chiffre
SEUILS_MAD = ((0.006, "conformité forte"), (0.012, "conformité acceptable"),
              (0.015, "conformité marginale"))
NON_CONFORME = "non-conformité"
MONTANT_MINIMUM = Decimal("10")
ECHANTILLON_MINIMUM = 300


@dataclass(frozen=True)
class ResultatBenford:
    effectif: int
    observe: dict[int, float]
    mad: float
    khi_deux: float
    probabilite: float
    verdict: str
    chiffre_le_plus_en_exces: int
    echantillon_suffisant: bool


def premier_chiffre(montant: Decimal) -> int | None:
    """Premier chiffre significatif d'un montant (1 à 9), None pour zéro."""
    valeur = abs(montant)
    if valeur == 0:
        return None
    texte = format(valeur.normalize(), "f").replace(".", "").lstrip("0")
    return int(texte[0])


def probabilite_khi_deux_pair(statistique: float, degres: int) -> float:
    """P(X >= statistique) pour un khi-deux à degrés de liberté pairs."""
    if degres % 2:
        raise ValueError("Formule valable seulement pour un nombre pair de degrés de liberté.")
    moitie = statistique / 2
    terme, somme = 1.0, 1.0
    for k in range(1, degres // 2):
        terme *= moitie / k
        somme += terme
    return math.exp(-moitie) * somme


def verdict_mad(mad: float) -> str:
    for seuil, libelle in SEUILS_MAD:
        if mad <= seuil:
            return libelle
    return NON_CONFORME


def analyser(montants: list[Decimal]) -> ResultatBenford | None:
    """Teste les montants >= 10 €. None s'il n'y a aucun montant exploitable."""
    chiffres = [premier_chiffre(m) for m in montants if abs(m) >= MONTANT_MINIMUM]
    chiffres = [c for c in chiffres if c]
    effectif = len(chiffres)
    if effectif == 0:
        return None
    comptes = {c: 0 for c in range(1, 10)}
    for chiffre in chiffres:
        comptes[chiffre] += 1
    observe = {c: comptes[c] / effectif for c in comptes}
    mad = sum(abs(observe[c] - ATTENDU[c]) for c in comptes) / 9
    khi = sum((comptes[c] - effectif * ATTENDU[c]) ** 2 / (effectif * ATTENDU[c]) for c in comptes)
    exces = max(comptes, key=lambda c: observe[c] - ATTENDU[c])
    return ResultatBenford(
        effectif=effectif,
        observe=observe,
        mad=mad,
        khi_deux=khi,
        probabilite=probabilite_khi_deux_pair(khi, 8),
        verdict=verdict_mad(mad),
        chiffre_le_plus_en_exces=exces,
        echantillon_suffisant=effectif >= ECHANTILLON_MINIMUM,
    )
