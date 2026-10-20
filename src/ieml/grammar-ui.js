/**
 * ADA IEML Lab — script grammar and AST inspection.
 *
 * The lexical scanner reimplements token categories of the seven supplied
 * historical source files; actual parsing requires an installed IEMLdev/ieml
 * package. Input/output are textContent-only, never innerHTML.
 */
const $ = id => document.getElementById(id);
const API = "http://127.0.0.1:8001";

function setStatus(msg) {
  $("grammarStatus").textContent = msg;
}
async function call(path, body=null) {
  const res=await fetch(API+path, body===null?undefined:{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const data=await res.json().catch(()=>({}));
  if(!res.ok)throw Error(typeof data.detail==="string" ? data.detail : "HTTP "+res.status);
  return data;
}
function addCell(row,text) {
  const cell=document.createElement("td");
  cell.textContent=String(text);
  row.append(cell);
}
function showLex(data) {
  const table=$("grammarTokens");
  table.replaceChildren();
  for(const token of data.tokens) {
    const row=document.createElement("tr");
    for(const text of [token.type, token.value, token.position,
                       token.line+":"+token.column])addCell(row,text);
    table.append(row);
  }
  const err=$("grammarErrors");
  err.replaceChildren();
  for(const e of data.errors){
    const line=document.createElement("p");
    line.textContent="Carácter inválido "+JSON.stringify(e.character)+
      " en línea "+e.line+", columna "+e.column;
    err.append(line);
  }
  $("grammarLexJSON").textContent=JSON.stringify(data,null,2);
  setStatus(data.lexicallyValid
    ? data.tokens.length+" tokens reconocidos. La sintaxis aún NO está verificada."
    : "Tokenización inválida: "+data.errors.length+" carácter(es) no admitido(s).");
}
async function lex() {
  const expression=$("grammarExpression").value;
  setStatus("Identificando tokens IEML…");
  try{
    showLex(await call("/api/upstream/script/lex?"+
      new URLSearchParams({expression})));
  }catch(e){setStatus("Error léxico: "+e.message)}
}
function renderAST(structure) {
  const tree=$("grammarAST");
  tree.replaceChildren();
  const stack=[{node:structure,level:0}];
  while(stack.length){
    const {node,level}=stack.pop();
    const line=document.createElement("p");
    line.style.paddingLeft=(level*20)+"px";
    line.textContent=(level?"↳ ":"")+node.type+" · "+node.canonical+
      " · capa "+node.layer+" · cardinal "+node.cardinal+
      (node.empty?" · vacío":"")+(node.paradigm?" · paradigma":"");
    tree.append(line);
    for(const child of [...(node.children||[])].reverse())
      stack.push({node:child,level:level+1});
    if(node.truncatedChildren){
      const span=document.createElement("small");
      span.textContent="Subárbol abreviado para limitar profundidad.";
      span.style.paddingLeft=((level+1)*20)+"px";
      tree.append(span);
    }
  }
}
async function inspect(){
  const expression=$("grammarExpression").value;
  setStatus("Solicitando análisis del parser IEML original…");
  try{
    const data=await call("/api/upstream/script/inspect",{expression});
    renderAST(data.structure);
    $("grammarASTJSON").textContent=JSON.stringify(data,null,2);
    setStatus("Sintaxis aceptada por parser instalado. Capa "+
      data.structure.layer+", cardinalidad "+data.structure.cardinal+
      ". La pertenencia al diccionario NO está certificada.");
  }catch(e){
    $("grammarAST").replaceChildren();
    $("grammarASTJSON").textContent="";
    setStatus("Inspección no disponible: "+e.message+
      ". La tokenización puede ejecutarse sin instalar el parser antiguo.");
  }
}
$("grammarLexBtn").addEventListener("click",lex);
$("grammarInspectBtn").addEventListener("click",inspect);
