"""Tiers, journaux et bilan d'ouverture 100 % fictifs du FEC d'exemple. Aucune société réelle."""
from datetime import date
from decimal import Decimal

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

JOURNAUX = {"AN": "A-nouveaux", "VE": "Ventes", "AC": "Achats", "BQ": "Banque",
            "OD": "Opérations diverses", "PA": "Paie", "NF": "Notes de frais"}

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
