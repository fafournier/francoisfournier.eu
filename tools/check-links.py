#!/usr/bin/env python3
"""
check-links.py — vérifie que les liens internes du site construit aboutissent.

Un lien interne cassé ne se voit pas à la construction : Hugo ne relit pas ce
qui est écrit à la main dans le corps des articles. Un chemin hérité d'une
migration — /posts/ au lieu de /articles/ — passe donc la compilation et ne se
découvre qu'en ligne.

Ne regarde que les liens internes. Les liens sortants ne sont pas vérifiés :
ils dépendent de serveurs tiers, et un blog qui échoue parce qu'un site cité
est momentanément en panne serait un contrôle raté.

Usage : python3 tools/check-links.py site/public
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

HREF = re.compile(r'(?:href|src)=["\']?([^"\'>\s]+)', re.I)


def cibles(racine: Path) -> set[str]:
    """Chemins servis : /a/b/ pour a/b/index.html, /a/b.css pour un fichier."""
    out = set()
    for f in racine.rglob("*"):
        if not f.is_file():
            continue
        rel = "/" + f.relative_to(racine).as_posix()
        out.add(rel)
        if f.name == "index.html":
            out.add(rel[: -len("index.html")])
    return out


def main() -> None:
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else "site/public")
    if not racine.is_dir():
        print(f"{racine} introuvable — construire d'abord.", file=sys.stderr)
        sys.exit(2)

    servis = cibles(racine)
    base = None
    idx = racine / "index.html"
    if idx.exists():
        m = re.search(r'<link rel=["\']?canonical["\']? href=["\']?([^"\'>\s]+)', idx.read_text(encoding="utf-8"))
        if m:
            base = urlparse(m.group(1)).netloc

    casses: list[tuple[str, str]] = []
    pages = 0
    for f in sorted(racine.rglob("*.html")):
        pages += 1
        page = "/" + f.relative_to(racine).as_posix()
        for lien in HREF.findall(f.read_text(encoding="utf-8")):
            u = urlparse(lien)
            if u.scheme in ("mailto", "tel", "data", "javascript"):
                continue
            if u.netloc and u.netloc != base:
                continue                      # lien sortant : non vérifié
            chemin = unquote(u.path)
            if not chemin or chemin.startswith("#"):
                continue
            if not chemin.startswith("/"):    # relatif à la page courante
                chemin = str(Path(page).parent / chemin)
            if chemin not in servis and chemin.rstrip("/") + "/" not in servis:
                casses.append((page, lien))

    for page, lien in casses:
        print(f"  {page} → {lien}", file=sys.stderr)
    if casses:
        print(f"\n{len(casses)} lien(s) interne(s) cassé(s) sur {pages} pages.", file=sys.stderr)
        sys.exit(1)
    print(f"Aucun lien interne cassé — {pages} pages vérifiées.")


if __name__ == "__main__":
    main()
