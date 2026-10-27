"""Génère deux FEC 100 % factices (2024 et 2025) d'une SAS de services imaginaire.

Graine fixe : relancer le script redonne exactement les mêmes fichiers.
Les anomalies de révision sont posées volontairement dans l'exercice 2025 et
décrites dans exemples/fec/manifeste.json, que les tests utilisent comme vérité.

Usage : python outils/generer_fec.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "lib"))

from calendrier import est_jour_ouvre  # noqa: E402
from fec import COLONNES_FEC  # noqa: E402
from montants import CENTIME, ZERO, arrondir  # noqa: E402

SIREN = "000000000"
SOCIETE = "Pivert Conseil SAS (société fictive)"
TVA = Decimal("0.20")
DOSSIER = RACINE / "exemples" / "fec"

CLIENTS = [
    ("C001", "Maison Ardoise"), ("C002", "Brasserie du Quai"), ("C003", "Optique Rivage"),
    ("C004", "Transports Verdier"), ("C005", "Clinique des Saules"), ("C006", "Librairie Méandre"),
    ("C007", "Garage Horizon"), ("C008", "Studio Basalte"), ("C009", "Hôtel des Pins"),
    ("C010", "Coopérative Blé d'Or"), ("C011", "Agence Nacre"), ("C012", "Menuiserie Carène"),
]
# (code, nom, compte de charge, libellé du compte, montant HT moyen, nombre par mois)
FOURNISSEURS = [
    ("F001", "SCI Les Tilleuls", "613200", "Locations immobilières", 1850, 1),
    ("F002", "Opérateur Télécom", "626000", "Frais postaux et télécom", 480, 1),
    ("F003", "Logiciels Nuage", "651000", "Redevances logiciels", 900, 2),
    ("F004", "Dév Indépendant Lemaire", "604000", "Achats de prestations", 3200, 4),
    ("F005", "Bureau Plus", "606400", "Fournitures administratives", 260, 2),
    ("F006", "Cabinet Juridique Orme", "622600", "Honoraires", 1250, 1),
    ("F007", "Assurances Mutuelles", "616000", "Primes d'assurance", 330, 1),
    ("F008", "Traiteur Événements", "625700", "Réceptions", 280, 1),
    ("F009", "Agence Voyages Pro", "625100", "Voyages et déplacements", 620, 2),
]
SALARIES = [f"S{n:02d}" for n in range(1, 10)]


@dataclass
class Ecriture:
    journal: str
    jour: date
    piece: str
    libelle: str
    lignes: list[dict] = field(default_factory=list)


@dataclass
class Exercice:
    annee: int
    rng: random.Random
    ecritures: list[Ecriture] = field(default_factory=list)
    a_lettrer: list[tuple[dict, dict, date]] = field(default_factory=list)

    def ajouter(self, journal, jour, piece, libelle, lignes):
        ecriture = Ecriture(journal, jour, piece, libelle, lignes)
        self.ecritures.append(ecriture)
        return ecriture


JOURNAUX = {"AN": "A-nouveaux", "VE": "Ventes", "AC": "Achats", "BQ": "Banque",
            "OD": "Opérations diverses", "PA": "Paie", "NF": "Notes de frais"}


def ligne(compte, libelle, debit=ZERO, credit=ZERO, aux="", aux_lib=""):
    return {"compte": compte, "compte_lib": libelle, "debit": arrondir(debit),
            "credit": arrondir(credit), "aux": aux, "aux_lib": aux_lib, "let": "", "date_let": None}


def jour_ouvre_aleatoire(rng, annee, mois, debut=1, fin=28):
    while True:
        jour = date(annee, mois, rng.randint(debut, fin))
        if est_jour_ouvre(jour):
            return jour


def montant_lognormal(rng, moyenne, sigma=0.55):
    """Montant positif dont la distribution suit bien la loi de Benford quand on en tire beaucoup."""
    mu = math.log(moyenne) - sigma * sigma / 2
    return arrondir(Decimal(str(math.exp(rng.gauss(mu, sigma)))))


def facture_vente(ex, jour, numero, client, ht):
    tva = arrondir(ht * TVA)
    code, nom = client
    lignes = [ligne("411000", "Clients", debit=ht + tva, aux=code, aux_lib=nom),
              ligne("706000", "Prestations de services", credit=ht),
              ligne("445710", "TVA collectée", credit=tva)]
    return ex.ajouter("VE", jour, f"FV{ex.annee}-{numero:04d}", f"Facture {nom}", lignes)


def facture_achat(ex, jour, numero, fournisseur, ht):
    code, nom, compte, compte_lib, _, _ = fournisseur
    tva = ZERO if compte in ("616000", "613200") else arrondir(ht * TVA)
    lignes = [ligne(compte, compte_lib, debit=ht)]
    if tva:
        lignes.append(ligne("445660", "TVA déductible sur ABS", debit=tva))
    lignes.append(ligne("401000", "Fournisseurs", credit=ht + tva, aux=code, aux_lib=nom))
    return ex.ajouter("AC", jour, f"FA{ex.annee}-{numero:04d}", f"Facture {nom}", lignes)


def reglement(ex, jour, piece, tiers_ligne, banque="512000"):
    """Encaissement ou décaissement d'une facture, lettré avec elle."""
    montant = tiers_ligne["debit"] or tiers_ligne["credit"]
    sens_client = tiers_ligne["debit"] > 0
    tiers = ligne(tiers_ligne["compte"], tiers_ligne["compte_lib"],
                  debit=ZERO if sens_client else montant, credit=montant if sens_client else ZERO,
                  aux=tiers_ligne["aux"], aux_lib=tiers_ligne["aux_lib"])
    banque_ligne = ligne(banque, "Banque", debit=montant if sens_client else ZERO,
                         credit=ZERO if sens_client else montant)
    libelle = ("Virement reçu " if sens_client else "Virement émis ") + tiers_ligne["aux_lib"]
    ex.ajouter("BQ", jour, piece, libelle, [banque_ligne, tiers])
    ex.a_lettrer.append((tiers_ligne, tiers, jour))


