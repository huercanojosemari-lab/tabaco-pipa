import json
import time
from pathlib import Path

OUT=Path('data/catalogo-global.json')
SOURCE_CATALOG=Path('data/catalogo.json')
SOURCE_URL='https://www.tobaccoreviews.com/advanced-search/'

# The external index currently presents an access/age gate to automated GitHub runners.
# Keep Pages deployable by creating a clearly marked local fallback from the verified
# editorial seed catalogue. Never fabricate the missing worldwide rows.
try:
    data=json.loads(SOURCE_CATALOG.read_text(encoding='utf-8'))
except Exception as exc:
    print(f'Could not read {SOURCE_CATALOG}: {exc}')
    raise SystemExit(1)

products=data.get('products',[])
blends=[]
for p in products:
    blends.append({
        'id':p.get('id') or f"{p.get('marca','')}-{p.get('nombre','')}".strip(),
        'nombre':p.get('nombre') or '',
        'marca':p.get('marca') or '',
        'resenas':int(p.get('numero_resenas') or 0),
        'valoracion':p.get('valoracion_comunidad'),
        'tipo':p.get('tipo') or '',
        'pais':p.get('origen') or '',
        'corte':p.get('corte') or '',
        'fuerza':p.get('fuerza') or '',
        'aromatizacion':p.get('aromatizacion') or '',
    })
blends=[b for b in blends if b['nombre']]
blends.sort(key=lambda x:(x['nombre'].casefold(),x['id'].casefold()))

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({
    'version':'4.1.0',
    'updated':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
    'source':'Pipateka editorial seed catalogue',
    'source_url':SOURCE_URL,
    'source_scope':'Fallback local: no inventa las filas que no pueden consultarse desde GitHub Actions. La referencia pública de TobaccoReviews se conserva como objetivo del índice mundial.',
    'total_blends_referencia':len(blends),
    'complete_source_total_reference':8582,
    'blends':blends,
},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Wrote deployable fallback with {len(blends)} blends; worldwide source remains unavailable to automated runner.')
