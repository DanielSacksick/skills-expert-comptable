"""Tests du skill rendez-vous-bilan : SIG calculés à la main, puis cohérence sur le FEC d'exemple."""
import json
from decimal import Decimal

from conftest import RACINE, ajouter_scripts

ajouter_scripts("rendez-vous-bilan")

from analyser_bilan import analyser  # noqa: E402
from graphiques import _court, _echelle, barres_n_n1, courbe_tresorerie  # noqa: E402
from rendre_page import construire  # noqa: E402
from sig import calculer_bilan, calculer_sig  # noqa: E402

D = Decimal

# Soldes (débit - crédit) d'une petite société, chiffrés à la main :
# ventes de marchandises 100 000, achats de marchandises 60 000, variation de stock +5 000 (6037 débiteur)
# prestations 50 000, sous-traitance 10 000, loyer 12 000, subvention 3 000, taxes 2 000,
# salaires 30 000, charges 12 000, dotations 4 000, autres produits 1 000, intérêts 1 500,
# produits financiers 500, exceptionnel +2 000 / -1 000, IS 4 000.
SOLDES = {
    "707000": D("-100000"), "607000": D("60000"), "603700": D("5000"),
    "706000": D("-50000"), "604000": D("10000"), "613200": D("12000"),
    "740000": D("-3000"), "635100": D("2000"), "641000": D("30000"), "645000": D("12000"),
    "681100": D("4000"), "758000": D("-1000"), "661100": D("1500"), "768000": D("-500"),
    "771000": D("-2000"), "671000": D("1000"), "695000": D("4000"),
    "512000": D("20000"), "411000": D("12000"), "401000": D("-6000"), "101300": D("-10000"),
    "164000": D("-8000"), "445510": D("-3000"),
}


def test_sig_a_la_main():
    sig = calculer_sig(SOLDES)
    assert sig.marge_commerciale == D("35000")          # 100 000 - 60 000 - 5 000
    assert sig.production_exercice == D("50000")
    assert sig.consommations_tiers == D("22000")        # 10 000 + 12 000
    assert sig.valeur_ajoutee == D("63000")             # 35 000 + 50 000 - 22 000
    assert sig.ebe == D("22000")                        # 63 000 + 3 000 - 2 000 - 42 000
    assert sig.resultat_exploitation == D("19000")      # 22 000 + 1 000 - 4 000
    assert sig.resultat_financier == D("-1000")
    assert sig.resultat_courant == D("18000")
    assert sig.resultat_exceptionnel == D("1000")
    assert sig.resultat_net == D("15000")
    assert sig.chiffre_affaires == D("150000")


def test_resultat_net_egal_produits_moins_charges():
    gestion = sum((-s for c, s in SOLDES.items() if c[0] in "67"), D(0))
    assert calculer_sig(SOLDES).resultat_net == gestion


def test_bilan_a_la_main():
    soldes = {**SOLDES, "512200": D("-1500")}
    sig = calculer_sig(soldes)
    bilan = calculer_bilan(soldes, sig)
    assert bilan.disponibilites == D("20000") and bilan.concours_bancaires == D("1500")
    assert bilan.tresorerie_nette == D("18500")
    assert bilan.creances_clients == D("12000") and bilan.dettes_fournisseurs == D("6000")
    assert bilan.bfr == D("3000")                       # 12 000 - 6 000 - 3 000
    assert bilan.capitaux_propres == D("25000")         # capital 10 000 + résultat 15 000
    assert bilan.emprunts == D("8000")
    assert bilan.delai_clients_jours == D("24")         # 12 000 / (150 000 x 1,2) x 365


def test_echelle_et_libelles():
    assert _echelle([D("1024530"), D("957810")]) == (D(0), D("1100000"))
    assert _echelle([D("-3500"), D("1200")]) == (D("-3500"), D("1200"))
    assert _court(D("1024530")) == "1,0 M€" and _court(D("45300")) == "45 k€" and _court(D("-800")) == "-800 €"


def test_graphiques_sans_n1():
    assert "<rect" in barres_n_n1([("CA", D("100"), None)])
    svg = courbe_tresorerie([("2025-01", D("10")), ("2025-02", D("-5"))], None)
    assert svg.count("<circle") == 2


def test_exemple_complet():
    dossier = RACINE / "exemples" / "fec"
    n = analyser(dossier / "000000000FEC20251231.txt")
    assert n["controle_resultat"] == n["sig"]["resultat_net"]
    assert n["bilan"]["concours_bancaires"] > 0         # la banque 512200 est à découvert dans l'exemple
    assert len(n["tresorerie_mensuelle"]) == 12


def test_page_complete():
    dossier = RACINE / "exemples" / "fec"
    en_texte = lambda bloc: json.loads(json.dumps(bloc, default=str))  # noqa: E731
    chiffres = {"client": "Exemple", "n": en_texte(analyser(dossier / "000000000FEC20251231.txt")),
                "n1": en_texte(analyser(dossier / "000000000FEC20241231.txt"))}
    messages = json.loads((RACINE / "exemples" / "sorties" / "rendez-vous-bilan" / "messages.json").read_text(encoding="utf-8"))
    page = construire(chiffres, messages)
    assert page.count("class='carte message'") == 3 and "<svg" in page and "1 024 530 €" in page
