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
MACBAREN_ARCHIVE = 'https://mac-baren.com/product/page/'
IMAGE_DIR = Path('assets/tins')

BRAND_PREFIXES = sorted([
    'A&C Petersen', 'Balkan Sobranie', 'Cornell & Diehl', 'Dan Tobacco',
    'Daughters & Ryan', 'Drucquer & Sons', 'G. L. Pease', 'Gawith & Hoggarth & Co',
    'Gawith, Hoggarth & Co', 'J.F. Germain & Son', 'James J. Fox', 'Kohlhase, Kopp und Co',
    'L.J. Peretti and Co.', 'Lane Limited', 'Mac Baren', 'McClelland', 'New York Pipe Club',
    'Ogden’s of Liverpool', "Ogden's of Liverpool", 'Peter Stokkebye', 'Pipeworks & Wilke',
    'Poschl Tabak', 'Robert McConnell', 'Samuel Gawith', 'Scandinavian Tobacco Group',
    'Seattle Pipe Club', "Smoker's Haven", 'Smoker’s Haven', 'Standard Tobacco Company of Pennsylvania',
    'Sutliff Tobacco Company', 'Tabak Träber', 'Torben Dansk', 'Tour du Monde des Anglais, en 80 blends',
    'V.B', 'Vincent Manil', 'Wessex'
], key=lambda x: (-len(x), x.casefold()))

CURRENT_MACBAREN_SLUGS = [
    'black-ambrosia', 'cherry-ambrosia', 'golden-ambrosia', 'club-blend', 'dark-twist',
    'golden-blend', 'harmony', 'latakia-blend', 'mixture', 'mixture-aromatic', 'mixture-modern',
    'navy-flake', 'plumcake', 'roll-cake', 'stockton', 'the-solent', 'vanilla-loose-cut',
    'vanilla-flake', 'vanilla-toffee', 'vanilla-roll-cake', 'virginia-flake', 'virginia-no-1',
    'cube-gold', 'cube-silver', 'hh-bold-kentucky-flake', 'hh-burley-flake', 'hh-latakia-flake',
    'hh-old-dark-fired-flake', 'hh-pure-virginia-flake', 'hh-vintage-latakia', 'hh-rustica-flake',
    'hh-balkan-blend'
]

ALIASES = {
    'dark-twist': ['Dark Twist Roll Cake', 'Dark Twist Loose Cut'],
    'mixture': ['Mixture: Scottish Blend', 'Mixture Flake', 'Mixture Modern', 'Mixture Aromatic'],
    'navy-flake': ['Navy Flake'], 'plumcake': ['Plumcake'], 'roll-cake': ['Roll Cake'],
    'stockton': ['Stockton'], 'the-solent': ['Solent Mixture'],
    'vanilla-loose-cut': ['Vanilla Cream Loose Cut', 'Vanilla Choice'],
    'vanilla-flake': ['Vanilla Cream Flake'], 'vanilla-toffee': ['Classic Amber'],
    'vanilla-roll-cake': ['Vanilla Roll Cake', 'Classic Roll Cake'],
    'virginia-flake': ['Virginia Flake'], 'virginia-no-1': ['Virginia No. 1'],
    'cube-gold': ['Cube Gold'], 'cube-silver': ['Cube Silver'],
    'hh-bold-kentucky-flake': ['HH Bold Kentucky', 'HH Bold Kentucky Flake'],
    'hh-burley-flake': ['HH Burley Flake'], 'hh-latakia-flake': ['HH Latakia Flake'],
    'hh-old-dark-fired-flake': ['HH Old Dark Fired'], 'hh-pure-virginia-flake': ['HH Pure Virginia'],
    'hh-vintage-latakia': ['HH Vintage Latakia'], 'hh-rustica-flake': ['HH Rustica'],
    'hh-balkan-blend': ['HH Balkan Blend']
}


def clean_text(value):
    return re.sub(r'\s+', ' ', html.unescape(value or '')).strip(' \t\r\n-')


def fetch_url(url, timeout=45):
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 PipatekaCatalog/9.0'})
    return urlopen(request, timeout=timeout).read().decode('utf-8', 'ignore')


def slugify(value):
    return re.sub(r'[^a-z0-9]+', '-', str(value).casefold()).strip('-') or 'blend'


class H4Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_h4 = False
        self.buf = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'h4':
            self.in_h4 = True
            self.buf = []

    def handle_endtag(self, tag):
        if tag.lower() == 'h4' and self.in_h4:
            value = clean_text(''.join(self.buf))
            if value:
                self.items.append(value)
            self.in_h4 = False
            self.buf = []

    def handle_data(self, data):
        if self.in_h4:
            self.buf.append(data)


