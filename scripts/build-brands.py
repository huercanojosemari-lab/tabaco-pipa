import html
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE='https://www.tobaccoreviews.com/browse/?pagenumber={}'
OUT=Path('data/marcas.json')


def clean(value):
    value=html.unescape(value or '')
    value=re.sub(r'<[^>]+>',' ',value)
    return re.sub(r'\s+',' ',value).strip()


def fetch(page):
    req=Request(BASE.format(page),headers={'User-Agent':'Mozilla/5.0 (compatible; PipatekaBrands/3.0)','Accept':'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8'})
    return urlopen(req,timeout=40).read().decode('utf-8','ignore')

rows=[]
for page in range(1,35):
    try:
        text=fetch(page)
        found=[]
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',text,re.S|re.I):
            link=re.search(r'(?:href|data-href)=[\"\']([^\"\']*/brand/([^/?\"\']+)(?:/[^\"\']*)?)[\"\']',row,re.I)
            if not link:
                continue
            cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S|re.I)
            if len(cells)<3:
                continue
            a=re.search(r'<a\b[^>]*>(.*?)</a>',cells[0],re.S|re.I)
            name=clean(a.group(1) if a else cells[0])
            nums=[clean(c) for c in cells[1:3]]
            m1=re.search(r'\d[\d,]*',nums[0]);m2=re.search(r'\d[\d,]*',nums[1])
            if name and m1 and m2:
                found.append({'marca':name,'blends':int(m1.group(0).replace(',','')),'resenas':int(m2.group(0).replace(',',''))})
        if not found:
            # Alternative table markup fallback.
            for line in text.splitlines():
                if '/brand/' not in line:
                    continue
                a=re.search(r'<a\b[^>]*>(.*?)</a>',line,re.S|re.I)
                name=clean(a.group(1)) if a else ''
                nums=re.findall(r'\b\d[\d,]*\b',clean(line))
                if name and len(nums)>=2:
                    rows.append({'marca':name,'blends':int(nums[-2].replace(',','')),'resenas':int(nums[-1].replace(',',''))})
        rows.extend(found)
        print(f'page {page}: {len(found)} brands')
    except Exception as exc:
        print(f'page {page}: {exc}')

merged={r['marca']:(r['blends'],r['resenas']) for r in rows if r.get('marca')}
brands=[{'marca':k,'blends':v[0],'resenas':v[1]} for k,v in merged.items()]
brands.sort(key=lambda x:x['marca'].casefold())

if len(brands)>=600:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'version':'3.0.0','updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':'TobaccoReviews','source_scope':'Índice público de marcas; no se reproducen textos de reseñas.','total_marcas_referencia':len(brands),'total_blends_referencia':sum(x['blends'] for x in brands),'marcas':brands},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {len(brands)} brands')
else:
    print(f'Only {len(brands)} brands fetched; keeping current data/marcas.json')
    if len(brands)>0:
        raise SystemExit(1)