# --- ouverture --------------------------------------------------------------

OUVERTURE_2024 = {
    "comptes": {"101300": ("Capital souscrit appelé versé", Decimal("-50000")),
                "106800": ("Autres réserves", Decimal("-80000")),
                "164000": ("Emprunts auprès des établissements de crédit", Decimal("-30000")),
                "218300": ("Matériel de bureau et informatique", Decimal("40000")),
                "281830": ("Amortissements matériel informatique", Decimal("-18000")),
                "431000": ("Sécurité sociale", Decimal("-14000")),
                "445510": ("TVA à décaisser", Decimal("-9000")),
                "512000": ("Banque", Decimal("144000"))},
    "tiers": [("411000", "Clients", "C002", "Brasserie du Quai", "FV2023-0187", date(2023, 11, 20), Decimal("9600")),
              ("411000", "Clients", "C005", "Clinique des Saules", "FV2023-0201", date(2023, 12, 8), Decimal("15400")),
              ("401000", "Fournisseurs", "F004", "Dév Indépendant Lemaire", "FA2023-0410", date(2023, 12, 15), Decimal("-8000"))],
}


def ecrire_ouverture(ex, ouverture):
    jour = date(ex.annee, 1, 1)
    lignes = []
    for compte, (libelle, solde) in sorted(ouverture["comptes"].items()):
        if solde:
            lignes.append(ligne(compte, libelle, debit=max(solde, ZERO), credit=max(-solde, ZERO)))
    for compte, libelle, aux, aux_lib, piece, piece_date, solde in ouverture["tiers"]:
        l = ligne(compte, libelle, debit=max(solde, ZERO), credit=max(-solde, ZERO), aux=aux, aux_lib=aux_lib)
        l["piece"], l["piece_date"] = piece, piece_date
        lignes.append(l)
    ex.ajouter("AN", jour, f"AN{ex.annee}", "Reprise des soldes", lignes)
    return [l for l in lignes if l["aux"]]


