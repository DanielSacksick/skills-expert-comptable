# Règles du projet

- Français, phrases simples, aucun tiret cadratin ni demi-cadratin (test_depot le vérifie).
- Ne jamais modifier une copie de `lib/` dans `skills/*/scripts/` : modifier `lib/`, puis `python outils/synchroniser.py`.
- Après toute modification d'un skill : `python outils/construire_zips.py`, puis `python -m pytest`.
- Python bibliothèque standard uniquement dans `skills/` et `lib/`. Montants en `Decimal`, jamais en float.
- Toute règle fiscale ou sociale ajoutée vient d'une source officielle lue (Légifrance, BOFiP, impots.gouv.fr, urssaf.fr, service-public.gouv.fr), avec le lien et la date de vérification dans `references/`.
- Aucun skill n'envoie, ne dépose ni ne paie. Les connecteurs mail servent à créer des brouillons.
- Données d'exemple 100 % fictives, produites par les générateurs de `outils/`. Aucune donnée réelle, aucun nom de vrai client.
- Frontmatter de SKILL.md : `name` et `description` (200 caractères maximum) seulement, pour rester compatible Claude.ai.
