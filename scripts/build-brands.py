import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE='https://www.tobaccoreviews.com/browse/?pagenumber={}'
OUT=Path('data/marcas.json')

rows=[]
for page in range(1,35):
    try:
        req=Request(BASE.format(page),headers={'User-Agent':'Mozilla/5.0 Pipateka catalog index'})
        html=urlopen(req,timeout=25).read().decode('utf-8','ignore')
        # The public browse table has rows in the form: <a ...>Brand</a></td><td>blends</td><td>reviews
        matches=re.findall(r'<a[^>]*href="/brand/[^\"]+"[^>]*>\s*(.*?)\s*</a>\s*</td>\s*<td[^>]*>\s*([0-9,]+)\s*</td>\s*<td[^>]*>\s*([0-9,]+)',html,re.S|re.I)
        for name,blends,reviews in matches:
            name=re.sub(r'<[^>]+>','',name).strip()
            if name:
                rows.append({'marca':name,'blends':int(blends.replace(',','')),'resenas':int(reviews.replace(',',''))})
        time.sleep(.2)
    except Exception as exc:
        print(f'page {page}: {exc}')

# Deduplicate by brand, preserving the newest occurrence.
merged={r['marca']:(r['blends'],r['resenas']) for r in rows}
brands=[{'marca':k,'blends':v[0],'resenas':v[1]} for k,v in merged.items()]
brands.sort(key=lambda x:x['marca'].casefold())

if len(brands) >= 600:
    OUT.write_text(json.dumps({'version':'2.0.0','updated':time.strftime('%Y-%m-%d'),'source':'TobaccoReviews','source_scope':'Índice público de marcas; no se reproducen textos de reseñas.','total_marcas_referencia':len(brands),'total_blends_referencia':sum(x['blends'] for x in brands),'marcas':brands},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {len(brands)} brands')
else:
    print(f'Only {len(brands)} brands fetched; keeping existing data/marcas.json')
