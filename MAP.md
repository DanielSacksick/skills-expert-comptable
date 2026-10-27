# MAP : skills-expert-comptable

> Plugin Claude Code de 5 skills pour l'expert-comptable de terrain, aussi téléversables dans Claude.ai.

## Stack
Python 3.10+ (bibliothèque standard uniquement), Markdown. Tests : pytest.

## Structure
.claude-plugin/    → plugin.json et marketplace.json (installation en une commande)
skills/<nom>/      → SKILL.md, scripts/ (Python), references/ (règles sourcées)
lib/               → Code commun (FEC, montants, calendrier) : seule version à modifier
outils/            → Synchronisation de lib/, générateurs de données factices, zips Claude.ai
exemples/          → Données 100 % fictives (fec/, relance-pieces/, portefeuille/, mails/) et sorties/
zips/              → Un zip par skill pour Claude.ai (généré)
docs/              → connecteurs.md, images du README
tests/             → Un fichier par skill + test_lib + test_depot (garde-fous)

## Entry Points
- `skills/revision-dossier/scripts/reviser.py` : contrôles FEC, feuille de travail
- `skills/rendez-vous-bilan/scripts/analyser_bilan.py` puis `rendre_page.py`
- `skills/relance-pieces/scripts/relancer.py`
- `skills/alerte-echeances/scripts/alerter.py`
- `skills/reponse-client/` : instructions et fiches seulement, pas de script

## Commands
test:       `python -m pytest`
lib → skills: `python outils/synchroniser.py` (après toute modification de lib/)
zips:       `python outils/construire_zips.py` (après toute modification d'un skill)
exemples:   `python outils/generer_fec.py` et `python outils/generer_banque.py`
plugin:     `claude plugin validate .`

## Decisions
- [2026-10-27] lib/ copiée dans chaque skill par outils/synchroniser.py : Claude.ai téléverse chaque skill seul, il doit être autonome. test_depot échoue si une copie diverge.
- [2026-10-27] Python sans dépendance : marche dans l'exécution de code de Claude.ai comme en local.
- [2026-10-27] Les calculs sont dans les scripts, la rédaction est faite par Claude (messages du bilan, réponses client).
- [2026-10-27] Règles fiscales vérifiées en ligne le 27/10/2026, liens dans chaque references/.

<!-- Updated: 2026-10-27 | Files: ~75 | Token estimate: ~700 -->
