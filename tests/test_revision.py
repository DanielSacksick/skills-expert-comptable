"""Tests du skill revision-dossier : cas construits à la main, puis FEC d'exemple contre son manifeste."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from conftest import RACINE, ajouter_scripts

ajouter_scripts("revision-dossier")

from benford import ATTENDU, premier_chiffre, probabilite_khi_deux_pair, analyser, verdict_mad  # noqa: E402
from controles import (controle_comptes_attente, controle_dates_atypiques, controle_ecarts,  # noqa: E402
                       controle_equilibre, controle_numerotation, controle_sens, controle_tiers)
from cycles import cycle_du_compte, sens_normal  # noqa: E402
from fec import LigneFec  # noqa: E402
from reviser import reviser  # noqa: E402

D = Decimal


def l(compte, debit="0", credit="0", jour=date(2025, 3, 3), num="OD00001", journal="OD", aux="", let="",
      piece_date=None):
    return LigneFec(0, journal, journal, num, jour, compte, f"Compte {compte}", aux, f"Tiers {aux}" if aux else "",
                    "P1", piece_date or jour, "Libellé", D(debit), D(credit), let, None, jour)


# --- Benford ----------------------------------------------------------------

def test_premier_chiffre():
    assert premier_chiffre(D("0.0472")) == 4
    assert premier_chiffre(D("1200.00")) == 1
    assert premier_chiffre(D("-987")) == 9
    assert premier_chiffre(D("0")) is None


def test_attendu_somme_a_un():
    assert abs(sum(ATTENDU.values()) - 1) < 1e-12
    assert round(ATTENDU[1], 4) == 0.3010


def test_khi_deux_valeurs_connues():
    # valeur critique classique du khi-deux à 8 ddl au seuil de 5 % : 15,507
    assert abs(probabilite_khi_deux_pair(15.507, 8) - 0.05) < 1e-3
    assert probabilite_khi_deux_pair(0, 8) == 1.0
    with pytest.raises(ValueError):
        probabilite_khi_deux_pair(3, 7)


def test_verdicts_mad():
    assert verdict_mad(0.004) == "conformité forte"
    assert verdict_mad(0.010) == "conformité acceptable"
    assert verdict_mad(0.014) == "conformité marginale"
    assert verdict_mad(0.02) == "non-conformité"


def test_benford_suite_geometrique_conforme_et_suite_truquee():
    # une suite géométrique couvre les ordres de grandeur : elle suit Benford
    geometrique = [D(str(round(10 * 1.01 ** k, 2))) for k in range(2000)]
    assert analyser(geometrique).verdict == "conformité forte"
    truquee = [D("480")] * 500 + geometrique[:500]
    resultat = analyser(truquee)
    assert resultat.verdict == "non-conformité" and resultat.chiffre_le_plus_en_exces == 4


def test_benford_ignore_petits_montants():
    assert analyser([D("5"), D("9.99")]) is None


# --- cycles et sens ---------------------------------------------------------

@pytest.mark.parametrize("compte, cycle", [("445710", "État, impôts et TVA"), ("603700", "Stocks"),
                                            ("604000", "Achats et fournisseurs"), ("512000", "Trésorerie"),
                                            ("281830", "Immobilisations"), ("999", "Non classé")])
def test_cycle_du_compte(compte, cycle):
    assert cycle_du_compte(compte) == cycle


def test_sens_normal():
    assert sens_normal("445660")[1] == "D"
    assert sens_normal("445710")[1] == "C"
    assert sens_normal("609000") is None  # rabais obtenus : sens inverse, pas contrôlé
    assert sens_normal("471000") is None


# --- contrôles sur petits jeux ----------------------------------------------

def test_equilibre():
    assert controle_equilibre([l("411", "100"), l("706", credit="100")]) == []
    constat = controle_equilibre([l("411", "100"), l("706", credit="90")])[0]
    assert constat.montant == D("10")


def test_comptes_attente():
    constats = controle_comptes_attente([l("471000", "50"), l("512000", credit="50"),
                                         l("472000", "20"), l("472000", credit="20")])
    assert [c.compte for c in constats] == ["471000"]


def test_numerotation_trou():
    lignes = [l("6", num=f"AC{n:05d}") for n in (1, 2, 3, 6, 7)]
    constat = controle_numerotation(lignes)[0]
    assert "AC00004, AC00005" in constat.detail


def test_dates_atypiques():
    lignes = [l("6", "1", jour=date(2025, 3, 15), num="OD1"),       # samedi
              l("6", "1", jour=date(2025, 7, 14), num="OD2"),       # férié
              l("6", "1", jour=date(2025, 3, 17), num="OD3"),       # lundi
              l("1", "1", jour=date(2025, 1, 1), num="AN1", journal="AN")]  # à-nouveaux exclus
    details = [c.detail for c in controle_dates_atypiques(lignes)]
    assert len(details) == 2 and "samedi" in details[0] and "Fête nationale" in details[1]


def test_dates_alsace_moselle():
    vendredi_saint = [l("6", "1", jour=date(2025, 4, 18))]
    assert controle_dates_atypiques(vendredi_saint) == []
    assert len(controle_dates_atypiques(vendredi_saint, alsace_moselle=True)) == 1


def test_tiers_ancien_et_lettrage():
    cloture = date(2025, 12, 31)
    lignes = [l("411000", "1000", aux="C1", piece_date=date(2024, 6, 1)),
              l("411000", "500", aux="C1", piece_date=date(2025, 12, 1)),
              l("401000", credit="80", aux="F1"), l("401000", "80", aux="F1")]
    constats = controle_tiers(lignes, cloture)
    ancien = next(c for c in constats if c.compte == "411000")
    assert ancien.montant == D("1000") and ancien.importance == "fort"
    assert any(c.compte == "401000" and c.importance == "faible" for c in constats)


def test_sens_par_tiers_et_banque():
    lignes = [l("401000", "300", aux="F1"), l("401000", credit="100", aux="F2"),
              l("512000", credit="50"), l("530000", "10")]
    comptes = {(c.compte, c.libelle) for c in controle_sens(lignes)}
    assert ("401000", "Tiers F1") in comptes and ("512000", "Compte 512000") in comptes
    assert len(comptes) == 2


def test_ecarts_seuils():
    n = [l("622600", "30000"), l("613200", "10500")]
    n1 = [l("622600", "10000"), l("613200", "10000")]
    constats = controle_ecarts(n, n1, D("5000"), D("20"))
    assert [c.compte for c in constats] == ["622600"]
    assert "+200,0 %" in constats[0].detail


# --- FEC d'exemple contre son manifeste --------------------------------------

DOSSIER = RACINE / "exemples" / "fec"


@pytest.fixture(scope="module")
def resultat_exemple():
    entete, constats, _ = reviser(DOSSIER / "000000000FEC20251231.txt", DOSSIER / "000000000FEC20241231.txt",
                                  D("5000"), D("20"))
    return entete, constats


def test_exemple_lu_sans_erreur(resultat_exemple):
    entete, constats = resultat_exemple
    assert entete["colonnes_manquantes"] == [] and entete["avertissements"] == []
    assert not [c for c in constats if c.controle == "equilibre"]


def test_toutes_les_anomalies_du_manifeste_sont_trouvees(resultat_exemple):
    _, constats = resultat_exemple
    manifeste = json.loads((DOSSIER / "manifeste.json").read_text(encoding="utf-8"))
    par = lambda controle: [c for c in constats if c.controle == controle]  # noqa: E731
    for anomalie in manifeste["anomalies"]:
        controle = anomalie["controle"]
        if controle == "comptes_attente":
            assert any(c.compte == anomalie["compte"] and c.montant == D(anomalie["solde"]) for c in par(controle))
        elif controle == "numerotation":
            assert all(n in par(controle)[0].detail for n in anomalie["numeros_manquants"])
        elif controle == "dates_atypiques":
            vues = {date.fromisoformat(d).strftime("%d/%m/%Y") for d in anomalie["dates"]}
            assert vues == {c.detail.split(" du ")[1][:10] for c in par(controle)}
        elif controle == "tiers_non_lettres":
            assert any(anomalie["tiers"] in c.detail and c.montant == D(anomalie["montant"]) for c in par(controle))
        elif controle == "sens_anormal":
            cible = anomalie.get("tiers", anomalie["compte"])
            assert any(cible in c.detail and abs(c.montant) == abs(D(anomalie["solde"])) for c in par(controle))
        elif controle == "ecarts_n_n1":
            assert set(anomalie["comptes"]) <= {c.compte for c in par(controle)}
        elif controle == "benford":
            assert any(c.compte == f"Journal {anomalie['journal']}" and f"chiffre {anomalie['chiffre_surrepresente']}"
                       in c.detail for c in par(controle))
        else:
            pytest.fail(f"Contrôle inconnu dans le manifeste : {controle}")
