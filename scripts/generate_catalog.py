#!/usr/bin/env python3
"""Genera un índice de juegos sin descargar ni alterar ROMs."""
import json
import zipfile
from pathlib import Path
from urllib.parse import quote

root = Path(__file__).resolve().parents[1]
roms = root / "roms"
systems = {"nes":"nes","fds":"nes","sfc":"snes","smc":"snes","fig":"snes",
"md":"segaMD","gen":"segaMD","smd":"segaMD","gb":"gb","gbc":"gbc",
"gba":"gba","sms":"segaMS","gg":"segaGG","z64":"n64","n64":"n64","v64":"n64"}
allowed = set(systems) | {"zip","bin","rom"}
excluded_roms = {"avspu.zip", "bloodbro.zip", "crusnusa.zip", "mk4.zip", "39in1.zip", "calspeed.zip", "sfiii3.zip"}
# MAME/FBNeo arcade set identifiers. Extend this map as new games are added.
arcade_names = {
    "1942": "1942 (1984)",
    "1942b": "1942 (Bootleg)",
    "bombjack": "Bomb Jack (1984)",
    "cadash": "Cadash (1989)",
    "dkong": "Donkey Kong (1981)",
    "frogger": "Frogger (1981)",
    "kof98": "The King of Fighters '98 (1998)",
    "mslug3": "Metal Slug 3 (2000)",
    "pang": "Pang (1989)",
    "pbobblen": "Puzzle Bobble (1994)",
    "rastan": "Rastan (1987)",
    "1941j": "1941: Counter Attack (1990)",
    "1944j": "1944: The Loop Master (2000)",
    "ddsom": "Dungeons & Dragons: Shadow over Mystara (1996)",
    "gngt": "Ghosts ’n Goblins (1985)",
    "megaman2": "Mega Man 2: The Power Fighters (1996)",
    "mwalk": "Michael Jackson’s Moonwalker (1990)",
    "toki": "Toki (1989)",
    "39in1": "39-in-1 Arcade Multigame",
    "arkanoid": "Arkanoid (1986)",
    "astdelux": "Asteroids Deluxe (1980)",
    "asterixeac": "Asterix (1992)",
    "bublbob2": "Bubble Symphony (1994)",
    "calspeed": "California Speed (1998)",
    "captavenu": "Captain America and The Avengers (1991)",
    "captcommb": "Captain Commando (1991)",
    "contra": "Contra Arcade (1987)",
    "ddragon3j": "Double Dragon 3: The Rosetta Stone (1990)",
    "fatfursp": "Fatal Fury Special (1993)",
    "galaga": "Galaga (1981)",
    "kodr1": "The King of Dragons (1991)",
    "mk4": "Mortal Kombat 4 (1997)",
    "mshvsf": "Marvel Super Heroes vs. Street Fighter (1997)",
    "nbajam": "NBA Jam (1993)",
    "pacman": "Pac-Man (1980)",
    "robocop2u": "RoboCop 2 (1991)",
    "sf2": "Street Fighter II: The World Warrior (1991)",
    "sfiii3": "Street Fighter III: 3rd Strike (1999)",
    "sfa3": "Street Fighter Alpha 3 (1998)",
    "tmnt2pj": "Teenage Mutant Ninja Turtles: Turtles in Time (1991)",
    "wwfmania": "WWF WrestleMania: The Arcade Game (1995)",

    "simpsons2p2": "The Simpsons Arcade (1991)",
    "dino": "Cadillacs and Dinosaurs (1993)",
    "punisher": "The Punisher (1993)",
    "avsp": "Alien vs. Predator (1994)",
    "captcomm": "Captain Commando (1991)",
    "ffight": "Final Fight (1989)",
    "knights": "Knights of the Round (1991)",
    "kod": "The King of Dragons (1991)",
    "wof": "Warriors of Fate (1992)",
    "ssriders": "Sunset Riders (1991)",
    "tmnt": "Teenage Mutant Ninja Turtles (1989)",
    "tmnt2": "Teenage Mutant Ninja Turtles: Turtles in Time (1991)",
    "xmen": "X-Men Arcade (1992)",
    "mslug": "Metal Slug (1996)",
    "mslug2": "Metal Slug 2 (1998)",
    "snowbros": "Snow Bros. (1990)",
    "bublbobl": "Bubble Bobble (1986)",
    "avspu": "Alien vs. Predator (1994)",
    "bloodbro": "Blood Bros. (1990)",
    "crusnusa": "Cruis'n USA Arcade (1994)",
    "ddragon2": "Double Dragon II: The Revenge (1988)",
    "ffightub": "Final Fight (1989)",
    "ga2": "Golden Axe: The Revenge of Death Adder (1992)",
    "goldnaxe": "Golden Axe Arcade (1989)",
    "mk": "Mortal Kombat Arcade (1992)",
    "mk2": "Mortal Kombat II Arcade (1993)",
    "mk3": "Mortal Kombat 3 Arcade (1995)",
    "umk3": "Ultimate Mortal Kombat 3 Arcade (1995)",
    "msh": "Marvel Super Heroes (1995)",
    "mvscu": "Marvel vs. Capcom: Clash of Super Heroes (1998)",
    "outrun": "Out Run (1986)",
    "ssridersubc": "Sunset Riders (1991)",
    "wboy": "Wonder Boy (1986)",
    "xmvsf": "X-Men vs. Street Fighter (1996)",
}
# Preserve manually curated names/systems across subsequent ROM uploads.
previous = {}
catalog_path = root / "juegos.json"
if catalog_path.exists():
    try:
        previous = {g["path"]: g for g in json.loads(catalog_path.read_text(encoding="utf-8")).get("games", [])}
    except (ValueError, KeyError, TypeError):
        previous = {}
games = []
for path in sorted(roms.iterdir(),key=lambda p:p.name.casefold()):
    if not path.is_file() or path.suffix.lower().lstrip(".") not in allowed or path.name.lower() in ({"readme.md"} | excluded_roms):
        continue
    extension = path.suffix.lower().lstrip(".")
    if extension == "zip":
        try:
            with zipfile.ZipFile(path) as archive:
                detected = {systems.get(Path(member.filename).suffix.lower().lstrip(".")) for member in archive.infolist() if not member.is_dir()}
                detected.discard(None)
                core = next(iter(detected)) if len(detected) == 1 else None
        except (zipfile.BadZipFile, OSError):
            core = None
    else:
        core = systems.get(extension)
    game_path = "roms/" + quote(path.name, safe="")
    old = previous.get(game_path, {})
    arcade_title = arcade_names.get(path.stem.lower()) if extension == "zip" else None
    if arcade_title:
        core = "arcade"
        name = arcade_title + ".zip"
    else:
        core = core or old.get("system")
        name = old.get("name", path.name)
    games.append({"name":name, "path":game_path,
                  "system":core, "size":path.stat().st_size})
(root/"juegos.json").write_text(json.dumps({"version":1,"games":games},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Catálogo generado: {len(games)} juegos")
