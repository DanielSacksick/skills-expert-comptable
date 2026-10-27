# Formules utilisées par le script

Les montants viennent des soldes du FEC (débit moins crédit). Le code est dans `scripts/sig.py`.

## Soldes intermédiaires de gestion

Le tableau des SIG figurait dans le système développé du plan comptable général (règlement ANC n° 2014-03, article 832-8 dans sa version initiale, [PDF ANC](https://www.anc.gouv.fr/files/anc/files/1_Normes_fran%C3%A7aises/Reglements/2014/Reglt2014-03/Reglt%202014-03_Plan%20comptable%20general.pdf)). Il n'est plus dans le PCG pour les exercices ouverts à compter du 1er janvier 2025 (règlement ANC n° 2022-06, [recueil PCG 2026](https://www.anc.gouv.fr/files/anc/files/1_Normes_fran%C3%A7aises/recueil/2026/Recueil-PCG-Janvier-2026.pdf)), mais reste l'outil d'analyse d'usage de la profession.

Le tableau officiel ne donnait que des postes, pas des numéros de comptes. Le rattachement des comptes ci-dessous est celui du script, conforme à l'usage ; il est modifiable dans `scripts/sig.py`.

| Solde | Calcul | Comptes |
|---|---|---|
| Marge commerciale | Ventes de marchandises moins coût d'achat des marchandises vendues | 707, 7097 moins 607, 6037, 6087, 6097 |
| Production de l'exercice | Production vendue, stockée et immobilisée | 70 (hors 707, 7097), 71, 72 |
| Consommations en provenance des tiers | Achats et charges externes | 60 (hors marchandises), 61, 62 |
| Valeur ajoutée | Marge commerciale + production moins consommations | |
| Excédent brut d'exploitation (EBE) | Valeur ajoutée + subventions moins impôts et taxes moins personnel | + 74, moins 63, moins 64 |
| Résultat d'exploitation | EBE + autres produits et reprises moins autres charges et dotations | + 75 (hors 755), 781, 791 ; moins 65 (hors 655), 681 |
| Résultat financier | Produits financiers moins charges financières | 76, 786, 796, 755 moins 66, 686, 655 |
| Résultat courant avant impôt | Exploitation + financier | |
| Résultat exceptionnel | Produits moins charges exceptionnels | 77, 787, 797 moins 67, 687 |
| Résultat net | Courant + exceptionnel moins participation et impôt | moins 69 |
| Chiffre d'affaires | Ventes de marchandises et production vendue | 70 |

Contrôle : le résultat net doit être égal à la somme des produits (classe 7) moins la somme des charges (classe 6). Le script le vérifie et prévient sinon.

Les quotes-parts de résultat sur opérations faites en commun (655, 755) sont rattachées au résultat financier par simplicité. Le tableau officiel les place entre le résultat d'exploitation et le résultat courant : le résultat courant est identique.

## Trésorerie

- Disponibilités : soldes débiteurs des comptes 50, 51, 53, 54.
- Concours bancaires : soldes créditeurs de ces mêmes comptes (découverts).
- Trésorerie nette : disponibilités moins concours bancaires.
- Courbe mensuelle : solde cumulé des comptes 50 à 54 à la fin de chaque mois, à-nouveaux compris.

## Besoin en fonds de roulement (simplifié)

Somme des soldes des comptes de stocks (classe 3) et de tiers (classe 4), hors comptes d'associés (45) et comptes d'attente (47). Les comptes de régularisation (486, 487) sont inclus car ils sont en classe 4.

C'est une lecture rapide, pas le BFR d'une analyse financière retraitée (pas de reclassement des effets escomptés, des dettes sur immobilisations ni de l'impôt).

## Délais de paiement

- Clients : créances clients (41 hors 419, moins 491) / (chiffre d'affaires × 1,2) × 365.
- Fournisseurs : dettes fournisseurs (40 hors 409) / (achats et charges externes 60 à 62 × 1,2) × 365.

Le coefficient 1,2 suppose une TVA à 20 % partout. Pour un client exonéré, à l'export ou au taux réduit, le délai est faussé : le dire.
