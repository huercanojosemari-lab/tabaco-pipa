import io, json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from PIL import Image

CATALOG = Path('data/catalogo-global.json')
IMAGE_DIR = Path('assets/tins')
API = 'https://mac-baren.com/wp-json/wp/v2/media?search={}&per_page=20'


def slugify(value):
    return re.sub(r'[^a-z0-9]+', '-', str(value).casefold()).strip('-')


def fetch_json(url):
    raw = urlopen(Request(url, headers={'User-Agent': 'PipatekaCatalog/9.0'}), timeout=30).read()
    return json.loads(raw.decode('utf-8-sig'))


def media_for(name):
    try:
        items = fetch_json(API.format(quote_plus(name)))
        exact = slugify(name)
        ranked = []
        for item in items:
            src = item.get('source_url') or ''
            if '/wp-content/uploads/' not in src:
                continue
            low = src.casefold()
            if any(x in low for x in ('logo', 'icon', 'avatar', 'banner')):
                continue
            title = str(item.get('slug') or item.get('title', {}).get('rendered') or '')
            score = 0
            if exact and exact in slugify(title): score += 5
            if exact and exact in slugify(src): score += 3
            ranked.append((score, src))
        if ranked:
            ranked.sort(reverse=True)
            return ranked[0][1]
    except Exception as exc:
        print('media search skipped', name, exc)
    return None


def download(name, source):
    dest = IMAGE_DIR / f'mac-baren--{slugify(name)}.jpg'
    if dest.exists() and dest.stat().st_size > 3000:
        return name, f'assets/tins/{dest.name}', 'local-cache'
    if not source:
        return name, None, None
    try:
        raw = urlopen(Request(source, headers={'User-Agent': 'PipatekaCatalog/9.0', 'Accept': 'image/jpeg,image/png,image/webp,*/*'}), timeout=30).read()
        if len(raw) < 3000 or len(raw) > 5_000_000:
            return name, None, source
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        im.thumbnail((500, 500))
        im.save(dest, 'JPEG', quality=90, optimize=True)
        return name, f'assets/tins/{dest.name}', source
    except Exception as exc:
        print('download skipped', name, exc)
        return name, None, source


def main():
    data = json.loads(CATALOG.read_text(encoding='utf-8-sig'))
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    targets = [b for b in data.get('blends', []) if str(b.get('marca', '')).casefold() == 'mac baren' and not b.get('imagen')]
    sources = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(media_for, b['nombre']): b['nombre'] for b in targets}
        for f in as_completed(futures):
            name = futures[f]
            sources[name] = f.result()
    lookup = {(b.get('marca'), b.get('nombre')): b for b in data.get('blends', [])}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(download, name, src): name for name, src in sources.items()}
        for f in as_completed(futures):
            name, path, source = f.result()
            b = lookup.get(('Mac Baren', name))
            if b and path:
                b['imagen'] = path
                b['imagen_fuente'] = source
    count = sum(1 for b in data.get('blends', []) if str(b.get('marca', '')).casefold() == 'mac baren' and b.get('imagen'))
    data['blends_con_imagen'] = sum(1 for b in data.get('blends', []) if b.get('imagen'))
    data['blends_mac_baren_con_imagen'] = count
    data['version'] = '9.0.1'
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Mac Baren image enrichment: {count} fichas con imagen')


if __name__ == '__main__':
    main()
