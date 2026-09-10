import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

BASE = 'https://www.tobaccoreviews.com/advanced-search/?pagenumber={}'
OUT = Path('data/catalogo-global.json')
TOTAL_PAGES = 430
WORKERS = 12

PATTERN = re.compile(
    r'<a[^>]*href="/blend/([^\"]+)"[^>]*>\s*(.*?)\s*</a>\s*</td>\s*'
    r'<td[^>]*>\s*([0-9,]+)\s*</td>\s*'
    r'<td[^>]*>\s*([0-9.\-]+)\s*</td>\s*'
    r'<td[^>]*>\s*(.*?)\s*</td>',
    re.S | re.I,
)


def clean(value):
    value = re.sub(r'<[^>]+>', '', value)
    value = (value.replace('&amp;', '&').replace('&quot;', '"')
                  .replace('&#39;', "'").replace('&lt;', '<').replace('&gt;', '>'))
    return re.sub(r'\s+', ' ', value).strip()


def fetch_page(page):
    req = Request(BASE.format(page), headers={
        'User-Agent': 'Mozilla/5.0 Pipateka catalog builder',
        'Accept': 'text/html,application/xhtml+xml',
    })
    for attempt in range(3):
        try:
            html = urlopen(req, timeout=12).read().decode('utf-8', 'ignore')
            rows = []
            for slug, name, reviews, rating, blend_type in PATTERN.findall(html):
                rows.append({
                    'id': slug.strip('/'),
                    'nombre': clean(name),
                    'resenas': int(reviews.replace(',', '')),
                    'valoracion': None if rating.strip() in ('', '-') else float(rating),
                    'tipo': clean(blend_type),
                })
            return page, rows, None
        except Exception as exc:
            if attempt == 2:
                return page, [], str(exc)
            time.sleep(0.5 * (attempt + 1))


rows = []
completed = 0
with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = [pool.submit(fetch_page, page) for page in range(1, TOTAL_PAGES + 1)]
    for future in as_completed(futures):
        page, page_rows, error = future.result()
        completed += 1
        rows.extend(page_rows)
        if error:
            print(f'page {page}: {error}')
        if completed % 20 == 0 or completed == TOTAL_PAGES:
            print(f'pages {completed}/{TOTAL_PAGES}: {len(rows)} rows')

unique = {}
for row in rows:
    unique[row['id']] = row
blends = sorted(unique.values(), key=lambda x: (x['nombre'].casefold(), x['id'].casefold()))

if len(blends) >= 8000:
    OUT.write_text(json.dumps({
        'version': '1.1.0',
        'updated': time.strftime('%Y-%m-%d'),
        'source': 'TobaccoReviews',
        'source_scope': 'Índice público de mezclas; no se reproducen textos de reseñas.',
        'total_blends_referencia': len(blends),
        'blends': blends
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(blends)} blends to {OUT}')
else:
    print(f'Only {len(blends)} blends fetched; keeping existing catalog if present')
    raise SystemExit(0)
