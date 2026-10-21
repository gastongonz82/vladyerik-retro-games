#!/usr/bin/env python3
"""Genera un índice de juegos sin descargar ni alterar ROMs."""
import json
from pathlib import Path
from urllib.parse import quote

root = Path(__file__).resolve().parents[1]
roms = root / "roms"
systems = {"nes":"nes","fds":"nes","sfc":"snes","smc":"snes","fig":"snes",
"md":"segaMD","gen":"segaMD","smd":"segaMD","gb":"gb","gbc":"gbc",
"gba":"gba","sms":"segaMS","gg":"segaGG","z64":"n64","n64":"n64","v64":"n64"}
allowed = set(systems) | {"zip","bin","rom"}
games = []
for path in sorted(roms.iterdir(),key=lambda p:p.name.casefold()):
    if not path.is_file() or path.suffix.lower().lstrip(".") not in allowed:
        continue
    extension = path.suffix.lower().lstrip(".")
    games.append({"name":path.name,"path":"roms/"+quote(path.name,safe=""),
                  "system":systems.get(extension),"size":path.stat().st_size})
(root/"juegos.json").write_text(json.dumps({"version":1,"games":games},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Catálogo generado: {len(games)} juegos")
