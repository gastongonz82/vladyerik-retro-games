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
# MAME/FBNeo arcade set identifiers. Extend this map as new games are added.
arcade_names = {
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
    if not path.is_file() or path.suffix.lower().lstrip(".") not in allowed or path.name.lower() in {"readme.md"}:
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
