import html
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE='https://r.jina.ai/http://www.tobaccoreviews.com/browse/?pagenumber={}'
OUT=Path('data/marcas.json')


def clean(value):
    value=html.unescape(value or '')
    value=re.sub(r'<[^>]+>',' ',value)
    return re.sub(r'\s+',' ',value).strip()


def fetch(page):
    req=Request(BASE.format(page),headers={'User-Agent':'Mozilla/5.0 PipatekaBrands/4.0','Accept':'text/plain,text/markdown;q=0.9,*/*;q=0.8'})
    return urlopen(req,timeout=60).read().decode('utf-8','ignore')


def parse(text):
    rows=[]
    in_table=False
    for raw in text.splitlines():
        line=raw.strip()
        if re.match(r'^Brand\s*\|\s*Blends\s*\|\s*Reviews',line,re.I):
            in_table=True
            continue
        if not in_table or not line.startswith('|'):
            continue
        if re.match(r'^\|\s*-+',line):
            continue
        cells=[clean(c) for c in line.strip('|').split('|')]
        if len(cells)<3:
            continue
        name=cells[0]
        m1=re.fullmatch(r'[\d,]+',cells[1]);m2=re.fullmatch(r'[\d,]+',cells[2])
        if name and m1 and m2:
            rows.append({'marca':name,'blends':int(cells[1].replace(',','')),'resenas':int(cells[2].replace(',',''))})
    return rows

rows=[]
for page in range(1,35):
    try:
        found=parse(fetch(page))
        rows.extend(found)
        print(f'page {page}: {len(found)} brands')
    except Exception as exc:
        print(f'page {page}: {exc}')

merged={r['marca']:(r['blends'],r['resenas']) for r in rows if r.get('marca')}
brands=[{'marca':k,'blends':v[0],'resenas':v[1]} for k,v in merged.items()]
brands.sort(key=lambda x:x['marca'].casefold())

if len(brands)>=600:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'version':'4.0.0','updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':'TobaccoReviews','source_scope':'Índice público de marcas; no se reproducen textos de reseñas.','total_marcas_referencia':len(brands),'total_blends_referencia':sum(x['blends'] for x in brands),'marcas':brands},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {len(brands)} brands')
else:
    print(f'Only {len(brands)} brands fetched; keeping current data/marcas.json')
    raise SystemExit(1)
