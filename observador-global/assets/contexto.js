/* El Observador Global — contextual glossary (free, no network calls). */
(()=>{'use strict';
const dataEl=document.getElementById('eog-context-data');
if(!dataEl)return;
let raw;
try{raw=JSON.parse(dataEl.textContent||'[]')}catch(e){return}
if(!Array.isArray(raw)||raw.length===0)return;
const entries=raw.filter(e=>e&&typeof e.title==='string'&&typeof e.text==='string'&&Array.isArray(e.terms)&&e.terms.length&&e.title.length<120&&e.text.length<650);
if(!entries.length)return;
const candidates=[];
for(let i=0;i<entries.length;i++)for(const term of entries[i].terms)if(typeof term==='string'&&term.length>2)candidates.push({term,entry:i});
candidates.sort((a,b)=>b.term.length-a.term.length);
const escapeReg=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
let re;
try{re=new RegExp('(^|[^\\p{L}\\p{N}])('+candidates.map(x=>escapeReg(x.term)).join('|')+')(?=$|[^\\p{L}\\p{N}])','giu')}catch(e){return}
const lookup=new Map(candidates.map(x=>[x.term.toLocaleLowerCase('es'),x.entry]));
const shade=document.createElement('div');shade.className='eog-shade';shade.hidden=true;
const pop=document.createElement('section');pop.className='eog-popover';pop.id='eog-context-popover';pop.setAttribute('role','dialog');pop.setAttribute('aria-modal','false');pop.setAttribute('aria-labelledby','eog-context-title');pop.hidden=true;
const head=document.createElement('div');head.className='eog-popover-head';
const headText=document.createElement('div'),kind=document.createElement('p'),title=document.createElement('h4'),body=document.createElement('p'),footer=document.createElement('p'),close=document.createElement('button');
kind.className='eog-popover-kind';title.className='eog-popover-title';title.id='eog-context-title';body.className='eog-popover-body';footer.className='eog-popover-footer';
footer.textContent='Contexto breve · Continuá leyendo sin salir de la noticia';
close.type='button';close.className='eog-popover-close';close.textContent='×';close.setAttribute('aria-label','Cerrar explicación');
headText.append(kind,title);head.append(headText,close);pop.append(head,body,footer);document.body.append(shade,pop);
let active=null;
function place(){
 if(!active||pop.hidden)return;
 if(window.innerWidth<=650){pop.style.top='auto';pop.style.left='12px';return}
 const r=active.getBoundingClientRect(),w=pop.offsetWidth,h=pop.offsetHeight,margin=12;
 let left=Math.max(margin,Math.min(r.left,window.innerWidth-w-margin));
 let top=r.bottom+11;
 if(top+h>window.innerHeight-margin)top=r.top-h-11;
 top=Math.max(margin,Math.min(top,window.innerHeight-h-margin));
 pop.style.left=left+'px';pop.style.top=top+'px'
}
function dismiss(restore=false){
 const old=active;active=null;pop.hidden=true;shade.hidden=true;
 if(old){old.setAttribute('aria-expanded','false');if(restore)old.focus({preventScroll:true})}
}
function show(button,index){
 if(active===button){dismiss();return}
 if(active)active.setAttribute('aria-expanded','false');
 active=button;button.setAttribute('aria-expanded','true');
 const e=entries[index];kind.textContent=e.kind||'EN CONTEXTO';title.textContent=e.title;body.textContent=e.text;pop.hidden=false;shade.hidden=false;place();
}
shade.addEventListener('click',()=>dismiss());
close.addEventListener('click',()=>dismiss(true));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!pop.hidden){e.preventDefault();dismiss(true)}});
window.addEventListener('resize',place,{passive:true});
window.addEventListener('scroll',place,{passive:true});

/* Criterio editorial: marcar la primera mención de las entidades realmente
   necesarias para entender cada bloque, sin dejar fuera a las del resumen. */
