"""Garde-fous du dépôt : copies de lib/ à jour, pas de tiret cadratin, pas de nom réel, pas d'envoi."""
import re
from pathlib import Path

import pytest

from conftest import RACINE

import sys
sys.path.insert(0, str(RACINE / "outils"))
from synchroniser import BESOINS, contenu_attendu  # noqa: E402

TIRETS = "[" + chr(0x2014) + chr(0x2013) + "]"
IGNORES = {".git", ".venv", "__pycache__", ".pytest_cache", "dist"}
# noms qui ne doivent jamais apparaître dans le dépôt public (encodés pour ne pas s'y trouver en clair)
INTERDITS = [bytes.fromhex(h).decode() for h in (
    "61686d6564", "7961636f7562", "616261646965", "63617361626c616e6361", "70696c6f74652d666563", "66696e70696c6f74")]


def fichiers_texte():
    for chemin in RACINE.rglob("*"):
        if chemin.is_file() and not IGNORES & set(chemin.relative_to(RACINE).parts):
            if chemin.suffix in (".py", ".md", ".json", ".txt", ".csv", ".html", ".ofx", ".eml", ".toml", ""):
                yield chemin


@pytest.mark.parametrize("skill, modules", BESOINS.items())
def test_copies_de_lib_a_jour(skill, modules):
    for nom in modules:
        copie = RACINE / "skills" / skill / "scripts" / nom
        assert copie.read_text(encoding="utf-8") == contenu_attendu(nom), \
            f"{copie} a divergé de lib/{nom} : lancer python outils/synchroniser.py"


def test_pas_de_tiret_cadratin_ni_demi_cadratin():
    fautifs = [str(c.relative_to(RACINE)) for c in fichiers_texte()
               if re.search(TIRETS, c.read_text(encoding="utf-8", errors="ignore"))]
    assert fautifs == []


def test_aucun_nom_reel():
    fautifs = []
    for chemin in fichiers_texte():
        texte = chemin.read_text(encoding="utf-8", errors="ignore").lower()
        fautifs += [f"{chemin.relative_to(RACINE)} : {nom}" for nom in INTERDITS if nom in texte]
    assert fautifs == []


def test_les_skills_ne_disent_jamais_d_envoyer():
    for skill in (RACINE / "skills").iterdir():
        texte = (skill / "SKILL.md").read_text(encoding="utf-8")
        assert "brouillon" in texte.lower(), f"{skill.name} doit rappeler qu'il ne produit que des brouillons"
        assert "secret professionnel" in texte, f"{skill.name} doit rappeler le secret professionnel"
        assert not re.search(r"\b(send_mail|send_draft|send_message|gmail_send)\b", texte), skill.name


def test_frontmatter_portable():
    for skill in (RACINE / "skills").iterdir():
        texte = (skill / "SKILL.md").read_text(encoding="utf-8")
        entete = texte.split("---")[1]
        champs = dict(ligne.split(":", 1) for ligne in entete.strip().splitlines())
        assert set(champs) <= {"name", "description", "license", "compatibility", "metadata"}
        assert champs["name"].strip() == skill.name
        assert len(champs["description"].strip()) <= 200, f"{skill.name} : description > 200 caractères"


def test_zips_claude_ai_a_jour():
    import zipfile
    from construire_zips import fichiers_du_skill
    for skill in (RACINE / "skills").iterdir():
        archive = zipfile.ZipFile(RACINE / "zips" / f"{skill.name}.zip")
        attendus = {f"{skill.name}/{f.relative_to(skill).as_posix()}": f.read_bytes() for f in fichiers_du_skill(skill)}
        assert {n: archive.read(n) for n in archive.namelist()} == attendus, \
            f"zips/{skill.name}.zip n'est pas à jour : lancer python outils/construire_zips.py"
