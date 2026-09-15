/* Home fixes: real image usage + honest live counts */
(function(){
  const escLocal=s=>String(s??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
  const locale=()=>localStorage.getItem('pipateka-lang')||'es';
  const T=k=>window.pipaT?window.pipaT(k):k;
  window.card=function(p){
    const q=window.pipaProduct?window.pipaProduct(p):p;
    const rating=p.valoracion_comunidad==null?'—':Number(p.valoracion_comunidad).toFixed(1);
    const reviews=p.numero_resenas?`(${p.numero_resenas.toLocaleString(locale()==='zh'?'zh-CN':locale())})`:'';
    const image=p.imagen?String(p.imagen):'';
    const visual=image
      ? `<img class="home-tin-photo" src="${escLocal(image)}" alt="${escLocal(p.nombre||'Mezcla')}" loading="lazy" onerror="this.closest('.product-visual').classList.add('image-failed');this.remove()">`
      : `<div class="tin-fallback"><span>${escLocal(p.nombre||'Pipateka')}</span></div>`;
    return `<article class="product-card"><a href="producto.html?id=${encodeURIComponent(p.id||`${p.marca}-${p.nombre}`)}" class="product-link"><div class="product-visual">${visual}</div><div class="product-info"><span class="brand">${escLocal(p.marca||'Marca')}</span><h3>${escLocal(p.nombre||T('product'))}</h3><div class="meta">${escLocal(q.tipo||'Ficha editorial')} ${q.pais?' · '+escLocal(q.pais):''}</div><div class="rating"><span class="star">★</span><b>${rating}</b> <span>${reviews}</span></div><div class="strength">${escLocal(q.fuerza||'Información en revisión')} <span class="arrow">${T('arrow')||'→'}</span></div></div></a></article>`;
  };
  function honestCounts(){const c=document.querySelector('.trust-grid>div:first-child');if(c){const b=c.querySelector('b'),s=c.querySelector('small');if(b)b.textContent='657 mezclas cargadas';if(s)s.textContent='de 122 marcas en el catálogo local'}}
  document.addEventListener('DOMContentLoaded',()=>{honestCounts();setTimeout(()=>{honestCounts();if(typeof window.render==='function')window.render()},900)});
})();
