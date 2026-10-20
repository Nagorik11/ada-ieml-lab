/**
 * ADA IEML Lab — LatticeStructure viewer.
 * Displays a directed hierarchy (parents/child) and an independent
 * containment relation (contains/contained_by). Mathematical join and meet
 * operations are NOT inferred.
 */
const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
let lastGraph = null;
function svgEl(tag, attrs, parent, text) {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs||{})) node.setAttribute(key, String(value));
  if (text !== undefined) node.textContent = text;
  if (parent) parent.append(node);
  return node;
}
async function post(path, body) {
  const response = await fetch("http://127.0.0.1:8001"+path, {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  if (!response.ok) {
    const err = await response.json().catch(()=>({}));
    throw Error(typeof err.detail==="string" ? err.detail : "HTTP "+response.status);
  }
  return response.json();
}
function layout(nodes) {
  const byId = new Map(nodes.map(n => [n.word,n]));
  const depths = new Map();
  function depth(key) {
    if(depths.has(key)) return depths.get(key);
    const node=byId.get(key);
    // Backend rejects cyclic parent hierarchies.
    const d=node.parents.length?1+Math.max(...node.parents.map(depth)):0;
    depths.set(key,d);return d;
  }
  for(const n of nodes)depth(n.word);
  const layers=new Map();
  for(const n of nodes){
    const d=depth(n.word);
    if(!layers.has(d)) layers.set(d,[]);
    layers.get(d).push(n.word);
  }
  const positions=new Map();
  let y=65;
  for(const d of [...layers.keys()].sort((a,b)=>a-b)){
    const names=layers.get(d).sort();
    for(let i=0;i<names.length;i++){
      const group=Math.floor(i/7);
      const col=i%7;
      const rowCount=Math.min(7,names.length-group*7);
      positions.set(names[i], {x:(col+1)*920/(rowCount+1),y:y+group*130});
    }
    y+=Math.ceil(names.length/7)*130;
  }
  return {positions,height:Math.max(220,y)};
}
function render(graph) {
  lastGraph = graph;
  const status=$("latticeStatus");
  status.textContent=graph.nodeCount+" nodos, "+graph.parentEdgeCount+
    " enlaces de ascendencia, "+graph.containmentEdgeCount+
    " enlaces de inclusión; raíces: "+(graph.roots.join(", ")||"ninguna");
  $("latticeJSON").textContent=JSON.stringify(graph,null,2);
  const table=$("latticeRows");table.replaceChildren();
  for(const n of graph.nodes) {
    const tr=document.createElement("tr");
    for(const text of [n.word,n.parents.join(", ")||"—",n.child.join(", ")||"—",
                       n.contains.join(", ")||"—",n.contained_by.join(", ")||"—"]) {
      const td=document.createElement("td");
      td.textContent=text;tr.append(td);
    }
    table.append(tr);
  }
  const svg=$("latticeSVG");svg.replaceChildren();
  if(!graph.nodes.length) return;
  if(graph.nodes.length>49) {
    svg.setAttribute("viewBox","0 0 920 110");
    svgEl("text",{x:20,y:50,fill:"#bad6f0","font-size":18},svg,
          "Se muestran tablas y JSON. Para el grafo, selecciona hasta 49 nodos.");
    return;
  }
  const {positions,height}=layout(graph.nodes);
  svg.setAttribute("viewBox","0 0 920 "+height);
  svg.setAttribute("role","img");
  svg.setAttribute("aria-label","Grafo de ascendencia e inclusión de "+graph.nodeCount+" nodos");
  const defs=svgEl("defs",{},svg);
  for(const [kind,color] of [["parent","#64d9b5"],["contains","#e7bb78"]]){
    const marker=svgEl("marker",{
      id:"lattice-arrow-"+kind,markerWidth:9,markerHeight:9,
      refX:19,refY:3,orient:"auto",markerUnits:"strokeWidth"
    },defs);
    svgEl("path",{d:"M0,0 L0,6 L6,3 z",fill:color},marker);
  }
  for(const edge of graph.edges){
    const a=positions.get(edge.source),b=positions.get(edge.target);
    if(!a||!b)continue;
    const color=edge.relation==="parent"?"#64d9b5":"#e7bb78";
    const line=svgEl("line",{
      x1:a.x,y1:a.y,x2:b.x,y2:b.y,
      stroke:color,"stroke-width":2,
      "stroke-dasharray":edge.relation==="contains"?"5 5":"",
      "marker-end":"url(#lattice-arrow-"+edge.relation+")"
    },svg);
    svgEl("title",{},line,edge.source+" → "+edge.target+" ("+edge.relation+")");
  }
  const roots=new Set(graph.roots);
  for(const node of graph.nodes){
    const p=positions.get(node.word);
    const g=svgEl("g",{},svg);
    svgEl("rect",{
      x:p.x-56,y:p.y-18,width:112,height:36,rx:9,
      fill:roots.has(node.word)?"#14504c":"#223b59",
      stroke:roots.has(node.word)?"#73ddbe":"#96b8d8",
      "stroke-width":1.4
    },g);
    const short=node.word.length>16?node.word.slice(0,13)+"…":node.word;
    svgEl("text",{
      x:p.x,y:p.y+5,"text-anchor":"middle",fill:"#f0f8ff",
      "font-size":13,"font-family":"monospace"
    },g,short);
    svgEl("title",{},g,node.word+
      (roots.has(node.word)?" (sin padre registrado)":""));
  }
}
function parseTerms() {
  const items=$("latticeTerms").value.split(/[\n,;]+/u).map(x=>x.trim()).filter(Boolean);
  if(!items.length)throw Error("Introduce al menos un término IEML.");
  if(items.length>300)throw Error("Máximo 300 términos.");
  return items;
}
async function fromReference() {
  $("latticeStatus").textContent="Consultando el índice IEML v0.4 importado…";
  try {
    render(await post("/api/lattice/reference",{terms:parseTerms()}));
  } catch(err) {
    $("latticeStatus").textContent="No se pudo consultar el índice: "+err.message;
  }
}
async function fromEdges() {
  $("latticeStatus").textContent="Validando relaciones declaradas…";
  try {
    const parsed=JSON.parse($("latticeEdgesJSON").value);
    if(!Array.isArray(parsed.words)||!Array.isArray(parsed.edges))
      throw Error("Se requieren arrays words y edges.");
    render(await post("/api/lattice/edges",parsed));
  } catch(err) {
    $("latticeStatus").textContent="No se pudo construir la retícula: "+err.message;
  }
}
$("latticeReferenceBtn").addEventListener("click",fromReference);
$("latticeEdgesBtn").addEventListener("click",fromEdges);
