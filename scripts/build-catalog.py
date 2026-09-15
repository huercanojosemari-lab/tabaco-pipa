import concurrent.futures,html,io,json,re,time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus,urljoin,urlparse
from urllib.request import Request,urlopen
from PIL import Image
OUT=Path('data/catalogo-global.json');SOURCE_CATALOG=Path('data/catalogo.json');TABACOTECA_URL='https://www.fumeursdepipe.net/tabacotheque.php';MACBAREN_URL='https://mac-baren.com/mac-baren/';IMAGE_DIR=Path('assets/tins')
BRAND_PREFIXES=sorted(set(['4noggins','A&C Petersen','Altadis','Amphora','Arango','Ashton','Astleys','Balkan Sobranie','Barling','Bell’s','Bell\'s','Bentley','Besson','Bjarne','Breizh Tobacco','Brigham','Butera','Capstan','Chacom','Charles Fairmorn','Comoy\'s of London','Cornell & Diehl','Dan Pipe','Dan Tobacco','Daughters & Ryan','Davidoff','Drucquer & Sons','Dunhill','E. Hoffman Company','Edgeworth','Ente Tabacchi Italiani','Erik Stokkebye','Erinmore','Esoterica','Flandria','Fribourg & Treyer','Friedman & Pease','G. De Graaff & Sons','G.L. Pease','Gallaher','Gauntleys','Gawith & Hoggarth & Co','Gawith, Hoggarth & Co','Germain’s','Germain\'s','Gladora Tobacco','Half & Half','Hans Schürch','Hearth & Home','Hermit','Heupink & Bloemen','HU Tobacco','Ilsteds','Imperial Tobacco','J.B. Vinche','J.F. Germain & Son','James J. Fox','Jean-Paul Couvert','John Aylesbury','John Cotton','John Patton','John Sinclair','Joseph Martin','Kendal Tobacco','Kohlhase, Kopp und Co','L.J. Peretti and Co.','Lane Limited','Larsen','Low Country','Mac Baren','McClelland','McLintock','Mélange maison','Motzek','Murray & Sons','Murray’s','Murray\'s','New York Pipe Club','Newminster','Ogden’s of Liverpool','Ogden\'s of Liverpool','Olaf Poulsson','Orlik','Paul Olsen','Peter Stokkebye','Peterson','Pfeifen Huber','Pfeifen Schneider','Pfeifen-Studio Mühlhausen','Pfeifendepot','Pipesandcigars.com','Pipeworks & Wilke','Planta','Poschl Tabak','Poul Stanwell','Rattray’s','Rattray\'s','Reiner','Richmond','Robert Lewis','Robert McConnell','Samuel Gawith','Scandinavian Tobacco Group','Schneiderwind','Seattle Pipe Club','Smoker’s Haven','Smoker\'s Haven','Solani','St-Group Assens','Standard Tobacco Company of Pennsylvania','Sutliff Tobacco Company','Synjeco','Tabacos Wilder','Tabak Träber','Tabakhaus Falkum','TAK','Tambolaka Natural Tobaccos','Timm','Torben Dansk','Toscani','Tour du Monde des Anglais, en 80 blends','Tranter Havana House','Troost','V.B','Vauen','Villiger','Vincent Manil','Wessex','Windels','Ramback']),key=lambda x:(-len(x),x.casefold()))
def clean_text(v):return re.sub(r'\s+',' ',html.unescape(v or '')).strip(' \t\r\n-')
class H4Parser(HTMLParser):
 def __init__(self):super().__init__();self.in_h4=False;self.buf=[];self.items=[]
 def handle_starttag(self,t,a):
  if t.lower()=='h4':self.in_h4=True;self.buf=[]
 def handle_endtag(self,t):
  if t.lower()=='h4' and self.in_h4:
   x=clean_text(''.join(self.buf));
   if x:self.items.append(x)
   self.in_h4=False;self.buf=[]
 def handle_data(self,d):
  if self.in_h4:self.buf.append(d)
def fetch_url(url):return urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 PipatekaCatalog/8.4'}),timeout=45).read().decode('utf-8','ignore')
def slugify(v):return re.sub(r'[^a-z0-9]+','-',str(v).casefold()).strip('-') or 'blend'
def split_brand_name(t):
 for b in BRAND_PREFIXES:
  if t.casefold().startswith(b.casefold()+' '):return b,t[len(b):].strip()
  if t.casefold()==b.casefold():return b,''
 p=t.split(' ',1);return(p[0],p[1]) if len(p)==2 else(t,'')
