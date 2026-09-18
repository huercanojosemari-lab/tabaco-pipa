import json, math, re
from pathlib import Path

CATALOG=Path("data/catalogo-global.json")
FRONTEND=Path("pipateka-data.js")

def old_rows():
    if not FRONTEND.exists(): return {}
    source=FRONTEND.read_text(encoding="utf-8")
    source=source.replace("const BBDD_TABACOS =","globalThis.__bb =")
    code="const fs=require('fs'); let s=fs.readFileSync(process.argv[1],'utf8'); eval(s); process.stdout.write(JSON.stringify(globalThis.__bb||[]));"
    import subprocess
    try:
        r=subprocess.run(["node","-e",code,str(FRONTEND)],capture_output=True,text=True,check=True)
        rows=json.loads(r.stdout or "[]")
        return {(str(x.get("marca","")).casefold(),str(x.get("nombre","")).casefold()):x for x in rows}
    except Exception as e:
        print("No se pudieron preservar fichas editoriales existentes:",e); return {}

def slugify(v):
    return re.sub(r"[^a-z0-9]+","-",str(v).casefold()).strip("-") or "brand"

def pop(reviews,rating):
    r=max(0,int(reviews or 0)); v=float(rating) if rating is not None else 0
    if not r and not v: return 1
    return max(1,min(100,round(12*math.log1p(r)+4*v)))

def strength_num(value):
    if isinstance(value,(int,float)): return max(0,min(5,int(round(value))))
    x=str(value or "").casefold()
    if not x: return 0
    if "overwhelming" in x or "very strong" in x: return 5
    if "medium to strong" in x or "strong" in x: return 4
    if "medium" in x: return 3
    if "mild to medium" in x: return 2
    if "mild" in x: return 1
    return 0

def make(row):
    brand=str(row.get("marca") or "").strip()
    name=str(row.get("nombre") or "").strip()
    typ=str(row.get("tipo") or "").strip() or "No especificado en la fuente"
    cut=str(row.get("corte") or "").strip() or "No especificado en la fuente"
    country=str(row.get("pais") or "").strip() or "No especificado en la fuente"
    flavor=str(row.get("aromatizacion") or "").strip()
    strength_text=str(row.get("fuerza_text") or row.get("fuerza") or "").strip()
    comp=row.get("composicion")
    if isinstance(comp,list): comp=", ".join(map(str,comp))
    comp=str(comp or "").strip() or "No especificada en la fuente"
    aroma=flavor or str(row.get("nota_estancia") or "").strip() or "No especificado en la fuente"
    production=str(row.get("produccion") or "").strip()
    availability=("Descatalogado según la ficha de TobaccoReviews." if "no longer in production" in production.casefold()
                  else "Estado de producción no especificado en la fuente.")
    desc=f"Marca: {brand}. Tipo: {typ}. Corte: {cut}. Fuerza: {strength_text or 'No especificada'}. País: {country}. Composición: {comp}."
    return {
        "id":row.get("id") or f"tr-{slugify(brand)}-{slugify(name)}",
        "nombre":name,"marca":brand,"tipo":typ,"corte":cut,
        "fuerza":strength_num(strength_text),"fuerza_text":strength_text or "No especificada en la fuente",
        "aroma":aroma,"aromatizacion":flavor or "No especificada en la fuente",
        "composicion":comp,"pais":country,
        "valoracion":row.get("valoracion"),"popularidad":pop(row.get("resenas"),row.get("valoracion")),
        "disponibilidad":availability,"produccion":production or "No especificada en la fuente",
        "descripcion":desc,"reseña_pipateka":f"Ficha documental de {name}: combina los campos estructurados disponibles de la fuente y no sustituye las reseñas literales de usuarios.",
        "imagen":row.get("imagen") or "assets/tins/editorial-tin.svg",
        "marca_imagen":row.get("marca_imagen") or f"assets/brands/{slugify(brand)}.svg",
        "reseñas":row.get("reseñas") if isinstance(row.get("reseñas"),list) else [],
        "_resenas_fuente":int(row.get("resenas") or 0),
        "fuente":row.get("fuente") or "Pipateka",
        "fuente_url":row.get("fuente_url"),
        "fuente_blend_url":row.get("fuente_blend_url"),
        "imagen_fuente":row.get("imagen_fuente"),
    }

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8")); old=old_rows(); rows=[]
    for raw in data.get("blends",[]):
        row=make(raw)
        k=(row["marca"].casefold(),row["nombre"].casefold())
        prev=old.get(k)
        if prev:
            for f,v in prev.items():
                if v not in ("",None,[],{}): row[f]=v
            row["marca_imagen"]=f"assets/brands/{slugify(row['marca'])}.svg"
            row["_resenas_fuente"]=int(raw.get("resenas") or prev.get("_resenas_fuente") or 0)
        rows.append(row)
    FRONTEND.write_text("const BBDD_TABACOS = "+json.dumps(rows,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
    print(f"Frontend catalogue synced: {len(rows)} fichas; {len({r['marca'] for r in rows})} marcas")
if __name__=="__main__": main()
