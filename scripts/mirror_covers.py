#!/usr/bin/env python3
"""Download verified Libretro cover art into the same GitHub Pages repo as the ROMs."""
import io, json, re, time
from pathlib import Path
from urllib.parse import quote, unquote
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'juegos.json').read_text(encoding='utf-8'))['games']
out=ROOT/'assets'/'retro-covers'
out.mkdir(parents=True,exist_ok=True)
manifest_path=ROOT/'retro-hosted-covers.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
systems={'nes':'Nintendo - Nintendo Entertainment System','snes':'Nintendo - Super Nintendo Entertainment System','segaMD':'Sega - Mega Drive - Genesis','segaGG':'Sega - Game Gear','n64':'Nintendo - Nintendo 64','arcade':'MAME'}
arcade_names={'dkong':['Donkey Kong (US set 1)','Donkey Kong'],'1942':['1942 (Revision B)','1942'],'1941j':['1941 - Counter Attack (Japan)','1941 - Counter Attack'],'1944j':['1944 - The Loop Master (Japan 000620)','1944 - The Loop Master'],'pacman':['Pac-Man (Midway)','Pac-Man'],'galaga':['Galaga (Namco rev. B)','Galaga'],'frogger':['Frogger (Sega set 1)','Frogger'],'sf2':['Street Fighter II - The World Warrior (World 910522)','Street Fighter II - The World Warrior'],'mslug':['Metal Slug - Super Vehicle-001','Metal Slug'],'mslug2':['Metal Slug 2 - Super Vehicle-001_II','Metal Slug 2'],'mslug3':['Metal Slug 3 (NGM-2560)','Metal Slug 3'],'simpsons2p2':['The Simpsons (2 Players World)','The Simpsons'],'dino':['Cadillacs and Dinosaurs (World 930201)','Cadillacs and Dinosaurs'],'goldnaxe':['Golden Axe (Version 1)','Golden Axe']}
session=requests.Session()
session.headers['User-Agent']='VLADYERIK-Cover-Mirror/1.0'
saved=0
for game in catalog:
 path=game.get('path','')
 system=game.get('system','')
 if not path.startswith('roms/') or system not in systems or path in manifest:continue
 rom=unquote(path.rsplit('/',1)[-1]).rsplit('.',1)[0]
 raw=game.get('name','').rsplit('.',1)[0]
 title=re.sub(r'\s*\([^)]*\)|\s*\[[^]]*\]','',raw).strip()
 names=arcade_names.get(rom.lower(),[title]) if system=='arcade' else [raw,title,title+' (USA)',title+' (Europe)',title+' (World)']
 if system=='arcade':names=list(dict.fromkeys(names+[title]))
 # Never guess unrelated cover art: only use exact-name candidate files.
 candidates=[]
 for typ in ('Named_Boxarts','Named_Titles','Named_Snaps'):
  for name in dict.fromkeys(n for n in names if n):
   safe=re.sub(r'[&*/:<>?|"\\]','_',name)
   candidates.append('https://thumbnails.libretro.com/'+quote(systems[system],safe='')+'/'+typ+'/'+quote(safe,safe='')+'.png')
 for url in candidates[:18]:
  try:
   response=session.get(url,timeout=7)
   if response.status_code!=200 or len(response.content)>8_000_000:continue
   image=Image.open(io.BytesIO(response.content))
   image.verify()
   image=Image.open(io.BytesIO(response.content)).convert('RGB')
   image.thumbnail((440,550),Image.Resampling.LANCZOS)
   target=out/(re.sub(r'[^a-z0-9_-]','_',rom.lower())+'-'+system+'.webp')
   image.save(target,'WEBP',quality=78,method=5)
   manifest[path]='assets/retro-covers/'+target.name
   saved+=1
   print('Saved',path,'->',target.name,flush=True)
   break
  except (requests.RequestException,OSError,ValueError):
   continue
 if saved and saved%25==0:
  manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('New covers:',saved,'Total hosted:',len(manifest))
