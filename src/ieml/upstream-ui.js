/**
 * UI for optional upstream IEMLdev/ieml grammar adapter.
 * No remote code is loaded in the browser. Python backend validates syntax
 * only if the GPL-3.0 upstream package is installed and operational.
 */
const $=id=>document.getElementById(id);
const BASE_URL="http://127.0.0.1:8001";
const ROLE_ROWS=[
  [0,"Raíz / proceso",null,"E:S:. · E:T:. · E:B:."],
  [1,"Iniciador","E:.n.-"],
  [2,"Interactante","E:.d.-"],
  [3,"Destinatario","E:.k.-"],
  [4,"Causalidad","E:.s.-"],
  [5,"Tiempo","E:.t.-"],
  [6,"Lugar","E:.l.-"],
  [7,"Intención","E:.m.-"],
  [8,"Manera","E:.f.-"]
];
const renderRoles = () => {
  const body=$("upstreamRolesRows");
  body.replaceChildren();
  for(const [index,name,address,extra] of ROLE_ROWS){
    const row=document.createElement("tr");
    for(const value of ["e"+index,name,address??"—",extra??"—"]){
      const td=document.createElement("td");td.textContent=value;row.append(td);
    }
    body.append(row);
  }
};
const renderOutput = result=>{
  $("upstreamParseJSON").textContent=JSON.stringify(result,null,2);
  $("upstreamResult").textContent=
    result.syntaxValid
      ? "Sintaxis aceptada · "+result.objectType+" · "+result.canonical+
        " (el diccionario NO se ha validado)"
      : "Sintaxis no validada";
};
async function request(path,body){
  const response=await fetch(BASE_URL+path,body?{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  }:undefined);
  if(!response.ok){
    const data=await response.json().catch(()=>({}));
    throw Error((typeof data.detail==="string" ? data.detail : "HTTP "+response.status).slice(0,400));
  }
  return response.json();
}
async function checkStatus(){
  const target=$("upstreamStatus");
  target.textContent="Verificando adaptador local…";
  try{
    const data=await request("/api/upstream/status");
    target.textContent=data.available
      ? "Paquete IEML detectado: versión "+(data.installedVersion||"sin metadata")+
        ". La disponibilidad del parser se comprueba al analizar."
      : "Paquete IEMLdev/ieml no instalado. Instálalo por separado si deseas validación sintáctica.";
    $("upstreamStatusJSON").textContent=JSON.stringify(data,null,2);
  }catch(error){
    target.textContent="Backend no disponible: "+error.message+
      ". La tabla de roles procede del código publicado por IEMLdev.";
  }
}
async function run(){
  const expression=$("upstreamExpression").value.trim();
  const kind=$("upstreamKind").value;
  if(!expression){$("upstreamResult").textContent="Escribe una expresión IEML.";return;}
  const target=$("upstreamResult");
  target.textContent="Analizando sintaxis con la biblioteca upstream…";
  try{
    const data=await request("/api/upstream/parse",{expression,kind});
    renderOutput(data);
  }catch(error){
    target.textContent="Sin validación: "+error.message;
    $("upstreamParseJSON").textContent="";
  }
}
renderRoles();
$("upstreamParseBtn").addEventListener("click",run);
$("upstreamStatusBtn").addEventListener("click",checkStatus);
