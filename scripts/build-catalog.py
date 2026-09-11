import concurrent.futures
import html
import io
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

from PIL import Image

OUT = Path('data/catalogo-global.json')
SOURCE_CATALOG = Path('data/catalogo.json')
TABACOTECA_URL = 'https://www.fumeursdepipe.net/tabacotheque.php'
IMAGE_DIR = Path('assets/tins')

BRAND_PREFIXES = [
    '4noggins','A&C Petersen','Altadis','Amphora','Arango','Ashton','Astleys','Balkan Sobranie',
    'Barling','Bell’s','Bell\'s','Bentley','Besson','Bjarne','Breizh Tobacco','Brigham','Butera',
    'Capstan','Chacom','Charles Fairmorn','Comoy\'s of London','Cornell & Diehl','Dan Pipe',
    'Dan Tobacco','Daughters & Ryan','Davidoff','Drucquer & Sons','Dunhill','E. Hoffman Company',
    'Edgeworth','Ente Tabacchi Italiani','Erik Stokkebye','Erinmore','Esoterica','Flandria',
    'Fribourg & Treyer','Friedman & Pease','G. De Graaff & Sons','G.L. Pease','Gallaher','Gauntleys',
    'Gawith & Hoggarth & Co','Gawith, Hoggarth & Co','Germain’s','Germain\'s','Gladora Tobacco',
    'Half & Half','Hans Schürch','Hearth & Home','Hermit','Heupink & Bloemen','HU Tobacco',
    'Ilsteds','Imperial Tobacco','J.B. Vinche','J.F. Germain & Son','James J. Fox','Jean-Paul Couvert',
    'John Aylesbury','John Cotton','John Patton','John Sinclair','Joseph Martin','Kendal Tobacco',
    'Kohlhase, Kopp und Co','L.J. Peretti and Co.','Lane Limited','Larsen','Low Country','Mac Baren',
    'McClelland','McLintock','Mélange maison','Motzek','Murray & Sons','Murray’s','Murray\'s',
    'New York Pipe Club','Newminster','Ogden’s of Liverpool','Ogden\'s of Liverpool','Olaf Poulsson',
    'Orlik','Paul Olsen','Peter Stokkebye','Peterson','Pfeifen Huber','Pfeifen Schneiderwind',
    'Pfeifen-Studio Mühlhausen','Pfeifendepot','Pipesandcigars.com','Pipeworks & Wilke','Planta',
    'Poschl Tabak','Poul Stanwell','Rattray’s','Rattray\'s','Reiner','Richmond','Robert Lewis',
    'Robert McConnell','Samuel Gawith','Scandinavian Tobacco Group','Schneiderwind','Seattle Pipe Club',
    'Smoker’s Haven','Smoker\'s Haven','Solani','St-Group Assens','Standard Tobacco Company of Pennsylvania',
    'Sutliff Tobacco Company','Synjeco','Tabacos Wilder','Tabak Träber','Tabakhaus Falkum','TAK',
    'Tambolaka Natural Tobaccos','Timm','Torben Dansk','Toscani','Tour du Monde des Anglais, en 80 blends',
    'Tranter Havana House','Troost','V.B','Vauen','Villiger','Vincent Manil','Wessex','Windels','Ramback'
]
BRAND_PREFIXES = sorted(set(BRAND_PREFIXES), key=lambda x: (-len(x), x.casefold()))


def clean_text(value: str) -> str:
    value = html.unescape(value or '')
    value = re.sub(r'\s+', ' ', value)
    return value.strip(' \t\r\n-')


class H4Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_h4 = False; self.buf = []; self.items = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'h4': self.in_h4 = True; self.buf = []
    def handle_endtag(self, tag):
        if tag.lower() == 'h4' and self.in_h4:
            text = clean_text(''.join(self.buf))
            if text: self.items.append(text)
            self.in_h4 = False; self.buf = []
    def handle_data(self, data):
        if self.in_h4: self.buf.append(data)


def fetch_source() -> str:
    req = Request(TABACOTECA_URL, headers={'User-Agent': 'Mozilla/5.0 PipatekaCatalog/3.0'})
    return urlopen(req, timeout=45).read().decode('utf-8', 'ignore')


def split_brand_name(text: str):
    for brand in BRAND_PREFIXES:
        if text.casefold().startswith(brand.casefold() + ' '): return brand, text[len(brand):].strip()
        if text.casefold() == brand.casefold(): return brand, ''
    parts = text.split(' ', 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (text, '')


def slugify(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '-', value.casefold()).strip('-')
    return value or 'blend'


def find_image(brand: str, blend: str):
    query = quote_plus(f'"{brand}" "{blend}" pipe tobacco tin')
    url = f'https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 PipatekaImages/2.0', 'Accept': 'text/html'})
    text = urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
    patterns = [
        r'"m"\s*:\s*\{[^{}]*?"murl"\s*:\s*"([^"]+)"',
        r'"murl"\s*:\s*"([^"]+)"',
    ]
    candidates = []
    for pattern in patterns:
        candidates.extend(m.group(1).replace('\\/', '/') for m in re.finditer(pattern, text))
        if candidates: break
    for full in candidates[:12]:
        low = full.lower()
        if any(x in low for x in ('logo','icon','avatar','.svg')): continue
        if urlparse(full).scheme in ('http','https'): return full
    return None


