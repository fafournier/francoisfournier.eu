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
  connect-src         → la balise de mesure vise bien un hôte autorisé

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

# La mesure d'audience : le script est servi en first-party, mais la balise
# qu'il poste part vers data-host-url. C'est connect-src qui l'autorise.
MESURE = re.compile(r"\bdata-website-id=", re.I)
BALISE = re.compile(r"\bdata-host-url=[\"']?(https?://[^\"'\s>]+)", re.I)


def csp_deployee() -> str:
    m = re.search(r'Content-Security-Policy\s+"(.+?)"',
                  HTACCESS.read_text(encoding="utf-8"))
    if not m:
        sys.exit(f"{HTACCESS} ne déclare aucune Content-Security-Policy.")
    return m.group(1)


def directives(csp: str) -> dict[str, set[str]]:
    """La CSP découpée par directive.

    Lire la politique en bloc et y chercher des hôtes au hasard donnerait
    une réponse fausse dès qu'une directive en porte un : un hôte autorisé
    pour connect-src rendrait aussi acceptable un script venu de là. Ce
    sont deux permissions différentes, et les confondre reviendrait à
    ouvrir script-src par la bande.
    """
    table: dict[str, set[str]] = {}
    for morceau in csp.split(";"):
        parties = morceau.split()
        if parties:
            table[parties[0].lower()] = set(parties[1:])
    return table


def hotes(table: dict[str, set[str]], directive: str) -> set[str]:
    """Les origines qu'une directive autorise, repli sur default-src."""
    valeurs = table.get(directive) or table.get("default-src") or set()
    return {v.rstrip("/") for v in valeurs if v.startswith("http")}


def main() -> None:
    csp = csp_deployee()
    if "script-src 'self'" not in csp:
        sys.exit("check-csp attend script-src 'self' — la CSP a changé, "
                 "ce contrôle doit être relu avant d'être cru.")

    table = directives(csp)
    autorises = hotes(table, "script-src") | hotes(table, "img-src")
    balise_ok = hotes(table, "connect-src")
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

        # La balise de mesure ne part pas d'un attribut src : le navigateur
        # la poste en fetch(), donc c'est connect-src qui tranche, et son
        # refus est parfaitement silencieux — la page s'affiche, la mesure
        # n'existe plus. Rien d'autre ne rattraperait ce désaccord.
        for destination in BALISE.findall(html):
            hote = re.match(r"https?://[^/]+", destination).group(0)
            if hote not in balise_ok:
                fautes.append(
                    f"{rel} : la balise de mesure vise {hote}, que "
                    f"connect-src n'autorise pas. Le navigateur la "
                    f"refusera sans rien dire. Ajoutez l'hôte à "
                    f"connect-src dans {HTACCESS}, ou corrigez umamiHost.")
        if MESURE.search(html) and not BALISE.search(html):
            fautes.append(f"{rel} : balise de mesure sans data-host-url — "
                          f"elle serait postée vers ce site même")

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
