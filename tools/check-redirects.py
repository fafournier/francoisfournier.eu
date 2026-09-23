#!/usr/bin/env python3
"""Refuse une redirection .htaccess qui boucle sur elle-même.

Le défaut rencontré, en ligne, sur francoisfournier.fr :

    Redirect 301 /index.html https://francoisfournier.fr/

Apache associe « / » à index.html — DirectoryIndex — avant que mod_alias
intervienne. La redirection se déclenchait donc sur la page d'accueil
elle-même et renvoyait vers « / » : 301 en boucle, accueil inaccessible.
Le site jumeau y échappait par hasard, son ancien fichier s'appelant
index_en.html, que DirectoryIndex ne désigne jamais.

Rien dans la construction ne pouvait le voir : le HTML était correct, les
liens internes valides. Seul le serveur bouclait.

La parade est de conditionner la règle à la requête réellement reçue :

    RewriteCond %{THE_REQUEST} \\s/index\\.html[\\s?] [NC]
    RewriteRule ^index\\.html$ https://exemple.fr/ [R=301,L]

%{THE_REQUEST} est la première ligne de la requête HTTP telle qu'elle est
arrivée : la règle ne part donc que si le navigateur a demandé /index.html,
jamais sur l'association interne.

Usage : python3 tools/check-redirects.py public/.htaccess
"""

import re
import sys
from pathlib import Path

# Ce que DirectoryIndex désigne par défaut chez la plupart des hébergeurs.
# Une redirection Redirect dont la source est l'un de ces noms boucle.
INDEX = ("index.html", "index.htm", "index.php")

REDIRECT = re.compile(
    r"^\s*Redirect(?:Match|Permanent|Temp)?\s+(?:\d{3}\s+)?(\S+)\s+(\S+)",
    re.I | re.M)


def main() -> None:
    chemins = [Path(a) for a in sys.argv[1:]] or [Path("public/.htaccess")]
    fautes = []
    verifies = 0

    for chemin in chemins:
        if not chemin.exists():
            sys.exit(f"{chemin} : introuvable.")
        verifies += 1
        for source, cible in REDIRECT.findall(chemin.read_text(encoding="utf-8")):
            nom = source.rstrip("/").rsplit("/", 1)[-1].lower()
            if nom in INDEX:
                fautes.append(
                    f"{chemin} : « Redirect {source} {cible} » boucle.\n"
                    f"      Apache associe le dossier à {nom} avant mod_alias : la\n"
                    f"      règle se déclenche sur la page elle-même. Conditionner\n"
                    f"      à %{{THE_REQUEST}} avec RewriteCond — voir l'en-tête de\n"
                    f"      ce script.")

    for f in fautes:
        print(f"  {f}", file=sys.stderr)
    if fautes:
        print(f"\n{len(fautes)} redirection(s) qui boucleraient.", file=sys.stderr)
        sys.exit(1)

    print(f"Aucune redirection en boucle — {verifies} fichier(s) vérifié(s).")


if __name__ == "__main__":
    main()