def download_image(item):
    brand, blend = item
    try:
        source = find_image(brand, blend)
        if not source: return brand, blend, None, None
        req = Request(source, headers={'User-Agent': 'Mozilla/5.0 PipatekaImages/2.0', 'Accept': 'image/avif,image/webp,image/jpeg,image/png,*/*'})
        raw = urlopen(req, timeout=20).read()
        if len(raw) < 3000 or len(raw) > 2_000_000: return brand, blend, None, source
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        image.thumbnail((220, 220))
        dest = IMAGE_DIR / f'{slugify(brand)}--{slugify(blend)}.jpg'
        image.save(dest, 'JPEG', quality=82, optimize=True)
        return brand, blend, f'assets/tins/{dest.name}', source
    except Exception as exc:
        print(f'Image skipped for {brand} / {blend}: {exc}')
        return brand, blend, None, None


def main():
    blends = []; seen = set()
    try:
        seed = json.loads(SOURCE_CATALOG.read_text(encoding='utf-8'))
        for p in seed.get('products', []):
            if not p.get('nombre') or not p.get('marca'): continue
            key = (p['marca'].casefold(), p['nombre'].casefold())
            if key in seen: continue
            seen.add(key)
            blends.append({'id': p.get('id') or f"{slugify(p['marca'])}-{slugify(p['nombre'])}", 'nombre': p['nombre'], 'marca': p['marca'], 'resenas': int(p.get('numero_resenas') or 0), 'valoracion': p.get('valoracion_comunidad'), 'tipo': p.get('tipo') or '', 'pais': p.get('origen') or '', 'corte': p.get('corte') or '', 'fuerza': p.get('fuerza') or '', 'aromatizacion': p.get('aromatizacion') or '', 'fuente': 'Pipateka editorial', 'imagen': None, 'imagen_fuente': None})
    except Exception as exc: print(f'Warning: could not read seed catalog: {exc}')

    try:
        parser = H4Parser(); parser.feed(fetch_source())
        for title in parser.items:
            brand, blend_name = split_brand_name(title)
            if not blend_name: continue
            key = (brand.casefold(), blend_name.casefold())
            if key in seen: continue
            seen.add(key)
            blends.append({'id': f'fp-{slugify(brand)}-{slugify(blend_name)}', 'nombre': blend_name, 'marca': brand, 'resenas': 0, 'valoracion': None, 'tipo': '', 'pais': '', 'corte': '', 'fuerza': '', 'aromatizacion': '', 'fuente': 'Fumeurs de Pipe · Tabacothèque', 'imagen': None, 'imagen_fuente': None})
        print(f'Imported additional blends from Tabacothèque; total before images: {len(blends)}')
    except Exception as exc: print(f'Warning: source import failed: {exc}')

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    pairs = [(b['marca'], b['nombre']) for b in blends]
    lookup = {(b['marca'], b['nombre']): b for b in blends}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for done, result in enumerate(pool.map(download_image, pairs), 1):
            brand, blend, image_path, image_source = result
            b = lookup[(brand, blend)]
            b['imagen'] = image_path; b['imagen_fuente'] = image_source
            if done % 50 == 0: print(f'Images processed: {done}/{len(pairs)}')

    blends.sort(key=lambda x: (x['marca'].casefold(), x['nombre'].casefold()))
    brand_counts = {}
    for b in blends: brand_counts[b['marca']] = brand_counts.get(b['marca'], 0) + 1
    payload = {'version':'7.0.0', 'updated':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'source':'Pipateka + Fumeurs de Pipe Tabacothèque + Bing Images (miniaturas)', 'source_url':TABACOTECA_URL, 'source_scope':'Índice de nombres de mezclas y marcas. Las miniaturas son referencias visuales enlazadas desde su fuente de imagen; Pipateka no reproduce textos de reseñas ni afirma disponibilidad comercial.', 'total_blends_cargados':len(blends), 'total_marcas_cargadas':len(brand_counts), 'blends_con_imagen':sum(1 for b in blends if b.get('imagen')), 'reference_tobaccoreviews_blends':8582, 'reference_tobaccoreviews_brands':667, 'blends':blends}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(blends)} blends across {len(brand_counts)} brands; images={payload["blends_con_imagen"]}')


if __name__ == '__main__': main()
