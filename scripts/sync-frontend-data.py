import json, math, subprocess
from pathlib import Path

CATALOG=Path("data/catalogo-global.json")
FRONTEND=Path("pipateka-data.js")

def old_rows():
    if not FRONTEND.exists(): return {}
    source=FRONTEND.read_text(encoding="utf-8").replace("const BBDD_TABACOS =","globalThis.__bb =")
    code="const fs=require('fs');let s=fs.readFileSync(process.argv[1],'utf8');eval(s);process.stdout.write(JSON.stringify(globalThis.__bb||[]));"
    try:
        r=subprocess.run(["node","-e",code,str(FRONTEND)],capture_output=True,text=True,check=True)
        rows=json.loads(r.stdout or "[]")
        return {(str(x.get("marca","")).casefold(),str(x.get("nombre","")).casefold()):x for x in rows}
    except Exception as e:
        print("No se pudieron preservar fichas editoriales existentes:",e)
        return {}

def pop(reviews,rating):
    r=max(0,int(reviews or 0)); v=float(rating) if rating not in (None,"") else 0
    if not r and not v: return 1
    return max(1,min(100,round(12*math.log1p(r)+4*v)))

def make(row):
    brand=str(row.get("marca") or "").strip()
    name=str(row.get("nombre") or "").strip()
    typ=str(row.get("tipo") or "").strip() or "Sin clasificar"
    comp=row.get("composicion")
    if isinstance(comp,list): comp=", ".join(map(str,comp))
    comp=str(comp or "No especificada en la fuente consultada.")
    cut=str(row.get("corte") or "No especificado en la fuente consultada.")
    strength_raw=row.get("fuerza")
    try:
        strength=float(strength_raw or 0)
    except (TypeError, ValueError):
        strength={"extremely mild":1,"very mild":1,"mild":1.5,"mild to medium":2,"medium":3,"medium to strong":4,"strong":4.5,"very strong":5,"overwhelming":5}.get(str(strength_raw).casefold().strip(),0)
    fuerza_label=str(row.get("fuerza_label") or "No especificada en la fuente consultada.")
    aroma=str(row.get("aroma") or "").strip()
    if not aroma:
        parts=[]
        if row.get("aromatizacion"): parts.append("Aromatización: "+str(row["aromatizacion"]))
        if row.get("nota_estancia"): parts.append("Nota de estancia: "+str(row["nota_estancia"]))
        if row.get("sabor"): parts.append("Sabor: "+str(row["sabor"]))
        aroma=". ".join(parts) if parts else "Perfil sensorial no especificado en la fuente consultada."
    production=str(row.get("produccion") or "No especificada en la fuente consultada.")
    availability=f"{production}. País registrado: {row.get('pais') or 'no especificado'}."
    return {
        "id":row.get("id") or f"tr-{brand.casefold()}-{name.casefold()}",
        "nombre":name,"marca":brand,"tipo":typ,"corte":cut,
        "fuerza":strength,"fuerza_label":fuerza_label,"aroma":aroma,
        "composicion":comp,"aromatizacion":str(row.get("aromatizacion") or "No especificada en la fuente consultada."),
        "nota_estancia":str(row.get("nota_estancia") or "No especificada en la fuente consultada."),
        "sabor":str(row.get("sabor") or "No especificado en la fuente consultada."),
        "pais":str(row.get("pais") or "No especificado en la fuente consultada."),
        "produccion":production,"packaging":str(row.get("packaging") or "No especificado en la fuente consultada."),
        "fabricante":str(row.get("fabricado_por") or row.get("marca") or "No especificado"),
        "mezclado_por":str(row.get("blended_por") or row.get("marca") or "No especificado"),
        "disponibilidad":availability,
        "imagen":row.get("imagen") or "assets/tins/editorial-tin.svg",
        "imagen_marca":row.get("imagen_marca") or f"assets/brands/{str(brand).casefold().replace(' ','-')}.svg",
        "valoracion":row.get("valoracion"),"popularidad":pop(row.get("resenas"),row.get("valoracion")),
        "descripcion":str(row.get("descripcion") or "Ficha de referencia del catálogo de Pipateka."),
        "reseñas":[],"_resenas_fuente":int(row.get("resenas") or 0),
        "fuente":str(row.get("fuente") or "Pipateka"),"fuente_url":row.get("fuente_detalle") or row.get("fuente_url") or ""
    }

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8"))
    old=old_rows(); rows=[]
    for raw in data.get("blends",[]):
        row=make(raw); k=(row["marca"].casefold(),row["nombre"].casefold()); prev=old.get(k)
        if prev:
            base=row.copy()
            for f,v in prev.items():
                if v not in ("",None,[],{}): base[f]=v
            base["_resenas_fuente"]=int(raw.get("resenas") or 0)
            if raw.get("imagen_marca"): base["imagen_marca"]=raw["imagen_marca"]
            row=base
        rows.append(row)
    FRONTEND.write_text("const BBDD_TABACOS = "+json.dumps(rows,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
    print(f"Frontend catalogue synced: {len(rows)} fichas; {len({r['marca'] for r in rows})} marcas; {sum(1 for r in rows if r.get('imagen_marca'))} imágenes de marca")
if __name__=="__main__": main()
