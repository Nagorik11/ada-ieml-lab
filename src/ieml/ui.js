import {AXES, getChar, getAlphabetMatrix, nearestSymbols, cosineSimilarity,
        tokenizeSymbols} from "./alphabet.js";
import {IEML_DOCS, findDocs} from "./docs.js";

const $ = (id) => document.getElementById(id);
const el = (tag, text, parent, className="") => {
  const node=document.createElement(tag);
  node.textContent=String(text);
  if(className) node.className=className;
  parent.appendChild(node);
  return node;
};
function renderAlphabet() {
  const tbody=$("alphabetBody");
  const matrix=getAlphabetMatrix();
  tbody.replaceChildren();
  for(let row=0;row<5;row++) {
    const tr=document.createElement("tr");
    el("th", AXES[row].key+" · "+AXES[row].es,tr);
    for(let col=0;col<5;col++) {
      const td=document.createElement("td");
      const character=matrix[row][col];
      const button=el("button",character.char,td,"alpha-cell");
      button.type="button";
      button.title=character.es;
      button.setAttribute("aria-label",character.char+": "+character.es);
      button.addEventListener("click",()=>selectSymbol(character.char));
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
}
let current="wo";
function selectSymbol(symbol) {
  const entry=getChar(symbol);
  if(!entry)return;
  current=entry.char;
  $("alphabetSelected").textContent=entry.char+" · "+entry.es;
  $("alphabetDescription").textContent="EN: "+entry.en+" | Sustancia: "+entry.row+
    " | Atributo: "+entry.col;
  $("alphabetVector").textContent="Vector gráfico 6D: ["+entry.vector.join(", ")+"]";
  $("alphaComparison").textContent="";
  const nearest=nearestSymbols(symbol,4);
  $("alphabetNeighbors").replaceChildren();
  nearest.forEach(n=>el("span",n.char+" ("+n.score.toFixed(3)+")",
                        $("alphabetNeighbors"),"chip"));
  document.querySelectorAll(".alpha-cell").forEach(button=>{
    button.setAttribute("aria-pressed",String(button.textContent===symbol));
  });
}
function compareSymbols() {
  const other=$("alphabetCompare").value.trim().toLowerCase();
  const score=cosineSimilarity(current,other);
  $("alphaComparison").textContent=score===null
    ?"Carácter no reconocido: introduzca uno de los 25 símbolos completos."
    :"Similitud coseno entre vectores gráficos 6D: "+score.toFixed(4)+
     ". No equivale a proximidad semántica validada.";
}
function analyzeSymbolExpression() {
  const tokens=tokenizeSymbols($("alphabetExpression").value);
  const valid=tokens.filter(t=>t.valid);
  const invalid=tokens.filter(t=>!t.valid);
  const output={schema:"ada-ieml-alphabet/v1",model:"research-5x5-6d",
    formalIEML:false,symbols:valid.map(t=>({
      char:t.entry.char,row:t.entry.row,col:t.entry.col,vector:t.entry.vector,
      es:t.entry.es
    })),unknown:invalid.map(t=>t.token)};
  $("alphabetOutput").textContent=JSON.stringify(output,null,2);
  $("alphabetParseStatus").textContent=valid.length+" símbolo(s) reconocido(s), "+
    invalid.length+" desconocido(s). Los términos deben estar separados por espacios o comas.";
}
function renderDocs(query="") {
  const box=$("iemlDocsResults");
  box.replaceChildren();
  const docs=findDocs(query);
  if(!docs.length)el("p","No hay documentos locales con ese término.",box);
  for(const doc of docs) {
    const article=el("article","",box,"ieml-doc");
    el("h3",doc.title,article);
    el("small",doc.source+" · "+doc.category,article);
    el("p",doc.text,article);
    el("small","Etiquetas: "+doc.tags.join(", "),article);
  }
  $("iemlDocsCount").textContent=docs.length+" / "+IEML_DOCS.length+" registros";
}
async function searchReference() {
  const q=$("referenceQuery").value.trim();
  if(!q) {
    $("referenceStatus").textContent="Introduce un término en inglés o francés.";
    return;
  }
  const status=$("referenceStatus");
  status.textContent="Consultando referencia IEML v0.4…";
  const tbody=$("referenceRows");tbody.replaceChildren();
  try {
    // The API is intentionally local; GitHub Pages cannot run this backend.
    const url="http://127.0.0.1:8001/api/reference/search?"+
      new URLSearchParams({q,limit:"15"});
    const res=await fetch(url);
    if(!res.ok) {
      const data=await res.json().catch(()=>({}));
      throw Error(data.detail||("HTTP "+res.status));
    }
    const data=await res.json();
    for(const result of data.results) {
      const tr=document.createElement("tr");
      for(const value of [result.term,
          Object.entries(result.labels??{}).map(([lang,names])=>lang+": "+names.join("; ")).join(" | "),
          result.match])el("td",value,tr);
      tbody.appendChild(tr);
    }
    status.textContent=data.results.length+" candidatos por etiqueta; revise cada correspondencia.";
  } catch(error) {
    status.textContent="Referencia no disponible: "+error.message+
      ". Inicie el backend e importe el JSON de referencia.";
  }
}
renderAlphabet();
selectSymbol(current);
renderDocs();
$("alphabetCompareBtn").addEventListener("click",compareSymbols);
$("alphabetAnalyzeBtn").addEventListener("click",analyzeSymbolExpression);
$("iemlDocsSearch").addEventListener("input",e=>renderDocs(e.target.value));
$("referenceSearchBtn").addEventListener("click",searchReference);