def split_brand_name(title):
    folded = title.casefold()
    for brand in BRAND_PREFIXES:
        if folded.startswith(brand.casefold() + ' '):
            return brand, title[len(brand):].strip()
        if folded == brand.casefold():
            return brand, ''
    parts = title.split(' ', 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (title, '')


def official_mac_baren_products():
    links = {slug: f'https://mac-baren.com/product/{slug}/' for slug in CURRENT_MACBAREN_SLUGS}
    try:
        text = fetch_url(MACBAREN_URL)
        pattern = r'(?:href|data-href)=[\"\'](https?://mac-baren\.com/product/[^\"\']+|/product/[^\"\']+)[\"\']'
        for match in re.finditer(pattern, text, re.I):
            url = urljoin(MACBAREN_URL, html.unescape(match.group(1))).split('#')[0]
            slug = url.rstrip('/').split('/product/')[-1]
            if slug:
                links[slug] = url
    except Exception as exc:
        print('Warning official index:', exc)
    print('Official Mac Baren product pages:', len(links))
    return links


def official_product_image(url):
    try:
        text = fetch_url(url)
        og = re.search(r'<meta[^>]+property=[\"\']og:image[\"\'][^>]+content=[\"\']([^\"\']+)', text, re.I)
        if not og:
            og = re.search(r'<meta[^>]+content=[\"\']([^\"\']+)[\"\'][^>]+property=[\"\']og:image[\"\']', text, re.I)
        if og:
            return urljoin(url, html.unescape(og.group(1)))
        slug = slugify(url.rstrip('/').split('/product/')[-1])
        images = re.findall(r'<img[^>]+(?:src|data-src)=[\"\']([^\"\']+)[\"\'][^>]*>', text, re.I)
        for raw in images:
            image_url = urljoin(url, html.unescape(raw))
            lower = image_url.lower()
            if 'wp-content/uploads' in lower and slug in lower and not any(x in lower for x in ('logo', 'icon', 'avatar')):
                return image_url
        for raw in images:
            image_url = urljoin(url, html.unescape(raw))
            lower = image_url.lower()
            if 'wp-content/uploads' in lower and not any(x in lower for x in ('logo', 'icon', 'avatar')):
                return image_url
    except Exception:
        pass
    return None


def official_archive_images():
    found = {}
    for page in range(1, 19):
        try:
            archive_url = MACBAREN_ARCHIVE if page == 1 else f'{MACBAREN_ARCHIVE}{page}/'
            text = fetch_url(archive_url)
            blocks = re.split(r'(?=<h[1-6][^>]*>)', text, flags=re.I)
            for block in blocks:
                headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', block, re.I | re.S)
                if not headings:
                    continue
                name = clean_text(re.sub(r'<[^>]+>', ' ', headings[0]))
                if not name:
                    continue
                image_ids = re.findall(r'vc_single_image[^>]+image=[\"\'](\d+)[\"\']', block, re.I)
                if not image_ids:
                    continue
                try:
                    media_json = fetch_url(f'https://mac-baren.com/wp-json/wp/v2/media/{image_ids[0]}', timeout=25)
                    source = re.search(r'\"source_url\":\"([^\"]+)\"', media_json)
                    if source:
                        found[name] = html.unescape(source.group(1).replace('\\/', '/'))
                except Exception:
                    continue
            print(f'Mac Baren archive page {page}: {len(found)} images mapped')
        except Exception as exc:
            print(f'Warning archive page {page}:', exc)
    return found


def official_mac_baren_images():
    pages = official_mac_baren_products()
    found = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(official_product_image, url): slug for slug, url in pages.items()}
        for future in concurrent.futures.as_completed(futures):
            image = future.result()
            if image:
                found[futures[future]] = image
    for name, image in official_archive_images().items():
        found[f'archive:{slugify(name)}'] = image
    print('Official Mac Baren image candidates:', len(found))
    return found


def official_image_for_blend(blend, official):
    target = slugify(blend)
    for slug, names in ALIASES.items():
        if target in {slugify(name) for name in names} and slug in official:
            return official[slug]
    if target in official:
        return official[target]
    for key, image in official.items():
        candidate = slugify(key.replace('archive:', ''))
        if candidate == target or candidate.startswith(target + '-') or target.startswith(candidate + '-'):
            return image
    return None


def find_image(brand, blend):
    query = quote_plus(f'"{brand}" "{blend}" pipe tobacco tin')
    url = f'https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1'
    try:
        text = fetch_url(url, timeout=25)
        candidates = []
        for pattern in [r'"m"\s*:\s*\{[^{}]*?"murl"\s*:\s*"([^\"]+)"', r'"murl"\s*:\s*"([^\"]+)"']:
            candidates.extend(m.group(1).replace('\\/', '/') for m in re.finditer(pattern, text))
            if candidates:
                break
        for candidate in candidates[:20]:
            if not any(x in candidate.lower() for x in ('logo', 'icon', 'avatar', '.svg')) and urlparse(candidate).scheme in ('http', 'https'):
                return candidate
    except Exception:
        pass
    return None


