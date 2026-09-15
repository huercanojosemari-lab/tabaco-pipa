import concurrent.futures
import html
import io
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image

OUT = Path('data/catalogo-global.json')
SOURCE_CATALOG = Path('data/catalogo.json')
TABACOTECA_URL = 'https://www.fumeursdepipe.net/tabacotheque.php'
MACBAREN_URL = 'https://mac-baren.com/mac-baren/'
IMAGE_DIR = Path('assets/tins')

BRAND_PREFIXES = sorted(set([
    '4noggins','A&C Petersen','Altadis','Amphora','Arango','Ashton','Astleys','Balkan Sobranie','Barling','Bell’s','Bell\'s','Bentley','Besson','Bjarne','Breizh Tobacco','Brigham','Butera','Capstan','Chacom','Charles Fairmorn','Comoy\'s of London','Cornell & Diehl','Dan Pipe','Dan Tobacco','Daughters & Ryan','Davidoff','Drucquer & Sons','Dunhill','E. Hoffman Company','Edgeworth','Ente Tabacchi Italiani','Erik Stokkebye','Erinmore','Esoterica','Flandria','Fribourg & Treyer','Friedman & Pease','G. De Graaff & Sons','G.L. Pease','Gallaher','Gauntleys','Gawith & Hoggarth & Co','Gawith, Hoggarth & Co','Germain’s','Germain\'s','Gladora Tobacco','Half & Half','Hans Schürch','Hearth & Home','Hermit','Heupink & Bloemen','HU Tobacco','Ilsteds','Imperial Tobacco','J.B. Vinche','J.F. Germain & Son','James J. Fox','Jean-Paul Couvert','John Aylesbury','John Cotton','John Patton','John Sinclair','Joseph Martin','Kendal Tobacco','Kohlhase, Kopp und Co','L.J. Peretti and Co.','Lane Limited','Larsen','Low Country','Mac Baren','McClelland','McLintock','Mélange maison','Motzek','Murray & Sons','Murray’s','Murray\'s','New York Pipe Club','Newminster','Ogden’s of Liverpool','Ogden\'s of Liverpool','Olaf Poulsson','Orlik','Paul Olsen','Peter Stokkebye','Peterson','Pfeifen Huber','Pfeifen Schneider','Pfeifen-Studio Mühlhausen','Pfeifendepot','Pipesandcigars.com','Pipeworks & Wilke','Planta','Poschl Tabak','Poul Stanwell','Rattray’s','Rattray\'s','Reiner','Richmond','Robert Lewis','Robert McConnell','Samuel Gawith','Scandinavian Tobacco Group','Schneiderwind','Seattle Pipe Club','Smoker’s Haven','Smoker\'s Haven','Solani','St-Group Assens','Standard Tobacco Company of Pennsylvania','Sutliff Tobacco Company','Synjeco','Tabacos Wilder','Tabak Träber','Tabakhaus Falkum','TAK','Tambolaka Natural Tobaccos','Timm','Torben Dansk','Toscani','Tour du Monde des Anglais, en 80 blends','Tranter Havana House','Troost','V.B','Vauen','Villiger','Vincent Manil','Wessex','Windels','Ramback'
]), key=lambda x: (-len(x), x.casefold()))


def clean_text(value: str) -> str:
    value = html.unescape(value or '')
    return re.sub(r'\s+', ' ', value).strip(' \t\r\n-')


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


def fetch_url(url: str) -> str:
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 PipatekaCatalog/8.1'})
    return urlopen(req, timeout=45).read().decode('utf-8', 'ignore')


def fetch_source() -> str:
    return fetch_url(TABACOTECA_URL)


