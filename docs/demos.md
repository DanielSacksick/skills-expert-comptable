# Les démos en 30 secondes

Une démo par skill : ce qu'on dépose, ce qu'on tape, ce qui apparaît, le détail à montrer du doigt. Toutes les données sont fictives.

## 1. revision-dossier

- **On dépose** : `exemples/fec/000000000FEC20251231.txt` et `000000000FEC20241231.txt`.
- **On tape** : « Révise ce FEC avant la clôture, l'autre fichier c'est l'an dernier. »
- **Ce qui apparaît** : « 17 points à justifier, dont 6 importants », puis les trois premiers, puis la feuille de travail HTML rangée par cycle.
- **À montrer** : le compte d'attente 471 non soldé de 3 480 €, les deux numéros d'écriture manquants AC00150 et AC00151, l'OD passée le jour de Noël, et la loi de Benford qui repère les notes de frais juste sous 500 €.
- **Sortie d'exemple** : [feuille-de-travail.html](../exemples/sorties/revision-dossier/feuille-de-travail.html).

## 2. rendez-vous-bilan

- **On dépose** : les deux mêmes FEC.
- **On tape** : « Prépare mon rendez-vous bilan avec la cliente, elle n'est pas comptable. »
- **Ce qui apparaît** : la page « Votre bilan 2025 en une page » : 4 chiffres clés, 3 messages, 2 graphiques, 4 questions, 4 conseils. Elle s'imprime sur une feuille A4.
- **À montrer** : le message 2, « Mais vous gardez un peu moins » : chiffre d'affaires +7 %, résultat -13 %, parce que les frais de réception, déplacements et honoraires passent de 27 000 € à 91 000 €.
- **Sortie d'exemple** : [rendez-vous.html](../exemples/sorties/rendez-vous-bilan/rendez-vous.html) et [rendez-vous.pdf](../exemples/sorties/rendez-vous-bilan/rendez-vous.pdf).

## 3. relance-pieces

- **On dépose** : le dossier `exemples/relance-pieces/` (deux clients, un relevé CSV, un relevé OFX, les listes de pièces reçues et les PDF).
- **On tape** : « Quelles pièces manquent pour septembre ? Prépare les relances. »
- **Ce qui apparaît** : Studio Ostinato, 7 pièces pour 4 693,38 € ; Boulangerie du Canal, 8 pièces pour 2 875,41 €. Puis le brouillon de mail pour chaque client.
- **À montrer** : chaque ligne du mail donne la date, le montant et le libellé exact de la banque. Et la pièce reçue sans mouvement en face (une facture de vaisselle payée par un autre moyen).
- **Sortie d'exemple** : [sorties/relance-pieces/](../exemples/sorties/relance-pieces/).

## 4. alerte-echeances

- **On dépose** : `exemples/portefeuille/portefeuille.csv` (10 clients).
- **On tape** : « Qu'est-ce qui tombe en décembre 2026 pour mes clients ? »
- **Ce qui apparaît** : 34 échéances, et en tête 3 clients dont la trésorerie ne suffira pas, puis un message par client.
- **À montrer** : Garage Horizon doit environ 25 400 € et n'a que 14 300 € ; sa TVA due le samedi 19 décembre est reportée au lundi 21. Le message : « prévoyez environ 25 400 € sur le compte ».
- **Sortie d'exemple** : [echeances-2026-12.md](../exemples/sorties/alerte-echeances/echeances-2026-12.md).

## 5. reponse-client

- **On dépose** : le texte de `exemples/mails/01-restaurant.txt` (ou on le colle).
- **On tape** : « Prépare la réponse à ce client. »
- **Ce qui apparaît** : une note pour l'expert-comptable (règle, lien BOFiP, certitude, infos manquantes) et un brouillon de mail qui commence par « Oui, ce repas peut passer en frais ».
- **À montrer** : le niveau de certitude différent pour la déduction (sûr) et pour la TVA (à confirmer). Puis le mail sur la voiture de société : là où deux pages officielles se contredisent, le skill refuse de donner un chiffre.
- **Sorties d'exemple** : [sorties/reponse-client/](../exemples/sorties/reponse-client/).