CURRENT_MACBAREN_SLUGS=['black-ambrosia','cherry-ambrosia','golden-ambrosia','club-blend','dark-twist','golden-blend','harmony','latakia-blend','mixture','mixture-aromatic','mixture-modern','navy-flake','plumcake','roll-cake','stockton','the-solent','vanilla-loose-cut','vanilla-flake','vanilla-toffee','vanilla-roll-cake','virginia-flake','virginia-no-1','cube-gold','cube-silver','hh-bold-kentucky-flake','hh-burley-flake','hh-latakia-flake','hh-old-dark-fired-flake','hh-pure-virginia-flake','hh-vintage-latakia','hh-rustica-flake','hh-balkan-blend']
def official_mac_baren_products():
 links={s:f'https://mac-baren.com/product/{s}/' for s in CURRENT_MACBAREN_SLUGS}
 try:
  text=fetch_url(MACBAREN_URL)
  for m in re.finditer(r'(?:href|data-href)=[\"\'](https?://mac-baren\.com/product/[^\"\']+|/product/[^\"\']+)[\"\']',text,re.I):
   u=urljoin(MACBAREN_URL,html.unescape(m.group(1))).split('#')[0];s=u.rstrip('/').split('/product/')[-1]
   if s:links[s]=u
 except Exception as e:print('Warning official index:',e)
 print('Official Mac Baren product pages:',len(links));return links
def official_product_image(url):
 try:
  t=fetch_url(url);m=re.search(r'<meta[^>]+property=[\"\']og:image[\"\'][^>]+content=[\"\']([^\"\']+)',t,re.I) or re.search(r'<meta[^>]+content=[\"\']([^\"\']+)[\"\'][^>]+property=[\"\']og:image[\"\']',t,re.I);return urljoin(url,html.unescape(m.group(1))) if m else None
 except Exception:return None
