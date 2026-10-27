# Cycles de révision et sens normal des comptes

La table exacte utilisée par le script est dans `scripts/cycles.py`. Ce fichier l'explique.

## Rattachement des comptes aux cycles

Le découpage en cycles est l'usage de la révision et de l'audit, il ne figure dans aucun texte. Le plus long préfixe de compte l'emporte.

| Cycle | Comptes |
|---|---|
| Capitaux propres | 10 à 15 |
| Emprunts et dettes financières | 16, 17, 519, 66, 76 |
| Immobilisations | 20 à 29, 68, 78, 675, 775 |
| Stocks | 3, 603 |
| Achats et fournisseurs | 40, 60, 61, 62 |
| Ventes et clients | 41, 70 à 75 |
| Social | 42, 43, 64 |
| État, impôts et TVA | 44, 63, 69 |
| Autres tiers et comptes d'attente | 45 à 49 |
| Trésorerie | 50 à 54, 58, 59 |
| Résultat exceptionnel | 67, 77 |

## Sens normal du solde

Un solde dans l'autre sens n'est pas forcément faux. Il est signalé « à justifier ».

| Compte | Sens normal | Si le sens est inverse |
|---|---|---|
| 401, 403, 404, 408 Fournisseurs | Créditeur | Double paiement, avoir non reçu, acompte. Reclasser en 409. |
| 409 Fournisseurs débiteurs | Débiteur | |
| 411, 413, 416, 418 Clients | Débiteur | Double encaissement, avoir à rembourser, acompte. Reclasser en 419. |
| 419 Clients créditeurs | Créditeur | |
| 421 Rémunérations dues | Créditeur | Avance ou acompte au salarié : à reclasser en 425. |
| 431, 437 Organismes sociaux | Créditeur | Trop versé, à réclamer. |
| 44551 TVA à décaisser | Créditeur | |
| 44562, 44566 TVA déductible | Débiteur | |
| 44567 Crédit de TVA | Débiteur | |
| 4457 TVA collectée | Créditeur | |
| 455 Comptes courants d'associés | Créditeur | Avance consentie à un associé : vérifier sa licéité. |
| 512 Banque | Débiteur | Découvert : vérifier l'autorisation, reclasser en 519 au bilan. |
| 53 Caisse | Débiteur | Impossible : une caisse ne peut pas être négative. |
| 10 Capital et réserves, 16 Emprunts, 28 Amortissements | Créditeur | |
| Classe 6 Charges | Débiteur | Sauf 609, 619, 629 (rabais obtenus), non contrôlés. |
| Classe 7 Produits | Créditeur | Sauf 709 (rabais accordés), non contrôlé. |

Les comptes 444 (impôt sur les sociétés), 467 et 471 ne sont pas contrôlés en sens : ils peuvent être dans les deux sens. Les 471 à 475 ont leur propre contrôle (ils doivent être soldés).

## Seuils retenus par défaut

| Contrôle | Seuil | Modifiable |
|---|---|---|
| Écarts N / N-1 | 5 000 € **et** 20 % | Oui, `--seuil-montant` et `--seuil-pourcent` |
| Ancienneté d'une créance ou dette non lettrée | 180 jours avant la clôture | Dans le code |
| Benford : montant minimum testé | 10 € | Dans le code |
| Benford : échantillon minimum pour conclure | 300 montants | Dans le code |
| Benford : non-conformité | écart absolu moyen (MAD) supérieur à 0,015 | Seuils de Nigrini |

Le seuil de signification est un choix de l'expert-comptable selon le dossier. Les valeurs par défaut sont un point de départ pour une petite entreprise.
