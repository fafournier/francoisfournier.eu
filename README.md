# francoisfournier.eu

Personal site — English. French version:
[francoisfournier.fr](https://github.com/fafournier/francoisfournier.fr).

Counterpart to the three blogs. They build the authority; this is what they
point at.

⚠️ **La traduction n'est pas terminée — et c'est un défaut, pas un choix.** Le
corps des pages est traduit, mais la relecture n'a jamais été faite et des
phrases françaises subsistent. Le `<title>` de `/career/` lit encore « Parcours —
François Fournier ». Une relecture complète est due.

## Structure

```
public/                 ce qui part en ligne, tel quel
├── index.html          /
├── career/index.html   /career/
├── legal/index.html    /legal/
├── assets/             images extraites + fonts.css
├── fonts/              Raleway & DM Serif Display (SIL OFL 1.1)
├── robots.txt
├── sitemap.xml
└── .htaccess           redirections 301 depuis les anciennes URL, cache
```

**Aucune étape de construction.** Trois pages écrites à la main : un générateur
ne supprimerait pas le travail de traduction, seulement la duplication de
l'ossature — et elle est déjà écrite. Le coût réel serait de ne plus pouvoir
ouvrir une page et la modifier.

### Les URL propres viennent de l'arborescence

`/career/` est un dossier contenant `index.html`. Pas de réécriture Apache, donc
rien qui casse le jour où sa configuration change.

C'est la correction d'un défaut réel : les pages pointaient déjà vers `/career/`
et `/legal/` alors que les fichiers s'appelaient `career.html` et `legal.html`,
avec un `.htaccess` sans aucune règle. Toute la navigation était en 404 — et avec
elle le lien « Mentions légales » que portent les trois blogs.

## Deux langues, deux domaines

`francoisfournier.fr` en français, `francoisfournier.eu` en anglais. Un dépôt
chacun, même structure, mêmes chemins.

C'est ce qui rend les liens corrects sans les toucher : `/career/` mène à la page
anglaise sur le `.eu` et à la française sur le `.fr`. Les deux versions
cohabitaient auparavant dans un même dossier avec des suffixes `_en`, et les
pages anglaises pointaient vers les URL françaises.

Chaque page porte un `canonical` et trois `hreflang` — sa langue, l'autre, et
`x-default` sur le français. Sans quoi Google traite deux traductions comme du
contenu dupliqué.

## Aucune ressource tierce

```bash
python3 tools/check-third-party.py public
```

Les pages chargeaient Google Fonts. Sur un site qui vend du conseil technique,
c'est l'IP du visiteur transmise hors UE sans consentement, sur les pages
commerciales. Les polices sont désormais servies localement — les mêmes fichiers
que les trois blogs, une seule provenance pour tout le dispositif.

## Liens internes

```bash
python3 tools/check-links.py public
```

Ne vérifie que les liens internes : un déploiement qui échoue parce qu'un site
cité est momentanément en panne serait un contrôle raté.

## Déployer

`.github/workflows/deploy.yml` part à chaque push touchant `public/`.

| Nom | Où | Valeur |
|-----|-----|--------|
| `DEPLOY_FTP_HOST` | **Variables** | le nom du serveur o2switch, celui que couvre son certificat |
| `DEPLOY_FTP_PATH` | **Variables** | `/` si le compte FTP est verrouillé sur le dossier du site |
| `DEPLOY_FTP_USER` | Secrets | identifiant du compte FTP |
| `DEPLOY_FTP_PASSWORD` | Secrets | son mot de passe — **sans virgule** |

Hôte et chemin vont dans Variables : ce ne sont pas des identifiants, et un
`DEPLOY_FTP_PATH` valant `/` masqué par GitHub rend chaque log illisible.

FTPS et non SSH parce qu'o2switch bloque le port 22 sauf pour des IP déclarées à
l'avance, et que les runners GitHub n'en ont pas de fixe. Voir le README du Signal
pour le détail.

Essai à blanc : Actions → Déploiement → Run workflow → « Simuler ». La simulation
se connecte, vérifie le certificat et la cible, et annonce ce qu'elle
transférerait et supprimerait, sans rien écrire.

## Poids

Les images étaient encodées en base64 dans le HTML — 95 % du poids de l'accueil.
Extraites en fichiers, le HTML passe de 1 Mo à 78 Ko et les images se mettent en
cache séparément.