def split_brand_name(text: str):
    for brand in BRAND_PREFIXES:
        if text.casefold().startswith(brand.casefold() + ' '): return brand, text[len(brand):].strip()
        if text.casefold() == brand.casefold(): return brand, ''
    parts = text.split(' ', 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (text, '')


def slugify(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '-', value.casefold()).strip('-')
    return value or 'blend'


def official_mac_baren_products():
    """Build a reliable slug -> official product page map from the manufacturer index."""
    try:
        text = fetch_url(MACBAREN_URL)
        links = {}
        for m in re.finditer(r'(?:href|data-href)=[\"\'](https?://mac-baren\.com/product/[^\"\']+|/product/[^\"\']+)[\"\']', text, re.I):
            url = urljoin(MACBAREN_URL, html.unescape(m.group(1))).split('#')[0]
            slug = url.rstrip('/').split('/product/')[-1]
            if slug: links[slug] = url
        print(f'Official Mac Baren product pages: {len(links)}')
        return links
    except Exception as exc:
        print(f'Warning: official Mac Baren index import failed: {exc}')
        return {}


def official_product_image(url: str):
    try:
        text = fetch_url(url)
        m = re.search(r'<meta[^>]+property=[\"\']og:image[\"\'][^>]+content=[\"\']([^\"\']+)', text, re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=[\"\']([^\"\']+)[\"\'][^>]+property=[\"\']og:image[\"\']', text, re.I)
        if m:
            return urljoin(url, html.unescape(m.group(1)))
    except Exception:
        return None
    return None


def official_mac_baren_images():
    products = official_mac_baren_products()
    found = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(official_product_image, u): slug for slug, u in products.items()}
        for future in concurrent.futures.as_completed(futures):
            slug = futures[future]
            image = future.result()
            if image: found[slug] = image
    print(f'Official Mac Baren image candidates: {len(found)}')
    return found


MACBAREN_ALIASES = {
    'dark-twist': ['Dark Twist Roll Cake', 'Dark Twist Loose Cut'],
    'mixture': ['Mixture: Scottish Blend', 'Mixture Flake', 'Mixture Modern', 'Mixture Aromatic'],
    'mixture-aromatic': ['Mixture Aromatic'],
    'mixture-modern': ['Mixture Modern'],
    'navy-flake': ['Navy Flake'],
    'plumcake': ['Plumcake'],
    'roll-cake': ['Roll Cake'],
    'stockton': ['Stockton'],
    'the-solent': ['Solent Mixture'],
    'vanilla-loose-cut': ['Vanilla Cream Loose Cut', 'Vanilla Choice'],
    'vanilla-flake': ['Vanilla Cream Flake'],
    'vanilla-toffee': ['Classic Amber'],
    'vanilla-roll-cake': ['Vanilla Roll Cake / Classic Roll Cake'],
    'virginia-flake': ['Virginia Flake'],
    'virginia-no-1': ['Virginia No. 1'],
    'cube-gold': ['Cube Gold'],
    'cube-silver': ['Cube Silver'],
}


def official_image_for_blend(blend: str, official):
    target = slugify(blend)
    for product_slug, names in MACBAREN_ALIASES.items():
        if any(slugify(n) == target for n in names) and product_slug in official:
            return official[product_slug]
    if target in official: return official[target]
    for product_slug, image_url in official.items():
        ps = slugify(product_slug)
        if ps.startswith(target + '-') or target.startswith(ps + '-'):
            return image_url
    return None


def find_image(brand: str, blend: str):
    query = quote_plus(f'"{brand}" "{blend}" pipe tobacco tin')
    url = f'https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 PipatekaImages/8.1', 'Accept': 'text/html'})
    text = urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
    candidates = []
    for pattern in [r'"m"\s*:\s*\{[^{}]*?"murl"\s*:\s*"([^"]+)"', r'"murl"\s*:\s*"([^"]+)"']:
        candidates.extend(m.group(1).replace('\\/', '/') for m in re.finditer(pattern, text))
        if candidates: break
    for full in candidates[:12]:
        low = full.lower()
        if any(x in low for x in ('logo','icon','avatar','.svg')): continue
        if urlparse(full).scheme in ('http','https'): return full
    return None


def download_image(item):
    brand, blend, preferred_source = item
    try:
        source = preferred_source or find_image(brand, blend)
        if not source: return brand, blend, None, None
        req = Request(source, headers={'User-Agent': 'Mozilla/5.0 PipatekaImages/8.1', 'Accept': 'image/avif,image/webp,image/jpeg,image/png,*/*'})
        raw = urlopen(req, timeout=25).read()
        if len(raw) < 3000 or len(raw) > 4_000_000: return brand, blend, None, source
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        image.thumbnail((360, 360))
        dest = IMAGE_DIR / f'{slugify(brand)}--{slugify(blend)}.jpg'
        image.save(dest, 'JPEG', quality=88, optimize=True)
        return brand, blend, f'assets/tins/{dest.name}', source
    except Exception as exc:
        print(f'Image skipped for {brand} / {blend}: {exc}')
        return brand, blend, None, preferred_source


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
    official = official_mac_baren_images()
    pairs = []
    for b in blends:
        preferred = official_image_for_blend(b['nombre'], official) if b['marca'].casefold() == 'mac baren' else None
        pairs.append((b['marca'], b['nombre'], preferred))
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
    payload = {'version':'8.1.0', 'updated':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'source':'Pipateka + Fumeurs de Pipe Tabacothèque + imágenes oficiales Mac Baren + referencias visuales', 'source_url':TABACOTECA_URL, 'source_scope':'Índice de nombres y datos de catálogo. Las imágenes se descargan durante la generación y quedan locales en Pipateka; para Mac Baren se prioriza el fabricante.', 'total_blends_cargados':len(blends), 'total_marcas_cargadas':len(brand_counts), 'blends_con_imagen':sum(1 for b in blends if b.get('imagen')), 'blends_mac_baren_con_imagen':sum(1 for b in blends if b.get('marca','').casefold() == 'mac baren' and b.get('imagen')), 'reference_tobaccoreviews_blends':8582, 'reference_tobaccoreviews_brands':667, 'blends':blends}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(blends)} blends across {len(brand_counts)} brands; images={payload["blends_con_imagen"]}; Mac Baren images={payload["blends_mac_baren_con_imagen"]}')


if __name__ == '__main__': main()
