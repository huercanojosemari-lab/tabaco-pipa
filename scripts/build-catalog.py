import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path('data/catalogo-global.json')
SOURCE_CATALOG = Path('data/catalogo.json')
TABACOTECA_URL = 'https://www.fumeursdepipe.net/tabacotheque.php'

# Marcas/prefijos observados en la fuente de la Tabacothèque. Se usan para separar
# el nombre de la marca del nombre de la mezcla sin copiar textos de reseñas.
BRAND_PREFIXES = [
    '4noggins','A&C Petersen','Altadis','Amphora','Arango','Ashton','Astleys','Balkan Sobranie',
    'Barling','Bell’s','Bell\'s','Bentley','Besson','Bjarne','Breizh Tobacco','Brigham','Butera',
    'Capstan','Chacom','Charles Fairmorn','Comoy\'s of London','Cornell & Diehl','Dan Pipe',
    'Dan Tobacco','Daughters & Ryan','Davidoff','Drucquer & Sons','Dunhill','E. Hoffman Company',
    'Edgeworth','Ente Tabacchi Italiani','Erik Stokkebye','Erinmore','Esoterica','Flandria',
    'Fribourg & Treyer','Friedman & Pease','G. De Graaff & Sons','G.L. Pease','Gallaher','Gauntleys',
    'Gawith & Hoggarth & Co','Gawith, Hoggarth & Co','Germain’s','Germain\'s','Gladora Tobacco',
    'Half & Half','Hans Schürch','Hearth & Home','Hermit','Heupink & Bloemen','HU Tobacco',
    'Ilsteds','Imperial Tobacco','J.B. Vinche','J.F. Germain & Son','James J. Fox','Jean-Paul Couvert',
    'John Aylesbury','John Cotton','John Patton','John Sinclair','Joseph Martin','Kendal Tobacco',
    'Kohlhase, Kopp und Co','L.J. Peretti and Co.','Lane Limited','Larsen','Low Country','Mac Baren',
    'McClelland','McLintock','Mélange maison','Motzek','Murray & Sons','Murray’s','Murray\'s',
    'New York Pipe Club','Newminster','Ogden’s of Liverpool','Ogden\'s of Liverpool','Olaf Poulsson',
    'Orlik','Paul Olsen','Peter Stokkebye','Peterson','Pfeifen Huber','Pfeifen Schneiderwind',
    'Pfeifen-Studio Mühlhausen','Pfeifendepot','Pipesandcigars.com','Pipeworks & Wilke','Planta',
    'Poschl Tabak','Poul Stanwell','Rattray’s','Rattray\'s','Reiner','Richmond','Robert Lewis',
    'Robert McConnell','Samuel Gawith','Scandinavian Tobacco Group','Schneiderwind','Seattle Pipe Club',
    'Smoker’s Haven','Smoker\'s Haven','Solani','St-Group Assens','Standard Tobacco Company of Pennsylvania',
    'Sutliff Tobacco Company','Synjeco','Tabacos Wilder','Tabak Träber','Tabakhaus Falkum','TAK',
    'Tambolaka Natural Tobaccos','Timm','Torben Dansk','Toscani','Tour du Monde des Anglais, en 80 blends',
    'Tranter Havana House','Troost','V.B','Vauen','Villiger','Vincent Manil','Wessex','Windels','Ramback'
]
BRAND_PREFIXES = sorted(set(BRAND_PREFIXES), key=lambda x: (-len(x), x.casefold()))


def clean_text(value: str) -> str:
    value = html.unescape(value or '')
    value = re.sub(r'\s+', ' ', value)
    return value.strip(' \t\r\n-')


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
            text = clean_text(''.join(self.buf))
            if text:
                self.items.append(text)
            self.in_h4 = False
            self.buf = []

    def handle_data(self, data):
        if self.in_h4:
            self.buf.append(data)


def fetch_source() -> str:
    req = Request(
        TABACOTECA_URL,
        headers={
            'User-Agent': 'Mozilla/5.0 PipatekaCatalog/1.0',
            'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
        },
    )
    return urlopen(req, timeout=45).read().decode('utf-8', 'ignore')


def split_brand_name(text: str):
    for brand in BRAND_PREFIXES:
        if text.casefold().startswith(brand.casefold() + ' '):
            return brand, text[len(brand):].strip()
        if text.casefold() == brand.casefold():
            return brand, ''
    # Fallback conservador: primera palabra como marca para registros no reconocidos.
    parts = text.split(' ', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return text, ''


def slugify(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '-', value.casefold()).strip('-')
    return value or 'blend'


def main():
    blends = []
    seen = set()

    # Conserva los registros editoriales propios y verificados de Pipateka.
    try:
        seed = json.loads(SOURCE_CATALOG.read_text(encoding='utf-8'))
        for p in seed.get('products', []):
            if not p.get('nombre') or not p.get('marca'):
                continue
            key = (p.get('marca', '').casefold(), p.get('nombre', '').casefold())
            if key in seen:
                continue
            seen.add(key)
            blends.append({
                'id': p.get('id') or f"{slugify(p['marca'])}-{slugify(p['nombre'])}",
                'nombre': p['nombre'],
                'marca': p['marca'],
                'resenas': int(p.get('numero_resenas') or 0),
                'valoracion': p.get('valoracion_comunidad'),
                'tipo': p.get('tipo') or '',
                'pais': p.get('origen') or '',
                'corte': p.get('corte') or '',
                'fuerza': p.get('fuerza') or '',
                'aromatizacion': p.get('aromatizacion') or '',
                'fuente': 'Pipateka editorial',
            })
    except Exception as exc:
        print(f'Warning: could not read seed catalog: {exc}')

    # Importa el índice de la Tabacothèque: nombres individuales de mezclas y marcas.
    imported = 0
    try:
        parser = H4Parser()
        parser.feed(fetch_source())
        for title in parser.items:
            brand, blend_name = split_brand_name(title)
            if not blend_name:
                continue
            key = (brand.casefold(), blend_name.casefold())
            if key in seen:
                continue
            seen.add(key)
            imported += 1
            blends.append({
                'id': f"fp-{slugify(brand)}-{slugify(blend_name)}",
                'nombre': blend_name,
                'marca': brand,
                'resenas': 0,
                'valoracion': None,
                'tipo': '',
                'pais': '',
                'corte': '',
                'fuerza': '',
                'aromatizacion': '',
                'fuente': 'Fumeurs de Pipe · Tabacothèque',
            })
        print(f'Imported {imported} additional blends from Tabacothèque')
    except Exception as exc:
        print(f'Warning: source import failed: {exc}')

    blends.sort(key=lambda x: (x['marca'].casefold(), x['nombre'].casefold()))

    # Agrupa las marcas realmente cargadas. Los recuentos son filas del índice local,
    # no equivalen automáticamente a disponibilidad comercial actual.
    brand_counts = {}
    for b in blends:
        brand_counts[b['marca']] = brand_counts.get(b['marca'], 0) + 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'version': '5.0.0',
        'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'Pipateka + Fumeurs de Pipe Tabacothèque',
        'source_url': TABACOTECA_URL,
        'source_scope': 'Índice de nombres de mezclas y marcas. Pipateka no reproduce textos de reseñas ni afirma disponibilidad comercial.',
        'total_blends_cargados': len(blends),
        'total_marcas_cargadas': len(brand_counts),
        'reference_tobaccoreviews_blends': 8582,
        'reference_tobaccoreviews_brands': 667,
        'blends': blends,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Wrote {len(blends)} blends across {len(brand_counts)} brands')


if __name__ == '__main__':
    main()
