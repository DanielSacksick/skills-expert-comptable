# Sources

Vérifiées le 27 octobre 2026.

## Le format du FEC

- Article A47 A-1 du Livre des procédures fiscales : les 18 champs dans l'ordre, séparateur tabulation ou barre verticale, dates au format AAAAMMJJ, variante Montant + Sens. [Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000027804775/)
- Commentaire administratif : BOI-CF-IOR-60-40-20, nom du fichier SirenFECAAAAMMJJ, première ligne d'en-tête. [BOFiP](https://bofip.impots.gouv.fr/bofip/9028-PGP.html)

## Le calendrier

- Jours fériés : article L3133-1 du Code du travail. [Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033020901/)
- Alsace-Moselle (Vendredi saint dans les communes ayant un temple protestant ou une église mixte, et 26 décembre) : article L3134-13. [Légifrance](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006902635)

## La loi de Benford

- Seuils de l'écart absolu moyen (MAD) sur le premier chiffre : 0,006 (conformité forte), 0,012 (acceptable), 0,015 (marginale), au-delà non-conformité. Mark Nigrini, *Benford's Law* (Wiley, 2012), table 7.1. Seuils empiriques, sans valeur critique théorique, cités notamment par le paquet R [benford.analysis](https://cran.r-project.org/package=benford.analysis).
- Limite à connaître : sur de très grands échantillons, ces seuils peuvent conclure à tort. Voir [Severe testing of Benford's law (arXiv 2202.05237)](https://arxiv.org/abs/2202.05237).
- Khi-deux à 8 degrés de liberté : probabilité calculée exactement (formule fermée pour un nombre pair de degrés).

## Ce qui n'a pas de texte officiel

Le découpage en cycles de révision et le tableau de sens normal des comptes sont l'usage de la profession, pas un texte. Ils sont décrits dans [cycles-et-sens.md](cycles-et-sens.md) pour que chaque cabinet puisse les adapter.
