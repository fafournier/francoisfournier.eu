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

**Des phrases françaises subsistent dans les pages anglaises. C'est un défaut à
corriger, pas un choix.** Le corps des pages est traduit, mais la relecture n'a
jamais été faite.

Connu à ce jour :

- le `<title>` de `/career/` lit encore « Parcours — François Fournier » ;
- le reste n'a pas été audité page par page.

Une relecture complète est due. En attendant, toute phrase française rencontrée
dans `public/` est un bug : la signaler, et la corriger si le contexte de la
tâche s'y prête.
