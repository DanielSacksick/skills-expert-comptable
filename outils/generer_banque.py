"""Génère les relevés bancaires et justificatifs 100 % fictifs du skill relance-pieces.

Deux clients imaginaires, septembre 2026. Graine fixe. La liste exacte des pièces manquantes
attendues est écrite dans exemples/relance-pieces/manifeste.json.

Usage : python outils/generer_banque.py
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "exemples" / "relance-pieces"

# (libellé bancaire, tiers sur la pièce, montant moyen, nombre dans le mois)
BOULANGERIE = [
    ("PRLV SEPA MINOTERIE DES TROIS PONTS", "Minoterie des Trois Ponts", 1840, 2),
    ("PRLV SEPA ENERGIE VERTE COMMUNE", "Énergie Verte Commune", 612, 1),
    ("CB EMBALLAGES DU MARCHE", "Emballages du Marché", 186, 3),
    ("CB LAITERIE COOPERATIVE VAL", "Laiterie Coopérative du Val", 420, 4),
    ("VIR SEPA SCI QUAI NEUF LOYER", "SCI Quai Neuf", 1450, 1),
    ("CB QUINCAILLERIE CENTRALE", "Quincaillerie Centrale", 74, 2),
    ("PRLV SEPA ASSURANCE ARTISANS", "Assurance des Artisans", 138, 1),
    ("CB FRUITS ET PRIMEURS LEON", "Fruits et Primeurs Léon", 96, 4),
]
STUDIO = [
    ("ACHAT CB MAGASIN MUSIQUE PRO", "Magasin Musique Pro", 890, 2),
    ("PRLV LOGICIEL AUDIO ABONNEMENT", "Logiciel Audio", 49, 1),
    ("VIR LOCATION BACKLINE SUD", "Location Backline Sud", 640, 2),
    ("CB TRAIN GRANDES LIGNES", "Train Grandes Lignes", 112, 3),
    ("PRLV ELECTRICITE STUDIO", "Électricité Studio", 284, 1),
    ("VIR INGENIEUR SON FREELANCE", "Ingénieur son indépendant", 1200, 2),
    ("CB RESTAURANT LE CONTREPOINT", "Restaurant Le Contrepoint", 68, 3),
]


def jours_ouvres(annee, mois):
    jour, fin = date(annee, mois, 1), date(annee, mois + 1, 1)
    while jour < fin:
        if jour.weekday() < 5:
            yield jour
        jour += timedelta(days=1)


def montant(rng, moyenne):
    return (Decimal(moyenne) * Decimal(str(round(rng.uniform(0.6, 1.4), 4)))).quantize(Decimal("0.01"))


def simuler(rng, fournisseurs, encaissements, manquer):
    jours = list(jours_ouvres(2026, 9))
    mouvements, pieces = [], []
    for libelle, tiers, moyen, nombre in fournisseurs:
        for _ in range(nombre):
            jour, valeur = rng.choice(jours), montant(rng, moyen)
            mouvements.append((jour, libelle, -valeur))
            pieces.append((jour - timedelta(days=rng.randint(0, 20)), tiers, valeur))
    for jour, libelle, valeur in encaissements:
        mouvements.append((jour, libelle, valeur))
    mouvements.sort()
    # on retire des pièces : celles-là devront être relancées
    indices = sorted(rng.sample(range(len(pieces)), manquer))
    absentes = [pieces[i] for i in indices]
    recues = [p for i, p in enumerate(pieces) if i not in indices]
    return mouvements, recues, absentes


def ecrire_csv(chemin, entete, lignes):
    chemin.write_text(";".join(entete) + "\n" + "\n".join(";".join(l) for l in lignes) + "\n", encoding="utf-8")


def fr(valeur):
    return str(valeur).replace(".", ",")


def mini_pdf(chemin, lignes):
    """PDF d'une page avec quelques lignes de texte, sans bibliothèque."""
    texte = "BT /F1 12 Tf 60 780 Td 16 TL " + " ".join(
        f"({l.encode('latin-1', 'replace').decode('latin-1').replace('(', '[').replace(')', ']')}) '" for l in lignes) + " ET"
    objets = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
              "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
              "/Resources << /Font << /F1 5 0 R >> >> >>",
              f"<< /Length {len(texte.encode('latin-1'))} >>\nstream\n{texte}\nendstream",
              "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    sortie, positions = b"%PDF-1.4\n", []
    for numero, objet in enumerate(objets, start=1):
        positions.append(len(sortie))
        sortie += f"{numero} 0 obj\n{objet}\nendobj\n".encode("latin-1")
    xref = len(sortie)
    sortie += f"xref\n0 {len(objets) + 1}\n0000000000 65535 f \n".encode()
    sortie += "".join(f"{p:010d} 00000 n \n" for p in positions).encode()
    sortie += f"trailer << /Size {len(objets) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    chemin.write_bytes(sortie)