def official_mac_baren_images():
 p=official_mac_baren_products();found={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  fs={pool.submit(official_product_image,u):s for s,u in p.items()}
  for f in concurrent.futures.as_completed(fs):
   im=f.result();
   if im:found[fs[f]]=im
 print('Official Mac Baren image candidates:',len(found));return found
ALIASES={'dark-twist':['Dark Twist Roll Cake','Dark Twist Loose Cut'],'mixture':['Mixture: Scottish Blend','Mixture Flake','Mixture Modern','Mixture Aromatic'],'mixture-aromatic':['Mixture Aromatic'],'mixture-modern':['Mixture Modern'],'navy-flake':['Navy Flake'],'plumcake':['Plumcake'],'roll-cake':['Roll Cake'],'stockton':['Stockton'],'the-solent':['Solent Mixture'],'vanilla-loose-cut':['Vanilla Cream Loose Cut','Vanilla Choice'],'vanilla-flake':['Vanilla Cream Flake'],'vanilla-toffee':['Classic Amber'],'vanilla-roll-cake':['Vanilla Roll Cake / Classic Roll Cake'],'virginia-flake':['Virginia Flake'],'virginia-no-1':['Virginia No. 1'],'cube-gold':['Cube Gold'],'cube-silver':['Cube Silver'],'hh-bold-kentucky-flake':['HH Bold Kentucky','HH Bold Kentucky Flake'],'hh-burley-flake':['HH Burley Flake'],'hh-latakia-flake':['HH Latakia Flake'],'hh-old-dark-fired-flake':['HH Old Dark Fired'],'hh-pure-virginia-flake':['HH Pure Virginia'],'hh-vintage-latakia':['HH Vintage Latakia'],'hh-rustica-flake':['HH Rustica'],'hh-balkan-blend':['HH Balkan Blend']}
def official_image_for_blend(blend,official):
 t=slugify(blend)
 for s,names in ALIASES.items():
  if any(slugify(n)==t for n in names) and s in official:return official[s]
 if t in official:return official[t]
 for s,u in official.items():
  ps=slugify(s)
  if ps.startswith(t+'-') or t.startswith(ps+'-'):return u
 return None
def find_image(brand,blend):
 q=quote_plus(f'"{brand}" "{blend}" pipe tobacco tin');u=f'https://www.bing.com/images/search?q={q}&form=HDRSC2&first=1';t=urlopen(Request(u,headers={'User-Agent':'Mozilla/5.0 PipatekaImages/8.4'}),timeout=25).read().decode('utf-8','ignore');cs=[]
 for p in [r'"m"\s*:\s*\{[^{}]*?"murl"\s*:\s*"([^"]+)"',r'"murl"\s*:\s*"([^"]+)"']:
  cs += [m.group(1).replace('\\/','/') for m in re.finditer(p,t)]
  if cs:break
 for x in cs[:12]:
  if not any(z in x.lower() for z in('logo','icon','avatar','.svg')) and urlparse(x).scheme in('http','https'):return x
 return None
def download_image(item):
 brand,blend,preferred=item;dest=IMAGE_DIR/f'{slugify(brand)}--{slugify(blend)}.jpg'
 if dest.exists() and dest.stat().st_size>3000:return brand,blend,f'assets/tins/{dest.name}','local-cache'
 try:
  source=preferred or find_image(brand,blend)
  if not source:return brand,blend,None,None
  raw=urlopen(Request(source,headers={'User-Agent':'Mozilla/5.0 PipatekaImages/8.4','Accept':'image/avif,image/webp,image/jpeg,image/png,*/*'}),timeout=25).read()
  if len(raw)<3000 or len(raw)>4_000_000:return brand,blend,None,source
  im=Image.open(io.BytesIO(raw)).convert('RGB');im.thumbnail((360,360));im.save(dest,'JPEG',quality=88,optimize=True);return brand,blend,f'assets/tins/{dest.name}',source
 except Exception as e:print('Image skipped',brand,blend,e);return brand,blend,None,preferred
def main():
 blends=[];seen=set()
 try:
  seed=json.loads(SOURCE_CATALOG.read_text(encoding='utf-8'))
  for p in seed.get('products',[]):
   if not p.get('nombre') or not p.get('marca'):continue
   k=(p['marca'].casefold(),p['nombre'].casefold())
   if k in seen:continue
   seen.add(k);blends.append({'id':p.get('id') or f"{slugify(p['marca'])}-{slugify(p['nombre'])}",'nombre':p['nombre'],'marca':p['marca'],'resenas':int(p.get('numero_resenas') or 0),'valoracion':p.get('valoracion_comunidad'),'tipo':p.get('tipo') or '','pais':p.get('origen') or '','corte':p.get('corte') or '','fuerza':p.get('fuerza') or '','aromatizacion':p.get('aromatizacion') or '','fuente':'Pipateka editorial','imagen':None,'imagen_fuente':None})
 except Exception as e:print('Seed warning',e)
 try:
  p=H4Parser();p.feed(fetch_url(TABACOTECA_URL))
  for title in p.items:
   brand,name=split_brand_name(title)
   if not name:continue
   k=(brand.casefold(),name.casefold())
   if k in seen:continue
   seen.add(k);blends.append({'id':f'fp-{slugify(brand)}-{slugify(name)}','nombre':name,'marca':brand,'resenas':0,'valoracion':None,'tipo':'','pais':'','corte':'','fuerza':'','aromatizacion':'','fuente':'Fumeurs de Pipe · Tabacothèque','imagen':None,'imagen_fuente':None})
 except Exception as e:print('Source warning',e)
 IMAGE_DIR.mkdir(parents=True,exist_ok=True);official=official_mac_baren_images();pairs=[]
 for b in blends:
  if b['marca'].casefold()=='mac baren':pairs.append((b['marca'],b['nombre'],official_image_for_blend(b['nombre'],official)))
 lookup={(b['marca'],b['nombre']):b for b in blends}
 with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
  for brand,name,path,source in pool.map(download_image,pairs):lookup[(brand,name)]['imagen']=path;lookup[(brand,name)]['imagen_fuente']=source
 blends.sort(key=lambda x:(x['marca'].casefold(),x['nombre'].casefold()));bc={}
 for b in blends:bc[b['marca']]=bc.get(b['marca'],0)+1
 payload={'version':'8.4.0','updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':'Pipateka + Fumeurs de Pipe Tabacothèque + imágenes oficiales Mac Baren + referencias visuales','source_url':TABACOTECA_URL,'source_scope':'Primera fase: biblioteca local de imágenes para Mac Baren. Se priorizan 32 páginas oficiales actuales y después referencias visuales; las copias se guardan en assets/tins y se reutilizan.','total_blends_cargados':len(blends),'total_marcas_cargadas':len(bc),'blends_con_imagen':sum(1 for b in blends if b.get('imagen')),'blends_mac_baren_con_imagen':sum(1 for b in blends if b.get('marca','').casefold()=='mac baren' and b.get('imagen')),'reference_tobaccoreviews_blends':8582,'reference_tobaccoreviews_brands':667,'blends':blends};OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');print(f'Wrote {len(blends)} blends across {len(bc)} brands; Mac Baren images={payload["blends_mac_baren_con_imagen"]}')
if __name__=='__main__':main()