# --- une année d'activité ---------------------------------------------------

@dataclass(frozen=True)
class Parametres:
    ca_mensuel: int
    nb_salaries: int
    salaire_moyen: int
    honoraires_moyen: int
    receptions_moyen: int
    is_precedent: Decimal
    anomalies: bool


def simuler_ventes(ex, p, mois, numeros, ouvertes):
    nb = ex.rng.randint(14, 20)
    for _ in range(nb):
        clients = [c for c in CLIENTS if not (p.anomalies and c[0] == "C011" and mois > 9)]
        client = ex.rng.choice(clients)
        ht = montant_lognormal(ex.rng, p.ca_mensuel / nb, 1.1)
        numeros["VE"] += 1
        jour = jour_ouvre_aleatoire(ex.rng, ex.annee, mois)
        facture = facture_vente(ex, jour, numeros["VE"], client, ht)
        paiement = jour + timedelta(days=ex.rng.randint(20, 60))
        while not est_jour_ouvre(paiement):
            paiement += timedelta(days=1)
        if paiement.year == ex.annee:
            reglement(ex, paiement, f"REL{paiement:%Y%m}", facture.lignes[0])
        else:
            ouvertes.append(facture.lignes[0])


def simuler_achats(ex, p, mois, numeros, ouvertes):
    for fournisseur in FOURNISSEURS:
        code, _, compte, _, moyen, nombre = fournisseur
        moyen = {"622600": p.honoraires_moyen, "625700": p.receptions_moyen}.get(compte, moyen)
        for _ in range(nombre):
            ht = Decimal(moyen) if code == "F001" else montant_lognormal(ex.rng, moyen, 1.0)
            numeros["AC"] += 1
            jour = jour_ouvre_aleatoire(ex.rng, ex.annee, mois)
            facture = facture_achat(ex, jour, numeros["AC"], fournisseur, ht)
            paiement = jour + timedelta(days=ex.rng.randint(0, 30))
            while not est_jour_ouvre(paiement):
                paiement += timedelta(days=1)
            if paiement.year != ex.annee:
                ouvertes.append(facture.lignes[-1])
                continue
            banque = "512200" if p.anomalies and code == "F009" and mois >= 10 else "512000"
            reglement(ex, paiement, f"VIR{paiement:%Y%m}", facture.lignes[-1], banque)


def simuler_paie(ex, p, mois):
    fin = jour_ouvre_aleatoire(ex.rng, ex.annee, mois, 26, 28)
    bruts = [montant_lognormal(ex.rng, p.salaire_moyen, 0.25) for _ in range(p.nb_salaries)]
    brut = sum(bruts, ZERO)
    patronal = arrondir(brut * Decimal("0.42"))
    salarial = arrondir(brut * Decimal("0.22"))
    lignes = [ligne("641100", "Salaires et appointements", debit=brut),
              ligne("645100", "Cotisations URSSAF", debit=patronal),
              ligne("431000", "Sécurité sociale", credit=patronal + salarial)]
    nets = []
    for salarie, montant in zip(SALARIES, bruts):
        net = arrondir(montant * Decimal("0.78"))
        nets.append(ligne("421000", "Personnel - rémunérations dues", credit=net, aux=salarie, aux_lib=f"Salarié {salarie}"))
    ecart = arrondir(brut - salarial) - sum((l["credit"] for l in nets), ZERO)
    nets[0]["credit"] += ecart
    ex.ajouter("PA", fin, f"PAIE{ex.annee}{mois:02d}", f"Paie {mois:02d}/{ex.annee}", lignes + nets)
    versement = fin + timedelta(days=1)
    while not est_jour_ouvre(versement) or versement.month != mois:
        versement -= timedelta(days=1)
    for net in nets:
        reglement(ex, versement, f"SAL{ex.annee}{mois:02d}", net)
    return patronal + salarial


