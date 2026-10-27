---
name: rendez-vous-bilan
description: Prépare le rendez-vous bilan à partir du FEC de clôture (et N-1) : SIG, trésorerie, BFR, 3 messages simples, graphiques, questions du client, conseils. Une page HTML.
---

# Préparer le rendez-vous bilan

Tu prépares le rendez-vous où l'expert-comptable présente ses comptes à un client qui n'est pas comptable (un artisan, une gérante de PME, un artiste). Tu produis une page HTML lisible en deux minutes, imprimable sur une feuille. Elle reste un brouillon que l'expert-comptable relit avant le rendez-vous.

## Ce qu'il faut

- Obligatoire : le FEC de l'exercice clos.
- Fortement conseillé : le FEC de l'exercice précédent (sans lui, pas de comparaison).
- Facultatif : le nom à afficher pour le client, le nom du cabinet, ce que l'expert-comptable sait du client (projets, inquiétudes).

## Étapes

1. **Les chiffres, par le script.** Tu ne calcules aucun chiffre toi-même.

   ```bash
   python scripts/analyser_bilan.py <FEC_N> --n1 <FEC_N-1> --client "Nom affiché" --sortie rdv
   ```

   Lis `rdv/chiffres.json`. S'il y a des avertissements (colonnes absentes, résultat qui ne recoupe pas), dis-le avant tout.

2. **Les mots, par toi.** Écris `rdv/messages.json` avec :
   - `messages` : exactement **trois** messages clés, chacun un titre de 5 mots maximum et deux phrases. Un sur l'activité (chiffre d'affaires, marge), un sur la rentabilité (résultat et ce qui l'explique), un sur l'argent (trésorerie, délais de paiement, dettes).
   - `questions` : les 3 à 5 questions que ce client va poser, avec une réponse courte.
   - `conseils` : 3 ou 4 conseils concrets pour l'année qui vient.
   - `cabinet` : le nom du cabinet si on te l'a donné.

   Le format exact est en tête de `scripts/rendre_page.py`, un exemple complet dans [references/exemple-messages.json](references/exemple-messages.json).

3. **La page.**

   ```bash
   python scripts/rendre_page.py rdv
   ```

   Rends disponible `rdv/rendez-vous.html` (dans Claude Code, donne le chemin ; dans Claude.ai, propose-le en fichier à télécharger). Elle s'imprime sur une page A4. Résume les trois messages dans ta réponse.

## Règles d'écriture

- Chaque chiffre cité vient de `chiffres.json`, arrondi pour être lu à voix haute (« 143 937 € » ou « environ 144 000 € », jamais un chiffre inventé ou recalculé de tête).
- Mots simples. Pas de « EBE », « BFR » ou « SIG » dans les messages : dis « ce que l'activité rapporte avant les amortissements », « l'argent bloqué dans les factures clients ». Les sigles restent dans les graphiques.
- Phrases courtes, sans jargon, sans tiret long.
- Une baisse se dit franchement, avec sa cause quand les comptes la montrent. Quand la cause n'est pas dans les comptes, écris une question à poser au client, pas une hypothèse présentée comme un fait.
- Pas de promesse fiscale. Sur l'impôt, la rémunération du dirigeant ou les dividendes, la réponse renvoie à un échange avec l'expert-comptable, parce que la réponse dépend de la situation personnelle du client.

## Données sensibles

Le FEC contient toute la comptabilité du client : noms de tiers, salaires, montants. Ces données sont couvertes par le secret professionnel et par le RGPD. Rappelle en une phrase de travailler dans un environnement validé par le cabinet, de pseudonymiser (remplacer les noms de clients, de salariés et de tiers par des codes) en cas de doute, et de ne jamais déposer de données réelles dans une conversation que le cabinet ne maîtrise pas.

## Les formules

Les soldes intermédiaires de gestion suivent le tableau du plan comptable général. Le BFR et les délais de paiement sont des approximations, expliquées dans [references/formules.md](references/formules.md). Le script vérifie que le résultat des SIG retombe exactement sur produits moins charges.

## Limites à dire honnêtement

- Le FEC ne contient pas les écritures d'inventaire qui ne sont pas encore passées. Si la clôture n'est pas finie, les chiffres bougeront.
- Les délais de paiement supposent une TVA à 20 % sur tout le chiffre d'affaires et tous les achats : c'est un ordre de grandeur.
- Aucune comparaison avec le secteur : le script ne connaît pas les moyennes de la profession.

## Connecteurs (bonus)

- MCP Pennylane : tu peux y vérifier une balance ou un grand livre pour répondre à une question précise. Le FEC reste la source des chiffres de la page.
- Gmail ou Outlook : si l'expert-comptable le demande, tu prépares un **brouillon** de mail d'invitation au rendez-vous avec la page en pièce jointe. Tu ne l'envoies jamais.

## Ce que tu ne fais jamais

- Envoyer la page au client, ou la présenter comme des comptes définitifs.
- Donner un conseil fiscal ou social chiffré qui n'a pas été vérifié par l'expert-comptable.
