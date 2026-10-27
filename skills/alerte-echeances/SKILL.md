---
name: alerte-echeances
description: Chaque mois, liste par client les échéances fiscales et sociales (TVA, IS, CFE, DSN...), estime les montants, vérifie la trésorerie et rédige le message « prévois environ X € ».
---

# Alerte des échéances du mois

Tu aides un expert-comptable à prévenir ses clients avant que les échéances tombent. Pour un mois donné, tu sors le calendrier de tout le portefeuille, les montants estimés, les clients dont la trésorerie risque de ne pas suivre, et un brouillon de message par client. Tu ne déclares, ne payes et n'envoies rien.

## Ce qu'il faut

- Le fichier portefeuille (CSV ou Excel exporté en CSV), une ligne par client. Colonnes décrites dans [references/format-portefeuille.md](references/format-portefeuille.md). Un exemple de 10 clients fictifs est dans `exemples/portefeuille/` du dépôt.
- Le mois visé (par défaut le mois prochain).

Si l'utilisateur n'a pas de portefeuille, propose-lui de le construire avec lui à partir de ce qu'il sait : c'est un tableau de 15 colonnes, un client par ligne.

## Étapes

1. Lance le script :

   ```bash
   python scripts/alerter.py <portefeuille.csv> --mois AAAA-MM --sortie echeances
   ```

2. Lis `echeances/echeances-AAAA-MM.json` et réponds :
   - **D'abord les trésoreries à surveiller** : les clients `insuffisante` puis `tendue`, avec le total à payer et le solde connu. C'est là que l'expert-comptable doit appeler.
   - **Le calendrier** : `echeances-AAAA-MM.md` (dans Claude Code, donne le chemin ; dans Claude.ai, propose-le en fichier à télécharger), avec le tableau par date.
   - **Les messages** : ils sont dans le même fichier, un par client, prêts à relire.
   - **Ce que le script ne sait pas** : les notes des échéances (montant à calculer, régime à vérifier) et la liste « Non géré » du calendrier fiscal.

3. Si l'expert-comptable te donne un chiffre plus récent (trésorerie, TVA du mois), mets à jour le portefeuille et relance le script. Ne recalcule jamais un total de tête.

## Données sensibles

Le portefeuille réunit les chiffres fiscaux et la trésorerie de tous les clients du cabinet. Ces données sont couvertes par le secret professionnel et par le RGPD. Rappelle en une phrase de travailler dans un environnement validé par le cabinet, de pseudonymiser (remplacer les noms de clients, de salariés et de tiers par des codes) en cas de doute, et de ne jamais déposer de données réelles dans une conversation que le cabinet ne maîtrise pas.

## Règles

Toutes les règles et leurs sources sont dans [references/calendrier-fiscal.md](references/calendrier-fiscal.md), vérifiées le 27 octobre 2026. Les points qui changent tout :

- Le jour limite de TVA dépend de chaque entreprise (entre le 15 et le 24) : il vient du portefeuille.
- Une échéance qui tombe un week-end ou un jour férié est reportée au jour ouvré suivant.
- Le régime simplifié de TVA disparaît le 1er janvier 2027. Pour janvier 2027 et après, le script prévient : il faut mettre à jour le régime de chaque client concerné.
- Les montants sont des **estimations** : un quart de l'IS de l'an dernier, la CFE de l'an dernier, la TVA habituelle. Les messages le disent.

Si la date du jour est postérieure à 2027 ou qu'une loi de finances est passée depuis le 27 octobre 2026, dis-le et invite à vérifier le calendrier fiscal officiel ([impots.gouv.fr, calendrier fiscal](https://www.impots.gouv.fr/professionnel/calendrier-fiscal)) avant de se fier aux montants.

## Connecteurs (bonus, jamais obligatoires)

- **Qonto** (MCP officiel) ou tout relevé déposé : met à jour le solde de trésorerie d'un client avant de lancer le script, avec son accord.
- **Pennylane** (MCP officiel) : peut donner la TVA des dernières déclarations et le dernier IS pour remplir le portefeuille.
- **Google Sheets, Excel sur OneDrive ou SharePoint** : le portefeuille peut y vivre. Exporte-le en CSV pour le script.
- **Gmail ou Outlook** : sur demande, chaque message devient un **brouillon** dans la boîte de l'expert-comptable. Jamais d'envoi.

## Ce que tu ne fais jamais

- Envoyer un message, programmer un paiement ou déposer une déclaration.
- Présenter un montant estimé comme le montant exact à payer.
