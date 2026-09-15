/* Pipateka — interacciones premium de portada */
(function(){
  const esc=s=>String(s??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const clean=s=>String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  let data=[];
  function ensureModal(){
    if(document.getElementById('pipatekaModal')) return;
    document.body.insertAdjacentHTML('beforeend',`<div class="pip-modal" id="pipatekaModal" aria-hidden="true"><div class="pip-modal-backdrop" data-modal-close></div><section class="pip-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="pipModalTitle"><button class="pip-modal-close" data-modal-close aria-label="Cerrar">×</button><div class="pip-modal-kicker" id="pipModalBrand"></div><h2 id="pipModalTitle"></h2><div class="pip-modal-grid"><div class="pip-modal-visual" id="pipModalVisual"></div><div class="pip-modal-copy"><p id="pipModalDescription"></p><div class="pip-modal-facts" id="pipModalFacts"></div><a class="pip-modal-link" id="pipModalLink">Abrir ficha completa →</a></div></div></section></div>`);
    document.addEventListener('click',e=>{if(e.target.closest('[data-modal-close]')) closeModal()});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});
  }
  function openModal(p){
    ensureModal();
    const modal=document.getElementById('pipatekaModal');
    document.getElementById('pipModalBrand').textContent=p.marca||'Pipateka';
    document.getElementById('pipModalTitle').textContent=p.nombre||'Ficha';
    document.getElementById('pipModalDescription').textContent=p.descripcion||p.resumen_editorial||'Ficha informativa en preparación.';
    const facts=[['Tipo',p.tipo],['Fuerza',p.fuerza],['Corte',p.corte],['Aromatización',p.aromatizacion],['Composición',(p.composicion||[]).join(', ')],['Valoración',p.valoracion!=null?Number(p.valoracion).toFixed(1)+' / 4':'—']].filter(x=>x[1]);
    document.getElementById('pipModalFacts').innerHTML=facts.map(([k,v])=>`<div><small>${esc(k)}</small><strong>${esc(v)}</strong></div>`).join('');
    const visual=document.getElementById('pipModalVisual');
    visual.innerHTML=p.imagen?`<img src="${esc(p.imagen)}" alt="${esc(p.nombre)}">`:`<div class="pip-modal-fallback"><span>${esc(p.nombre)}</span></div>`;
    const link=document.getElementById('pipModalLink');link.href=`producto.html?id=${encodeURIComponent(p.id||`${p.marca}-${p.nombre}`)}`;
    modal.classList.add('is-open');modal.setAttribute('aria-hidden','false');document.body.classList.add('modal-open');
  }
  function closeModal(){const m=document.getElementById('pipatekaModal');if(!m)return;m.classList.remove('is-open');m.setAttribute('aria-hidden','true');document.body.classList.remove('modal-open')}
  async function load(){try{const r=await fetch('data/catalogo-global.json?homepage='+Date.now());if(r.ok){const j=await r.json();data=j.blends||[]}}catch(e){console.warn('Pipateka: no se pudo cargar el catálogo para el modal',e)}}
  document.addEventListener('DOMContentLoaded',()=>{ensureModal();load();document.addEventListener('click',e=>{const a=e.target.closest('#cards .product-link');if(!a)return;e.preventDefault();const id=new URL(a.href,location.href).searchParams.get('id');const p=data.find(x=>String(x.id)===String(id))||data.find(x=>`${x.marca}-${x.nombre}`===id);if(p)openModal(p);else location.href=a.href})});
})();
