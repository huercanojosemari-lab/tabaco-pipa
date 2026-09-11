import concurrent.futures
import html
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE='https://r.jina.ai/http://www.tobaccoreviews.com/browse/?pagenumber={}'
OUT=Path('data/marcas.json')
WORKERS=8

def clean(value):
    value=html.unescape(value or '')
    value=re.sub(r'<[^>]+>',' ',value)
    return re.sub(r'\s+',' ',value).strip()

def fetch(page):
    req=Request(BASE.format(page),headers={'User-Agent':'Mozilla/5.0 PipatekaBrands/7.0','Accept':'text/plain,text/markdown;q=0.9,*/*;q=0.8'})
    return urlopen(req,timeout=30).read().decode('utf-8','ignore')

def parse(text):
    rows=[]; in_table=False
    for raw in text.splitlines():
        line=raw.strip()
        if re.search(r'Brand\s*\|.*Blends.*\|.*Reviews',line,re.I): in_table=True; continue
        if not in_table or not line.startswith('|') or re.match(r'^\|\s*-+',line): continue
        cells=[clean(c) for c in line.strip('|').split('|')]
        if len(cells)>=3 and re.fullmatch(r'[\d,]+',cells[1]) and re.fullmatch(r'[\d,]+',cells[2]) and cells[0]:
            rows.append({'marca':cells[0],'blends':int(cells[1].replace(',','')),'resenas':int(cells[2].replace(',',''))})
    return rows

def worker(page):
    try:return page,parse(fetch(page)),None
    except Exception as exc:return page,[],str(exc)

rows=[];errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures=[pool.submit(worker,p) for p in range(1,35)]
    for done,f in enumerate(concurrent.futures.as_completed(futures),1):
        page,found,error=f.result();rows.extend(found)
        if error:errors.append((page,error))
        print(f'pages {done}/34: page {page} -> {len(found)} brands; errors={len(errors)}')

merged={r['marca']:(r['blends'],r['resenas']) for r in rows if r.get('marca')}
brands=[{'marca':k,'blends':v[0],'resenas':v[1]} for k,v in merged.items()]
brands.sort(key=lambda x:x['marca'].casefold())
if len(brands)>=600:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'version':'7.0.0','updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':'TobaccoReviews','source_scope':'Índice público de marcas; no se reproducen textos de reseñas.','total_marcas_referencia':len(brands),'total_blends_referencia':sum(x['blends'] for x in brands),'marcas':brands},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {len(brands)} brands; errors={len(errors)}')
else:
    print(f'No se pudo refrescar el índice remoto ({len(brands)} marcas recibidas). Se conserva data/marcas.json para no romper la web.')
    # Do not fail deployment: the remote source currently returns an age/access gate to runners.
