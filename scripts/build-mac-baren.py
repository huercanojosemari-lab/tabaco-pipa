import json
import re
from pathlib import Path
from unicodedata import normalize

SOURCE = Path('data/mac-baren.json')
GLOBAL = Path('data/catalogo-global.json')
OUT = Path('data/mac-baren.json')

TYPE_TEXT = {
    'Aromatic': 'mezcla aromática, donde el tratamiento de la hoja acompaña al carácter natural del tabaco.',
    'Burley Based': 'mezcla con protagonismo de Burley, normalmente asociada a matices tostados, terrosos y de fruto seco.',
    'English': 'mezcla de orientación inglesa, con mayor peso de notas ahumadas, terrosas y especiadas.',
    'Balkan': 'mezcla de perfil profundo y especiado, pensada para quienes disfrutan de una mayor complejidad de hojas.',
    'Virginia/Perique': 'mezcla basada en el contraste entre el dulzor de Virginia y el carácter especiado de Perique.',
    'Virginia/Burley': 'mezcla que combina el dulzor de Virginia con el cuerpo más terroso y tostado del Burley.',
    'Straight Virginia': 'mezcla centrada en Virginia, con énfasis en sus matices dulces, vegetales, cítricos o de fruta madura.',
    'Virginia Based': 'mezcla con Virginia como eje principal, buscando equilibrio entre dulzor natural y carácter de hoja.',
    'Virginia/Latakia': 'mezcla que contrapone el dulzor de Virginia con el carácter ahumado de Latakia.',
    'Cavendish Based': 'mezcla de perfil suave y redondo en la que el Cavendish tiene un papel protagonista.',
    'Cigar Leaf Based': 'mezcla con presencia de hoja de tipo cigarro y un carácter más oscuro y robusto.',
    'Scottish': 'mezcla de tradición escocesa, construida para ofrecer capas de sabor y un perfil reconocible.',
    'Other': 'mezcla de perfil particular que no encaja de forma limpia en una sola familia.',
}


def key(s):
    s = normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().casefold()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def base_description(name, typ):
    text = TYPE_TEXT.get(typ, 'mezcla de perfil propio dentro del catálogo de Mac Baren.')
    return f'{name} es una mezcla de Mac Baren. {text} Esta ficha editorial resume su posición en el catálogo y separa los datos de referencia de la valoración de la comunidad.'


def community_review(name, typ, rating, reviews):
    if rating is None:
        reception = 'todavía no dispone de una media comunitaria suficientemente representativa'
    elif rating >= 3.5:
        reception = 'recibe una acogida especialmente favorable'
    elif rating >= 3:
        reception = 'recibe una acogida generalmente positiva'
    elif rating >= 2.5:
        reception = 'divide algo más las opiniones, aunque mantiene una base de valoraciones favorable'
    else:
        reception = 'presenta una recepción más irregular y claramente dependiente de las preferencias personales'
    family = {
        'Aromatic':'los comentarios suelen girar alrededor del equilibrio entre el aroma añadido y la hoja base',
        'Burley Based':'los comentarios suelen fijarse en el cuerpo, los matices tostados y el carácter del Burley',
        'English':'los comentarios suelen valorar la profundidad, el humo y la evolución del perfil',
        'Balkan':'los comentarios suelen centrarse en la complejidad, las especias y el carácter de las hojas oscuras',
        'Virginia/Perique':'los comentarios suelen contrastar el dulzor de Virginia con la intensidad especiada de Perique',
        'Virginia/Burley':'los comentarios suelen valorar el equilibrio entre dulzor, cuerpo y notas de fruto seco',
        'Straight Virginia':'los comentarios suelen centrarse en el dulzor natural y la evolución de la Virginia',
        'Virginia Based':'los comentarios suelen valorar el carácter de Virginia y su equilibrio general',
        'Virginia/Latakia':'los comentarios suelen destacar el contraste entre dulzor y notas ahumadas',
        'Cavendish Based':'los comentarios suelen prestar atención a suavidad, dulzor y comportamiento aromático',
        'Cigar Leaf Based':'los comentarios suelen destacar el carácter oscuro y más contundente',
        'Scottish':'los comentarios suelen valorar la mezcla de hojas y la complejidad del conjunto',
        'Other':'los comentarios reflejan un perfil particular que depende mucho del gusto del fumador',
    }.get(typ, 'los comentarios reflejan opiniones variadas sobre su perfil')
    score = 'sin media disponible' if rating is None else f'{float(rating):.2f}/4'
    return f'Reseña Pipateka: {reception}. {family}. En conjunto, la conversación comunitaria ofrece una impresión de {"perfil bien definido" if rating and rating >= 3 else "perfil con opiniones más divididas"}. Referencia consultada: {reviews} reseñas y media {score}. Esta reseña es una síntesis editorial original y no reproduce literalmente opiniones de terceros.'


def main():
    raw = json.loads(SOURCE.read_text(encoding='utf-8'))
    if isinstance(raw, str):
        raw = json.loads(raw)
    original = raw.get('blends', [])
    global_rows = []
    if GLOBAL.exists():
        data = json.loads(GLOBAL.read_text(encoding='utf-8'))
        global_rows = [b for b in data.get('blends', []) if str(b.get('marca','')).casefold() == 'mac baren']
    image_by_name = {key(b.get('nombre')): b for b in global_rows}
    result = []
    seen = set()
    for b in original:
        name = str(b.get('nombre','')).strip()
        if not name or key(name) in seen: continue
        seen.add(key(name))
        match = image_by_name.get(key(name), {})
        typ = b.get('tipo') or match.get('tipo') or ''
        rating = b.get('valoracion')
        reviews = int(b.get('resenas') or 0)
        row = {
            'nombre': name,
            'marca': 'Mac Baren',
            'tipo': typ,
            'valoracion': rating,
            'resenas': reviews,
            'imagen': match.get('imagen'),
            'imagen_fuente': match.get('imagen_fuente'),
            'descripcion': base_description(name, typ),
            'reseña_pipateka': community_review(name, typ, rating, reviews),
            'fuente_datos': 'TobaccoReviews + Pipateka editorial',
            'fuente_datos_url': 'https://www.tobaccoreviews.com/brand/36/mac-baren/'
        }
        result.append(row)
    result.sort(key=lambda x: key(x['nombre']))
    payload = {
        'version': '2.0.0',
        'marca': 'Mac Baren',
        'actualizado': __import__('datetime').datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'fuente': 'TobaccoReviews + Pipateka editorial',
        'fuente_url': 'https://www.tobaccoreviews.com/brand/36/mac-baren/',
        'nota': 'Las descripciones y reseñas Pipateka son síntesis editoriales originales. No reproducen literalmente reseñas de terceros.',
        'total_blends': len(result),
        'blends_con_imagen': sum(1 for x in result if x.get('imagen')),
        'blends': result
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Mac Baren: {len(result)} fichas; imágenes locales: {payload["blends_con_imagen"]}')


if __name__ == '__main__': main()
