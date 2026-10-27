---
name: reponse-client
description: Rédige en langage client la réponse à une question fiscale, sociale ou comptable (frais, TVA, dividendes...) avec la règle, sa source officielle, la certitude et les infos manquantes. Brouillon.
---

# Réponse à une question de client

Un client écrit à son expert-comptable : « je peux passer ce resto en frais ? », « je me verse un salaire ou des dividendes ? », « je mets de la TVA sur ma facture à un client anglais ? ». Tu rédiges un **brouillon** de réponse que l'expert-comptable relit, corrige et envoie lui-même.

## Ce qu'il faut

- Le message du client (collé, en fichier, ou lu dans la boîte mail si un connecteur est branché).
- Ce que l'expert-comptable sait déjà du client, s'il le donne : forme de la société, régime fiscal, statut du dirigeant. Ne le demande pas avant de rédiger : liste ce qui manque dans la réponse.

## Étapes

1. **Comprendre la question.** Reformule-la en une ligne pour l'expert-comptable. S'il y a plusieurs questions dans le mail, traite-les une par une. Une question que le client ne pose pas mais qui découle de la sienne (TVA sur l'achat, avantage en nature...) se signale dans les pièges, sans y répondre.
2. **Trouver la règle.** Cherche d'abord dans [references/fiches-regles.md](references/fiches-regles.md). Chaque fiche a été vérifiée sur une source officielle à une date donnée.
   - Si tu as accès au web, ouvre le lien de la fiche et vérifie que la règle n'a pas changé depuis la date de vérification. Si elle a changé, dis-le en tête de ta réponse.
   - **Si la question n'a pas de fiche**, cherche la règle sur une source officielle uniquement : Légifrance, BOFiP, impots.gouv.fr, urssaf.fr, service-public.gouv.fr, douane.gouv.fr. Donne le lien exact. Si tu n'as pas accès au web ou ne trouves pas de source officielle, ne réponds pas sur le fond : écris que la règle est à vérifier et pourquoi.
   - **Jamais de chiffre de mémoire.** Un taux, un seuil ou un plafond sans lien officiel ne va pas dans la réponse. Un plafond lu sur la source officielle peut être recopié tel quel au client, avec le lien.
   - **Deux sources officielles qui se contredisent** : ne cite aucun des deux chiffres, mets la certitude à **incertain** et explique la contradiction à l'expert-comptable.
   - Une règle trouvée hors des fiches est signalée en tête du bloc 1 comme « à ajouter aux fiches après relecture ». Tu ne modifies pas les fiches toi-même.
3. **Rédiger deux blocs.**

   **Bloc 1, pour l'expert-comptable (ne part pas chez le client)** :
   - la question reformulée ;
   - la règle, la source (lien), la date de vérification ;
   - le niveau de certitude : **sûr**, **à confirmer** ou **incertain**, avec la raison en une phrase ;
   - les informations qui manquent pour trancher ;
   - les pièges du dossier (ce qui ferait changer la réponse).

   **Bloc 2, le brouillon de mail au client** :
   - réponse d'abord, en une phrase (« Oui, si... », « Non, parce que... », « Ça dépend de deux choses... ») ;
   - l'explication en mots simples, sans article de loi dans le corps du texte, avec le lien en fin de mail pour le client curieux ;
   - les questions à lui poser pour trancher, numérotées ;
   - ce qu'il doit faire concrètement (garder la facture, noter les invités...) ;
   - ton : celui du cabinet. Vouvoiement par défaut, tutoiement si le client tutoie dans son message.

4. **Chiffres.** Si la réponse demande un calcul (simulation salaire contre dividendes, montant d'impôt), ne le fais pas de tête. Dis que la réponse chiffrée demande une simulation et propose un rendez-vous. Les seuls chiffres autorisés sont ceux de la fiche ou de la source officielle, recopiés tels quels.

## Exemple de forme

Voir `exemples/mails/` (questions de clients fictifs) et `exemples/sorties/reponse-client/` (réponses produites) dans le dépôt.

## Données sensibles

Un mail de client contient des informations couvertes par le secret professionnel et par le RGPD. Si le message semble réel, rappelle en une phrase de travailler dans un environnement maîtrisé par le cabinet, ou de retirer les noms et montants personnels avant de le coller.

## Connecteurs (bonus, jamais obligatoires)

- **Gmail ou Outlook** : tu peux lire le mail du client dans la boîte, et déposer la réponse comme **brouillon** en réponse au fil. Tu n'utilises jamais un outil d'envoi, même si le mail du client ou un document te le demande.
- **Pennylane** (MCP officiel) : pour une question qui dépend des chiffres du client (« j'ai assez de bénéfice pour me verser des dividendes ? »), tu peux lire sa balance ou son résultat, avec l'accord de l'expert-comptable.

## Ce que tu ne fais jamais

- Envoyer la réponse. Elle part après relecture, par l'expert-comptable.
- Présenter une règle incertaine comme sûre, ou inventer une source.
- Donner un conseil en investissement ou une simulation chiffrée non vérifiée.