def ecrire_client(nom, client, mouvements, recues, format_releve):
    dossier = DOSSIER / nom
    (dossier / "pieces").mkdir(parents=True, exist_ok=True)
    (dossier / "client.json").write_text(json.dumps(client, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if format_releve == "csv":
        ecrire_csv(dossier / "releve.csv", ["Date", "Libellé", "Montant"],
                   [[f"{j:%d/%m/%Y}", l, fr(v)] for j, l, v in mouvements])
    else:
        blocs = "".join(f"<STMTTRN><TRNTYPE>{'DEBIT' if v < 0 else 'CREDIT'}<DTPOSTED>{j:%Y%m%d}"
                        f"<TRNAMT>{v}<FITID>{nom}{i:04d}<NAME>{l}</STMTTRN>\n"
                        for i, (j, l, v) in enumerate(mouvements))
        (dossier / "releve.ofx").write_text(
            "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\n\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>EUR\n"
            f"<BANKTRANLIST>\n{blocs}</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>\n", encoding="utf-8")
    lignes = []
    for numero, (jour, tiers, valeur) in enumerate(sorted(recues), start=1):
        fichier = f"pieces/{jour:%Y%m%d}-{numero:02d}.pdf"
        lignes.append([fichier, f"{jour:%d/%m/%Y}", tiers, fr(valeur)])
        mini_pdf(dossier / fichier, [f"FACTURE (document fictif)", tiers, f"Date : {jour:%d/%m/%Y}",
                                     f"Total TTC : {fr(valeur)} EUR", f"Client : {client['nom']}"])
    ecrire_csv(dossier / "justificatifs.csv", ["fichier", "date", "tiers", "montant"], lignes)


def main():
    rng = random.Random(2026)
    clients = []
    boulangerie = {"nom": "Boulangerie du Canal (fictive)", "prenom_contact": "Camille", "periode": "septembre 2026",
                   "sans_piece": ["remise cb"]}
    remises = [(j, "REMISE CB TPE 0042", montant(rng, 2300)) for j in jours_ouvres(2026, 9)]
    mvts, recues, absentes = simuler(rng, BOULANGERIE, remises, 8)
    mvts.append((date(2026, 9, 15), "PRLV URSSAF COTISATIONS", Decimal("-1873.00")))
    # une pièce reçue pour un achat payé par la carte personnelle de la gérante
    recues.append((date(2026, 9, 21), "Grossiste Vaisselle Pro", Decimal("329.90")))
    ecrire_client("boulangerie-du-canal", boulangerie, sorted(mvts), recues, "csv")
    clients.append((boulangerie["nom"], absentes))
    studio = {"nom": "Studio Ostinato (fictif)", "prenom_contact": "Noé", "periode": "septembre 2026"}
    cachets = [(date(2026, 9, 8), "VIR LABEL INDEPENDANT AURORE", Decimal("4800.00")),
               (date(2026, 9, 24), "VIR ASSOCIATION FESTIVAL DES DUNES", Decimal("2650.00"))]
    mvts, recues, absentes = simuler(rng, STUDIO, cachets, 6)
    recues.append((date(2026, 9, 8), "Label indépendant Aurore", Decimal("4800.00")))
    mvts.append((date(2026, 9, 30), "FRAIS BANCAIRES TENUE DE COMPTE", Decimal("-14.50")))
    ecrire_client("studio-ostinato", studio, sorted(mvts), recues, "ofx")
    absentes.append((date(2026, 9, 24), "Association Festival des Dunes (facture de vente)", Decimal("2650.00")))
    clients.append((studio["nom"], absentes))
    manifeste = {"avertissement": "Données 100 % fictives générées par outils/generer_banque.py.",
                 "pieces_manquantes": {nom: sorted([{"montant": str(v), "tiers": t} for _, t, v in absentes],
                                                   key=lambda x: -Decimal(x["montant"]))
                                       for nom, absentes in clients}}
    (DOSSIER / "manifeste.json").write_text(json.dumps(manifeste, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    for nom, absentes in clients:
        print(nom, ":", len(absentes), "pièces manquantes attendues")


if __name__ == "__main__":
    main()
