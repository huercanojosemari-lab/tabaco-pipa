import json
import time
from pathlib import Path

CATALOG = Path('data/catalogo-global.json')
OUT = Path('data/marcas.json')


def main():
    if not CATALOG.exists():
        raise SystemExit('data/catalogo-global.json no existe; ejecuta build-catalog.py primero.')

    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    counts = {}
    for blend in data.get('blends', []):
        brand = str(blend.get('marca') or '').strip()
        if not brand:
            continue
        key = brand.casefold()
        if key not in counts:
            counts[key] = {'marca': brand, 'blends': 0, 'resenas': 0}
        counts[key]['blends'] += 1
        counts[key]['resenas'] += int(blend.get('resenas') or 0)

    brands = sorted(counts.values(), key=lambda x: x['marca'].casefold())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        'version': '8.0.0',
        'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': data.get('source', 'Pipateka catalog'),
        'source_scope': 'Marcas derivadas de las mezclas realmente cargadas en el índice local; no representa disponibilidad comercial.',
        'total_marcas_cargadas': len(brands),
        'total_blends_cargados': len(data.get('blends', [])),
        'total_marcas_referencia': data.get('reference_tobaccoreviews_brands', 667),
        'total_blends_referencia': data.get('reference_tobaccoreviews_blends', 8582),
        'marcas': brands,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(brands)} loaded brands from {len(data.get("blends", []))} blend rows')


if __name__ == '__main__':
    main()
