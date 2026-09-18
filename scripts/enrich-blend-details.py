import html
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

CATALOG=Path("data/catalogo-global.json")

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self,data):
        if data and not re.match(r'^[\\s\\xa0]+$',data):
            self.parts.append(data)
    def text(self):
        return re.sub(r'\\s+',' ',html.unescape(' '.join(self.parts))).strip()

def fetch(url):
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 PipatekaEnrichment/1.0"})
    return urlopen(req,timeout=30).read().decode('utf-8','ignore')

def text_from_html(source):
    p=TextParser()
    p.feed(source)
    return p.text()

def value_after(text,label,next_labels):
    m=re.search(r'\\b'+re.escape(label)+r'\\s*(.*?)\\s*(?=\\b(?:'+ '|'.join(map(re.escape,next_labels)) +r')\\b|$)',text,re.I)
    return m.group(1).strip(' |:-') if m else ''

def parse(url):
    raw=fetch(url)
    text=text_from_html(raw)
    details={}
    labels=['Brand','Series','Blended By','Manufactured By','Blend Type','Contents','Flavoring','Cut','Packaging','Country','Production','Strength','Room Note','Taste']
    for label in labels:
        others=[x for x in labels if x!=label]
        v=value_after(text,label,others)
        if v: details[label.lower().replace(' ','_')]=v
    return details

def strength_num(s):
    x=str(s or '').casefold()
    if not x: return 0
    if 'overwhelming' in x or 'very strong' in x: return 5
    if 'strong' in x: return 4
    if 'medium to strong' in x: return 4
    if 'medium' in x: return 3
    if 'mild to medium' in x: return 2
    if 'mild' in x: return 1
    return 0

def main():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    rows=data.get('blends',[])
    targets=[b for b in rows if b.get('fuente_blend_url') and str(b.get('fuente_blend_url')).find('tobaccoreviews.com/blend/')>=0]
    print(f'Enrichment targets: {len(targets)}')
    results={}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures={pool.submit(parse,b['fuente_blend_url']):b for b in targets}
        for f in as_completed(futures):
            b=futures[f]
            try:
                results[(b.get('marca'),b.get('nombre'))]=f.result()
            except Exception as exc:
                print('Enrichment skipped',b.get('marca'),b.get('nombre'),exc)
    filled=0
    for b in rows:
        d=results.get((b.get('marca'),b.get('nombre')))
        if not d: continue
        before=json.dumps(b,ensure_ascii=False,sort_keys=True)
        mapping={
            'tipo':d.get('blend_type',''),
            'corte':d.get('cut',''),
            'composicion':d.get('contents',''),
            'pais':d.get('country',''),
            'aromatizacion':d.get('flavoring',''),
            'fuerza_text':d.get('strength',''),
            'nota_estancia':d.get('room_note',''),
            'sabor':d.get('taste',''),
            'produccion':d.get('production',''),
        }
        for k,v in mapping.items():
            if v and (not b.get(k) or b.get(k) in ('Sin dato','Sin clasificar')):
                b[k]=v
        b['fuerza']=strength_num(b.get('fuerza_text') or b.get('fuerza'))
        after=json.dumps(b,ensure_ascii=False,sort_keys=True)
        if after!=before: filled+=1
    data['enrichment']={
        'source':'TobaccoReviews individual blend pages',
        'updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'targets':len(targets),
        'rows_updated':filled,
        'fields':['tipo','corte','composicion','pais','aromatizacion','fuerza_text','nota_estancia','sabor','produccion']
    }
    CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Enrichment completed: {filled} fichas actualizadas')
if __name__=='__main__':
    main()
