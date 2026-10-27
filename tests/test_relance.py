"""Tests du skill relance-pieces : lecture des relevés, règles de rapprochement, exemple contre manifeste."""
import json
from datetime import date
from decimal import Decimal

from conftest import RACINE, ajouter_scripts

ajouter_scripts("relance-pieces")

from rapprochement import pieces_manquantes, rapprocher, ressemblance  # noqa: E402
from relancer import rediger_mail, traiter_client  # noqa: E402
from releves import Justificatif, Mouvement, lire_releve  # noqa: E402

D = Decimal


def test_csv_debit_credit_et_virgule(tmp_path):
    chemin = tmp_path / "releve.csv"
    chemin.write_text("Date opération;Libellé;Débit;Crédit\n02/09/2026;CB BOULANGER;12,50;\n"
                      "03/09/2026;VIR CLIENT;;1 200,00\n", encoding="cp1252")
    mouvements = lire_releve(chemin)
    assert mouvements == [Mouvement(date(2026, 9, 2), "CB BOULANGER", D("-12.50")),
                          Mouvement(date(2026, 9, 3), "VIR CLIENT", D("1200.00"))]


def test_csv_virgule_et_montant_signe(tmp_path):
    chemin = tmp_path / "releve.csv"
    chemin.write_text("date,label,amount\n2026-09-02,Abonnement,-49.00\n", encoding="utf-8")
    assert lire_releve(chemin)[0].montant == D("-49.00")


def test_ofx(tmp_path):
    chemin = tmp_path / "releve.ofx"
    chemin.write_text("<OFX><STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20260915120000<TRNAMT>-84.20"
                      "<NAME>CB GARAGE<MEMO>CARTE 1234</STMTTRN></OFX>", encoding="utf-8")
    assert lire_releve(chemin) == [Mouvement(date(2026, 9, 15), "CB GARAGE CARTE 1234", D("-84.20"))]


def test_ressemblance():
    assert ressemblance("PRLV SEPA MINOTERIE DES TROIS PONTS", "Minoterie des Trois Ponts") == 1.0
    assert ressemblance("CB GARAGE", "Fleuriste") == 0.0


def test_rapprochement_montant_fenetre_et_tiers():
    mouvements = [Mouvement(date(2026, 9, 10), "CB FLEURISTE ROSE", D("-50.00")),
                  Mouvement(date(2026, 9, 12), "CB GARAGE DU PONT", D("-50.00")),
                  Mouvement(date(2026, 9, 20), "CB LIBRAIRIE", D("-30.00")),
                  Mouvement(date(2026, 9, 30), "FRAIS BANCAIRES", D("-9.00"))]
    justificatifs = [Justificatif("a.pdf", date(2026, 9, 12), "Garage du Pont", D("50.00")),
                     Justificatif("b.pdf", date(2026, 9, 9), "Fleuriste Rose", D("50.00")),
                     Justificatif("c.pdf", date(2026, 6, 1), "Librairie", D("30.00"))]  # trop ancienne
    rapprochements, orphelins = rapprocher(mouvements, justificatifs)
    assert rapprochements[0].justificatif.fichier == "b.pdf"
    assert rapprochements[1].justificatif.fichier == "a.pdf"
    assert rapprochements[3].sans_piece
    assert [m.libelle for m in pieces_manquantes(rapprochements)] == ["CB LIBRAIRIE"]
    assert [j.fichier for j in orphelins] == ["c.pdf"]


def test_tri_par_montant():
    rapprochements, _ = rapprocher([Mouvement(date(2026, 9, 1), "A", D("-10")),
                                    Mouvement(date(2026, 9, 2), "B", D("-900")),
                                    Mouvement(date(2026, 9, 3), "C", D("300"))], [])
    assert [m.libelle for m in pieces_manquantes(rapprochements)] == ["B", "C", "A"]


def test_mail_complet_et_vide():
    assert "tout est complet" in rediger_mail({"periode": "mai"}, [])
    mail = rediger_mail({"prenom_contact": "Alex", "periode": "mai"},
                        [Mouvement(date(2026, 5, 3), "CB X", D("-1240"))])
    assert "1 justificatif à nous transmettre" in mail and "1 240,00 €" in mail and "03/05/2026" in mail


def test_exemple_contre_manifeste(tmp_path):
    dossier = RACINE / "exemples" / "relance-pieces"
    manifeste = json.loads((dossier / "manifeste.json").read_text(encoding="utf-8"))["pieces_manquantes"]
    for client in ("boulangerie-du-canal", "studio-ostinato"):
        resultat = traiter_client(dossier / client, tmp_path)
        attendus = manifeste[resultat["client"]]
        assert sorted(abs(D(m["montant"])) for m in resultat["manquants"]) == \
            sorted(D(a["montant"]) for a in attendus)
        assert (tmp_path / f"{client}-relance.md").exists()
    boulangerie = traiter_client(dossier / "boulangerie-du-canal", tmp_path)
    assert [j["tiers"] for j in boulangerie["justificatifs_sans_mouvement"]] == ["Grossiste Vaisselle Pro"]
