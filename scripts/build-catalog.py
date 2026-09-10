import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = 'https://www.tobaccoreviews.com/advanced-search/?pagenumber={}'
OUT = Path('data/catalogo-global.json')
TOTAL_PAGES = 430

rows = []
for page in range(1, TOTAL_PAGES + 1):
    try:
        req = Request(BASE.format(page), headers={'User-Agent': 'Mozilla/5.0 Pipateka catalog builder'})
        html = urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
        # Public table rows expose the blend link followed by review count, rating and type.
        matches = re.findall(
            r'<a[^>]*href="/blend/([^\"]+)"[^>]*>\s*(.*?)\s*</a>\s*</td>\s*'
            r'<td[^>]*>\s*([0-9,]+)\s*</td>\s*'
            r'<td[^>]*>\s*([0-9.\-]+)\s*</td>\s*'
            r'<td[^>]*>\s*(.*?)\s*</td>',
            html, re.S | re.I
        )
        for slug, name, reviews, rating, blend_type in matches:
            clean = lambda s: re.sub(r'<[^>]+>', '', s).replace('&amp;', '&').strip()
            rows.append({
                'id': slug.strip('/'),
                'nombre': clean(name),
                'resenas': int(reviews.replace(',', '')),
                'valoracion': None if rating.strip() in ('', '-') else float(rating),
                'tipo': clean(blend_type),
            })
        if page % 10 == 0:
            print(f'page {page}/{TOTAL_PAGES}: {len(rows)} blends')
        time.sleep(0.12)
    except Exception as exc:
        print(f'page {page}: {exc}')

unique = {}
for row in rows:
    unique[row['id']] = row
blends = sorted(unique.values(), key=lambda x: (x['nombre'].casefold(), x['id'].casefold()))

if len(blends) >= 8000:
    OUT.write_text(json.dumps({
        'version': '1.0.0',
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
