#!/usr/bin/env python3
"""
Vérifie qu'aucune **ressource** n'est chargée depuis un domaine tiers.

Ne regarde que ce que le navigateur va chercher tout seul : scripts, feuilles
de style, polices, images, iframes, et les url() du CSS. Les liens sortants
(`<a href>`) sont ignorés — citer une source par un lien est normal et ne
transmet aucune donnée tant que le lecteur ne clique pas.

C'est la distinction qui compte pour le RGPD : une police Google chargée par la
page envoie l'IP du visiteur sans qu'il ait rien demandé ; un lien vers
yoast.com n'envoie rien.

Usage : python3 tools/check-third-party.py site/public
Sortie : code 1 et liste des fautifs si une ressource tierce est trouvée.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Attributs qui déclenchent une requête automatique du navigateur.
RESOURCE_PATTERNS = [
    (re.compile(r'<script[^>]+src=["\']?([^"\'\s>]+)', re.I), "script"),
    (re.compile(r'<img[^>]+src=["\']?([^"\'\s>]+)', re.I), "img"),
    (re.compile(r'<iframe[^>]+src=["\']?([^"\'\s>]+)', re.I), "iframe"),
    (re.compile(r'<(?:video|audio|source)[^>]+src=["\']?([^"\'\s>]+)', re.I), "media"),
]

# <link> est ambigu : seuls certains rel déclenchent une requête. canonical,
# alternate et me sont des métadonnées — les compter donnerait un faux positif
# sur le propre domaine du site.
LINK_TAG = re.compile(r'<link\b[^>]*>', re.I)
LINK_REL = re.compile(r'\brel=["\']?([^"\'\s>]+)', re.I)
LINK_HREF = re.compile(r'\bhref=["\']?([^"\'\s>]+)', re.I)
REL_QUI_CHARGE = {"stylesheet", "preload", "icon", "shortcut", "apple-touch-icon",
                  "manifest", "prefetch", "preconnect", "dns-prefetch"}

CSS_URL = re.compile(r'url\(\s*["\']?([^"\')\s]+)', re.I)


def host_of(url: str) -> str | None:
    """Hôte d'une URL absolue. None pour tout ce qui reste local."""
    if url.startswith(("data:", "#", "/", "mailto:", "tel:")) or not url.strip():
        return None
    if url.startswith("//"):
        url = "https:" + url
    if not re.match(r"^[a-z][a-z0-9+.-]*://", url, re.I):
        return None            # chemin relatif
    return (urlparse(url).hostname or "").lower() or None


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "site/public")
    if not root.is_dir():
        sys.exit(f"répertoire introuvable : {root}")

    allowed = {h.lower() for h in sys.argv[2:]}
    fautifs: list[tuple[str, str, str, str]] = []

    for f in list(root.rglob("*.html")) + list(root.rglob("*.css")):
        texte = f.read_text(encoding="utf-8", errors="replace")
        trouves = []
        if f.suffix == ".html":
            for pattern, kind in RESOURCE_PATTERNS:
                trouves += [(u, kind) for u in pattern.findall(texte)]
            for balise in LINK_TAG.findall(texte):
                rel = LINK_REL.search(balise)
                href = LINK_HREF.search(balise)
                if not href:
                    continue
                rels = set((rel.group(1) if rel else "").lower().split())
                if rels & REL_QUI_CHARGE:
                    trouves.append((href.group(1), f"link {'/'.join(sorted(rels))}"))
        trouves += [(u, "css url()") for u in CSS_URL.findall(texte)]

        for url, kind in trouves:
            h = host_of(url)
            if h and h not in allowed:
                fautifs.append((str(f.relative_to(root)), kind, h, url[:70]))

    if fautifs:
        print(f"{len(fautifs)} ressource(s) tierce(s) chargée(s) :\n")
        for fichier, kind, hote, url in sorted(set(fautifs))[:20]:
            print(f"  {hote:32} {kind:9} {fichier}")
            print(f"  {'':32} {url}")
        print("\nLes polices et scripts doivent être servis localement.")
        sys.exit(1)

    n = len(list(root.rglob("*.html")))
    print(f"Aucune ressource tierce — {n} pages vérifiées.")
    print("(Les liens sortants dans le texte ne sont pas concernés : ils ne "
          "déclenchent aucune requête.)")


if __name__ == "__main__":
    main()
