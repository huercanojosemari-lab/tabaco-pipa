import concurrent.futures
import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import random

CATALOG = Path("data/catalogo-global.json")
CACHE = Path("data/tobaccoreviews-enrichment.json")

STRENGTH_SCORES = {
    "extremely mild": 1, "very mild": 1, "mild": 1.5, "mild to medium": 2,
    "medium": 3, "medium to strong": 4, "strong": 4.5, "very strong": 5,
    "overwhelming": 5,
}

CUT_HINTS = [
    ("ready rubbed", "Ready Rubbed"), ("broken flake", "Broken Flake"),
    ("flake", "Flake"), ("plug", "Plug"), ("cube", "Cube"),
    ("curly", "Curly Cut"), ("rope", "Rope"), ("ribbon", "Ribbon"),
    ("shag", "Shag"), ("kake", "Cake"), ("cake", "Cake"),
    ("mixture", "Mixture"), ("roll cake", "Roll Cake"), ("twist", "Twist"),
]

def clean(v):
    return re.sub(r"\\s+", " ", html.unescape(v or "")).strip()

def fetch(url, timeout=8):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 PipatekaEnricher/1.0", "Accept": "text/html,application/xhtml+xml"})
    return urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag_stack=[]
        self.h1=[]
        self.ps=[]
        self.trs=[]
        self.current=[]
        self.current_cells=[]
        self.in_td=False
        self.in_th=False
        self.in_h1=False
        self.in_p=False
    def handle_starttag(self, tag, attrs):
        t=tag.lower(); self.tag_stack.append(t)
        if t=="h1": self.in_h1=True; self.current=[]
        elif t=="p": self.in_p=True; self.current=[]
        elif t=="tr": self.current_cells=[]
        elif t in ("td","th"):
            self.current=[]; self.in_td=(t=="td"); self.in_th=(t=="th")
    def handle_endtag(self, tag):
        t=tag.lower()
        if t=="h1" and self.in_h1:
            val=clean(" ".join(self.current))
            if val: self.h1.append(val)
            self.in_h1=False
        elif t=="p" and self.in_p:
            val=clean(" ".join(self.current))
            if val: self.ps.append(val)
            self.in_p=False
        elif t in ("td","th") and (self.in_td or self.in_th):
            self.current_cells.append(clean(" ".join(self.current)))
            self.current=[]; self.in_td=False; self.in_th=False
        elif t=="tr":
            if self.current_cells:
                self.trs.append(self.current_cells)
            self.current_cells=[]
        if self.tag_stack:
            self.tag_stack.pop()
    def handle_data(self,data):
        if self.in_h1 or self.in_p or self.in_td or self.in_th:
            self.current.append(data)

def parse_page(source):
    parser=PageParser(); parser.feed(source)
    details={}
    for cells in parser.trs:
        if len(cells)>=2:
            key=clean(cells[0]).casefold()
            val=clean(" ".join(cells[1:]))
            if key and val and key not in details: details[key]=val
    plain=re.sub(r"<script[^>]*>.*?</script>", " ", source, flags=re.I|re.S)
    plain=re.sub(r"<style[^>]*>.*?</style>", " ", plain, flags=re.I|re.S)
    plain=clean(re.sub(r"<[^>]+>", "\n", plain))
    def profile(label, stop):
        m=re.search(rf"{re.escape(label)}\\s+(.+?)\\s+{re.escape(stop)}", plain, flags=re.I|re.S)
        return clean(m.group(1)) if m else ""
    return {
        "titulo": parser.h1[0] if parser.h1 else "",
        "descripcion": next((p for p in parser.ps if len(p)>=45 and "Please login" not in p and "Average Rating" not in p), ""),
        "brand": details.get("brand",""),
        "blended_by": details.get("blended by",""),
        "manufactured_by": details.get("manufactured by",""),
        "blend_type": details.get("blend type",""),
        "contents": details.get("contents",""),
        "flavoring": details.get("flavoring",""),
        "cut": details.get("cut",""),
        "packaging": details.get("packaging",""),
        "country": details.get("country",""),
        "production": details.get("production",""),
        "strength": profile("Strength", "Extremely Mild \\-> Overwhelming"),
        "profile_flavoring": profile("Flavoring", "None Detected \\-> Extra Strong"),
        "room_note": profile("Room Note", "Unnoticeable \\-> Overwhelming"),
        "taste": profile("Taste", "Extremely Mild \\(Flat\\) \\-> Overwhelming"),
        "average": "",
        "reviews": 0,
    } | parse_average(plain)

def parse_average(plain):
    m=re.search(r"Average Rating\\s+(\\d+(?:\\.\\d+)?)\\s*/\\s*4\\s+([\\d,]+)\\s+reviews", plain, flags=re.I)
    return {"average": float(m.group(1)) if m else "", "reviews": int(m.group(2).replace(",","")) if m else 0}

def cut_from_name(name):
    n=clean(name).casefold()
    for hint,cut in CUT_HINTS:
        if hint in n: return cut
    return ""

