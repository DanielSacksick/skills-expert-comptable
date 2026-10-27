# Format du fichier portefeuille

Un CSV (séparateur `;` ou `,`), une ligne par client. Il se tient dans Excel et s'exporte en CSV. Les montants peuvent avoir une virgule décimale.

| Colonne | Contenu | Exemple |
|---|---|---|
| `client` | Nom du dossier | Garage Horizon |
| `contact` | Prénom utilisé dans le message | Malik |
| `tutoiement` | `oui` si l'expert-comptable tutoie ce client | non |
| `regime_tva` | `mensuel`, `trimestriel`, `simplifie` ou `franchise` | mensuel |
| `jour_tva` | Jour limite de TVA affiché dans l'espace professionnel (15 à 24) | 19 |
| `tva_par_periode` | TVA nette habituelle d'un mois (ou d'un trimestre) | 6100 |
| `tva_annuelle_n1` | Régime simplifié : TVA due l'an dernier, ligne 57 de la CA12 | 9800 |
| `cloture` | Jour et mois de clôture | 31/12 |
| `soumis_is` | `oui` si la société est à l'impôt sur les sociétés | oui |
| `is_dernier_exercice` | IS du dernier exercice clos | 18200 |
| `cfe_n1` | CFE payée l'an dernier | 2900 |
| `cfe_mensualisee` | `oui` si la CFE est prélevée chaque mois | non |
| `effectif` | Nombre de salariés | 6 |
| `cotisations_mensuelles` | Cotisations sociales habituelles d'un mois | 11800 |
| `tresorerie` | Dernier solde bancaire connu | 14300 |

Les chiffres viennent de ce que le cabinet sait déjà : dernières déclarations, dernier bilan, dernier relevé. Plus la trésorerie est récente, plus l'alerte est utile.
