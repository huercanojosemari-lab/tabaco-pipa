import html
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

CATALOG=Path("data/catalogo-global.json")
OUT_DIR=Path("assets/brands")

def slug(v):
    return re.sub(r"[^a-z0-9]+","-",str(v).casefold()).strip("-") or "marca"

def initials(name):
    words=[w for w in re.split(r"[^A-Za-zÀ-ÿ0-9]+",str(name)) if w]
    stop={"and","&","of","the","de","du","co","company","tobacco","tobaccos","tabacco","tabak","tabacs"}
    core=[w for w in words if w.casefold() not in stop]
    source=core or words
    return "".join(w[0] for w in source[:3]).upper()[:3] or "P"

def svg(name):
    safe=escape(name)
    ini=escape(initials(name))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" role="img" aria-label="{safe}">
  <rect x="14" y="14" width="612" height="332" rx="28" fill="#f4efe5" stroke="#9b762f" stroke-width="3"/>
  <circle cx="320" cy="132" r="70" fill="#1f2729"/>
  <text x="320" y="155" text-anchor="middle" font-family="Georgia, serif" font-size="54" font-weight="700" fill="#f4efe5">{ini}</text>
  <path d="M190 225 H450" stroke="#9b762f" stroke-width="3"/>
  <text x="320" y="270" text-anchor="middle" font-family="Georgia, serif" font-size="30" font-weight="700" fill="#1f2729">{safe}</text>
  <text x="320" y="305" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" letter-spacing="3" fill="#76552f">PIPATEKA · MARCA</text>
</svg>'''

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8"))
    brands=sorted({str(b.get("marca","")).strip() for b in data.get("blends",[]) if str(b.get("marca","")).strip()},key=str.casefold)
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    mapping={}
    for brand in brands:
        path=OUT_DIR/(slug(brand)+".svg")
        path.write_text(svg(brand),encoding="utf-8")
        mapping[brand]=f"assets/brands/{path.name}"
    for b in data.get("blends",[]):
        brand=str(b.get("marca","")).strip()
        if brand: b["imagen_marca"]=mapping[brand]
    data["brand_image_count"]=len(mapping)
    data["brand_image_note"]="Marca tipográfica local de Pipateka. Se usa como imagen de identificación de la marca cuando no existe una fotografía de producto local."
    CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    Path("data/brand-images.json").write_text(json.dumps({"total":len(mapping),"marcas":mapping},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Brand images generated: {len(mapping)}")
if __name__=="__main__": main()
