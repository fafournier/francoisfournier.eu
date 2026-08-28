# francoisfournier.eu

Site vitrine de François Fournier, **version anglaise**. Trois pages, pas de générateur.

## Ce qui part en ligne

`public/` est déployé tel quel. Tout ce qui s'y trouve sera public ; rien
d'autre ne l'est.

| Chemin | URL |
|--------|-----|
| `public/index.html` | `/` |
| `public/career/index.html` | `/career/` |
| `public/legal/index.html` | `/legal/` |

**Les URL propres viennent de l'arborescence, jamais d'une réécriture.** Une
nouvelle page se crée en `public/<nom>/index.html`. Ne pas créer `<nom>.html` à
la racine : c'est exactement le défaut qui rendait toute la navigation morte
avant la reprise.

## Règles à ne pas enfreindre

**Aucune ressource tierce.** Pas de Google Fonts, pas de CDN, pas de script
externe, pas d'image distante. Les polices sont dans `public/fonts/`, déclarées
par `public/assets/fonts.css`. Ce site vend du conseil technique : une IP de
visiteur transmise hors UE sans consentement y est un défaut RGPD gratuit.
`tools/check-third-party.py` fait échouer le déploiement le cas échéant.

**Pas d'image en base64 dans le HTML.** Les images vivent dans
`public/assets/`, nommées `img-<empreinte>.<ext>`. L'inline coûte 33 % de
surpoids et interdit la mise en cache — c'était 95 % du poids de l'accueil.

**Les deux domaines restent alignés.** Toute modification structurelle
(navigation, `<head>`, pied de page) se fait dans les deux dépôts. Les chemins
sont identiques de part et d'autre : `/career/` existe dans les deux langues.

**Chaque page porte son `canonical` et ses trois `hreflang`** — sa langue,
l'autre, et `x-default` vers le français. Sans quoi Google lit deux traductions
comme du contenu dupliqué.

## Avant de pousser

```bash
python3 tools/check-third-party.py public
python3 tools/check-links.py public
```

Les deux tournent aussi dans le workflow. `check-links.py` ne vérifie que les
liens internes : les liens sortants dépendent de serveurs tiers, et un
déploiement qui échoue parce qu'un site cité est en panne serait un contrôle
raté.

## Déploiement

Push sur `main` touchant `public/` → GitHub Actions → FTPS vers o2switch.
Détail des secrets dans `README.md`.

FTPS et non SSH : o2switch bloque le port 22 sauf pour des IP déclarées à
l'avance, et les runners GitHub n'ont pas d'IP sortante fixe.

## Le reste du dispositif

Ce site est la destination ; les blogs sont ce qui y amène.

| Dépôt | Rôle |
|-------|------|
| `leSignalBlogFr` | blog professionnel — décisions techniques, dette, IA. **Source de vérité des layouts et outils partagés.** |
| `pragmatiqueBlogFr` | blog technique et pédagogique, public étudiant |
| `theSignalBlogEn` | version anglaise du Signal |
| `francoisfournier.fr` / `.eu` | vitrine, fr / en |

`check-links.py` et `check-third-party.py` viennent de `leSignalBlogFr/tools/`.
Les corriger là-bas d'abord, puis les recopier.

## État connu

La relecture de l'anglais a été faite. Trois éléments restent **volontairement**
en français, et ne sont pas des oublis :

- `Mentions légales (FR)` en pied de page — c'est le libellé d'un lien vers le
  site français, il doit rester dans la langue de sa destination ;
- les titres de conférences réellement données en français (`Les outils du
  Manager`, `Votre monde`) — traduire le titre d'une intervention la
  travestirait ; seul son cadre est en anglais ;
- `Lycée de Presles`, glosé `(secondary school)`.

Deux points ouverts, non traités car ils ne relèvent pas de la traduction :

- les pages annoncent « Twenty years » alors que le blog anglais a été passé à
  25 ans. La page française dit « vingt ans » : corriger une seule des deux
  créerait une divergence. À trancher pour les deux à la fois.
L'adresse de contact est `fr@ncois.francoisfournier.fr`, la même sur les cinq
sites. Le domaine porte un catch-all, donc les variantes que les lecteurs
recopieront de mémoire arrivent aussi. **Ne pas la « corriger » : le @ interne
est voulu, et la partie locale est bien `fr`.**
