import concurrent.futures
import html
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = 'https://www.tobaccoreviews.com/advanced-search/?pagenumber={}'
OUT = Path('data/catalogo-global.json')
TOTAL_PAGES = 430
WORKERS = 12

def fetch_page(page):
    try:
        req = Request(BASE.format(page), headers={'User-Agent': 'Mozilla/5.0 (compatible; PipatekaCatalog/1.0)', 'Accept': 'text/html,application/xhtml+xml'})
        with urlopen(req, timeout=12) as response:
            text = response.read().decode('utf-8', 'ignore')
        matches = re.findall(r'<a[^>]*href=["\']/blend/([^"\']+)["\'][^>]*>\s*(.*?)\s*</a>\s*</td>\s*<td[^>]*>\s*([0-9,]+)\s*</td>\s*<td[^>]*>\s*([0-9.\-]+)\s*</td>\s*<td[^>]*>\s*(.*?)\s*</td>', text, re.S | re.I)
        clean = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).strip()
        return page, [{'id': slug.strip('/'), 'nombre': clean(name), 'resenas': int(reviews.replace(',', '')), 'valoracion': None if rating.strip() in ('', '-') else float(rating), 'tipo': clean(blend_type)} for slug, name, reviews, rating, blend_type in matches], None
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return page, [], str(exc)

rows, errors = [], []
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = [pool.submit(fetch_page, page) for page in range(1, TOTAL_PAGES + 1)]
    completed = 0
    for future in concurrent.futures.as_completed(futures):
        page, page_rows, error = future.result()
        rows.extend(page_rows)
        completed += 1
        if error: errors.append((page, error))
        if completed % 10 == 0 or completed == TOTAL_PAGES: print(f'pages {completed}/{TOTAL_PAGES}: {len(rows)} rows; errors={len(errors)}')

unique = {row['id']: row for row in rows if row.get('id') and row.get('nombre')}
blends = sorted(unique.values(), key=lambda x: (x['nombre'].casefold(), x['id'].casefold()))
if len(blends) < 8000:
    print(f'ABORT: only {len(blends)} blends fetched; refusing to publish a partial catalog.')
    raise SystemExit(1)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({'version': '1.1.0', 'updated': time.strftime('%Y-%m-%d'), 'source': 'TobaccoReviews', 'source_scope': 'Índice público de mezclas; no se reproducen textos de reseñas.', 'total_blends_referencia': len(blends), 'total_paginas_fuente': TOTAL_PAGES, 'blends': blends}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Wrote {len(blends)} blends to {OUT}; source errors={len(errors)}')
