#!/usr/bin/env python3
"""Vérifie que le site construit tient sous sa propre CSP.

Une CSP stricte a ceci de traître qu'elle ne casse rien à la construction :
elle casse dans le navigateur du lecteur, en silence, et seulement la
fonctionnalité concernée. Un script en ligne ajouté six mois plus tard ne
s'exécutera simplement pas.

Ce contrôle lit la CSP réellement déployée — celle du .htaccess, pas une
copie — et refuse ce qu'elle refuserait :

  script-src 'self'   → aucun <script> en ligne, aucun gestionnaire onclick=
  default-src 'self'  → aucune origine tierce dans src= ou href= de ressource

style-src porte 'unsafe-inline' à dessein (mermaid écrit dans le SVG qu'il
génère) : les styles en ligne ne sont donc pas signalés.

Usage : python3 tools/check-csp.py site/public [site/static/.htaccess]
"""
import re
import sys
from pathlib import Path

RACINE = Path(sys.argv[1] if len(sys.argv) > 1 else "site/public")
HTACCESS = Path(sys.argv[2] if len(sys.argv) > 2 else "site/static/.htaccess")

# Balises qui déclenchent une requête : une origine tierce y est refusée.
# href d'un <a> n'en déclenche aucune — les liens sortants sont légitimes.
RESSOURCE = re.compile(
    r"<(?:script|img|iframe|audio|video|source|embed|object)\b[^>]*?"
    r"\bsrc=[\"']?(https?://[^\"'\s>]+)", re.I)
FEUILLE = re.compile(
    r"<link\b[^>]*?\brel=[\"']?stylesheet[\"']?[^>]*?"
    r"\bhref=[\"']?(https?://[^\"'\s>]+)", re.I)
# Un <script> sans src ET porteur d'un type JavaScript. Les blocs de
# données — JSON-LD en particulier — sont aussi des <script>, mais le
# navigateur ne les exécute pas et la CSP ne les bloque pas : les
# signaler aurait fait échouer le contrôle sur chaque page du site.
JS = r"(?:text/javascript|application/javascript|module|text/ecmascript)"
INLINE = re.compile(
    rf"<script(?![^>]*\bsrc=)(?![^>]*\btype=(?![\"']?{JS}))[^>]*>"
    r"(?!\s*</script>)", re.I)
# Tout attribut on…= à l'intérieur d'une balise. Une liste nommée avait
# été essayée d'abord : elle laissait passer onmouseout, présent sur le
# site. Il y a plus de quatre-vingts évènements DOM — les énumérer, c'est
# se tromper. Le motif exige d'être dans une balise, pour ne pas
# confondre avec du texte.
HANDLER = re.compile(r"<[a-z][^>]*?\son[a-z]{2,}\s*=", re.I)


def csp_deployee() -> str:
    m = re.search(r'Content-Security-Policy\s+"(.+?)"',
                  HTACCESS.read_text(encoding="utf-8"))
    if not m:
        sys.exit(f"{HTACCESS} ne déclare aucune Content-Security-Policy.")
    return m.group(1)


def hotes_autorises(csp: str) -> set[str]:
    """Les origines explicitement listées dans la CSP, s'il y en a."""
    return set(re.findall(r"https://[a-z0-9.-]+", csp))


def main() -> None:
    csp = csp_deployee()
    if "script-src 'self'" not in csp:
        sys.exit("check-csp attend script-src 'self' — la CSP a changé, "
                 "ce contrôle doit être relu avant d'être cru.")

    autorises = hotes_autorises(csp)
    pages = sorted(RACINE.rglob("*.html"))
    if not pages:
        sys.exit(f"Aucune page sous {RACINE} — le site est-il construit ?")

    fautes = []
    for page in pages:
        html = page.read_text(encoding="utf-8", errors="ignore")
        rel = page.relative_to(RACINE)

        if INLINE.search(html):
            fautes.append(f"{rel} : <script> en ligne — script-src 'self' "
                          f"l'empêchera de s'exécuter, sans rien signaler")
        if HANDLER.search(html):
            fautes.append(f"{rel} : gestionnaire d'évènement en attribut "
                          f"(onclick=…) — refusé par script-src 'self'")
        for url in RESSOURCE.findall(html) + FEUILLE.findall(html):
            hote = re.match(r"https?://[^/]+", url).group(0)
            if hote not in autorises:
                fautes.append(f"{rel} : ressource tierce {hote} — refusée "
                              f"par default-src 'self'")

    for f in sorted(set(fautes)):
        print(f"  {f}", file=sys.stderr)
    if fautes:
        print(f"\n{len(set(fautes))} élément(s) que la CSP déployée refuserait.",
              file=sys.stderr)
        sys.exit(1)

    print(f"Rien que la CSP refuserait — {len(pages)} pages vérifiées.")
    print(f"CSP lue dans {HTACCESS}.")


if __name__ == "__main__":
    main()