const seen=new Map();
const targets=document.querySelectorAll('main .lead p, main .feature h3, main .feature .story-paragraph, main .brief h3, main .brief p, main .analysis p, main .watch-list strong, main .watch-list p, main .river article strong, main .river article p');
const categoryWeight={'PERSONA':5,'EMPRESA':5,'ACTOR ARMADO':5,'INSTITUCIÓN':4,'ORGANISMO':4,'CONCEPTO':4,'CONFERENCIA':4,'LUGAR':3,'REGIÓN':3,'PAÍS':2,'JUGADOR':2};
const priorityOf=i=>{
 const e=entries[i];
 const editorial=e.priority==='esencial'?10:e.priority==='alta'?8:e.priority==='baja'?0:undefined;
 return editorial===undefined?(categoryWeight[e.kind]||3):editorial;
};
let total=0;
for(const block of targets){
 if(total>=100)break;
 const section=block.closest('article, .lead, .analysis, .watch-list, .river')||block;
 if(!seen.has(section))seen.set(section,new Set());
 const already=seen.get(section);
 const isLead=!!block.closest('.lead');
 /* El panorama editorial debe explicar los actores principales: no limitarlo a 3. */
 const maxBlock=isLead?10:block.matches('h3')?3:block.classList.contains('story-paragraph')?4:3;
 const walker=document.createTreeWalker(block,NodeFilter.SHOW_TEXT,{
  acceptNode(node){
   const parent=node.parentElement;
   if(!parent||!node.nodeValue.trim()||parent.closest('a,button,script,style,.sources,.eog-term,.eog-popover'))return NodeFilter.FILTER_REJECT;
   return NodeFilter.FILTER_ACCEPT
  }
 });
 const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
 const matches=[];let counter=0;
 for(const node of nodes){
  re.lastIndex=0;let match;
  while((match=re.exec(node.nodeValue))!==null){
   const word=match[2],index=lookup.get(word.toLocaleLowerCase('es'));
   if(index===undefined||already.has(index))continue;
   const start=match.index+match[1].length;
   matches.push({node,start,end:start+word.length,word,index,sequence:counter++});
  }
 }
 if(!matches.length)continue;
 /* Selección por relevancia: en textos densos, personas y entidades
    esenciales tienen precedencia frente a referencias conocidas. */
 const firstByEntry=new Map();
 for(const m of matches){
  if(!firstByEntry.has(m.index))firstByEntry.set(m.index,m);
 }
 const selected=[...firstByEntry.values()]
  .sort((a,b)=>priorityOf(b.index)-priorityOf(a.index)||a.sequence-b.sequence)
  .slice(0,Math.min(maxBlock,100-total));
 const byNode=new Map();
 for(const m of selected){
  if(!byNode.has(m.node))byNode.set(m.node,[]);
  byNode.get(m.node).push(m);
  already.add(m.index);
  total++;
 }
 for(const [node,matchesInNode] of byNode){
  matchesInNode.sort((a,b)=>a.start-b.start);
  const text=node.nodeValue,frag=document.createDocumentFragment();
  let cursor=0;
  for(const match of matchesInNode){
   frag.appendChild(document.createTextNode(text.slice(cursor,match.start)));
   const btn=document.createElement('button');
   btn.type='button';btn.className='eog-term';btn.textContent=match.word;
   btn.setAttribute('aria-label',match.word+': tocar para saber más');
   btn.setAttribute('aria-expanded','false');
   btn.setAttribute('aria-haspopup','dialog');
   btn.setAttribute('aria-controls',pop.id);
   btn.addEventListener('click',()=>show(btn,match.index));
   frag.appendChild(btn);
   cursor=match.end;
  }
  frag.appendChild(document.createTextNode(text.slice(cursor)));
  node.replaceWith(frag);
 }
}

if(total){
 const first=document.querySelector('main .lead');
 if(first){const tip=document.createElement('div');tip.className='eog-context-hint';const dot=document.createElement('span');dot.className='eog-mini-dot';dot.setAttribute('aria-hidden','true');tip.append(dot,document.createTextNode('Tocá las palabras subrayadas para ver su contexto'));first.append(tip)}
}
})();