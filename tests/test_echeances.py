"""Tests du skill alerte-echeances : règles d'échéance sur des cas connus et portefeuille d'exemple."""
from dataclasses import replace
from datetime import date
from decimal import Decimal

from conftest import RACINE, ajouter_scripts

ajouter_scripts("alerte-echeances")

from alerter import etat_tresorerie, lire_portefeuille, rediger_message, total_a_payer  # noqa: E402
from echeances import Client, echeances_du_mois  # noqa: E402

D = Decimal
BASE = Client(nom="Test", contact="Alex", tutoiement=False, regime_tva="mensuel", jour_tva=19,
              tva_par_periode=D("6100"), tva_annuelle_n1=D("0"), cloture=(31, 12), soumis_is=True,
              is_dernier_exercice=D("18200"), cfe_n1=D("2900"), cfe_mensualisee=False, effectif=6,
              cotisations_mensuelles=D("11800"), tresorerie=D("14300"))


def natures(client, annee, mois):
    return {e.nature: e for e in echeances_du_mois(client, annee, mois)}


def test_decembre_2026_report_du_samedi():
    e = natures(BASE, 2026, 12)
    assert e["TVA (CA3) du mois précédent"].jour == date(2026, 12, 21)   # 19/12/2026 est un samedi
    assert e["Acompte d'impôt sur les sociétés"].montant == D("4550")     # 18 200 / 4
    assert e["Solde de CFE"].montant == D("2900")                         # sous 3 000 € : pas d'acompte en juin
    assert e["DSN et cotisations sociales du mois précédent"].jour == date(2026, 12, 15)


def test_acompte_is_dispense_et_arrondi():
    dispense = natures(replace(BASE, is_dernier_exercice=D("3000")), 2026, 3)["Acompte d'impôt sur les sociétés"]
    assert dispense.montant == 0 and "Dispensé" in dispense.note
    assert natures(replace(BASE, is_dernier_exercice=D("10002")), 2026, 3)[
        "Acompte d'impôt sur les sociétés"].montant == D("2501")          # 2 500,50 arrondi à l'euro supérieur
    assert "Acompte d'impôt sur les sociétés" not in natures(BASE, 2026, 4)


def test_acompte_is_15_mars_2026_un_dimanche():
    # 15/03/2026 est un dimanche : report au lundi 16
    assert natures(BASE, 2026, 3)["Acompte d'impôt sur les sociétés"].jour == date(2026, 3, 16)


def test_solde_is():
    assert natures(BASE, 2027, 5)["Solde d'impôt sur les sociétés"].jour == date(2027, 5, 18)  # samedi 15, puis lundi de Pentecôte
    decale = replace(BASE, cloture=(30, 6))
    assert "Solde d'impôt sur les sociétés" in natures(decale, 2026, 10)


def test_cfe_avec_acompte():
    gros = replace(BASE, cfe_n1=D("3100"))
    assert natures(gros, 2026, 6)["Acompte de CFE (50 % de la CFE de l'an dernier)"].montant == D("1550")
    assert natures(gros, 2026, 12)["Solde de CFE"].montant == D("1550")
    assert "Solde de CFE" not in natures(replace(BASE, cfe_mensualisee=True), 2026, 12)


def test_regime_simplifie_2026_puis_2027():
    simplifie = replace(BASE, regime_tva="simplifie", tva_annuelle_n1=D("9800"))
    assert natures(simplifie, 2026, 7)["Acompte de TVA (CA12), 55 % de la TVA de l'an dernier"].montant == D("5390")
    assert natures(simplifie, 2026, 12)["Acompte de TVA (CA12), 40 % de la TVA de l'an dernier"].montant == D("3920")
    petit = natures(replace(simplifie, tva_annuelle_n1=D("999")), 2026, 12)
    assert next(e for n, e in petit.items() if n.startswith("Acompte de TVA")).montant == 0
    assert not any(n.startswith("Acompte de TVA") for n in natures(simplifie, 2027, 7))
    assert "TVA : changement de régime" in natures(simplifie, 2027, 1)


def test_trimestriel_et_franchise():
    assert "TVA (CA3) du trimestre précédent" in natures(replace(BASE, regime_tva="trimestriel"), 2027, 1)
    assert not natures(replace(BASE, regime_tva="trimestriel"), 2027, 2).get("TVA (CA3) du trimestre précédent")
    assert not any("TVA" in n for n in natures(replace(BASE, regime_tva="franchise"), 2026, 12))


def test_grande_entreprise_le_5():
    e = natures(replace(BASE, effectif=60), 2026, 12)["DSN et cotisations sociales du mois précédent"]
    assert e.jour == date(2026, 12, 7)                                    # 05/12/2026 samedi


def test_liasse_et_das2():
    assert natures(BASE, 2027, 5)["Liasse fiscale (2065)"].jour == date(2027, 5, 4)
    assert "DAS2 (honoraires de plus de 2 400 € par bénéficiaire)" in natures(BASE, 2027, 1)


def test_tresorerie_et_message():
    echeances = echeances_du_mois(BASE, 2026, 12)
    total = total_a_payer(echeances)
    assert total == D("25350")
    assert etat_tresorerie(BASE, total) == "insuffisante"
    assert etat_tresorerie(replace(BASE, tresorerie=D("30000")), total) == "tendue"
    message = rediger_message(BASE, echeances, 12)
    assert "prévoyez environ 25 400 €" in message and "DSN" in message and "risque d'être juste" in message
    assert "prévois" in rediger_message(replace(BASE, tutoiement=True), echeances, 12)


def test_portefeuille_exemple():
    clients = lire_portefeuille(RACINE / "exemples" / "portefeuille" / "portefeuille.csv")
    assert len(clients) == 10
    alertes = [c.nom for c in clients
               if etat_tresorerie(c, total_a_payer(echeances_du_mois(c, 2026, 12))) == "insuffisante"]
    assert len(alertes) == 3
