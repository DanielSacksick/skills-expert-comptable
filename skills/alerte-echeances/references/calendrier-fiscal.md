# Règles d'échéances utilisées par le script

Vérifiées sur les sources officielles le 27 octobre 2026. Chaque valeur codée dans `scripts/echeances.py` est ici avec son lien. Avant de se fier au script pour une année nouvelle, relire ce fichier : une loi de finances peut tout changer.

## Report d'une échéance de paiement

Un paiement dû un samedi, un dimanche ou un jour férié est reporté au premier jour ouvrable suivant. Art. 199-0 de l'annexe IV du CGI, [Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006301997). La page CFE d'impots.gouv parle de « premier jour ouvré suivant » : le script reporte au premier jour qui n'est ni un samedi, ni un dimanche, ni un jour férié.

Jours fériés : art. L3133-1 du Code du travail ([Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033020901/)). Alsace-Moselle : art. L3134-13 ([Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006902635)).

Les dates de **dépôt** de déclarations (liasse, CA12) suivent leurs propres textes, résumés plus bas.

## Impôt sur les sociétés

- Acomptes : « au plus tard les 15 mars, 15 juin, 15 septembre et 15 décembre de chaque année ». Art. 1668 CGI, [Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033836779).
- Montant : chaque acompte vaut le quart de l'impôt calculé sur le résultat du dernier exercice clos, aux taux de l'exercice en cours, arrondi à l'euro. Le premier acompte est provisoire et se régularise avec le deuxième. [BOI-IS-DECLA-20-10](https://bofip.impots.gouv.fr/bofip/3558-PGP.html/identifiant=BOI-IS-DECLA-20-10-20200610).
- Le script prend l'IS du dernier exercice divisé par 4. C'est juste si les taux n'ont pas changé, approximatif sinon.
- Dispense : IS de référence n'excédant pas 3 000 € (même BOI, § 360).
- Solde : le 15 du quatrième mois qui suit la clôture, le 15 mai pour une clôture au 31 décembre. Art. 1668, 2 CGI ; [calendrier fiscal](https://www.impots.gouv.fr/professionnel/calendrier-fiscal/2026-05).
- Pas d'acompte au premier exercice d'une société nouvelle, et moins de quatre acomptes pour un exercice de moins de douze mois : non géré par le script, à corriger à la main.

## TVA

- Régime réel normal (CA3) : échéance entre le 15 et le 24 du mois suivant, à la date affichée dans l'espace professionnel du client. Elle dépend de la forme juridique, du nom et du lieu ([BOI-TVA-DECLA-20-20-10-10](https://bofip.impots.gouv.fr/bofip/1001-PGP.html)). **C'est pourquoi le portefeuille porte un champ `jour_tva` par client.**
- Régime simplifié (CA12), jusqu'au 31 décembre 2026 : acompte de juillet égal à 55 % et acompte de décembre égal à 40 % de la TVA due au titre de l'année précédente (ligne 57 de la CA12). Dispense si cette TVA est inférieure à 1 000 €. [impots.gouv.fr/professionnel/tva](https://www.impots.gouv.fr/professionnel/tva).
- **Suppression du régime simplifié au 1er janvier 2027** (loi n° 2025-127, art. 38) : les redevables passent à la CA3, trimestrielle si le chiffre d'affaires ne dépasse pas 1 000 000 € (et 1 100 000 € l'année en cours), mensuelle sinon ou sur option. Plus d'acompte en juillet ni en décembre 2027 pour les exercices civils. Dernière CA12 au 4 mai 2027 pour les exercices clos au 31 décembre 2026. [Actualité impots.gouv](https://www.impots.gouv.fr/actualite/le-regime-simplifie-dimposition-la-tva-est-supprime-compter-du-1er-janvier-2027).
- À partir de janvier 2027, le script signale le changement et attend que le portefeuille soit mis à jour (`regime_tva` = `trimestriel` ou `mensuel`).

## Cotisation foncière des entreprises (CFE)

- Solde au 15 décembre, acompte au 15 juin. [impots.gouv.fr](https://www.impots.gouv.fr/professionnel/questions/comment-puis-je-acceder-mon-avis-de-cfe-et-le-payer).
- Acompte dû si la CFE de l'année précédente est supérieure ou égale à 3 000 €, égal à 50 % de celle-ci, sauf mensualisation. [Fiche CET-IFER 2026](https://www.impots.gouv.fr/sites/default/files/media/3_Documentation/depliants/pro_fiche_cet-ifer_2026.pdf), [service-public A16590](https://www.service-public.gouv.fr/entreprendre/actualites/A16590?profil=societe&lang=fr). Le seuil s'apprécie établissement par établissement : le script raisonne sur le total du client, à corriger pour un client à plusieurs établissements.
- Le montant de l'année n'est connu qu'avec l'avis : le script prend la CFE de l'an dernier.

## Cotisations sociales et DSN

- Moins de 50 salariés : DSN et paiement le 15 du mois suivant. 50 salariés et plus : le 5 du mois suivant (et le 15 pour les salaires versés le mois suivant). [entreprendre.service-public.gouv.fr F34059](https://entreprendre.service-public.gouv.fr/vosdroits/F34059).
- Les travailleurs non salariés (cotisations personnelles du dirigeant) ne sont pas gérés : leurs échéanciers sont propres à chacun.

## Déclarations sans paiement

- Liasse fiscale (2065) : 2e jour ouvré suivant le 1er mai pour une clôture au 31 décembre, avec un délai supplémentaire de 15 jours pour la télédéclaration. [impots.gouv.fr](https://www.impots.gouv.fr/professionnel/resultat-imposable-limpot-sur-le-revenu-ir-ou-limpot-sur-les-societes?l=fr). Exercices décalés : non gérés.
- DAS2 : honoraires et commissions de plus de **2 400 €** par bénéficiaire et par an (seuil relevé à partir des revenus 2024), déclaration dans le courant de janvier. [BOI-BIC-DECLA-30-70-20](https://bofip.impots.gouv.fr/bofip/8661-PGP.html/identifiant=BOI-BIC-DECLA-30-70-20-20250212).

## Non géré, à dire au client

- CVAE (entreprises au chiffre d'affaires élevé), taxe sur les véhicules, taxe d'apprentissage, impôts locaux autres que la CFE, échéances des dirigeants non salariés, prélèvement à la source des salariés au-delà de la DSN.
