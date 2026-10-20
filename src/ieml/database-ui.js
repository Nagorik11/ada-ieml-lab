/**
 * ADA IEML Lab — IEMLDatabase.ipynb integration.
 *
 * Historical read-only IEMLdev/ieml-language database panel. No SSH keys,
 * hardcoded personal paths, or automatic clones. Requests use local FastAPI.
 */
const $ = id => document.getElementById(id);
const API = "http://127.0.0.1:8001";
let currentTerm = "wa.";

async function query(path, params) {
  const url = API+path+"?"+new URLSearchParams(params);
  const response = await fetch(url);
  if (!response.ok) {
    const data = await response.json().catch(()=>({}));
    const problem=typeof data.detail==="string" ? data.detail : "HTTP "+response.status;
    throw Error(problem.slice(0,500));
  }
  return response.json();
}
function notice(id,msg) { $(id).textContent=String(msg); }
function showJSON(id,data){ $(id).textContent=JSON.stringify(data,null,2); }
function append(tag,text,parent){
  const node=document.createElement(tag);
  node.textContent=String(text);
  parent.append(node);
  return node;
}
function showDescriptors(data){
  const table=$("databaseDescriptorRows");table.replaceChildren();
  for(const row of data.items){
    const tr=document.createElement("tr");
    for(const value of [row.ieml,row.language,row.category,row.values.join("; ")])
      append("td",value,tr);
    table.append(tr);
  }
  notice("databaseDescriptorStatus",data.items.length+
    " descriptor(es) del checkout local. Fuente: IEMLdev/ieml-language.");
  showJSON("databaseDescriptorJSON",data);
}
async function status(){
  try {
    const data=await query("/api/upstream/database/status",{});
    notice("databaseStatus",
      data.readyToAttempt ?
      "Copia IEML configurada y paquete detectado; consultas sujetas a compatibilidad." :
      "Falta copia local y/o paquete upstream. Configura IEML_DATABASE_PATH; la API nunca clona por SSH.");
    showJSON("databaseStatusJSON",data);
  } catch(err) { notice("databaseStatus","API local no disponible: "+err.message); }
}
async function descriptors(term){
  const value=String(term||"").trim();
  if(!value){notice("databaseDescriptorStatus","Escribe un término IEML.");return;}
  currentTerm=value;
  notice("databaseDescriptorStatus","Consultando descriptores…");
  try {
    const lang=$("databaseLanguage").value||undefined;
    showDescriptors(await query("/api/upstream/database/descriptors",{
      term:value,...(lang?{language:lang}:{})
    }));
  } catch(err) { notice("databaseDescriptorStatus","No disponible: "+err.message); }
}
async function list(){
  notice("databaseListStatus","Cargando términos publicados…");
  try {
    const kind=$("databaseKind").value||undefined;
    const q=$("databaseListQuery").value.trim();
    const data=await query("/api/upstream/database/terms",{
      ...(kind?{kind}:{}),q,limit:"25",offset:"0"
    });
    const box=$("databaseTermResults");box.replaceChildren();
    for(const term of data.items){
      const btn=append("button",term,box);
      btn.className="alt";
      btn.type="button";
      btn.addEventListener("click",()=>{
        $("databaseTerm").value=term;
        descriptors(term);
      });
    }
    notice("databaseListStatus",data.items.length+" / "+data.total+
      " términos mostrados. Selecciona uno para ver descriptores.");
    showJSON("databaseListJSON",data);
  }catch(err){notice("databaseListStatus","No disponible: "+err.message);}
}
async function relations(){
  const term=$("databaseTerm").value.trim();
  if(!term){notice("databaseRelationStatus","Selecciona un término.");return;}
  notice("databaseRelationStatus","Consultando grafo de relaciones…");
  try {
    const data=await query("/api/upstream/database/relations",{
      term,relation:$("databaseRelationKind").value,limit:"20"
    });
    const box=$("databaseRelationResults");box.replaceChildren();
    for(const item of data.items)append("span",item,box).className="chip";
    notice("databaseRelationStatus",data.total+
      " relaciones encontradas; se muestran hasta "+data.limit+".");
    showJSON("databaseRelationJSON",data);
  }catch(err){notice("databaseRelationStatus","No disponible: "+err.message);}
}
async function table(){
  const term=$("databaseTableTerm").value.trim();
  if(!term){notice("databaseTableStatus","Escribe la expresión de una tabla.");return;}
  notice("databaseTableStatus","Leyendo tabla jerárquica…");
  try {
    const data=await query("/api/upstream/database/table",{term});
    const body=$("databaseTableRows");body.replaceChildren();
    for(const row of data.cells){
      const tr=document.createElement("tr");
      for(const value of row)append("td",value,tr);
      body.append(tr);
    }
    notice("databaseTableStatus","Tabla "+data.term+
      " · matriz "+data.shape.join(" × ")+
      " · padre: "+(data.parent||"no definido"));
    showJSON("databaseTableJSON",data);
  }catch(err){notice("databaseTableStatus","No disponible: "+err.message);}
}
$("databaseStatusBtn").addEventListener("click",status);
$("databaseListBtn").addEventListener("click",list);
$("databaseDescriptorBtn").addEventListener("click",()=>{
  descriptors($("databaseTerm").value);
});
$("databaseRelationsBtn").addEventListener("click",relations);
$("databaseTableBtn").addEventListener("click",table);
