import html, json, re
from pathlib import Path

CATALOG=Path('data/catalogo-global.json')
OUT=Path('assets/brands')

def slugify(v):
    return re.sub(r'[^a-z0-9]+','-',str(v).casefold()).strip('-') or 'brand'

def xml(v):
    return html.escape(str(v),quote=True)

def monogram(name):
    parts=[p for p in re.split(r'[^A-Za-z0-9À-ÿ]+',name) if p]
    if not parts: return 'P'
    if len(parts)==1: return parts[0][0].upper()
    return (parts[0][0]+parts[-1][0]).upper()

def make(name):
    n=xml(name)
    m=xml(monogram(name))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="150" viewBox="0 0 420 150" role="img" aria-labelledby="title desc">
<title>{n}</title><desc>Identidad gráfica local de la marca {n} para el catálogo Pipateka.</desc>
<rect x="3" y="3" width="414" height="144" rx="18" fill="#f7f3eb" stroke="#c7a466" stroke-width="6"/>
<circle cx="75" cy="75" r="42" fill="#20201d"/>
<text x="75" y="89" text-anchor="middle" font-family="Georgia,serif" font-size="34" font-weight="700" fill="#f7f3eb">{m}</text>
<text x="135" y="72" font-family="Georgia,serif" font-size="25" font-weight="700" fill="#20201d">{n}</text>
<text x="135" y="100" font-family="Arial,sans-serif" font-size="11" letter-spacing="2" fill="#8a6a2f">PIPATEKA · MARCA</text>
</svg>'''

def main():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    brands=sorted({str(b.get('marca')).strip() for b in data.get('blends',[]) if b.get('marca')})
    OUT.mkdir(parents=True,exist_ok=True)
    for brand in brands:
        (OUT/f'{slugify(brand)}.svg').write_text(make(brand),encoding='utf-8')
    print(f'Generated {len(brands)} brand images in {OUT}')
if __name__=='__main__':
    main()