def simuler_notes_de_frais(ex, p, mois):
    nombre = ex.rng.randint(3, 6)
    montants = [montant_lognormal(ex.rng, 70, 0.9) for _ in range(nombre)]
    if p.anomalies:
        montants += [arrondir(Decimal(ex.rng.randint(40000, 49999)) / 100) for _ in range(5)]
    for numero, ttc in enumerate(montants, start=1):
        jour = jour_ouvre_aleatoire(ex.rng, ex.annee, mois, 1, 24)
        salarie = ex.rng.choice(SALARIES[: p.nb_salaries])
        compte, libelle = ex.rng.choice([("625100", "Voyages et déplacements"), ("625700", "Réceptions")])
        ht = arrondir(ttc / (1 + TVA))
        ecriture = ex.ajouter("NF", jour, f"NDF{ex.annee}{mois:02d}-{numero:02d}", f"Note de frais {salarie}",
                              [ligne(compte, libelle, debit=ht),
                               ligne("445660", "TVA déductible sur ABS", debit=ttc - ht),
                               ligne("421000", "Personnel - rémunérations dues", credit=ttc,
                                     aux=salarie, aux_lib=f"Salarié {salarie}")])
        remboursement = jour_ouvre_aleatoire(ex.rng, ex.annee, mois, 25, 28)
        reglement(ex, remboursement, f"NDF{ex.annee}{mois:02d}", ecriture.lignes[-1])


def solde_mois(ex, compte, mois):
    return sum((l["credit"] - l["debit"] for e in ex.ecritures if e.jour.month == mois and e.journal != "AN"
                for l in e.lignes if l["compte"] == compte), ZERO)


def simuler_tva(ex, mois):
    collectee = solde_mois(ex, "445710", mois)
    deductible = -solde_mois(ex, "445660", mois)
    fin = date(ex.annee, mois, 28)
    while not est_jour_ouvre(fin):
        fin -= timedelta(days=1)
    ex.ajouter("OD", fin, f"CA3-{ex.annee}{mois:02d}", f"Déclaration de TVA {mois:02d}/{ex.annee}",
               [ligne("445710", "TVA collectée", debit=collectee),
                ligne("445660", "TVA déductible sur ABS", credit=deductible),
                ligne("445510", "TVA à décaisser", credit=collectee - deductible)])
    return collectee - deductible


def payer(ex, jour, piece, libelle, compte, compte_lib, montant):
    while not est_jour_ouvre(jour):
        jour += timedelta(days=1)
    ex.ajouter("BQ", jour, piece, libelle, [ligne(compte, compte_lib, debit=montant),
                                           ligne("512000", "Banque", credit=montant)])


