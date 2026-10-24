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
# Preserve every existing real cover; only placeholder entries may be replaced.
original_real_covers={key:value for key,value in manifest.items() if not value.endswith('.svg')}
systems={'nes':'Nintendo - Nintendo Entertainment System','snes':'Nintendo - Super Nintendo Entertainment System','segaMD':'Sega - Mega Drive - Genesis','segaGG':'Sega - Game Gear','n64':'Nintendo - Nintendo 64','arcade':'MAME'}
arcade_names={'dkong':['Donkey Kong (US set 1)','Donkey Kong'],'1942':['1942 (Revision B)','1942'],'1941j':['1941 - Counter Attack (Japan)','1941 - Counter Attack'],'1944j':['1944 - The Loop Master (Japan 000620)','1944 - The Loop Master'],'pacman':['Pac-Man (Midway)','Pac-Man'],'galaga':['Galaga (Namco rev. B)','Galaga'],'frogger':['Frogger (Sega set 1)','Frogger'],'sf2':['Street Fighter II - The World Warrior (World 910522)','Street Fighter II - The World Warrior'],'mslug':['Metal Slug - Super Vehicle-001','Metal Slug'],'mslug2':['Metal Slug 2 - Super Vehicle-001_II','Metal Slug 2'],'mslug3':['Metal Slug 3 (NGM-2560)','Metal Slug 3'],'simpsons2p2':['The Simpsons (2 Players World)','The Simpsons'],'dino':['Cadillacs and Dinosaurs (World 930201)','Cadillacs and Dinosaurs'],'goldnaxe':['Golden Axe (Version 1)','Golden Axe']}
# Exact Libretro names for additional arcade sets already supported by Retro Arcade.
arcade_names.update({
 '1942b':['1942 (Revision B)','1942'],
 'arkanoid':['Arkanoid (World)','Arkanoid'],
 'asterixeac':['Asterix (ver EAD)','Asterix'],
 'bublbob2':['Bubble Symphony (Ver 2.5O 1994_10_05)','Bubble Symphony'],
 'cadash':['Cadash (World)','Cadash'],
 'captavenu':['Captain America and The Avengers (US Rev 1.9)','Captain America and The Avengers'],
 'captcommb':['Captain Commando (World 911202)','Captain Commando'],
 'contra':['Contra (US, set 1)','Contra'],
 'ddragon2':['Double Dragon II - The Revenge (World)','Double Dragon II - The Revenge'],
 'ddragon3j':['Double Dragon 3 - The Rosetta Stone (Japan)','Double Dragon 3 - The Rosetta Stone'],
 'ddsom':['Dungeons & Dragons - Shadow over Mystara (Euro 960619)','Dungeons & Dragons - Shadow over Mystara'],
 'fatfursp':['Fatal Fury Special (NGM-058 ~ NGH-058)','Fatal Fury Special'],
 'ffightub':['Final Fight (USA, set 2)','Final Fight (World, set 1)','Final Fight'],
 'ga2':['Golden Axe_ The Revenge of Death Adder (World)','Golden Axe_ The Revenge of Death Adder'],
 'gngt':["Ghosts'n Goblins (US)","Ghosts'n Goblins (World)"],
 'knights':['Knights of the Round (World 911127)','Knights of the Round'],
 'kodr1':['The King of Dragons (World 910711)','The King of Dragons'],
 'mk':['Mortal Kombat (rev 5.0 T-Unit 03_19_93)','Mortal Kombat'],
 'mk2':['Mortal Kombat II (rev L3.1)','Mortal Kombat II'],
 'mk3':['Mortal Kombat 3 (rev 2.1)','Mortal Kombat 3'],
 'mk4':['Mortal Kombat 4 (version 3.0)','Mortal Kombat 4'],
 'msh':['Marvel Super Heroes (Euro 951024)','Marvel Super Heroes'],
 'mshvsf':['Marvel Super Heroes Vs. Street Fighter (USA 970827)','Marvel Super Heroes Vs. Street Fighter'],
 'mvscu':['Marvel Vs. Capcom_ Clash of Super Heroes (USA 980123)','Marvel Vs. Capcom_ Clash of Super Heroes'],
 'nbajam':['NBA Jam (rev 3.01 4_07_93)','NBA Jam'],
 'outrun':['Out Run (sitdown_upright, Rev B)','Out Run'],
 'pang':['Pang (World)','Pang'],
 'pbobblen':['Puzzle Bobble (Neo-Geo)','Puzzle Bobble / Bust-A-Move'],
 'punisher':['The Punisher (World 930422)','The Punisher'],
 'robocop2u':['Robocop 2 (US)','Robocop 2'],
 'sfa3':['Street Fighter Alpha 3 (USA 980904)','Street Fighter Alpha 3'],
 'sfiii3':['Street Fighter III 3rd Strike - Fight for the Future (USA 990608)','Street Fighter III 3rd Strike'],
 'simpsons2p2':['The Simpsons (2 Players World)','The Simpsons'],
 'snowbros':['Snow Bros. - Nick _ Tom (set 1)','Snow Bros. - Nick _ Tom'],
 'tmnt2pj':['Teenage Mutant Ninja Turtles - Turtles in Time (4 Players ver UAA)','Teenage Mutant Ninja Turtles - Turtles in Time'],
 'toki':['Toki (World, set 1)','Toki (World)','Toki'],
 'wof':['Warriors of Fate (World 921031)','Warriors of Fate'],
 'wwfmania':['WWF WrestleMania_ The Arcade Game (rev 1.30 08_10_95)','WWF WrestMania'],
})
session=requests.Session()
session.headers['User-Agent']='VLADYERIK-Cover-Mirror/1.0'
# Replace generated placeholder cards with actual game art whenever available.
# Index the real thumbnail directories to resolve different ROM naming conventions.
from html.parser import HTMLParser
from difflib import SequenceMatcher
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   href=dict(attrs).get('href','')
   if href.lower().endswith('.png'):self.links.append(unquote(href).split('/')[-1][:-4])
