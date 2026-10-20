const analysis=document.getElementById('analysis'),comparisonMetric=document.getElementById('comparison-metric');
const individualCandidate=document.getElementById('individual-candidate');
const pedroRows=new Map(data.pedro.zones.map(r=>[r.id,r]));
const isPedro=()=>!compare()&&individualCandidate.value==='pedro';
function individualZones(){return isPedro()?data.zones.filter(r=>r.capital).map(r=>({...r,...pedroRows.get(r.id)})):data.zones}
const comparisonRows=new Map(data.comparison.rows.map(r=>[r.id,r]));
const compare=()=>analysis.value==='comparison';
const comparisonField=()=>comparisonMetric.value==='absolute'?'difference_votes':'difference_pp';
const comparisonValue=row=>{const r=comparisonRows.get(row.key);return r?.status==='exploratory'?r[comparisonField()]??null:null};
const comparisonExtent=()=>Math.max(0,...data.comparison.rows.map(r=>Math.abs(r[comparisonField()]??0)));
const signed=new Intl.NumberFormat('pt-BR',{maximumFractionDigits:3,signDisplay:'exceptZero'});
function comparisonColor(value,extent){
 if(value==null)return '#c9cecb';
 const t=extent?Math.min(1,Math.abs(value)/extent):0;
 const target=value<0?[211,112,30]:[34,105,170];
 return `rgb(${target.map(c=>Math.round(245+(c-245)*t)).join(',')})`;
}
const individualNote=document.querySelector('aside > .note');
const originalFill=fill;
fill=function(row){return compare()?comparisonColor(comparisonValue(row),comparisonExtent()):originalFill(row)};
const originalChoose=choose;
choose=function(code,preserveNeighborhood=false){
 originalChoose(code,preserveNeighborhood);
 if(!compare()){updateIndividual();return;}
 const r=comparisonRows.get(code),value=r?.[comparisonField()]??null,absolute=comparisonMetric.value==='absolute';
 document.getElementById('share').textContent=value==null?'Indisponível':signed.format(value)+(absolute?' votos':' p.p.');
 document.getElementById('share').nextElementSibling.textContent=value==null?'Dados ausentes ou incompatíveis':value===0?'Mesma '+(absolute?'quantidade de votos':'participação territorial'):(value>0?'Léo Lupi':'Pedro Porto')+(absolute?' teve mais votos':' tem maior concentração relativa');
 for(const [id,prefix,key,total]of [['votes','Léo Lupi','leo',13195],['denominator','Pedro Porto','pedro',4220]]){
  const el=document.getElementById(id),v=r?.[key+'_votes'],p=r?.[key+'_distribution'];
  el.textContent=v==null?'Indisponível':nf.format(v)+' votos';
  el.nextElementSibling.textContent=prefix+' · '+(p==null?'sem participação disponível':pf.format(p)+'% de seus '+nf.format(total)+' votos na capital');
 }
 geometryNote.textContent+=(r?.status==='missing_data'?' Dados incompletos: comparação indisponível.':'');
 let extra=document.getElementById('comparison-differences');
 if(!extra){extra=document.createElement('p');extra.id='comparison-differences';extra.className='note';document.getElementById('denominator').parentElement.after(extra)}
 extra.hidden=false;extra.textContent=r?.difference_votes==null?'':`Léo − Pedro: ${signed.format(r.difference_votes)} votos; ${r.difference_pp==null?'indisponível':signed.format(r.difference_pp)+' p.p.'} da distribuição territorial.`;
};
const originalUpdateMetric=updateMetric;
updateMetric=function(){
 if(!compare()){originalUpdateMetric();updateIndividual();return}
 const absolute=comparisonMetric.value==='absolute',extent=comparisonExtent(),unit=absolute?' votos':' p.p.';
 document.getElementById('metric-caption').textContent=absolute?'Diferença de votos · Léo Lupi − Pedro Porto':'Distribuição territorial · participação da zona no total de Léo − participação no total de Pedro';
 const legend=document.getElementById('legend');legend.replaceChildren();
 const bar=document.createElement('div');bar.style.cssText='width:100%;height:14px;border-radius:4px;background:linear-gradient(to right,#d3701e,#f5f5f5,#2269aa)';legend.append(bar);
 const text=document.createElement('div');text.style.cssText='display:flex;justify-content:space-between;gap:12px;width:100%';
 for(const label of ['Pedro '+signed.format(-extent)+unit,'0','Léo +'+areaFormat.format(extent)+unit]){const span=document.createElement('span');span.textContent=label;text.append(span)}legend.append(text);
 for(const row of rows){const p=paths.get(row.key);if(!p)continue;p.setAttribute('fill',fill(row));const r=comparisonRows.get(row.key);p.querySelector('title').textContent=r?`${row.label}: Léo ${nf.format(r.leo_votes)} votos · Pedro ${nf.format(r.pedro_votes)} votos · diferença ${signed.format(comparisonValue(row))}${unit}`:`${row.label}: comparação indisponível`}
 choose(select.value,true);
};
const originalRender=render;
render=function(){
 originalRender();if(compare())updateMetric();
};
function snapshotView(){return {mode:mode.value,scope:scope.value,key:select.value,neighborhood:neighborhoodSelect.value,box:[...box],initial:[...initial],candidate:individualCandidate.value,metric:metric.value}}
function restoreView(saved){
 if(!saved)return;
 neighborhoodSelect.value=saved.neighborhood;
 if(rows.some(r=>r.key===saved.key))choose(saved.key,true);
 box=[...saved.box];initial=[...saved.initial];view();updateNeighborhoods();
}
function updateIndividual(){
 if(compare())return;
 const pedro=isPedro(),name=pedro?'Pedro Porto':'Léo Lupi',office=pedro?'vereador':'deputado estadual',year=pedro?'2024':'2026';
 document.querySelector('h1').textContent=name+' no Rio de Janeiro';document.title=name+' · Votos no RJ';
 document.querySelector('header p').textContent=`12345 · PDT · ${office} · 1º turno de ${year}`;
 document.getElementById('metric-caption').textContent=metric.value==='votes'?`Quantidade de votos válidos para ${name} · ${year}`:`Percentual dos votos válidos para ${office} · ${year}`;
 document.getElementById('share').nextElementSibling.textContent=metric.value==='votes'?`votos válidos para ${name}`:mode.value==='zones'?'dos votos válidos da zona':'dos votos válidos do município';
 document.getElementById('votes').nextElementSibling.textContent=metric.value==='votes'?'dos votos válidos do cargo':`votos válidos para ${name}`;
 document.getElementById('denominator').nextElementSibling.textContent=`votos válidos para ${office} · ${year}`;
 const total=pedro?data.pedro.total_votes:23105,valid=pedro?data.pedro.office_valid_votes:8479421;
 document.querySelector('aside .state').textContent=`${nf.format(total)} votos ${pedro?'na capital':'no RJ'} · ${pf.format(100*total/valid)}% dos votos válidos para ${office} · ${year}`;
 const municipalLink=document.querySelector('footer a[href="leo-lupi-2026-rj.csv"]');municipalLink.hidden=pedro;
 const zoneLink=document.getElementById('individual-csv');zoneLink.href=pedro?'pedro-porto-2024-capital.csv':'leo-lupi-2026-rj-zones.csv';zoneLink.textContent=pedro?'CSV Pedro Porto · 49 zonas · 2024':'CSV Léo Lupi · 165 zonas · 2026';
 document.querySelector('header .tag').textContent=pedro?'49 zonas · Capital · TSE + TRE-RJ':'92 municípios · TSE + IBGE';
}
const zoneDownload=document.querySelector('footer a[href="leo-lupi-2026-rj-zones.csv"]');zoneDownload.id='individual-csv';
let previousView=null;
function setControls(){
 const active=compare(),pedro=isPedro();
 mode.disabled=active;scope.disabled=active;mode.parentElement.hidden=pedro;
 document.getElementById('scope-label').hidden=pedro||mode.value!=='zones';
 metric.parentElement.hidden=active;individualCandidate.parentElement.hidden=active;
 document.getElementById('comparison-controls').hidden=!active;
 document.querySelector('aside .state').hidden=active;individualNote.hidden=active;
 const extra=document.getElementById('comparison-differences');if(extra)extra.hidden=!active;
}
individualCandidate.addEventListener('change',()=>{
 const saved=snapshotView(),capital=mode.value==='zones'&&scope.value==='capital';
 if(individualCandidate.value==='pedro'){mode.value='zones';scope.value='capital'}
 render();updateMetric();setControls();if(capital)restoreView(saved);
});
analysis.addEventListener('change',()=>{
 const active=compare();
 if(active){previousView=snapshotView();mode.value='zones';scope.value='capital'}
 else if(previousView){mode.value=previousView.mode;scope.value=previousView.scope;individualCandidate.value=previousView.candidate;metric.value=previousView.metric}
 render();updateMetric();setControls();
 if(!active)restoreView(previousView);
 else{document.querySelector('h1').textContent='Léo Lupi × Pedro Porto';document.querySelector('header p').textContent='Deputado estadual 2026 × Vereador 2024 · PDT · 1º turno'}
});
comparisonMetric.addEventListener('change',updateMetric);
