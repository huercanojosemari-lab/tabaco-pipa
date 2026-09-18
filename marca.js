const $=s=>document.querySelector(s);
const collator=new Intl.Collator('es-ES',{sensitivity:'base',numeric:true,ignorePunctuation:true});
const norm=s=>String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLocaleLowerCase('es-ES');
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function imageMarkup(b){
  const title=`${b.marca||''} ${b.nombre||''}`;
  const local=b.imagen||'assets/tins/editorial-tin.svg';
  return `<div class="blend-thumb"><img loading="lazy" alt="${esc(title)}" title="${esc(title)}" src="${esc(local)}" onerror="this.onerror=null;this.src='assets/tins/editorial-tin.svg'"><span class="image-source">Imagen local</span></div>`;
}
function description(b){
  if(b.descripcion) return b.descripcion;
  const bits=[];
  if(b.tipo) bits.push(`Tipo: ${b.tipo}.`);
  if(b.corte && b.corte!=='Sin dato') bits.push(`Corte: ${b.corte}.`);
  if(b.composicion) bits.push(`Composición: ${b.composicion}.`);
  return bits.join(' ')||'Ficha de referencia del catálogo de Pipateka.';
}
function reviewText(b){return b.reseña_pipateka || b.aroma || 'Ficha de referencia sin síntesis editorial adicional.'}
function render(rows,brand){
  const q=norm($('#blendSearch').value||'');
  const list=rows.filter(b=>!q||norm([b.nombre,b.tipo,b.corte,b.composicion,b.aroma].join(' ')).includes(q)).sort((a,b)=>collator.compare(a.nombre,b.nombre));
  $('#brandBlendList').innerHTML=list.length?list.map(b=>`<article class="blend-item"><div class="blend-main">${imageMarkup({...b,marca:b.marca||brand})}<div class="blend-copy"><strong>${esc(b.nombre)}</strong><small>${esc(b.tipo||'Sin clasificar')}</small><p>${esc(description(b))}</p><p class="blend-review"><b>Nota de ficha:</b> ${esc(reviewText(b))}</p></div></div><span class="blend-rating">${b.valoracion==null?'Sin valoración':Number(b.valoracion).toFixed(2)+' ★'}${Number(b._resenas_fuente||0)?' · '+Number(b._resenas_fuente).toLocaleString('es-ES')+' reseñas':''}</span></article>`).join(''):`<div class="brand-empty">No se encontraron mezclas para esta búsqueda.</div>`;
}
function load(){
  const requested=new URLSearchParams(location.search).get('brand');
  if(!requested){location.replace('catalogo.html');return}
  const all=Array.isArray(globalThis.BBDD_TABACOS)?globalThis.BBDD_TABACOS:[];
  const rowsAll=all.filter(b=>b&&b.marca&&b.nombre);
  const requestedNorm=norm(requested);
  const brand=rowsAll.find(b=>norm(b.marca)===requestedNorm)?.marca;
  if(!brand){
    $('#brandName').textContent='Marca no encontrada';
    $('#brandDescription').textContent='Esta marca no figura en el catálogo cargado de Pipateka.';
    $('#brandBlendCount').textContent='0'; $('#brandReviewCount').textContent='0'; return;
  }
  const rows=rowsAll.filter(b=>norm(b.marca)===norm(brand));
  $('#brandName').textContent=brand;
  $('#brandBlendCount').textContent=rows.length.toLocaleString('es-ES');
  $('#brandReviewCount').textContent=rows.reduce((sum,b)=>sum+(Number(b._resenas_fuente)||0),0).toLocaleString('es-ES');
  $('#brandDescription').textContent=`Catálogo individual de ${brand}, con sus mezclas indexadas en Pipateka.`;
  document.title=`Pipateka · ${brand}`;
  $('#blendSearch').addEventListener('input',()=>render(rows,brand));
  render(rows,brand);
}
document.addEventListener('DOMContentLoaded',load);
