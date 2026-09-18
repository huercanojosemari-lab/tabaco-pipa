import json, math, subprocess
from pathlib import Path
CATALOG=Path("data/catalogo-global.json")
FRONTEND=Path("pipateka-data.js")

def old_rows():
    if not FRONTEND.exists(): return {}
    source=FRONTEND.read_text(encoding="utf-8")
    source=source.replace("const BBDD_TABACOS =","globalThis.__bb =")
    code="const fs=require('fs'); let s=fs.readFileSync(process.argv[1],'utf8'); eval(s); process.stdout.write(JSON.stringify(globalThis.__bb||[]));"
    try:
        r=subprocess.run(["node","-e",code,str(FRONTEND)],capture_output=True,text=True,check=True)
        rows=json.loads(r.stdout or "[]")
        return {(str(x.get("marca","")).casefold(),str(x.get("nombre","")).casefold()):x for x in rows}
    except Exception as e:
        print("No se pudieron preservar fichas editoriales existentes:",e); return {}

def pop(reviews,rating):
    r=max(0,int(reviews or 0)); v=float(rating) if rating is not None else 0
    if not r and not v: return 1
    return max(1,min(100,round(12*math.log1p(r)+4*v)))

def make(row):
    brand=str(row.get("marca") or "").strip(); name=str(row.get("nombre") or "").strip()
    typ=str(row.get("tipo") or "").strip() or "Sin clasificar"
    flavor=str(row.get("aromatizacion") or "").strip()
    aroma=f"Tipo: {typ}."
    if flavor: aroma+=f" Aromatización registrada: {flavor}."
    comp=row.get("composicion")
    if isinstance(comp,list): comp=", ".join(map(str,comp))
    elif not comp: comp="Composición no especificada en el índice resumido."
    return {"id":row.get("id") or f"tr-{brand.casefold()}-{name.casefold()}","nombre":name,"marca":brand,
            "tipo":typ,"corte":str(row.get("corte") or "Sin dato"),"fuerza":0,"aroma":aroma,
            "composicion":str(comp),"valoracion":row.get("valoracion"),"popularidad":pop(row.get("resenas"),row.get("valoracion")),
            "disponibilidad":"Ficha de referencia; la disponibilidad comercial depende del país y la fecha.",
            "imagen":row.get("imagen") or "assets/tins/editorial-tin.svg","reseñas":[],"_resenas_fuente":int(row.get("resenas") or 0)}

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8")); old=old_rows(); rows=[]
    for raw in data.get("blends",[]):
        row=make(raw); k=(row["marca"].casefold(),row["nombre"].casefold()); prev=old.get(k)
        if prev:
            base=row.copy()
            for f,v in prev.items():
                if v not in ("",None,[],{}): base[f]=v
            base["_resenas_fuente"]=int(raw.get("resenas") or 0); row=base
        rows.append(row)
    FRONTEND.write_text("const BBDD_TABACOS = "+json.dumps(rows,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
    print(f"Frontend catalogue synced: {len(rows)} fichas; {len({r['marca'] for r in rows})} marcas")
if __name__=="__main__": main()
