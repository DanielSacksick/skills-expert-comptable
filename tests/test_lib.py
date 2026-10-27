"""Tests de la bibliothèque commune (lib/)."""
from datetime import date
from decimal import Decimal

import pytest

from calendrier import est_jour_ouvre, jour_ouvre_suivant, jours_feries, nieme_jour_ouvre, paques
from fec import COLONNES_FEC, lire_fec_texte, soldes_par_compte
from montants import arrondir, formater_euros, lire_montant, pourcentage


# --- montants ---------------------------------------------------------------

@pytest.mark.parametrize(
    "texte, attendu",
    [
        ("1 234,56", "1234.56"),
        ("1234.56", "1234.56"),
        ("1.234,56", "1234.56"),
        ("-12,5", "-12.5"),
        ("", "0"),
        (" 4 200,00 €", "4200.00"),
    ],
)
def test_lire_montant(texte, attendu):
    assert lire_montant(texte) == Decimal(attendu)


def test_lire_montant_illisible():
    with pytest.raises(ValueError):
        lire_montant("douze")


def test_formater_euros():
    assert formater_euros(Decimal("4200")) == "4 200,00 €"
    assert formater_euros(Decimal("4249.5"), 0) == "4 250 €"
    assert formater_euros(Decimal("-1234567.891")) == "-1 234 567,89 €"
    assert formater_euros(Decimal("12")) == "12,00 €"


def test_arrondir_et_pourcentage():
    assert arrondir(Decimal("4249"), 100) == Decimal("4200")
    assert arrondir(Decimal("4250"), 100) == Decimal("4300")
    assert pourcentage(1, 3) == Decimal("33.3")
    assert pourcentage(1, 0) is None


# --- calendrier -------------------------------------------------------------

@pytest.mark.parametrize(
    "annee, attendu",
    [(2024, date(2024, 3, 31)), (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)), (2027, date(2027, 3, 28))],
)
def test_paques(annee, attendu):
    assert paques(annee) == attendu


def test_jours_feries_2026():
    feries = jours_feries(2026)
    assert len(feries) == 11
    assert date(2026, 4, 6) in feries  # lundi de Pâques
    assert date(2026, 5, 14) in feries  # Ascension
    assert date(2026, 5, 25) in feries  # lundi de Pentecôte
    alsace = jours_feries(2026, alsace_moselle=True)
    assert len(alsace) == 13
    assert date(2026, 4, 3) in alsace and date(2026, 12, 26) in alsace


def test_jours_ouvres():
    assert not est_jour_ouvre(date(2026, 7, 14))
    assert not est_jour_ouvre(date(2026, 3, 14))  # samedi
    assert jour_ouvre_suivant(date(2026, 3, 14)) == date(2026, 3, 16)
    assert jour_ouvre_suivant(date(2026, 3, 16)) == date(2026, 3, 16)
    # 1er mai 2026 = vendredi ; 4 mai lundi = 1er jour ouvré ; 5 mai = 2e
    assert nieme_jour_ouvre(2026, 5, 1, 2) == date(2026, 5, 5)


# --- FEC --------------------------------------------------------------------

def _fec(lignes, separateur="\t", entete=COLONNES_FEC):
    return "\n".join([separateur.join(entete)] + [separateur.join(l) for l in lignes])


LIGNE_DEBIT = ["VE", "Ventes", "1", "20250115", "411000", "Clients", "C01", "Client A", "F1",
               "20250115", "Facture F1", "1200,00", "", "AA", "20250210", "20250115", "", ""]
LIGNE_CREDIT = ["VE", "Ventes", "1", "20250115", "706000", "Prestations", "", "", "F1",
                "20250115", "Facture F1", "", "1000,00", "", "", "20250115", "", ""]
LIGNE_TVA = ["VE", "Ventes", "1", "20250115", "445710", "TVA collectée", "", "", "F1",
             "20250115", "Facture F1", "0,00", "200,00", "", "", "20250115", "", ""]


def test_lire_fec_tabulation():
    fichier = lire_fec_texte(_fec([LIGNE_DEBIT, LIGNE_CREDIT, LIGNE_TVA]))
    assert fichier.colonnes_manquantes == ()
    assert len(fichier.lignes) == 3
    premiere = fichier.lignes[0]
    assert premiere.ecriture_date == date(2025, 1, 15)
    assert premiere.debit == Decimal("1200.00") and premiere.credit == 0
    assert premiere.date_let == date(2025, 2, 10)
    soldes = soldes_par_compte(fichier.lignes)
    assert soldes == {"411000": Decimal("1200"), "706000": Decimal("-1000"), "445710": Decimal("-200")}


def test_lire_fec_barre_verticale():
    fichier = lire_fec_texte(_fec([LIGNE_DEBIT], separateur="|"))
    assert fichier.separateur == "|"
    assert fichier.lignes[0].compte_num == "411000"


def test_lire_fec_montant_sens():
    entete = [c for c in COLONNES_FEC if c not in ("Debit", "Credit")]
    entete[11:11] = ["Montant", "Sens"]
    ligne = LIGNE_CREDIT[:11] + ["1000,00", "C"] + LIGNE_CREDIT[13:]
    fichier = lire_fec_texte(_fec([ligne], entete=entete))
    assert fichier.colonnes_manquantes == ()
    assert fichier.lignes[0].credit == Decimal("1000.00")


def test_lire_fec_colonne_manquante_et_ligne_cassee():
    entete = [c for c in COLONNES_FEC if c != "ValidDate"]
    ligne = [v for i, v in enumerate(LIGNE_DEBIT) if i != 15]
    fichier = lire_fec_texte(_fec([ligne, ["trop", "court"]], entete=entete))
    assert fichier.colonnes_manquantes == ("ValidDate",)
    assert len(fichier.lignes) == 1
    assert "Ligne 3" in fichier.avertissements[0]


def test_lire_fec_separateur_inconnu():
    with pytest.raises(ValueError):
        lire_fec_texte(";".join(COLONNES_FEC))
