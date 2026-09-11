import concurrent.futures
import html
import json
import math
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCE = 'https://www.tobaccoreviews.com/advanced-search/?pagenumber={}'
READER = 'https://r.jina.ai/http://www.tobaccoreviews.com/advanced-search/?pagenumber={}'
OUT = Path('data/catalogo-global.json')
FALLBACK_PAGES = 430
WORKERS = 8


def clean(value):
    value = html.unescape(value or '')
    value = re.sub(r'<[^>]+>', ' ', value)
    value = re.sub(r'\[[^\]]*\]\(([^)]+)\)', r'\1', value)
    return re.sub(r'\s+', ' ', value).strip()


def fetch_page(page):
    url = READER.format(page)
    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; PipatekaCatalog/2.0)',
            'Accept': 'text/plain,text/markdown;q=0.9,*/*;q=0.8',
        })
        with urlopen(req, timeout=40) as response:
            text = response.read().decode('utf-8', 'ignore')

        total_match = re.search(r'Displaying\s+[\d,]+\s*-\s*[\d,]+\s+of\s+([\d,]+)\s+Blends', text, re.I)
        total = int(total_match.group(1).replace(',', '')) if total_match else None

        parsed = []
        for raw in text.splitlines():
            line = raw.strip()
            if '/blend/' not in line:
                continue
            # Markdown reader output normally keeps the result as:
            # | [Brand-Blend](https://.../blend/123/slug/) | 513 | 2.55 | Aromatic |
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) < 4:
                continue
            link = re.search(r'\[([^\]]+)\]\((https?://[^)]+/blend/([^/)]+)/[^)]*)\)', cells[0], re.I)
            if not link:
                link = re.search(r'href=["\']([^"\']*/blend/([^"\']+))["\']', cells[0], re.I)
                if not link:
                    continue
                label = clean(cells[0])
                blend_id = link.group(2).strip('/')
            else:
                label = clean(link.group(1))
                blend_id = link.group(3).strip('/')

            name = label
            reviews_match = re.search(r'\d[\d,]*', cells[1])
            rating_match = re.search(r'\d+(?:\.\d+)?', cells[2])
            reviews = int(reviews_match.group(0).replace(',', '')) if reviews_match else 0
            rating = float(rating_match.group(0)) if rating_match else None
            blend_type = clean(cells[3])
            if not name or name.lower() == 'name':
                continue

            parsed.append({
                'id': blend_id,
                'nombre': name,
                'resenas': reviews,
                'valoracion': rating,
                'tipo': blend_type,
            })

        return page, total, parsed, None
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return page, None, [], str(exc)


# Read the first page separately so the number of pages follows the live count.
first_page, total, first_rows, first_error = fetch_page(1)
if first_error:
    print(f'First page reader error: {first_error}')
    raise SystemExit(1)

if not total:
    total = FALLBACK_PAGES * 20

total_pages = max(1, math.ceil(total / 20))
print(f'Source reports {total} blends across {total_pages} pages')

rows = list(first_rows)
errors = []

pages = range(2, total_pages + 1)
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = [pool.submit(fetch_page, page) for page in pages]
    for completed, future in enumerate(concurrent.futures.as_completed(futures), 2):
        page, page_total, page_rows, error = future.result()
        rows.extend(page_rows)
        if error:
            errors.append((page, error))
        if completed % 10 == 0 or completed >= total_pages:
            print(f'pages {completed}/{total_pages}: {len(rows)} rows; errors={len(errors)}')

unique = {row['id']: row for row in rows if row.get('id') and row.get('nombre')}
blends = sorted(unique.values(), key=lambda x: (x['nombre'].casefold(), x['id'].casefold()))

expected_min = max(8000, int(total * 0.98))
if len(blends) < expected_min:
    print(f'ABORT: only {len(blends)} unique blends fetched; expected at least {expected_min}.')
    raise SystemExit(1)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    'version': '2.0.0',
    'updated': time.strftime('%Y-%m-%d'),
    'source': 'TobaccoReviews',
    'source_scope': 'Índice público de mezclas; no se reproducen textos de reseñas.',
    'source_url': 'https://www.tobaccoreviews.com/advanced-search/',
    'total_blends_referencia': len(blends),
    'total_paginas_fuente': total_pages,
    'blends': blends,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Wrote {len(blends)} blends to {OUT}; source errors={len(errors)}')
