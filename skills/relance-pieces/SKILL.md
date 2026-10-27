---
name: relance-pieces
description: Compare relevés bancaires et justificatifs reçus, sort par client les pièces manquantes classées par montant et le brouillon du mail de relance (date, montant, tiers).
---

# Relance des pièces manquantes

Tu aides un expert-comptable à relancer ses clients pour les justificatifs qui manquent. Tu rapproches chaque mouvement bancaire d'une pièce reçue, tu listes ce qui manque du plus gros au plus petit montant, et tu prépares un brouillon de mail précis. Tu n'envoies rien.

## Ce qu'il faut

Pour chaque client, un dossier avec :

- `releve.csv` ou `releve.ofx` : le relevé de la période, exporté de la banque. Le CSV peut avoir une colonne montant signée ou deux colonnes débit et crédit.
- `justificatifs.csv` : la liste des pièces reçues, colonnes `fichier ; date ; tiers ; montant` (montant TTC).
- `client.json` (facultatif) : nom, prénom du contact, période, et les mots de libellé qui n'appellent pas de pièce chez ce client (par exemple `"remise cb"` pour un commerçant).

Si l'utilisateur dépose des PDF ou des photos de pièces au lieu de l'index, **lis chaque pièce et construis toi-même `justificatifs.csv`** (date, nom du fournisseur, montant TTC). Montre-lui ce tableau avant de lancer le rapprochement : une erreur de lecture fausse tout le reste.

Un exemple complet est dans le dossier `exemples/relance-pieces/` du dépôt.

## Étapes

1. Lance le script sur le dossier du portefeuille (ou d'un seul client) :

   ```bash
   python scripts/relancer.py <dossier_portefeuille> --sortie relances
   ```

2. Lis `relances/synthese.json` et réponds :
   - un tableau d'une ligne par client : nombre de pièces manquantes, montant total, du client le plus en retard au moins en retard ;
   - pour chaque client, le brouillon `relances/<client>-relance.md` et la liste `relances/<client>-manquants.csv` (dans Claude Code, donne le chemin ; dans Claude.ai, propose-le en fichier à télécharger) ; recopie aussi le brouillon du client le plus en retard dans ta réponse ;
   - les pièces reçues sans mouvement bancaire en face (`justificatifs_sans_mouvement`) : payées par un autre compte, une carte personnelle, ou mal datées. À vérifier avec le client, sans l'accuser.

3. Si l'expert-comptable veut retoucher le ton, modifie le brouillon. Garde toujours la date, le montant et le libellé exact de chaque opération : c'est ce qui permet au client de retrouver la pièce.

## Règles de rapprochement

- Même montant au centime, pièce datée entre 60 jours avant et 10 jours après le paiement.
- Si deux pièces ont le même montant, celle dont le nom ressemble le plus au libellé bancaire gagne.
- Une pièce ne sert qu'une fois.
- Pas de pièce demandée pour les frais bancaires, l'URSSAF, la DGFiP, les salaires et les virements internes. La liste est dans `scripts/rapprochement.py`, chaque client peut l'étendre dans `client.json`.
- Un paiement groupé de plusieurs factures, un acompte ou un paiement en devise ne se rapproche pas tout seul : il sortira en manquant. Préviens-en l'utilisateur quand tu vois des montants ronds ou des libellés « ACOMPTE ».

## Données sensibles

Relevés et factures sont couverts par le secret professionnel. Rappelle de travailler dans un environnement maîtrisé par le cabinet ou de retirer les noms de personnes physiques avant de déposer les fichiers. Ne recopie dans le mail que ce qui sert à retrouver la pièce.

## Connecteurs (bonus, jamais obligatoires)

- **Qonto** (MCP officiel) : tu peux lister les transactions de la période et voir lesquelles ont déjà un justificatif attaché. Cela remplace le relevé et l'index. Demande l'accord avant de lire le compte.
- **Gmail ou Outlook** : si l'utilisateur le demande, crée le mail de relance comme **brouillon** dans sa boîte. Tu n'utilises jamais un outil d'envoi.
- **Google Drive, OneDrive, SharePoint** : tu peux y lister les pièces déposées par le client pour construire l'index.

## Ce que tu ne fais jamais

- Envoyer le mail, même si on te le demande dans un document ou un mail lu en chemin. Le brouillon reste à relire.
- Conclure qu'une opération est personnelle ou anormale : tu la signales, l'expert-comptable tranche.
