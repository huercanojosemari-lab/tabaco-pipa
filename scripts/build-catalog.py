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
OUT = Path('data/catalogo-global.json')
WORKERS = 10


def clean(value):
    value = html.unescape(value or '')
    value = re.sub(r'<script\b[^>]*>.*?</script>', ' ', value, flags=re.I | re.S)
    value = re.sub(r'<style\b[^>]*>.*?</style>', ' ', value, flags=re.I | re.S)
    value = re.sub(r'<[^>]+>', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def page_html(page):
    url = SOURCE.format(page)
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; PipatekaCatalog/3.0)',
        'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.8',
    })
    with urlopen(req, timeout=40) as response:
        return response.read().decode('utf-8', 'ignore')


def parse_page(page, text):
    total_match = re.search(r'Displaying\s+[\d,]+\s*-\s*[\d,]+\s+of\s+([\d,]+)\s+Blends', text, re.I)
    total = int(total_match.group(1).replace(',', '')) if total_match else None
    parsed = []

    rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', text, flags=re.I | re.S)
    for row in rows:
        link = re.search(r'(?:href|data-href)=[\"\']([^\"\']*/blend/([^/?\"\']+)(?:/[^\"\']*)?)[\"\']', row, flags=re.I)
        if not link:
            continue
        cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row, flags=re.I | re.S)
        if len(cells) < 2:
            continue
        name = clean(re.sub(r'<a\b[^>]*>.*?</a>', lambda m: clean(m.group(0)), cells[0], flags=re.I | re.S))
        if not name:
            # Prefer visible anchor label when table cell contains nested markup.
            a = re.search(r'<a\b[^>]*>(.*?)</a>', cells[0], flags=re.I | re.S)
            name = clean(a.group(1)) if a else clean(cells[0])
        numbers = [clean(c) for c in cells[1:]]
        reviews_match = re.search(r'\d[\d,]*', numbers[0] if numbers else '')
        rating_match = re.search(r'\d+(?:\.\d+)?', numbers[1] if len(numbers) > 1 else '')
        reviews = int(reviews_match.group(0).replace(',', '')) if reviews_match else 0
        rating = float(rating_match.group(0)) if rating_match else None
        blend_type = clean(cells[3]) if len(cells) >= 4 else ''
        if name and name.lower() != 'name':
            parsed.append({
                'id': link.group(2).strip('/'),
                'nombre': name,
                'resenas': reviews,
                'valoracion': rating,
                'tipo': blend_type,
            })

    # Fallback for alternative markup: inspect lines containing /blend/.
    if not parsed:
        for line in text.splitlines():
            if '/blend/' not in line:
                continue
            m = re.search(r'href=[\"\']([^\"\']*/blend/([^/?\"\']+))', line, re.I)
            if not m:
                continue
            label = re.search(r'<a\b[^>]*>(.*?)</a>', line, re.I | re.S)
            name = clean(label.group(1)) if label else clean(line)
            nums = re.findall(r'\b\d[\d,]*(?:\.\d+)?\b', clean(line))
            reviews = int(nums[-3].replace(',', '')) if len(nums) >= 3 else 0
            rating = float(nums[-2]) if len(nums) >= 2 and '.' in nums[-2] else None
            if name and name.lower() != 'name':
                parsed.append({'id': m.group(2).strip('/'), 'nombre': name, 'resenas': reviews, 'valoracion': rating, 'tipo': ''})

    return total, parsed


def fetch_page(page):
    try:
        text = page_html(page)
        total, parsed = parse_page(page, text)
        return page, total, parsed, None
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return page, None, [], str(exc)


_, total, first_rows, first_error = fetch_page(1)
if first_error:
    print(f'First page error: {first_error}')
    raise SystemExit(1)
if not total:
    total = 8582

total_pages = max(1, math.ceil(total / 20))
print(f'Source reports {total} blends across {total_pages} pages')

rows = list(first_rows)
errors = []
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = [pool.submit(fetch_page, page) for page in range(2, total_pages + 1)]
    done = 1
    for future in concurrent.futures.as_completed(futures):
        done += 1
        page, page_total, page_rows, error = future.result()
        rows.extend(page_rows)
        if error:
            errors.append((page, error))
        if done % 25 == 0 or done == total_pages:
            print(f'pages {done}/{total_pages}: {len(rows)} rows; errors={len(errors)}')

unique = {row['id']: row for row in rows if row.get('id') and row.get('nombre')}
blends = sorted(unique.values(), key=lambda x: (x['nombre'].casefold(), x['id'].casefold()))
expected_min = max(8000, int(total * 0.98))
if len(blends) < expected_min:
    print(f'ABORT: only {len(blends)} unique blends fetched; expected at least {expected_min}.')
    raise SystemExit(1)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    'version': '3.0.0',
    'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'source': 'TobaccoReviews',
    'source_scope': 'Índice público de mezclas; no se reproducen textos de reseñas.',
    'source_url': 'https://www.tobaccoreviews.com/advanced-search/',
    'total_blends_referencia': len(blends),
    'total_paginas_fuente': total_pages,
    'blends': blends,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Wrote {len(blends)} blends to {OUT}; source errors={len(errors)}')
