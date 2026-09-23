#!/usr/bin/env python3
"""
make-og.py — fabrique la carte de partage de la vitrine.

Partagé sur LinkedIn, le site ne montrait rien : ni titre, ni résumé, ni
vignette. Les blogs ont une carte générée par Hugo à chaque construction ;
ici il n'y a pas de générateur, donc l'image est produite une fois, à la
main, et versionnée.

**Ce script ne tourne pas dans le workflow**, pour la même raison que la
génération d'illustrations sur les blogs : le rendu d'une police n'est pas
garanti identique d'une version de Pillow à l'autre, et deux constructions
du même commit donneraient deux fichiers différents. À la main, regardé,
commité.

La palette et les textes sont lus dans public/index.html — il n'y a pas de
fichier de configuration sur ce site, et recopier les valeurs ici les
ferait diverger au premier changement de teinte.

Usage : python3 tools/make-og.py
Dépendance : Pillow (pip install Pillow), uniquement pour ce script.
"""

import html
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow est nécessaire : pip install Pillow")

RACINE = Path(__file__).resolve().parent.parent
PAGE = RACINE / "public" / "index.html"
SORTIE = RACINE / "public" / "assets" / "og.jpg"
PORTRAIT = RACINE / "public" / "assets" / "img-f255a1d274.jpg"
POLICES = Path(__file__).resolve().parent / "fonts"

L, H = 1200, 630
COLONNE = 430              # largeur de la bande portrait, à droite
MARGE = 64


def variable(nom: str, defaut: str) -> str:
    m = re.search(rf"--{nom}:\s*(#[0-9a-fA-F]{{3,8}})", PAGE.read_text(encoding="utf-8"))
    return m.group(1) if m else defaut


def texte(motif: str) -> str:
    m = re.search(motif, PAGE.read_text(encoding="utf-8"), re.S)
    if not m:
        sys.exit(f"Introuvable dans {PAGE.name} : {motif}")
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).split())


def couper(dessin, phrase: str, police, largeur: int) -> list[str]:
    lignes, courante = [], ""
    for mot in phrase.split():
        essai = f"{courante} {mot}".strip()
        if dessin.textlength(essai, font=police) <= largeur or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def main() -> None:
    fond = variable("noir", "#0e0e10")
    accent = variable("violet-accent", "#7c3aed")
    blanc = variable("blanc", "#f8f6ff")
    gris = variable("gris-texte", "#9b93b0")

    titre = texte(r"<h1[^>]*>(.*?)</h1>")
    role = texte(r"<title>(.*?)</title>").split("—")[-1].split("|")[-1].strip()

    img = Image.new("RGB", (L, H), fond)
    d = ImageDraw.Draw(img)

    # Portrait à droite, recadré pour remplir la bande.
    if PORTRAIT.exists():
        p = Image.open(PORTRAIT).convert("RGB")
        ech = max(COLONNE / p.width, H / p.height)
        p = p.resize((round(p.width * ech), round(p.height * ech)), Image.LANCZOS)
        # Cadrage haut, comme object-position: center 8% sur le site.
        gauche = (p.width - COLONNE) // 2
        haut = round(p.height * 0.08)
        haut = min(haut, p.height - H)
        img.paste(p.crop((gauche, haut, gauche + COLONNE, haut + H)), (L - COLONNE, 0))

        # Dégradé du fond vers le portrait : pas de bord net.
        fondu = Image.new("L", (160, 1))
        for x in range(160):
            fondu.putpixel((x, 0), int(255 * (1 - x / 159)))
        masque = fondu.resize((160, H))
        img.paste(Image.new("RGB", (160, H), fond), (L - COLONNE - 80, 0), masque)

    largeur_texte = L - COLONNE - MARGE - 40

    sur = ImageFont.truetype(str(POLICES / "raleway.ttf"), 22)
    gros = ImageFont.truetype(str(POLICES / "dmserif.ttf"), 58)
    nom = ImageFont.truetype(str(POLICES / "raleway.ttf"), 26)

    y = 150
    d.text((MARGE, y), role.upper(), font=sur, fill=accent)
    y += 56

    lignes = couper(d, titre, gros, largeur_texte)
    for ligne in lignes:
        d.text((MARGE, y), ligne, font=gros, fill=blanc)
        y += 72

    y += 18
    d.rectangle([MARGE, y, MARGE + 72, y + 3], fill=accent)
    y += 34
    d.text((MARGE, y), "François Fournier", font=nom, fill=gris)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    # JPEG et non PNG : l'image est à 60 % une photographie, où le PNG
    # pèse cinq fois plus pour un résultat que personne ne distingue.
    img.save(SORTIE, "JPEG", quality=86, optimize=True, progressive=True)
    print(f"{SORTIE.relative_to(RACINE)} — {L}×{H}, fond {fond}, accent {accent}, "
          f"{SORTIE.stat().st_size // 1024} Ko")
    print(f"  titre : {titre}")
    print(f"  rôle  : {role}")


if __name__ == "__main__":
    main()
