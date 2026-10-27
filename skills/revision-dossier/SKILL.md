---
name: revision-dossier
description: Révise un FEC avant clôture (attente, numérotation, week-ends, lettrage, sens des soldes, Benford, N/N-1) et sort la feuille de travail cycle par cycle.
---

# Révision du dossier avant clôture

Tu aides un expert-comptable à réviser un dossier à partir de son FEC (fichier des écritures comptables, format de l'article A47 A-1 du LPF). Tu produis une feuille de travail : les points à justifier, rangés par cycle, du plus important au moins important. Tu ne corriges rien dans la comptabilité.

## Ce qu'il faut

- Obligatoire : le FEC de l'exercice à réviser (`.txt` ou `.csv`, séparateur tabulation ou barre verticale).
- Conseillé : le FEC de l'exercice précédent, pour les écarts N contre N-1.
- Facultatif : le seuil de signification du dossier (par défaut 5 000 € et 20 %), et si le client est en Alsace-Moselle.

S'il manque le FEC, demande-le. Rappelle qu'il s'exporte depuis n'importe quel logiciel comptable (Pennylane, Cegid, ACD, Sage, Tiime, MyUnisoft...), c'est une obligation légale.

## Avant de commencer : les données

Un FEC contient des données de clients couvertes par le secret professionnel. Si le fichier semble réel (vrais noms de tiers, de salariés), rappelle en une phrase : travailler dans un environnement maîtrisé par le cabinet, ou pseudonymiser les libellés de tiers avant. Ne recopie jamais de noms de salariés dans la feuille de travail au-delà de ce qui est nécessaire.

## Étapes

1. Lance le script. Il fait tous les calculs, toi tu n'en refais aucun de tête.

   ```bash
   python scripts/reviser.py <FEC_N> --n1 <FEC_N-1> --seuil-montant 5000 --seuil-pourcent 20 --sortie revision
   ```

   Ajoute `--alsace-moselle` si le client y est établi. Le chemin `scripts/` est relatif au dossier de ce skill.

2. Lis `revision/revision.json`. Si `avertissements` ou `colonnes_manquantes` ne sont pas vides, dis-le d'abord : le FEC n'est peut-être pas conforme, les résultats sont à prendre avec prudence.

3. Réponds en quatre blocs courts :
   - **En une phrase** : nombre de points, dont combien importants.
   - **Les 3 points à regarder en premier** : les constats `fort` aux montants les plus élevés, chacun en une ligne avec ce qu'il faut demander au client.
   - **La feuille de travail** : donne le chemin de `revision/feuille-de-travail.html` (lisible dans un navigateur, imprimable) et de la version Markdown.
   - **Ce que l'outil ne voit pas** : voir la section Limites, en deux lignes.

4. Si l'expert-comptable te demande d'approfondir un point, relis les lignes du FEC concernées (compte, tiers, numéro d'écriture) et propose une explication possible, en disant que c'est une hypothèse.

## Les contrôles

| Contrôle | Ce qui sort | Pourquoi |
|---|---|---|
| Équilibre des journaux | Journal où débit et crédit diffèrent | Un FEC déséquilibré est inexploitable |
| Comptes d'attente (471 à 475) | Solde non nul à la clôture | Rien ne doit rester en attente au bilan |
| Numérotation | Numéros d'écriture manquants, par journal | Écriture supprimée ou export incomplet |
| Week-ends et jours fériés | Écritures datées un samedi, un dimanche ou un jour férié (à-nouveaux exclus) | Normal pour une carte, suspect pour une OD manuelle |
| Lettrage des tiers | Créances et dettes non lettrées de plus de 180 jours, tiers soldés mais non lettrés | Relance, dépréciation, lettrage oublié |
| Sens des soldes | Fournisseur débiteur, client créditeur, banque créditrice, caisse créditrice, TVA... | Double paiement, avoir manquant, découvert |
| Loi de Benford | Journaux dont le premier chiffre des montants s'écarte de la loi | Seuils contournés, saisies répétées |
| Écarts N / N-1 | Comptes de charges et produits qui bougent au-delà du seuil | Ce que le client devra expliquer |

Le détail des règles, des cycles et du sens normal de chaque compte est dans [references/cycles-et-sens.md](references/cycles-et-sens.md). Les sources sont dans [references/sources.md](references/sources.md).

## Limites à dire honnêtement

- Un constat n'est pas une erreur. Une banque créditrice peut être un découvert autorisé, une écriture du samedi un paiement par carte. C'est à l'expert-comptable d'apprécier.
- La loi de Benford ne vaut que sur beaucoup de montants variés. La paie, les loyers et les abonnements s'en écartent normalement. En dessous de 300 montants, le script ne conclut pas.
- L'outil ne voit pas les pièces. Il ne contrôle ni les stocks, ni les cut-off, ni les engagements hors bilan, ni la cohérence avec la liasse.
- Plan comptable français uniquement (PCG).

## Connecteurs (bonus, jamais obligatoires)

- Si le MCP Pennylane est branché, tu peux lire le grand livre et la balance d'un dossier pour compléter un point. Le FEC reste la source du script : demande l'export FEC.
- Si Google Drive ou SharePoint est branché, tu peux y chercher le FEC du dossier, avec l'accord de l'utilisateur.

## Ce que tu ne fais jamais

- Modifier la comptabilité, passer une écriture, ou présenter un constat comme une certitude.
- Envoyer quoi que ce soit au client. Tu produis un brouillon de feuille de travail, l'expert-comptable décide.
