"""Rend lib/ importable dans les tests.

Les scripts des skills sont importés par chaque fichier de test via ajouter_scripts().
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "lib"))


def ajouter_scripts(skill: str) -> Path:
    """Ajoute skills/<skill>/scripts au chemin d'import et renvoie ce dossier."""
    dossier = RACINE / "skills" / skill / "scripts"
    if str(dossier) not in sys.path:
        sys.path.insert(1, str(dossier))
    return dossier
