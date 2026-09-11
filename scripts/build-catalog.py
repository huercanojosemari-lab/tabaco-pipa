import concurrent.futures
import html
import json
import math
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE='https://r.jina.ai/http://www.tobaccoreviews.com/advanced-search/?pagenumber={}'
OUT=Path('data/catalogo-global.json')
WORKERS=10


def clean(value):
    value=html.unescape(value or '')
    value=re.sub(r'<[^>]+>',' ',value)
    return re.sub(r'\s+',' ',value).strip()


def fetch(page):
    req=Request(BASE.format(page),headers={'User-Agent':'Mozilla/5.0 PipatekaCatalog/4.0','Accept':'text/plain,text/markdown;q=0.9,*/*;q=0.8'})
    text=urlopen(req,timeout=60).read().decode('utf-8','ignore')
    total_match=re.search(r'Displaying\s+[\d,]+\s*-\s*[\d,]+\s+of\s+([\d,]+)\s+Blends',text,re.I)
    total=int(total_match.group(1).replace(',','')) if total_match else None
    rows=[]
    in_table=False
    for raw in text.splitlines():
        line=raw.strip()
        if re.match(r'^Name\s*\|\s*Reviews',line,re.I):
            in_table=True
            continue
        if not in_table or not line.startswith('|') or re.match(r'^\|\s*-+',line):
            continue
        cells=[clean(c) for c in line.strip('|').split('|')]
        if len(cells)<4:
            continue
        name=cells[0]
        if not name or name.lower() in ('name','blend type'):
            continue
        reviews_match=re.fullmatch(r'[\d,]+',cells[1])
        rating_match=re.fullmatch(r'(?:\d+(?:\.\d+)?|--|-)',cells[2])
        if not reviews_match or not rating_match:
            continue
        rating=None if cells[2] in ('--','-') else float(cells[2])
        rows.append({'id':re.sub(r'[^a-z0-9]+','-',name.casefold()).strip('-'),'nombre':name,'resenas':int(cells[1].replace(',','')),'valoracion':rating,'tipo':cells[3]})
    return total,rows


def worker(page):
    try:
        total,rows=fetch(page)
        return page,total,rows,None
    except Exception as exc:
        return page,None,[],str(exc)

first_total,first_rows=fetch(1)
total=first_total or 8582
total_pages=max(1,math.ceil(total/20))
print(f'Source reports {total} blends across {total_pages} pages')
rows=list(first_rows);errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures=[pool.submit(worker,p) for p in range(2,total_pages+1)]
    for done,future in enumerate(concurrent.futures.as_completed(futures),start=2):
        page,page_total,page_rows,error=future.result();rows.extend(page_rows)
        if error: errors.append((page,error))
        if done%25==0 or done==total_pages: print(f'pages {done}/{total_pages}: {len(rows)} rows; errors={len(errors)}')

unique={row['id']:row for row in rows if row.get('id') and row.get('nombre')}
blends=sorted(unique.values(),key=lambda x:(x['nombre'].casefold(),x['id']))
expected_min=max(8000,int(total*.98))
if len(blends)<expected_min:
    print(f'ABORT: only {len(blends)} unique blends fetched; expected at least {expected_min}.')
    raise SystemExit(1)

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'version':'4.0.0','updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':'TobaccoReviews','source_scope':'Índice público de mezclas; no se reproducen textos de reseñas.','source_url':'https://www.tobaccoreviews.com/advanced-search/','total_blends_referencia':len(blends),'total_paginas_fuente':total_pages,'blends':blends},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Wrote {len(blends)} blends; source errors={len(errors)}')
