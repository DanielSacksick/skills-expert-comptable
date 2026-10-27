"""Mise en forme de la feuille de travail de révision (Markdown et HTML autonome)."""
from __future__ import annotations

from collections import defaultdict
from html import escape

from controles import FAIBLE, FORT, MOYEN, Constat
from montants import formater_euros

ORDRE_IMPORTANCE = {FORT: 0, MOYEN: 1, FAIBLE: 2}
PASTILLES = {FORT: "🔴", MOYEN: "🟠", FAIBLE: "⚪"}
NOMS_CONTROLES = {
    "equilibre": "Équilibre des journaux", "comptes_attente": "Comptes d'attente",
    "numerotation": "Numérotation des écritures", "dates_atypiques": "Week-ends et jours fériés",
    "tiers_non_lettres": "Lettrage des tiers", "sens_anormal": "Soldes dans le mauvais sens",
    "ecarts_n_n1": "Écarts N / N-1", "benford": "Loi de Benford",
}


def par_cycle(constats: list[Constat]) -> dict[str, list[Constat]]:
    groupes: dict[str, list[Constat]] = defaultdict(list)
    for constat in constats:
        groupes[constat.cycle].append(constat)
    rang = lambda cycle: min(ORDRE_IMPORTANCE[c.importance] for c in groupes[cycle])  # noqa: E731
    return {cycle: sorted(groupes[cycle], key=lambda c: (ORDRE_IMPORTANCE[c.importance], -abs(c.montant)))
            for cycle in sorted(groupes, key=lambda cy: (rang(cy), cy))}


def resume(constats: list[Constat]) -> dict[str, int]:
    return {niveau: sum(1 for c in constats if c.importance == niveau) for niveau in (FORT, MOYEN, FAIBLE)}


def en_markdown(entete: dict, constats: list[Constat], controles_passes: list[str]) -> str:
    compte = resume(constats)
    lignes = [f"# Feuille de travail de révision : {entete['dossier']}", "",
              f"Exercice clos le {entete['cloture']} · {entete['nb_lignes']} lignes · "
              f"comparaison N-1 : {entete['n1']} · seuil de signification : {entete['seuil']}", "",
              f"**{len(constats)} points à justifier** : {compte[FORT]} importants, {compte[MOYEN]} à vérifier, "
              f"{compte[FAIBLE]} mineurs.", "",
              "Contrôles passés : " + ", ".join(NOMS_CONTROLES[c] for c in controles_passes) + ".", ""]
    for cycle, groupe in par_cycle(constats).items():
        lignes += [f"## {cycle}", "", "| | Contrôle | Constat | À faire | Justifié ? |", "|---|---|---|---|---|"]
        for c in groupe:
            lignes.append(f"| {PASTILLES[c.importance]} | {NOMS_CONTROLES[c.controle]} | {c.detail} | {c.a_faire} | ☐ |")
        lignes.append("")
    lignes += ["---", "Brouillon produit par un outil d'aide à la révision. Chaque point reste à apprécier par "
               "l'expert-comptable : un constat n'est pas une erreur certaine."]
    return "\n".join(lignes) + "\n"


STYLE = """
:root{--fond:#fbfaf7;--texte:#1d1d1b;--doux:#6b6a65;--trait:#e4e1d9;--fort:#c0392b;--moyen:#d68910;--faible:#95a5a6}
@media (prefers-color-scheme:dark){:root{--fond:#171716;--texte:#ecebe6;--doux:#a3a29c;--trait:#33322f}}
body{background:var(--fond);color:var(--texte);font:15px/1.5 system-ui,-apple-system,sans-serif;margin:0;padding:24px 16px}
main{max-width:1100px;margin:auto}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 8px}
.meta{color:var(--doux)}.cartes{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}
.carte{border:1px solid var(--trait);border-radius:10px;padding:12px 16px;min-width:140px}
.carte b{display:block;font-size:28px}.fort b{color:var(--fort)}.moyen b{color:var(--moyen)}.faible b{color:var(--faible)}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid var(--trait);padding:8px;text-align:left;vertical-align:top}
th{color:var(--doux);font-weight:500;font-size:13px}.pastille{width:10px;height:10px;border-radius:50%;display:inline-block}
.p-fort{background:var(--fort)}.p-moyen{background:var(--moyen)}.p-faible{background:var(--faible)}
.montant{white-space:nowrap;text-align:right}footer{margin-top:32px;color:var(--doux);font-size:13px}
@media (max-width:700px){td:nth-child(4),th:nth-child(4){display:none}}
"""


def en_html(entete: dict, constats: list[Constat], controles_passes: list[str]) -> str:
    compte = resume(constats)
    blocs = []
    for cycle, groupe in par_cycle(constats).items():
        rangees = "".join(
            f"<tr><td><span class='pastille p-{c.importance}'></span></td><td>{escape(NOMS_CONTROLES[c.controle])}</td>"
            f"<td>{escape(c.detail)}</td><td>{escape(c.a_faire)}</td>"
            f"<td class='montant'>{escape(formater_euros(c.montant)) if c.montant else ''}</td><td>☐</td></tr>"
            for c in groupe)
        blocs.append(f"<h2>{escape(cycle)}</h2><table><tr><th></th><th>Contrôle</th><th>Constat</th>"
                     f"<th>À faire</th><th>Montant</th><th>Justifié</th></tr>{rangees}</table>")
    controles = ", ".join(NOMS_CONTROLES[c] for c in controles_passes)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Révision {escape(entete['dossier'])}</title>
<style>{STYLE}</style></head><body><main>
<h1>Feuille de travail de révision</h1>
<p class="meta">{escape(entete['dossier'])} · exercice clos le {escape(entete['cloture'])} · {entete['nb_lignes']} lignes ·
N-1 : {escape(entete['n1'])} · seuil de signification : {escape(entete['seuil'])}</p>
<div class="cartes"><div class="carte fort"><b>{compte[FORT]}</b>points importants</div>
<div class="carte moyen"><b>{compte[MOYEN]}</b>à vérifier</div><div class="carte faible"><b>{compte[FAIBLE]}</b>mineurs</div></div>
<p class="meta">Contrôles passés : {escape(controles)}.</p>
{''.join(blocs)}
<footer>Brouillon produit par un outil d'aide à la révision. Chaque point reste à apprécier par
l'expert-comptable : un constat n'est pas une erreur certaine.</footer></main></body></html>
"""
