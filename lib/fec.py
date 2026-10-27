"""Lecture d'un Fichier des Écritures Comptables (FEC).

Format défini par l'article A47 A-1 du Livre des procédures fiscales et commenté
au BOFiP (BOI-CF-IOR-60-40-20). Liens dans references/sources.md du skill.

Ce que le lecteur accepte :
- séparateur tabulation ou barre verticale (les deux prévus par le texte) ;
- encodage UTF-8 (avec ou sans BOM) ou Windows-1252 / Latin-1 ;
- dates AAAAMMJJ, montants avec virgule ou point décimal ;
- la variante Montant + Sens (D/C ou +1/-1) à la place de Debit + Credit.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from montants import ZERO, lire_montant

COLONNES_FEC = (
    "JournalCode",
    "JournalLib",
    "EcritureNum",
    "EcritureDate",
    "CompteNum",
    "CompteLib",
    "CompAuxNum",
    "CompAuxLib",
    "PieceRef",
    "PieceDate",
    "EcritureLib",
    "Debit",
    "Credit",
    "EcritureLet",
    "DateLet",
    "ValidDate",
    "Montantdevise",
    "Idevise",
)

_ENCODAGES = ("utf-8-sig", "cp1252")
_SEPARATEURS = ("\t", "|")


@dataclass(frozen=True)
class LigneFec:
    numero_ligne: int
    journal_code: str
    journal_lib: str
    ecriture_num: str
    ecriture_date: date | None
    compte_num: str
    compte_lib: str
    comp_aux_num: str
    comp_aux_lib: str
    piece_ref: str
    piece_date: date | None
    ecriture_lib: str
    debit: Decimal
    credit: Decimal
    ecriture_let: str
    date_let: date | None
    valid_date: date | None

    @property
    def solde(self) -> Decimal:
        """Débit moins crédit."""
        return self.debit - self.credit

    @property
    def montant(self) -> Decimal:
        """Le montant de la ligne, quel que soit le sens."""
        return self.debit if self.debit else self.credit


@dataclass(frozen=True)
class FichierFec:
    lignes: tuple[LigneFec, ...]
    separateur: str
    encodage: str
    colonnes_manquantes: tuple[str, ...]
    avertissements: tuple[str, ...] = field(default=())


def lire_date(texte: str) -> date | None:
    """'20250331' ou '2025-03-31' ou '31/03/2025' -> date. Vide -> None."""
    brut = (texte or "").strip()
    if not brut:
        return None
    for motif in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(brut[:10], motif).date()
        except ValueError:
            continue
    raise ValueError(f"Date illisible : {texte!r}")


def _decoder(contenu: bytes) -> tuple[str, str]:
    for encodage in _ENCODAGES:
        try:
            return contenu.decode(encodage), encodage
        except UnicodeDecodeError:
            continue
    return contenu.decode("latin-1"), "latin-1"


def _detecter_separateur(entete: str) -> str:
    for separateur in _SEPARATEURS:
        if entete.count(separateur) >= 10:
            return separateur
    raise ValueError(
        "Séparateur non reconnu : le FEC doit utiliser la tabulation ou la barre verticale."
    )


def _debit_credit(champs: dict[str, str]) -> tuple[Decimal, Decimal]:
    if "Debit" in champs or "Credit" in champs:
        return lire_montant(champs.get("Debit")), lire_montant(champs.get("Credit"))
    montant = lire_montant(champs.get("Montant"))
    sens = (champs.get("Sens") or "").strip().upper()
    if sens in ("D", "+1", "1"):
        return montant, ZERO
    if sens in ("C", "-1"):
        return ZERO, montant
    raise ValueError(f"Sens inconnu : {sens!r}")


def _construire_ligne(numero: int, champs: dict[str, str]) -> LigneFec:
    debit, credit = _debit_credit(champs)
    texte = lambda nom: (champs.get(nom) or "").strip()  # noqa: E731
    return LigneFec(
        numero_ligne=numero,
        journal_code=texte("JournalCode"),
        journal_lib=texte("JournalLib"),
        ecriture_num=texte("EcritureNum"),
        ecriture_date=lire_date(texte("EcritureDate")),
        compte_num=texte("CompteNum"),
        compte_lib=texte("CompteLib"),
        comp_aux_num=texte("CompAuxNum"),
        comp_aux_lib=texte("CompAuxLib"),
        piece_ref=texte("PieceRef"),
        piece_date=lire_date(texte("PieceDate")),
        ecriture_lib=texte("EcritureLib"),
        debit=debit,
        credit=credit,
        ecriture_let=texte("EcritureLet"),
        date_let=lire_date(texte("DateLet")),
        valid_date=lire_date(texte("ValidDate")),
    )


def lire_fec_texte(texte: str, encodage: str = "utf-8") -> FichierFec:
    """Lit un FEC déjà décodé."""
    lignes_brutes = [ligne for ligne in texte.splitlines() if ligne.strip()]
    if not lignes_brutes:
        raise ValueError("FEC vide.")
    separateur = _detecter_separateur(lignes_brutes[0])
    entete = [nom.strip() for nom in lignes_brutes[0].split(separateur)]
    variante_sens = "Montant" in entete and "Sens" in entete
    attendues = [c for c in COLONNES_FEC if not (variante_sens and c in ("Debit", "Credit"))]
    manquantes = tuple(c for c in attendues if c not in entete)
    avertissements = []
    lignes = []
    for numero, brute in enumerate(lignes_brutes[1:], start=2):
        valeurs = brute.split(separateur)
        if len(valeurs) != len(entete):
            avertissements.append(
                f"Ligne {numero} : {len(valeurs)} champs au lieu de {len(entete)}, ignorée."
            )
            continue
        try:
            lignes.append(_construire_ligne(numero, dict(zip(entete, valeurs))))
        except ValueError as erreur:
            avertissements.append(f"Ligne {numero} : {erreur}, ignorée.")
    return FichierFec(
        lignes=tuple(lignes),
        separateur=separateur,
        encodage=encodage,
        colonnes_manquantes=manquantes,
        avertissements=tuple(avertissements),
    )


def lire_fec(chemin: str | Path) -> FichierFec:
    """Lit un FEC depuis un fichier .txt ou .csv."""
    texte, encodage = _decoder(Path(chemin).read_bytes())
    return lire_fec_texte(texte, encodage)


def soldes_par_compte(lignes: tuple[LigneFec, ...] | list[LigneFec]) -> dict[str, Decimal]:
    """Solde (débit moins crédit) de chaque CompteNum."""
    soldes: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for ligne in lignes:
        soldes[ligne.compte_num] += ligne.solde
    return dict(soldes)


def soldes_par_tiers(lignes: tuple[LigneFec, ...] | list[LigneFec]) -> dict[tuple[str, str], Decimal]:
    """Solde de chaque couple (compte, compte auxiliaire), pour les comptes de tiers."""
    soldes: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    for ligne in lignes:
        if ligne.comp_aux_num:
            soldes[(ligne.compte_num, ligne.comp_aux_num)] += ligne.solde
    return dict(soldes)


def libelles_comptes(lignes: tuple[LigneFec, ...] | list[LigneFec]) -> dict[str, str]:
    """Premier libellé rencontré pour chaque compte (et chaque compte auxiliaire)."""
    libelles: dict[str, str] = {}
    for ligne in lignes:
        libelles.setdefault(ligne.compte_num, ligne.compte_lib)
        if ligne.comp_aux_num:
            libelles.setdefault(ligne.comp_aux_num, ligne.comp_aux_lib)
    return libelles