def simuler_annee(annee, ouverture, p, graine):
    ex = Exercice(annee, random.Random(graine))
    reprises = ecrire_ouverture(ex, ouverture)
    numeros = {"VE": 0, "AC": 0}
    ouvertes = []
    urssaf_due = -ouverture["comptes"]["431000"][1]
    tva_due = -ouverture["comptes"]["445510"][1]
    # les créances et dettes reprises sont réglées en début d'année
    for reprise in reprises:
        if not (reprise["aux"] == "C007"):
            reglement(ex, jour_ouvre_aleatoire(ex.rng, annee, 1, 5, 25), f"REP{annee}01", reprise)
        else:
            ouvertes.append(reprise)
    if p.anomalies:
        injecter_anomalies(ex)
    if annee == 2024:
        # la facture de Garage Horizon qui ne sera jamais payée (créance ancienne en 2025)
        impayee = facture_vente(ex, date(2024, 5, 10), 900, ("C007", "Garage Horizon"), Decimal("6000.00"))
        ouvertes.append(impayee.lignes[0])
    acompte_is = arrondir(p.is_precedent / 4)
    capital_restant = -ouverture["comptes"]["164000"][1]
    for mois in range(1, 13):
        simuler_ventes(ex, p, mois, numeros, ouvertes)
        simuler_achats(ex, p, mois, numeros, ouvertes)
        simuler_notes_de_frais(ex, p, mois)
        payer(ex, date(annee, mois, 15), f"URS{annee}{mois:02d}", "Cotisations URSSAF",
              "431000", "Sécurité sociale", urssaf_due)
        payer(ex, date(annee, mois, 20), f"TVA{annee}{mois:02d}", "Paiement TVA",
              "445510", "TVA à décaisser", tva_due)
        urssaf_due = simuler_paie(ex, p, mois)
        tva_due = simuler_tva(ex, mois)
        interets = arrondir(capital_restant * Decimal("0.035") / 12)
        jour = jour_ouvre_aleatoire(ex.rng, annee, mois, 5, 10)
        ex.ajouter("BQ", jour, f"ECH{annee}{mois:02d}", "Échéance emprunt",
                   [ligne("164000", "Emprunts auprès des établissements de crédit", debit=Decimal(800)),
                    ligne("661100", "Intérêts des emprunts", debit=interets),
                    ligne("512000", "Banque", credit=800 + interets)])
        capital_restant -= 800
        frais = montant_lognormal(ex.rng, 95, 0.3)
        ex.ajouter("BQ", jour_ouvre_aleatoire(ex.rng, annee, mois, 26, 28), f"FB{annee}{mois:02d}",
                   "Frais bancaires", [ligne("627000", "Services bancaires", debit=frais),
                                       ligne("512000", "Banque", credit=frais)])
        if mois == 6 and "120000" in ouverture["comptes"]:
            report = -ouverture["comptes"]["120000"][1]
            ex.ajouter("OD", date(annee, 6, 30), f"AFF{annee}", "Affectation du résultat",
                       [ligne("120000", "Résultat de l'exercice (bénéfice)", debit=report),
                        ligne("106800", "Autres réserves", credit=report)])
        if mois in (3, 6, 9, 12) and acompte_is:
            payer(ex, date(annee, mois, 15), f"IS{annee}{mois:02d}", "Acompte d'impôt sur les sociétés",
                  "444000", "État - impôt sur les bénéfices", acompte_is)
    cloturer(ex)
    lettrer(ex)
    return ex, ouvertes


def injecter_anomalies(ex):
    a = ex.annee
    # compte d'attente non soldé : deux sorties de banque sans pièce
    for jour, montant, libelle in ((date(a, 11, 18), Decimal("2150.00"), "Prélèvement SEPA non identifié"),
                                   (date(a, 12, 9), Decimal("1330.00"), "Virement émis sans pièce")):
        ex.ajouter("BQ", jour, f"ATT{jour:%Y%m%d}", libelle,
                   [ligne("471000", "Compte d'attente", debit=montant), ligne("512000", "Banque", credit=montant)])
    # fournisseur payé deux fois
    facture = facture_achat(ex, date(a, 10, 7), 900, FOURNISSEURS[4], Decimal("1650.00"))
    reglement(ex, date(a, 10, 21), f"VIR{a}10", facture.lignes[-1])
    montant = facture.lignes[-1]["credit"]
    ex.ajouter("BQ", date(a, 11, 4), f"VIR{a}11", "Virement émis Bureau Plus",
               [ligne("401000", "Fournisseurs", debit=montant, aux="F005", aux_lib="Bureau Plus"),
                ligne("512000", "Banque", credit=montant)])
    # client qui a payé deux fois la même facture
    vente = facture_vente(ex, date(a, 6, 10), 900, ("C011", "Agence Nacre"), Decimal("2000.00"))
    reglement(ex, date(a, 7, 8), f"REL{a}07", vente.lignes[0])
    ttc = vente.lignes[0]["debit"]
    ex.ajouter("BQ", date(a, 7, 22), f"REL{a}07", "Virement reçu Agence Nacre",
               [ligne("512000", "Banque", debit=ttc),
                ligne("411000", "Clients", credit=ttc, aux="C011", aux_lib="Agence Nacre")])
    # écritures passées un week-end ou un jour férié
    for jour, montant in ((date(a, 3, 16), "1800.00"), (date(a, 8, 9), "2400.00"),
                          (date(a, 7, 14), "950.00"), (date(a, 12, 25), "3100.00")):
        ex.ajouter("OD", jour, f"REG{jour:%m%d}", "Régularisation manuelle",
                   [ligne("622600", "Honoraires", debit=Decimal(montant)),
                    ligne("604000", "Achats de prestations", credit=Decimal(montant))])


