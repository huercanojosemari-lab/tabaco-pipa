import html, json, re
from pathlib import Path
from urllib.request import Request, urlopen

CATALOG = Path("data/catalogo-global.json")

KNOWN_BRANDS = {
    "Mac Baren": "https://www.tobaccoreviews.com/brand/36/mac-baren/",
    "Peterson": "https://www.tobaccoreviews.com/brand/45/peterson/",
    "Samuel Gawith": "https://www.tobaccoreviews.com/brand/51/samuel-gawith/",
    "Cornell & Diehl": "https://www.tobaccoreviews.com/brand/15/cornell/",
    "Gawith, Hoggarth & Co.": "https://www.tobaccoreviews.com/brand/28/gawith-hoggarth-co/",
    "Dan Tobacco": "https://www.tobaccoreviews.com/brand/17/dan-tobacco/",
    "Sutliff Tobacco Company": "https://www.tobaccoreviews.com/brand/756/sutliff-tobacco-company/",
    "Rattray's": "https://www.tobaccoreviews.com/brand/48/rattray/",
    "Dunhill": "https://www.tobaccoreviews.com/brand/22/dunhill/",
    "Esoterica Tobacciana": "https://www.tobaccoreviews.com/brand/24/esoterica-tobacciana/",
    "McClelland": "https://www.tobaccoreviews.com/brand/37/mcclelland/",
    "Seattle Pipe Club": "https://www.tobaccoreviews.com/brand/339/seattle-pipe-club/",
    "Wessex": "https://www.tobaccoreviews.com/brand/82/wessex/",
    "A&C Petersen": "https://www.tobaccoreviews.com/brand/1/a-c-petersen/",
}

ALIASES = {
    "gawith, hoggarth & co.": "gawith, hoggarth & co.",
    "gawith & hoggarth & co": "gawith, hoggarth & co.",
    "rattray": "rattray's",
    "rattray’s": "rattray's",
    "a & c petersen": "a&c petersen",
    "a&c petersen": "a&c petersen",
}

def clean(v):
    return re.sub(r"\\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", v or ""))).strip()

def bkey(v):
    x=clean(v).casefold().replace("’","'")
    return ALIASES.get(x,x)

def slug(v):
    return re.sub(r"[^a-z0-9]+","-",v.casefold()).strip("-")

def fetch(url):
    return urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0 PipatekaCatalog/10.1"}),timeout=45).read().decode("utf-8","ignore")

def parse_brand(brand,url):
    html_text=fetch(url)
    rows=re.findall(r"<tr[^>]*>(.*?)</tr>",html_text,re.I|re.S)
    out={}
    for raw in rows:
        m=re.search(r'href=["\']([^"\']*/blend/[^"\']*)["\'][^>]*>(.*?)</a>',raw,re.I|re.S)
        if not m: continue
        name=clean(m.group(2))
        cells=[clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>",raw,re.I|re.S)]
        if not name or len(cells)<2: continue
        reviews_match=re.search(r"\\d[\\d,]*",cells[1])
        reviews=int(reviews_match.group(0).replace(",","")) if reviews_match else 0
        rating=None
        if len(cells)>=3:
            rm=re.search(r"\\d+(?:\\.\\d+)?",cells[2])
            if rm: rating=float(rm.group(0))
        blend_type=clean(cells[4]) if len(cells)>=5 else ""
        out[name.casefold()]={"id":f"tr-{slug(brand)}-{slug(name)}","nombre":name,"marca":brand,
            "resenas":reviews,"valoracion":rating,"tipo":blend_type,"pais":"","corte":"","fuerza":"",
            "aromatizacion":"","fuente":"TobaccoReviews","imagen":None,"imagen_fuente":None,
            "fuente_url":url.rstrip("/")+"/"+""}
    return list(out.values())

def main():
    data=json.loads(CATALOG.read_text(encoding="utf-8"))
    merged={}
    for row in data.get("blends",[]):
        brand=clean(row.get("marca")); name=clean(row.get("nombre"))
        if brand and name: merged[(bkey(brand),name.casefold())]=row
    counts={}
    for brand,url in KNOWN_BRANDS.items():
        rows=parse_brand(brand,url); counts[brand]=len(rows)
        for row in rows:
            k=(bkey(row["marca"]),row["nombre"].casefold())
            if k in merged:
                old=merged[k]
                for f,v in row.items():
                    if v not in ("",None,[],{}): old[f]=v
                old["marca"]=brand; old["fuente"]="TobaccoReviews + Pipateka"; old["fuente_url"]=url
            else:
                row["fuente_url"]=url
                merged[k]=row
    rows=sorted(merged.values(),key=lambda x:(x.get("marca","").casefold(),x.get("nombre","").casefold()))
    data["blends"]=rows
    data["total_blends_cargados"]=len(rows)
    data["total_marcas_cargadas"]=len({x.get("marca") for x in rows if x.get("marca")})
    data["known_brand_sources"]=counts
    data["known_brand_total"]=sum(counts.values())
    data["source_scope"]="Índice combinado de Fumeurs de Pipe y listados completos de marcas principales de TobaccoReviews."
    CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Known brand rows:",counts)
    print(f"Total blend rows: {len(rows)}")
if __name__=="__main__": main()
