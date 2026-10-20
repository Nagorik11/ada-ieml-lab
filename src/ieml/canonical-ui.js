/**
 * ADA IEML Lab — nine orthonormal structural basis assignment UI.
 * Requires the local FastAPI backend; does not synthesize formal IEML USLs.
 */
const byId = id => document.getElementById(id);
const ROLES = [
  "Raíz","Iniciador","Interactante","Destinatario","Causalidad",
  "Tiempo","Lugar","Intención","Manera"
];
let lastResult = null;
const projectionBox=byId("canonicalProjection");
for(let i=0;i<ROLES.length;i++){
  const label=document.createElement("label");
  label.className="canonical-choice";
  const input=document.createElement("input");
  input.type="checkbox";input.value=String(i);input.checked=true;
  input.className="canonical-projection-checkbox";
  label.append(input,document.createTextNode(" e"+i+" · "+ROLES[i]));
  projectionBox.append(label);
}
function item(parent,tag,value) {
  const element=document.createElement(tag);
  element.textContent=String(value);
  parent.append(element);
  return element;
}
function visualBar(cell,value) {
  const holder=document.createElement("div");
  holder.className="canonical-bar-track";
  const bar=document.createElement("span");
  bar.className="canonical-bar-fill";
  bar.style.width=(Math.min(Math.abs(value),1)*100)+"%";
  holder.append(bar);
  cell.append(holder);
}
function render(output) {
  const table=byId("canonicalRows");table.replaceChildren();
  const graphs=byId("canonicalVectors");graphs.replaceChildren();
  for(const [sentenceIndex,record] of output.sentences.entries()){
    const canonical=record.canonical;
    const heading=document.createElement("tr");
    heading.className="canonical-sentence";
    const summary=item(heading,"th","Oración "+(sentenceIndex+1)+": "+record.sentence);
    summary.colSpan=5;table.append(heading);
    for(const role of canonical.roles) {
      const row=document.createElement("tr");
      item(row,"td",role.basis);
      item(row,"td",role.name);
      item(row,"td",role.evidence||"—");
      const weight=item(row,"td",role.coefficient.toFixed(3));
      weight.className="canonical-number";
      const graph=document.createElement("td");
      visualBar(graph,role.coefficient);
      row.append(graph);
      table.append(row);
    }
    const block=document.createElement("div");
    block.className="canonical-result";
    item(block,"p","Oración "+(sentenceIndex+1)+" · s = ["+
      canonical.vector.map(v=>Number(v.toFixed(3))).join(", ")+"]");
    item(block,"p","Norma Euclidiana: "+canonical.norm.toFixed(4)+
      " · Proyección: ["+canonical.projection.vector.map(v=>Number(v.toFixed(3))).join(", ")+"]");
    if(canonical.accent)item(block,"p","Acento "+canonical.accent.basis+
      " × "+canonical.accent.scale+": ["+canonical.accent.vector.map(v=>Number(v.toFixed(3))).join(", ")+"]");
    graphs.append(block);
  }
  byId("canonicalJSON").textContent=JSON.stringify(output,null,2);
  const recognized=output.sentences.reduce((sum,s)=>sum+s.canonical.activeRoleIndices.length,0);
  byId("canonicalStatus").textContent=
    output.sentences.length+" oración(es), "+recognized+" asignaciones de rol. "+
    "Representación estructural experimental, no codificación semántica formal.";
}
async function run() {
  const status=byId("canonicalStatus");
  const text=byId("naturalText").value.trim();
  if(!text){status.textContent="Escribe una oración en la sección 07.";return;}
  status.textContent="Extrayendo roles y proyectando sobre e0…e8…";
  const selected=[...document.querySelectorAll(".canonical-projection-checkbox:checked")]
    .map(x=>Number(x.value));
  const accentChoice=byId("canonicalAccent").value;
  const accent_role=accentChoice===""?null:Number(accentChoice);
  const accent_scale=Number(byId("canonicalScale").value);
  if(!Number.isFinite(accent_scale)||accent_scale<0||accent_scale>10){
    status.textContent="Escala de acento inválida (0 a 10).";return;
  }
  try {
    const res=await fetch("http://127.0.0.1:8001/api/canonical",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        text,mode:byId("canonicalMode").value,
        accent_role,accent_scale,projection_roles:selected
      })
    });
    if(!res.ok){
      const details=await res.json().catch(()=>({}));
      const reason=typeof details.detail==="string"?details.detail:("HTTP "+res.status);
      throw Error(reason);
    }
    const output=await res.json();
    lastResult=output;
    render(output);
  }catch(err){
    status.textContent="No se pudo calcular: "+err.message+
      ". Revisa que FastAPI y spaCy estén disponibles en el puerto 8001.";
  }
}
function exportJSON() {
  if(!lastResult){byId("canonicalStatus").textContent="Analiza un texto antes de exportar.";return;}
  const url=URL.createObjectURL(new Blob([JSON.stringify(lastResult,null,2)],
    {type:"application/json"}));
  const a=document.createElement("a");a.href=url;a.download="ada-ieml-canonical-r9.json";
  a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
byId("canonicalRun").addEventListener("click",run);
byId("canonicalExport").addEventListener("click",exportJSON);