def resultat(ex):
    return -sum((l["debit"] - l["credit"] for e in ex.ecritures for l in e.lignes
                 if l["compte"][0] in "67"), ZERO)


def impot_societes(benefice):
    """Barème fictif pour les données d'exemple : 15 % puis 25 % au-delà de 42 500 €."""
    if benefice <= 0:
        return ZERO
    tranche = min(benefice, Decimal(42500))
    return arrondir(tranche * Decimal("0.15") + (benefice - tranche) * Decimal("0.25"), 1)


def cloturer(ex):
    fin = date(ex.annee, 12, 31)
    ex.ajouter("OD", fin, f"AMO{ex.annee}", "Dotation aux amortissements",
               [ligne("681120", "Dotations aux amortissements des immobilisations corporelles", debit=Decimal(8000)),
                ligne("281830", "Amortissements matériel informatique", credit=Decimal(8000))])
    impot = impot_societes(resultat(ex))
    if impot:
        ex.ajouter("OD", fin, f"IS{ex.annee}", "Impôt sur les sociétés de l'exercice",
                   [ligne("695000", "Impôt sur les bénéfices", debit=impot),
                    ligne("444000", "État - impôt sur les bénéfices", credit=impot)])


def lettrer(ex):
    compteurs: dict[tuple[str, str], int] = {}
    for facture, reglement_ligne, jour in ex.a_lettrer:
        cle = (facture["compte"], facture["aux"])
        compteurs[cle] = compteurs.get(cle, 0) + 1
        code = code_lettrage(compteurs[cle])
        for l in (facture, reglement_ligne):
            l["let"], l["date_let"] = code, jour


def code_lettrage(rang):
    lettres = ""
    while rang:
        rang, reste = divmod(rang - 1, 26)
        lettres = chr(65 + reste) + lettres
    return lettres


def numeroter(ex, trou_achats=False):
    """Numéro continu par journal, dans l'ordre des dates. Option : supprime deux numéros en AC."""
    par_journal: dict[str, int] = {}
    numeros = {}
    for ecriture in sorted(ex.ecritures, key=lambda e: (e.jour, e.journal, e.piece)):
        rang = par_journal.get(ecriture.journal, 0) + 1
        if trou_achats and ecriture.journal == "AC" and rang == 150:
            rang += 2
        par_journal[ecriture.journal] = rang
        numeros[id(ecriture)] = f"{ecriture.journal}{rang:05d}"
    return numeros


# --- sorties ----------------------------------------------------------------

def ouverture_suivante(ex):
    soldes: dict[str, Decimal] = {}
    libelles: dict[str, str] = {}
    tiers = []
    for ecriture in ex.ecritures:
        for l in ecriture.lignes:
            if l["compte"][0] in "67":
                continue
            if l["aux"]:
                if not l["let"]:
                    tiers.append((l["compte"], l["compte_lib"], l["aux"], l["aux_lib"],
                                  l.get("piece", ecriture.piece), l.get("piece_date", ecriture.jour),
                                  l["debit"] - l["credit"]))
                continue
            soldes[l["compte"]] = soldes.get(l["compte"], ZERO) + l["debit"] - l["credit"]
            libelles.setdefault(l["compte"], l["compte_lib"])
    comptes = {c: (libelles[c], s) for c, s in soldes.items() if s}
    comptes["120000"] = ("Résultat de l'exercice (bénéfice)", -resultat(ex))
    return {"comptes": comptes, "tiers": tiers}