def normalize(name):
 name=unquote(name).lower().replace('_',' ').replace('’',"'")
 name=re.sub(r'\([^)]*\)|\[[^]]*\]',' ',name)
 name=re.sub(r'[^a-z0-9]+',' ',name)
 return ' '.join(name.split())
def get_index(system,kind):
 url='https://thumbnails.libretro.com/'+quote(systems[system],safe='')+'/'+kind+'/'
 try:
  response=session.get(url,timeout=25)
  response.raise_for_status()
  parser=Links();parser.feed(response.text)
  return parser.links
 except requests.RequestException:return []
saved=0
indexes={}
for game in catalog:
 path=game.get('path','')
 system=game.get('system','')
 if not path.startswith('roms/') or system not in systems or (path in manifest and not manifest[path].endswith('.svg')):continue
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
 # Search the published directory for a genuine box, title screen or screenshot.
 # Avoid unrelated matches: require a high title similarity.
 for kind in ('Named_Boxarts','Named_Titles','Named_Snaps'):
  key=(system,kind)
  if key not in indexes:indexes[key]=get_index(system,kind)
  expected=[normalize(n) for n in names if n]
  matches=[]
  for entry in indexes[key]:
   actual=normalize(entry)
   if not actual:continue
   score=max((SequenceMatcher(None,e,actual).ratio() for e in expected),default=0)
   if any(e==actual for e in expected):score=1.0
   if score>=0.83:matches.append((score,entry))
  matches.sort(reverse=True)
  for _,entry in matches[:3]:
   url='https://thumbnails.libretro.com/'+quote(systems[system],safe='')+'/'+kind+'/'+quote(entry.replace('&','_').replace('/','_'),safe='')+'.png'
   if url not in candidates:candidates.append(url)
 for url in candidates[:18]+candidates[18:27]:
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
manifest.update(original_real_covers)
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('New covers:',saved,'Total hosted:',len(manifest))
