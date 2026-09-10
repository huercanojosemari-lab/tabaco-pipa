const cards=document.querySelector('#cards');
const featured=document.querySelector('#featuredCards');
const search=document.querySelector('#search');
const typeSelect=document.querySelector('#typeSelect');
const brandSelect=document.querySelector('#brandSelect');
const strengthSelect=document.querySelector('#strengthSelect');
const aromaSelect=document.querySelector('#aromaSelect');
const resultCount=document.querySelector('#resultCount');
let products=[];
let sortMode='default';

const fallback=[
{id:'demo-virginia',marca:'Pipateka',nombre:'Virginia Dorado',tipo:'Virginia',composicion:['Virginia'],imagen_local:'assets/images/virginia.svg',resumen_editorial:'Ficha de demostración.',valoracion_comunidad:8.5},
{id:'demo-english',marca:'Pipateka',nombre:'English No. 7',tipo:'English',composicion:['Latakia','Oriental/Turkish','Virginia'],imagen_local:'assets/images/english.svg',resumen_editorial:'Ficha de demostración.',valoracion_comunidad:8.0}
];

const categories=['Todos','Virginia','Virginia/Perique','Virginia/Burley','English','Balkan','Aromáticos','Oriental','Burley','Cavendish'];
const slug=p=>p.id||`${p.marca||''}-${p.nombre||''}`.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
const normalize=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const esc=v=>String(v??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#039;'}[m]));
const haystack=p=>normalize([p.marca,p.nombre,p.fabricante,p.origen,p.tipo,p.corte,p.aromatizacion,p.fuerza,p.aroma,p.sabor,p.combustion,p.equilibrio,...(p.composicion||[]),p.resumen_editorial].filter(Boolean).join(' '));
const has=p=>term=>haystack(p).includes(normalize(term));

function categoryMatch(p,category){
  if(category==='Todos') return true;
  if(category==='Virginia/Perique') return has(p)('virginia')&&has(p)('perique');
  if(category==='Virginia/Burley') return has(p)('virginia')&&has(p)('burley');
  if(category==='Virginia') return has(p)('virginia');
  if(category==='English') return has(p)('english');
  if(category==='Balkan') return has(p)('balkan');
  if(category==='Aromáticos') return normalize(p.tipo).includes('aromatic') || (p.aromatizacion && !['none detected','none'].includes(normalize(p.aromatizacion)));
  if(category==='Oriental') return has(p)('oriental')||has(p)('turkish');
  if(category==='Burley') return has(p)('burley');
  if(category==='Cavendish') return has(p)('cavendish');
  return normalize(p.tipo)===normalize(category);
}

function optionList(select,items,firstValue,firstLabel){
  if(!select) return;
  select.innerHTML=`<option value="${esc(firstValue)}">${esc(firstLabel)}</option>`+items.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');
}

function setupFilters(){
  optionList(typeSelect,categories.slice(1),'Todos','Tipos');
  optionList(brandSelect,[...new Set(products.map(p=>p.marca).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es')),'Todas','Marca');
  optionList(strengthSelect,[...new Set(products.map(p=>p.fuerza).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es')),'Todas','Fuerza');
  optionList(aromaSelect,[...new Set(products.map(p=>p.aromatizacion).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es')),'Todas','Aromatización');
}

function filtered(){
  const q=normalize(search?.value||'');
  const list=products.filter(p=>{
    const typeOk=!typeSelect?.value||typeSelect.value==='Todos'||categoryMatch(p,typeSelect.value);
    const brandOk=!brandSelect?.value||brandSelect.value==='Todas'||p.marca===brandSelect.value;
    const strengthOk=!strengthSelect?.value||strengthSelect.value==='Todas'||p.fuerza===strengthSelect.value;
    const aromaOk=!aromaSelect?.value||aromaSelect.value==='Todas'||p.aromatizacion===aromaSelect.value;
    return (!q||haystack(p).includes(q))&&typeOk&&brandOk&&strengthOk&&aromaOk;
  });
  if(sortMode==='rating') list.sort((a,b)=>(Number(b.valoracion_comunidad)||0)-(Number(a.valoracion_comunidad)||0));
  if(sortMode==='reviews') list.sort((a,b)=>(Number(b.numero_resenas)||0)-(Number(a.numero_resenas)||0));
  return list;
}

function productCard(p,compact=false){
  const rating=p.valoracion_comunidad?`★ ${esc(p.valoracion_comunidad)}`:'Ficha';
  const count=p.numero_resenas?` (${esc(p.numero_resenas)})`:'';
  const image=esc(p.imagen_local||'assets/images/hero.svg');
  if(compact) return `<article class="featured-card"><img src="${image}" alt="Representación local de ${esc(p.nombre)}" loading="lazy"><div class="featured-body"><div class="brand-name">${esc(p.marca)}</div><h3>${esc(p.nombre)}</h3><div class="meta">${esc(p.tipo||'Sin clasificar')} · ${esc((p.composicion||[]).slice(0,2).join('/'))}</div><div class="rating"><b>★</b> ${esc(p.valoracion_comunidad||'—')}${count}</div><div class="strength">●●○ ${esc(p.fuerza||'Media')}</div></div></article>`;
  const composition=(p.composicion||[]).length?`<p><strong>Composición:</strong> ${esc(p.composicion.join(', '))}</p>`:'';
  return `<article class="card"><img src="${image}" alt="Representación local de ${esc(p.nombre)}" loading="lazy"><div class="card-body"><span class="tag">${esc(p.tipo||'Sin clasificar')}</span><h3>${esc(p.nombre)}</h3><p><strong>${esc(p.marca||'Marca no indicada')}</strong></p>${composition}<p>${esc(p.resumen_editorial||'Ficha en investigación.')}</p><div class="scores"><span class="score">Comunidad <b>${rating}${count}</b></span>${p.fuerza?`<span class="score">Fuerza <b>${esc(p.fuerza)}</b></span>`:''}${p.corte?`<span class="score">Corte <b>${esc(p.corte)}</b></span>`:''}</div><a class="card-link" href="producto.html?id=${encodeURIComponent(slug(p))}">Ver ficha completa →</a></div></article>`;
}

function render(){
  const list=filtered();
  if(resultCount) resultCount.textContent=`${list.length} resultado${list.length===1?'':'s'}`;
  if(featured) featured.innerHTML=list.slice(0,6).map(p=>productCard(p,true)).join('');
  if(!cards) return;
  cards.innerHTML=list.length?list.map(p=>productCard(p)).join(''):'<div class="empty"><strong>No hay resultados.</strong><br>Prueba otra categoría o cambia los filtros.</div>';
}

function scrollResults(){document.querySelector('#resenas')?.scrollIntoView({behavior:'smooth',block:'start'});}
function applyCategory(category){if(typeSelect) typeSelect.value=categories.includes(category)?category:'Todos';sortMode='default';render();scrollResults();}
function applyBrand(brand){if(brandSelect) brandSelect.value=brand||'Todas';sortMode='default';render();scrollResults();}
function applySort(mode){sortMode=mode||'default';render();scrollResults();}

document.querySelectorAll('[data-category]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();applyCategory(el.dataset.category);}));
document.querySelectorAll('[data-brand]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();applyBrand(el.dataset.brand);}));
document.querySelectorAll('[data-sort]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();applySort(el.dataset.sort);}));
document.querySelectorAll('[data-reset]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();if(search)search.value='';if(typeSelect)typeSelect.value='Todos';if(brandSelect)brandSelect.value='Todas';if(strengthSelect)strengthSelect.value='Todas';if(aromaSelect)aromaSelect.value='Todas';sortMode='default';render();scrollResults();}));
[search,typeSelect,brandSelect,strengthSelect,aromaSelect].filter(Boolean).forEach(el=>el.addEventListener(el===search?'input':'change',()=>{sortMode='default';render();}));
document.querySelector('#searchButton')?.addEventListener('click',()=>{sortMode='default';render();scrollResults();});
document.querySelector('.more-filters')?.addEventListener('click',scrollResults);

async function load(){
  try{
    const r=await fetch('data/catalogo.json',{cache:'no-store'});
    if(!r.ok) throw Error('catalogo');
    const data=await r.json();
    products=Array.isArray(data.products)?data.products:[];
    if(!products.length) throw Error('empty');
  }catch(e){products=fallback;}
  setupFilters();
  render();
}
load();