def ecrire_fec(ex, chemin, trou_achats=False):
    numeros = numeroter(ex, trou_achats)
    texte = lambda d: d.strftime("%Y%m%d") if d else ""  # noqa: E731
    montant = lambda m: f"{m:.2f}".replace(".", ",") if m else "0,00"  # noqa: E731
    lignes = ["\t".join(COLONNES_FEC)]
    ordre = sorted(ex.ecritures, key=lambda e: (e.jour, e.journal, numeros[id(e)]))
    for ecriture in ordre:
        valide = ecriture.jour + timedelta(days=ex.rng.randint(0, 6))
        for l in ecriture.lignes:
            lignes.append("\t".join([
                ecriture.journal, JOURNAUX[ecriture.journal], numeros[id(ecriture)], texte(ecriture.jour),
                l["compte"], l["compte_lib"], l["aux"], l["aux_lib"], l.get("piece", ecriture.piece),
                texte(l.get("piece_date", ecriture.jour)), ecriture.libelle, montant(l["debit"]),
                montant(l["credit"]), l["let"], texte(l["date_let"]), texte(valide), "", ""]))
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return len(lignes) - 1


def soldes_tiers(ex):
    soldes: dict[tuple[str, str], Decimal] = {}
    for e in ex.ecritures:
        for l in e.lignes:
            if l["aux"]:
                cle = (l["compte"], l["aux"])
                soldes[cle] = soldes.get(cle, ZERO) + l["debit"] - l["credit"]
    return soldes


def solde_compte(ex, compte):
    return sum((l["debit"] - l["credit"] for e in ex.ecritures for l in e.lignes if l["compte"] == compte), ZERO)


def manifeste(ex):
    tiers = soldes_tiers(ex)
    return {
        "avertissement": "Données 100 % fictives générées par outils/generer_fec.py. Aucune société réelle.",
        "societe": SOCIETE,
        "exercice": ex.annee,
        "anomalies": [
            {"controle": "comptes_attente", "compte": "471000", "solde": str(solde_compte(ex, "471000"))},
            {"controle": "numerotation", "journal": "AC", "numeros_manquants": ["AC00150", "AC00151"]},
            {"controle": "dates_atypiques", "dates": ["2025-03-16", "2025-08-09", "2025-07-14", "2025-12-25"]},
            {"controle": "tiers_non_lettres", "compte": "411000", "tiers": "C007", "piece": "FV2024-0900",
             "date": "2024-05-10", "montant": "7200.00"},
            {"controle": "sens_anormal", "compte": "401000", "tiers": "F005", "solde": str(tiers[("401000", "F005")])},
            {"controle": "sens_anormal", "compte": "411000", "tiers": "C011", "solde": str(tiers[("411000", "C011")])},
            {"controle": "sens_anormal", "compte": "512200", "solde": str(solde_compte(ex, "512200"))},
            {"controle": "ecarts_n_n1", "comptes": ["622600", "625700"]},
            {"controle": "benford", "journal": "NF", "chiffre_surrepresente": 4},
        ],
    }


def main():
    DOSSIER.mkdir(parents=True, exist_ok=True)
    p2024 = Parametres(ca_mensuel=68000, nb_salaries=8, salaire_moyen=3500, honoraires_moyen=1250,
                       receptions_moyen=280, is_precedent=Decimal("24000"), anomalies=False)
    ex2024, _ = simuler_annee(2024, OUVERTURE_2024, p2024, graine=2024)
    n1 = ecrire_fec(ex2024, DOSSIER / f"{SIREN}FEC20241231.txt")
    is_2024 = solde_compte(ex2024, "695000")
    p2025 = Parametres(ca_mensuel=94000, nb_salaries=9, salaire_moyen=3550, honoraires_moyen=3500,
                       receptions_moyen=800, is_precedent=is_2024, anomalies=True)
    ex2025, _ = simuler_annee(2025, ouverture_suivante(ex2024), p2025, graine=2025)
    n = ecrire_fec(ex2025, DOSSIER / f"{SIREN}FEC20251231.txt", trou_achats=True)
    (DOSSIER / "manifeste.json").write_text(json.dumps(manifeste(ex2025), ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    print(f"FEC 2024 : {n1} lignes, résultat {resultat(ex2024)} ; FEC 2025 : {n} lignes, résultat {resultat(ex2025)}")
    print(f"Banque fin 2025 : {solde_compte(ex2025, '512000')} ; 512200 : {solde_compte(ex2025, '512200')}")


if __name__ == "__main__":
    main()