def download_image(item):
    brand, blend, preferred = item
    destination = IMAGE_DIR / f'{slugify(brand)}--{slugify(blend)}.jpg'
    if destination.exists() and destination.stat().st_size > 3000:
        return brand, blend, f'assets/tins/{destination.name}', 'local-cache'
    source = preferred or find_image(brand, blend)
    if not source:
        return brand, blend, None, None
    try:
        request = Request(source, headers={'User-Agent': 'Mozilla/5.0 PipatekaImages/9.0', 'Accept': 'image/avif,image/webp,image/jpeg,image/png,*/*'})
        raw = urlopen(request, timeout=25).read()
        if len(raw) < 3000 or len(raw) > 4_000_000:
            return brand, blend, None, source
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        image.thumbnail((360, 360))
        image.save(destination, 'JPEG', quality=88, optimize=True)
        return brand, blend, f'assets/tins/{destination.name}', source
    except Exception as exc:
        print('Image skipped', brand, blend, exc)
        return brand, blend, None, source


def load_blends():
    blends = []
    seen = set()

    # Conserva el catálogo consolidado ya publicado para que una fuente externa
    # lenta o temporalmente caída no haga desaparecer fichas existentes.
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            for product in previous.get('blends', []):
                name = product.get('nombre')
                brand = product.get('marca')
                if not name or not brand:
                    continue
                key = (str(brand).casefold(), str(name).casefold())
                if key in seen:
                    continue
                seen.add(key)
                blends.append(product.copy())
            print(f'Preserved consolidated catalogue: {len(blends)} rows')
        except Exception as exc:
            print('Previous catalogue warning:', exc)

    if SOURCE_CATALOG.exists():
        try:
            seed = json.loads(SOURCE_CATALOG.read_text(encoding='utf-8'))
            for product in seed.get('products', []):
                name = product.get('nombre')
                brand = product.get('marca')
                if not name or not brand:
                    continue
                key = (str(brand).casefold(), str(name).casefold())
                if key in seen:
                    continue
                seen.add(key)
                blends.append({
                    'id': product.get('id') or f'{slugify(brand)}-{slugify(name)}',
                    'nombre': name, 'marca': brand,
                    'resenas': int(product.get('numero_resenas') or 0),
                    'valoracion': product.get('valoracion_comunidad'),
                    'tipo': product.get('tipo') or '', 'pais': product.get('origen') or '',
                    'corte': product.get('corte') or '', 'fuerza': product.get('fuerza') or '',
                    'aromatizacion': product.get('aromatizacion') or '',
                    'fuente': 'Pipateka editorial', 'imagen': product.get('imagen'), 'imagen_fuente': product.get('imagen_fuente')
                })
        except Exception as exc:
            print('Seed warning:', exc)

    try:
        parser = H4Parser()
        parser.feed(fetch_url(TABACOTECA_URL))
        for title in parser.items:
            brand, name = split_brand_name(title)
            if not name:
                continue
            key = (brand.casefold(), name.casefold())
            if key in seen:
                continue
            seen.add(key)
            blends.append({
                'id': f'fp-{slugify(brand)}-{slugify(name)}', 'nombre': name, 'marca': brand,
                'resenas': 0, 'valoracion': None, 'tipo': '', 'pais': '', 'corte': '',
                'fuerza': '', 'aromatizacion': '', 'fuente': 'Fumeurs de Pipe · Tabacothèque',
                'imagen': None, 'imagen_fuente': None
            })
    except Exception as exc:
        print('Source warning:', exc)
    return blends

def main():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    blends = load_blends()
    official = official_mac_baren_images()
    pairs = []
    for blend in blends:
        if blend['marca'].casefold() == 'mac baren':
            pairs.append((blend['marca'], blend['nombre'], official_image_for_blend(blend['nombre'], official)))
    lookup = {(x['marca'], x['nombre']): x for x in blends}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        for brand, name, path, source in pool.map(download_image, pairs):
            lookup[(brand, name)]['imagen'] = path
            lookup[(brand, name)]['imagen_fuente'] = source

    blends.sort(key=lambda x: (x['marca'].casefold(), x['nombre'].casefold()))
    brand_counts = {}
    for blend in blends:
        brand_counts[blend['marca']] = brand_counts.get(blend['marca'], 0) + 1
    mac_baren_images = sum(1 for blend in blends if blend.get('marca', '').casefold() == 'mac baren' and blend.get('imagen'))
    payload = {
        'version': '9.0.0',
        'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'Pipateka + Fumeurs de Pipe Tabacothèque + imágenes oficiales Mac Baren',
        'source_url': TABACOTECA_URL,
        'source_scope': 'Biblioteca local Mac Baren con páginas actuales y archivo oficial; las imágenes descargadas se reutilizan localmente.',
        'total_blends_cargados': len(blends),
        'total_marcas_cargadas': len(brand_counts),
        'blends_con_imagen': sum(1 for blend in blends if blend.get('imagen')),
        'blends_mac_baren_con_imagen': mac_baren_images,
        'reference_tobaccoreviews_blends': 8582,
        'reference_tobaccoreviews_brands': 667,
        'blends': blends
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(blends)} blends across {len(brand_counts)} brands; Mac Baren images={mac_baren_images}')


if __name__ == '__main__':
    main()
