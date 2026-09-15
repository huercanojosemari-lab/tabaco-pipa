(() => {
  'use strict';
  const state = { items: [...BBDD_TABACOS], all: [...BBDD_TABACOS], query: '', type: '', sort: 'popularidad' };
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const normalize = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const stars = value => { const n=Math.max(0,Math.min(5,Number(value)||0)); return '★'.repeat(Math.round(n))+'☆'.repeat(5-Math.round(n)); };
  const strength = value => Array.from({length:5},(_,i)=>`<i class="${i<Number(value)?'on':''}"></i>`).join('');
  const card = item => `<article class="tobacco-card" data-card-id="${esc(item.id)}" tabindex="0" role="button" aria-label="Abrir ficha de ${esc(item.nombre)}"><div class="card-image"><span class="type-badge">${esc(item.tipo)}</span><img src="${esc(item.imagen)}" alt="Ilustración de ${esc(item.marca)} ${esc(item.nombre)}"></div><div class="card-body"><div class="card-brand">${esc(item.marca)}</div><h3>${esc(item.nombre)}</h3><div class="card-meta">${esc(item.corte)} · ${esc(item.aroma)}</div><div class="rating-line"><span class="stars" aria-label="${item.valoracion} de 4">${stars(Number(item.valoracion)*1.25)}</span><span>${Number(item.valoracion).toFixed(2)}/4</span></div><div class="rating-line"><span>Fuerza</span><span class="strength-dots">${strength(item.fuerza)}</span></div></div></article>`;
  function render() {
    const grid = $('#catalogGrid'); if (!grid) return;
    const q=normalize(state.query);
    let rows=state.all.filter(x => (!q || normalize([x.nombre,x.marca,x.tipo,x.corte,x.composicion].join(' ')).includes(q)) && (!state.type || normalize(x.tipo).includes(normalize(state.type))));
    if(state.sort==='valoracion') rows.sort((a,b)=>Number(b.valoracion)-Number(a.valoracion));
    else if(state.sort==='nombre') rows.sort((a,b)=>normalize(a.nombre).localeCompare(normalize(b.nombre),'es'));
    else rows.sort((a,b)=>Number(b.popularidad)-Number(a.popularidad));
    $('#resultCount').textContent=`${rows.length} fichas visibles`;
    grid.innerHTML=rows.length?rows.map(card).join(''):'<div class="empty-state">No hay fichas que coincidan con la búsqueda. Prueba otro término o restablece los filtros.</div>';
    $$('.tobacco-card',grid).forEach(el=>{el.addEventListener('click',()=>openDetail(el.dataset.cardId));el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openDetail(el.dataset.cardId)}})});
  }
  function openDetail(id){
    const item=state.all.find(x=>x.id===id); if(!item) return;
    $('#detailImage').src=item.imagen; $('#detailImage').alt=`${item.marca} ${item.nombre}`;
    $('#detailBrand').textContent=item.marca; $('#detailName').textContent=item.nombre;
    const specs=[['Tipo de mezcla',item.tipo],['Corte',item.corte],['Fuerza',`${item.fuerza}/5`],['Aroma / nota de estancia',item.aroma],['Composición',item.composicion],['Disponibilidad en Europa',item.disponibilidad],['Valoración',`${Number(item.valoracion).toFixed(2)}/4`],['Popularidad',`${item.popularidad}/100`]];
    $('#detailSpecs').innerHTML=specs.map(([a,b])=>`<div class="spec"><b>${esc(a)}</b><span>${esc(b)}</span></div>`).join('');
    const reviews=item.reseñas||[];
    $('#reviewsList').innerHTML=reviews.map(r=>`<div class="review"><div class="review-head"><strong>${esc(r.usuario)}</strong><span>${esc(r.fecha)} · <span class="stars">${stars(Number(r.puntuacion))}</span></span></div><p>${esc(r.texto)}</p></div>`).join('');
    $('#communityNote').textContent='Estas reseñas se presentan como síntesis editorial de opiniones comunitarias; no se atribuyen a usuarios concretos.';
    $('#detailModal').classList.add('is-open'); document.body.classList.add('modal-lock'); $('#modalClose').focus();
  }
  function closeDetail(){ $('#detailModal').classList.remove('is-open'); document.body.classList.remove('modal-lock'); }
  function setup(){
    const search=$('#mainSearch'), type=$('#typeFilter'), sort=$('#sortSelect');
    if(!$('#catalogGrid')) return;
    const types=[...new Set(BBDD_TABACOS.map(x=>x.tipo))].sort((a,b)=>a.localeCompare(b,'es'));
    type.innerHTML='<option value="">Todos los tipos</option>'+types.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');
    sort.innerHTML='<option value="popularidad">🔥 Más Populares</option><option value="valoracion">★ Mejor valorados</option><option value="nombre">Nombre (A-Z)</option>';
    search.addEventListener('input',e=>{state.query=e.target.value;render()}); type.addEventListener('change',e=>{state.type=e.target.value;render()}); sort.addEventListener('change',e=>{state.sort=e.target.value;render()});
    $('#clearFilters')?.addEventListener('click',()=>{state.query='';state.type='';state.sort='popularidad';search.value='';type.value='';sort.value='popularidad';render()});
    $('#searchButton')?.addEventListener('click',()=>{search.focus();render()});
    $('#modalClose')?.addEventListener('click',closeDetail); $('#detailModal')?.addEventListener('click',e=>{if(e.target.id==='detailModal')closeDetail()}); document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDetail()});
    render();
  }
  async function enrich(){
    try { const r=await fetch('data/catalogo-global.json?x='+Date.now()); if(!r.ok) return; const data=await r.json(); const external=(data.blends||[]).filter(x=>x.marca&&x.nombre).map((x,i)=>({id:`catalog-${i}-${normalize(x.marca+'-'+x.nombre).replace(/[^a-z0-9]+/g,'-')}`,nombre:x.nombre,marca:x.marca,tipo:x.tipo||'Sin clasificar',corte:x.corte||'No especificado',fuerza:Number(x.fuerza)||3,aroma:x.aroma||'Perfil no documentado',composicion:x.composicion||'Composición no documentada en el índice local',valoracion:Number(x.valoracion)||0,popularidad:Number(x.resenas)||0,disponibilidad:'Consultar disponibilidad en el mercado europeo.',imagen:x.imagen||'assets/tins/editorial-tin.svg',reseñas:[]}));
      const keys=new Set(state.all.map(x=>normalize(x.marca+'|'+x.nombre))); external.forEach(x=>{if(!keys.has(normalize(x.marca+'|'+x.nombre)))state.all.push(x)}); render();
    } catch(_) {}
  }
  document.addEventListener('DOMContentLoaded',()=>{setup();enrich()});
})();
