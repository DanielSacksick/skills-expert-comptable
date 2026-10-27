"""Copie la bibliothèque commune lib/ dans le dossier scripts/ de chaque skill.

Pourquoi : sur Claude.ai, chaque skill est téléversé seul (un zip par skill). Il doit donc
embarquer ses propres copies. lib/ reste la seule version qu'on modifie ;
tests/test_synchronisation.py échoue si une copie a divergé.

Usage : python outils/synchroniser.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
LIB = RACINE / "lib"
# modules de lib/ dont chaque skill a besoin
BESOINS = {
    "revision-dossier": ("fec.py", "montants.py", "calendrier.py"),
    "rendez-vous-bilan": ("fec.py", "montants.py"),
    "relance-pieces": ("montants.py",),
    "alerte-echeances": ("montants.py", "calendrier.py"),
}
ENTETE = "# COPIE GÉNÉRÉE depuis lib/{nom} par outils/synchroniser.py : ne pas modifier ici.\n"


def contenu_attendu(nom: str) -> str:
    return ENTETE.format(nom=nom) + (LIB / nom).read_text(encoding="utf-8")


def synchroniser() -> list[Path]:
    ecrits = []
    for skill, modules in BESOINS.items():
        dossier = RACINE / "skills" / skill / "scripts"
        dossier.mkdir(parents=True, exist_ok=True)
        for nom in modules:
            cible = dossier / nom
            cible.write_text(contenu_attendu(nom), encoding="utf-8")
            ecrits.append(cible)
    return ecrits


if __name__ == "__main__":
    for chemin in synchroniser():
        print("copié :", chemin.relative_to(RACINE))