def summary(row):
    bits=[]
    typ=row.get("tipo") or row.get("blend_type")
    if typ: bits.append(f"Tipo: {typ}.")
    if row.get("composicion"): bits.append(f"Composición: {row['composicion']}.")
    if row.get("corte") and row["corte"]!="No especificado": bits.append(f"Corte: {row['corte']}.")
    if row.get("fuerza_label") and row["fuerza_label"]!="No especificada": bits.append(f"Fuerza: {row['fuerza_label']}.")
    if row.get("aromatizacion"): bits.append(f"Aromatización: {row['aromatizacion']}.")
    if row.get("nota_estancia"): bits.append(f"Nota de estancia: {row['nota_estancia']}.")
    return " ".join(bits) or "Ficha de referencia del catálogo; se muestran los datos publicados por las fuentes consultadas."

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8"))
    cache={}
    if CACHE.exists():
        try: cache=json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception: cache={}
    targets=[b for b in data.get("blends",[]) if b.get("fuente_blend_url")]
    def work(b):
        url=b["fuente_blend_url"]; key=b.get("id") or url
        if key in cache: return key, cache[key]
        try:
            page=fetch(url)
            parsed=parse_page(page)
            parsed["url"]=url; parsed["ok"]=True
            return key, parsed
        except Exception as exc:
            return key, {"url":url,"ok":False,"error":str(exc)}
    done=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=48) as pool:
        for key,parsed in pool.map(work, targets):
            cache[key]=parsed; done+=1
            if done%100==0: print(f"Enrichment: {done}/{len(targets)}")
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    CACHE.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding="utf-8")
    ok=0
    for b in data.get("blends",[]):
        key=b.get("id")
        p=cache.get(key)
        if not p or not p.get("ok"): continue
        ok+=1
        if p.get("brand"): b["marca"]=p["brand"]
        if p.get("blend_type"): b["tipo"]=p["blend_type"]
        if p.get("contents"): b["composicion"]=p["contents"]
        if p.get("flavoring"): b["aromatizacion"]=p["flavoring"]
        elif "aromatizacion" not in b or not b.get("aromatizacion"): b["aromatizacion"]="None Detected"
        if p.get("cut"): b["corte"]=p["cut"]
        elif not b.get("corte"): b["corte"]=cut_from_name(b.get("nombre",""))
        if p.get("country"): b["pais"]=p["country"]
        if p.get("production"): b["produccion"]=p["production"]
        if p.get("packaging"): b["packaging"]=p["packaging"]
        if p.get("blended_by"): b["blended_por"]=p["blended_by"]
        if p.get("manufactured_by"): b["fabricado_por"]=p["manufactured_by"]
        if p.get("descripcion"): b["descripcion"]=p["descripcion"]
        if p.get("average") not in ("",None): b["valoracion"]=p["average"]
        if p.get("reviews"): b["resenas"]=p["reviews"]
        if p.get("strength"): b["fuerza_label"]=p["strength"]
        if p.get("profile_flavoring"): b["aromatizacion_nivel"]=p["profile_flavoring"]
        if p.get("room_note"): b["nota_estancia"]=p["room_note"]
        if p.get("taste"): b["sabor"]=p["taste"]
        if b.get("fuerza_label"):
            b["fuerza"]=STRENGTH_SCORES.get(str(b["fuerza_label"]).casefold(),0)
        else:
            b["fuerza"]=float(b.get("fuerza") or 0)
        b["fuente_detalle"]=p.get("url")
        b["fuente"]="TobaccoReviews + Pipateka"
    for b in data.get("blends",[]):
        if not b.get("tipo"): b["tipo"]="Sin clasificar; fuente no especifica el tipo"
        if not b.get("pais"): b["pais"]="No especificado en la fuente consultada"
        if not b.get("corte"): b["corte"]=cut_from_name(b.get("nombre","")) or "No especificado en la fuente consultada"
        if not b.get("composicion"): b["composicion"]="No especificada en la fuente consultada"
        if not b.get("aromatizacion"): b["aromatizacion"]="No especificada en la fuente consultada"
        if not b.get("fuerza_label"): b["fuerza_label"]="No especificada en la fuente consultada"
        if "fuerza" not in b or b.get("fuerza") in (None,""): b["fuerza"]=0
        if not b.get("nota_estancia"): b["nota_estancia"]="No especificada en la fuente consultada"
        if not b.get("sabor"): b["sabor"]="No especificado en la fuente consultada"
        if not b.get("produccion"): b["produccion"]="No especificada en la fuente consultada"
        if not b.get("packaging"): b["packaging"]="No especificado en la fuente consultada"
        if not b.get("descripcion"):
            b["descripcion"]=summary(b)
        b["reseña_pipateka"]=f"Datos de comunidad: {int(b.get('resenas') or 0):,} reseñas; media {b.get('valoracion') if b.get('valoracion') not in (None,'') else 'no disponible'} / 4. Síntesis editorial de Pipateka, sin reproducir literalmente opiniones de terceros."
    data["enrichment_version"]="1.0.0"
    data["enrichment_updated"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    data["enrichment_results"]={"detail_urls":len(targets),"pages_ok":ok}
    CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Enriquecidas {ok}/{len(targets)} fichas con páginas técnicas.")

if __name__=="__main__": main()
