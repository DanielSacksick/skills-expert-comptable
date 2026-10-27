"""Produit la page du rendez-vous bilan (HTML autonome, imprimable sur une page).

Usage : python rendre_page.py rdv
Lit rdv/chiffres.json (écrit par analyser_bilan.py) et rdv/messages.json (écrit par Claude) :
    {"messages": [{"titre": "...", "texte": "..."}, x3],
     "questions": [{"question": "...", "reponse": "..."}],
     "conseils": ["..."],
     "cabinet": "Nom du cabinet (facultatif)"}
Écrit rdv/rendez-vous.html.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from html import escape
from pathlib import Path

from graphiques import barres_n_n1, courbe_tresorerie
from montants import formater_euros, pourcentage

STYLE = """
:root{--fond:#fcfcfb;--carte:#ffffff;--texte:#0b0b0b;--doux:#52514e;--trait:#e6e4de;--n:#2a78d6;--n1:#b5b3ab;
--hausse:#1a7f37;--baisse:#b42318}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fond:#1a1a19;--carte:#222220;--texte:#f0efec;
--doux:#c3c2b7;--trait:#3a3936;--n:#3987e5;--n1:#6d6c66;--hausse:#4ac26b;--baisse:#ff7b72}}
:root[data-theme="dark"]{--fond:#1a1a19;--carte:#222220;--texte:#f0efec;--doux:#c3c2b7;--trait:#3a3936;--n:#3987e5;
--n1:#6d6c66;--hausse:#4ac26b;--baisse:#ff7b72}
*{box-sizing:border-box}body{margin:0;background:var(--fond);color:var(--texte);font:15px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:980px;margin:auto;padding:28px 16px}h1{font-size:26px;margin:0}h2{font-size:17px;margin:28px 0 10px}
.sous{color:var(--doux);margin:2px 0 20px}.grille{display:grid;gap:12px}
.tuiles{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}.messages{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.carte{background:var(--carte);border:1px solid var(--trait);border-radius:12px;padding:14px 16px}
.tuile b{display:block;font-size:26px;font-variant-numeric:tabular-nums}.tuile small{color:var(--doux)}
.hausse{color:var(--hausse)}.baisse{color:var(--baisse)}.message h3{margin:0 0 6px;font-size:16px}
.message .num{color:var(--n);font-weight:700;margin-right:6px}
.graphes{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}svg{width:100%;height:auto;display:block}
.axe{stroke:var(--trait);stroke-width:1}.n{fill:var(--n)}.n1{fill:var(--n1)}
.ligne-n{fill:none;stroke:var(--n);stroke-width:2}.ligne-n1{fill:none;stroke:var(--n1);stroke-width:2;stroke-dasharray:5 4}
.cible{fill:transparent}.cible:hover{fill:var(--n);fill-opacity:.25}
.valeur{font-size:12px;fill:var(--texte);text-anchor:middle;font-variant-numeric:tabular-nums}.fin{text-anchor:start}
.poste{font-size:12px;fill:var(--doux);text-anchor:middle}
.legende{display:flex;gap:16px;color:var(--doux);font-size:13px;margin-bottom:6px}
.legende i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
details{border-bottom:1px solid var(--trait);padding:8px 0}summary{cursor:pointer;font-weight:600}
ul{margin:0;padding-left:20px}li{margin:4px 0}footer{margin-top:28px;color:var(--doux);font-size:12px}
@media print{body{font-size:12px}main{padding:0}details{padding:3px 0}details>*{display:block}h2{margin:14px 0 6px}}
"""


def charger(dossier: Path) -> tuple[dict, dict]:
    chiffres = json.loads((dossier / "chiffres.json").read_text(encoding="utf-8"))
    chemin_messages = dossier / "messages.json"
    if not chemin_messages.exists():
        raise SystemExit(f"{chemin_messages} manquant : écrire d'abord les messages, questions et conseils.")
    messages = json.loads(chemin_messages.read_text(encoding="utf-8"))
    if len(messages.get("messages", [])) != 3:
        raise SystemExit("messages.json doit contenir exactement 3 messages clés.")
    return chiffres, messages


def _d(valeur) -> Decimal | None:
    return None if valeur is None else Decimal(str(valeur))


def tuile(titre: str, n: Decimal | None, n1: Decimal | None, unite: str = "€", plus_est_mieux: bool = True) -> str:
    if n is None:
        return ""
    texte = formater_euros(n, 0) if unite == "€" else f"{n} {unite}"
    evolution = ""
    if n1 is not None:
        taux = pourcentage(n - n1, abs(n1))
        if taux is not None:
            bon = (taux >= 0) == plus_est_mieux
            fleche = "▲" if taux >= 0 else "▼"
            evolution = (f"<small class='{'hausse' if bon else 'baisse'}'>{fleche} {str(abs(taux)).replace('.', ',')} %"
                         f"</small> <small>contre {formater_euros(n1, 0) if unite == '€' else f'{n1} {unite}'} en N-1</small>")
    return f"<div class='carte tuile'><small>{escape(titre)}</small><b>{escape(texte)}</b>{evolution}</div>"


def construire(chiffres: dict, messages: dict) -> str:
    n, n1 = chiffres["n"], chiffres.get("n1")
    sig = lambda bloc, cle: _d(bloc["sig"][cle]) if bloc else None  # noqa: E731
    bil = lambda bloc, cle: _d(bloc["bilan"][cle]) if bloc else None  # noqa: E731
    tuiles = "".join([
        tuile("Chiffre d'affaires", sig(n, "chiffre_affaires"), sig(n1, "chiffre_affaires")),
        tuile("Résultat net", sig(n, "resultat_net"), sig(n1, "resultat_net")),
        tuile("Trésorerie au 31/12", bil(n, "tresorerie_nette"), bil(n1, "tresorerie_nette")),
        tuile("Délai moyen de paiement des clients", bil(n, "delai_clients_jours"), bil(n1, "delai_clients_jours"),
              "jours", plus_est_mieux=False),
    ])
    postes = [(nom, sig(n, cle), sig(n1, cle)) for nom, cle in (
        ("Chiffre d'affaires", "chiffre_affaires"), ("Valeur ajoutée", "valeur_ajoutee"),
        ("Excédent brut d'exploitation", "ebe"), ("Résultat net", "resultat_net"))]
    serie = lambda bloc: [(m, _d(v)) for m, v in bloc["tresorerie_mensuelle"]] if bloc else None  # noqa: E731
    cartes = "".join(f"<div class='carte message'><h3><span class='num'>{i}</span>{escape(m['titre'])}</h3>"
                     f"<p>{escape(m['texte'])}</p></div>" for i, m in enumerate(messages["messages"], start=1))
    questions = "".join(f"<details><summary>{escape(q['question'])}</summary><p>{escape(q['reponse'])}</p></details>"
                        for q in messages.get("questions", []))
    conseils = "".join(f"<li>{escape(c)}</li>" for c in messages.get("conseils", []))
    legende = ("<div class='legende'><span><i style='background:var(--n1)'></i>Exercice précédent</span>"
               "<span><i style='background:var(--n)'></i>Exercice " + str(n["exercice"]) + "</span></div>") if n1 else ""
    cabinet = escape(messages.get("cabinet", "votre cabinet d'expertise comptable"))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Bilan {n['exercice']}</title>
<style>{STYLE}</style></head><body><main>
<h1>Votre bilan {n['exercice']} en une page</h1>
<p class="sous">{escape(chiffres['client'])} · préparé par {cabinet} pour notre rendez-vous</p>
<div class="grille tuiles">{tuiles}</div>
<h2>Les trois choses à retenir</h2><div class="grille messages">{cartes}</div>
<h2>D'une année sur l'autre</h2>{legende}
<div class="grille graphes"><div class="carte">{barres_n_n1(postes)}</div>
<div class="carte"><small>Argent disponible en banque à la fin de chaque mois</small>
{courbe_tresorerie(serie(n), serie(n1))}</div></div>
<h2>Les questions que vous allez sûrement nous poser</h2>{questions}
<h2>Pour l'année qui vient</h2><ul>{conseils}</ul>
<footer>Chiffres issus de la comptabilité de l'exercice, avant validation définitive des comptes annuels.
Document de travail préparé pour le rendez-vous, à relire avec votre expert-comptable.</footer>
</main></body></html>
"""


def main() -> None:
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else "rdv")
    chiffres, messages = charger(dossier)
    sortie = dossier / "rendez-vous.html"
    sortie.write_text(construire(chiffres, messages), encoding="utf-8")
    print(f"Page écrite : {sortie}")


if __name__ == "__main__":
    main()
