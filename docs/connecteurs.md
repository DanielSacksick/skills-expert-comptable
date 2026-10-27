# Brancher Claude aux outils du cabinet (état au 27 octobre 2026)

Règle du pack : chaque skill marche d'abord avec des fichiers déposés (FEC, CSV, OFX, Excel, PDF, mail collé). Un connecteur fait gagner du temps, il n'est jamais obligatoire.

Légende du verdict : **branchable** (connecteur prêt, sans développement), **API** (API documentée mais pas de serveur MCP officiel, il faut développer ou auditer un MCP communautaire), **export** (on passe par un fichier), **fermé** (pas d'accès possible pour un cabinet).

## Production comptable

| Outil | API publique | MCP | Ce que le pack utilise | Verdict |
|---|---|---|---|---|
| Pennylane | Oui, [Company et Firm API](https://pennylane.readme.io/docs/what-apis-are-available.md), [export FEC](https://pennylane.readme.io/reference/exportfec.md) | **Officiel**, [mcp.pennylane.com](https://www.pennylane.com/fr/mcp), lecture seule, sans surcoût pour les cabinets | FEC exporté (ou lu par le MCP) | **branchable** |
| Cegid Loop | Oui, [developers.cegid.com](https://developers.cegid.com/docreference/BusinessUnits/Loop-Api-Management-Docs/GetStart.html), clé « Advanced » payante | Communautaire au stade de squelette ([Nijal-AI/cegid-mcp](https://github.com/Nijal-AI/cegid-mcp)) | Export FEC | **API** |
| Cegid Quadra | Pas d'API publique trouvée | Non | Export FEC ou ASCII Quadra | **export** |
| ACD (i-Suite Expert) | API réservée aux clients ACD ([Chift](https://docs.chift.eu/help/connectors/accounting/acd)) | Non | Export FEC | **API** |
| Sage 100 | Pas d'API REST native ([Chift](https://chift.eu/blog/sage-100-fr-france-integration)) | Non | Export FEC | **export** |
| Sage Génération Experts | API OData pour partenaires ([page Sage](https://www.sage.com/fr-ma/experts-comptables/produits/sage-generation-experts-connect/)) | Non | Export FEC | **API** |
| Tiime | Pas d'API publique documentée | Communautaire sur API interne non documentée, à éviter ([tiime-mcp](https://github.com/cmoi936/tiime-mcp)) | Export FEC | **export** |
| Inqom | Doc API annoncée, non vérifiée ([aide Inqom](https://help.inqom.com/fr/api-inqom-ressources)) | Non | Export FEC | **API** (à confirmer) |
| MyUnisoft | Oui, ouverte aux cabinets ([api-partenaires](https://github.com/MyUnisoft/api-partenaires), [doc](https://docs.api.myunisoft.fr/)) | Communautaire ([myunisoft-mcp-server](https://github.com/melvynBuilds/myunisoft-mcp-server)) | Export FEC | **API** |

Tous ces logiciels produisent un FEC, c'est une obligation légale. C'est pour ça que les skills révision et rendez-vous bilan partent du FEC : ils marchent avec n'importe quel logiciel.

## Banque

| Outil | Accès | Verdict |
|---|---|---|
| Qonto | **MCP officiel** [mcp.qonto.com](https://docs.qonto.com/mcp/overview) : transactions, relevés, justificatifs attachés. Ne peut pas déplacer d'argent. | **branchable** |
| Bridge (BPCE) | [API](https://docs.bridgeapi.io/) sur contrat. Le [MCP Bridge](https://docs.bridgeapi.io/mcp) ne sert que la documentation, pas les données. | **API** |
| Powens | [API](https://docs.powens.com/) sur contrat commercial | **API** |
| Relevés CSV, OFX, CAMT.053 | Lus directement par le skill relance-pieces | **export** |

## Mails, agenda, fichiers

| Outil | Accès | Verdict |
|---|---|---|
| Gmail, Google Agenda, Google Drive | [Connecteurs officiels Claude](https://support.claude.com/fr/articles/10166901-use-google-workspace-connectors) | **branchable** |
| Outlook, OneDrive, SharePoint, Excel | [Connecteur Microsoft 365](https://support.claude.com/fr/articles/15183774-se-connecter-a-microsoft-365), compte pro Entra et accord d'un administrateur. Brouillons de mail seulement si l'admin active l'écriture. | **branchable** |

## Administrations

| Service | Accès | Verdict |
|---|---|---|
| impots.gouv (espace pro) | Portail web. Le dépôt automatisé passe par l'[EDI](https://www.impots.gouv.fr/professionnel/teleprocedures-efi-ou-edi) via un partenaire agréé. Les [API DGFiP](https://www.impots.gouv.fr/comment-acceder-aux-api-de-la-dgfip) sont réservées aux organismes habilités. | **fermé** |
| net-entreprises (DSN) | [API DSN](https://www.net-entreprises.fr/declaration/api-dsn/) pour les logiciels de paie, pas pour un assistant | **fermé** |
| URSSAF | [API Tierce Déclaration](https://www.data.gouv.fr/dataservices/api-tierce-declaration-auto-entrepreneur) limitée aux micro-entrepreneurs, sur mandat | **fermé** |
| API Entreprise | [Réservée aux administrations](https://entreprise.api.gouv.fr/) | **fermé** |

Conséquence pour le pack : aucun skill ne dépose, ne déclare ni ne paie. Ils préparent, l'expert-comptable dépose lui-même.

## Ce qu'il faut retenir

1. **Branché en 5 minutes** : Pennylane (MCP officiel), Qonto (MCP officiel), Gmail et Drive, Microsoft 365.
2. **Par fichier, partout** : le FEC (tous les logiciels), les relevés CSV et OFX, les Excel de suivi.
3. **Développement nécessaire** : Cegid Loop, MyUnisoft, ACD, Sage Génération Experts, Bridge, Powens.
4. **Fermé** : toutes les administrations.
5. **Sécurité** : un MCP communautaire lit des données clients. Auditer le code avant de le brancher, préférer les connecteurs officiels.
