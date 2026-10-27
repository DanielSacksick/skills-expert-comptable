"""Rattachement d'un compte du PCG à un cycle de révision et sens normal de son solde.

Le découpage en cycles est l'usage courant de la révision (il n'a pas de texte officiel).
Les plus longs préfixes gagnent : 4457 passe avant 44, 6037 avant 60.
Voir references/cycles-et-sens.md pour la table commentée.
"""
from __future__ import annotations

CYCLES = (
    ("Capitaux propres", ("10", "11", "12", "13", "14", "15")),
    ("Emprunts et dettes financières", ("16", "17", "66", "76", "519")),
    ("Immobilisations", ("20", "21", "22", "23", "26", "27", "28", "29", "68", "78", "675", "775")),
    ("Stocks", ("3", "603")),
    ("Achats et fournisseurs", ("40", "60", "61", "62")),
    ("Ventes et clients", ("41", "70", "71", "72", "74", "75")),
    ("Social", ("42", "43", "64")),
    ("État, impôts et TVA", ("44", "63", "69")),
    ("Autres tiers et comptes d'attente", ("45", "46", "47", "48", "49")),
    ("Trésorerie", ("50", "51", "52", "53", "54", "58", "59")),
    ("Résultat exceptionnel", ("67", "77")),
    ("Autres charges et produits", ("65", "79")),
)

# sens normal du solde : "D" débiteur, "C" créditeur
SENS_NORMAL = (
    ("401", "C", "Fournisseur"), ("403", "C", "Fournisseur, effets à payer"),
    ("404", "C", "Fournisseur d'immobilisations"), ("408", "C", "Factures non parvenues"),
    ("409", "D", "Fournisseur débiteur (avances, avoirs)"),
    ("411", "D", "Client"), ("413", "D", "Client, effets à recevoir"), ("416", "D", "Client douteux"),
    ("418", "D", "Factures à établir"), ("419", "C", "Client créditeur (avances, avoirs)"),
    ("421", "C", "Rémunérations dues"), ("431", "C", "Sécurité sociale"),
    ("437", "C", "Autres organismes sociaux"),
    ("44551", "C", "TVA à décaisser"), ("44562", "D", "TVA déductible sur immobilisations"),
    ("44566", "D", "TVA déductible"), ("44567", "D", "Crédit de TVA"), ("4457", "C", "TVA collectée"),
    ("455", "C", "Compte courant d'associé"),
    ("512", "D", "Banque"), ("53", "D", "Caisse"),
    ("10", "C", "Capital et réserves"), ("16", "C", "Emprunt"), ("28", "C", "Amortissements"),
    ("6", "D", "Charge"), ("7", "C", "Produit"),
)
# rabais, remises et ristournes : sens inverse de leur classe
EXCEPTIONS_SENS = ("609", "619", "629", "709")

# précisions affichées quand le sens est inattendu
COMMENTAIRES_SENS = {
    "512": "Banque créditrice : découvert ? Vérifier l'autorisation et le reclasser en 519 au bilan.",
    "53": "Une caisse ne peut pas être créditrice : écriture manquante ou erreur d'imputation.",
    "455": "Compte courant d'associé débiteur : vérifier qu'il ne s'agit pas d'un prêt interdit au dirigeant.",
    "401": "Fournisseur débiteur : double paiement, avoir non reçu ou acompte ? Reclasser en 409 si besoin.",
    "411": "Client créditeur : double encaissement, avoir à rembourser ou acompte ? Reclasser en 419 si besoin.",
}


def _plus_long_prefixe(compte: str, prefixes: tuple[str, ...]) -> str | None:
    candidats = [p for p in prefixes if compte.startswith(p)]
    return max(candidats, key=len) if candidats else None


def cycle_du_compte(compte: str) -> str:
    meilleur, cycle_retenu = "", "Non classé"
    for cycle, prefixes in CYCLES:
        prefixe = _plus_long_prefixe(compte, prefixes)
        if prefixe and len(prefixe) > len(meilleur):
            meilleur, cycle_retenu = prefixe, cycle
    return cycle_retenu


def sens_normal(compte: str) -> tuple[str, str, str] | None:
    """(préfixe, sens attendu, nature) ou None si le sens n'est pas contrôlé."""
    if _plus_long_prefixe(compte, EXCEPTIONS_SENS):
        return None
    prefixe = _plus_long_prefixe(compte, tuple(p for p, _, _ in SENS_NORMAL))
    if prefixe is None:
        return None
    return next(entree for entree in SENS_NORMAL if entree[0] == prefixe)


def commentaire_sens(prefixe: str) -> str:
    cle = _plus_long_prefixe(prefixe, tuple(COMMENTAIRES_SENS))
    return COMMENTAIRES_SENS.get(cle, "Solde dans le sens inverse de la nature du compte : à justifier.")
