"""Construit un zip par skill, prêt à téléverser dans Claude.ai (Personnaliser > Skills).

Chaque zip contient le dossier du skill à sa racine (<skill>/SKILL.md, scripts/, references/).
Dates fixées pour que deux constructions identiques donnent le même fichier.

Usage : python outils/construire_zips.py
"""
from __future__ import annotations

import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "zips"
DATE_FIXE = (2026, 1, 1, 0, 0, 0)
IGNORES = {"__pycache__", ".DS_Store"}


def fichiers_du_skill(dossier: Path) -> list[Path]:
    return sorted(f for f in dossier.rglob("*") if f.is_file() and not IGNORES & set(f.parts) and f.suffix != ".pyc")


def construire(dossier: Path) -> Path:
    SORTIE.mkdir(exist_ok=True)
    cible = SORTIE / f"{dossier.name}.zip"
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as archive:
        for fichier in fichiers_du_skill(dossier):
            info = zipfile.ZipInfo(f"{dossier.name}/{fichier.relative_to(dossier).as_posix()}", DATE_FIXE)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, fichier.read_bytes())
    return cible


if __name__ == "__main__":
    for skill in sorted((RACINE / "skills").iterdir()):
        if skill.is_dir():
            print("construit :", construire(skill).relative_to(RACINE))
