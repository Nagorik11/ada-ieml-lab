/**
 * ADA IEML Lab — 25-cell alphabet explorer.
 * Derived from the user-provided ieml-alphabet.js.
 * This 5×5 matrix/6D graphic embedding is an experimental research model,
 * distinct from the v0.4 parser's six primitives (E,U,A,S,B,T).
 */
export const AXES = Object.freeze([
  { key:"U", en:"Virtual", es:"Virtual" },
  { key:"A", en:"Actual", es:"Actual" },
  { key:"S", en:"Sign", es:"Signo" },
  { key:"B", en:"Being", es:"Ser" },
  { key:"T", en:"Thing", es:"Cosa" }
]);
const SEGMENTS = {
  U: { substance:[0.5,0,0.5], attribute:[0,0,0] },
  A: { substance:[0.5,0.5,0], attribute:[0,0.5,0] },
  S: { substance:[0.75,0,0.75], attribute:[0.5,0,0.5] },
  B: { substance:[0.5,0,0], attribute:[0,0.5,0.5] },
  T: { substance:[0,0,1], attribute:[0,0,1] }
};
const RECORDS = [
  ["wo","U","U","Reflect / Virtual of Virtual","Orientar / Reflexionar (Virtual de lo Virtual)"],
  ["wa","U","A","Act / Actual of Virtual","Actuar (Actual de lo Virtual)"],
  ["y","U","S","Know / Sign of Virtual","Saber (Signo de lo Virtual)"],
  ["o","U","B","Want / Being of Virtual","Querer (Ser de lo Virtual)"],
  ["e","U","T","Be able / Thing of Virtual","Poder (Cosa de lo Virtual)"],
  ["wu","A","U","Perceive / Virtual of Actual","Percibir (Virtual de lo Actual)"],
  ["we","A","A","Reconstitute / Actual of Actual","Reconstituir (Actual de lo Actual)"],
  ["u","A","S","State / Sign of Actual","Expresar / Enunciar (Signo de lo Actual)"],
  ["a","A","B","Commit / Being of Actual","Comprometerse (Ser de lo Actual)"],
  ["i","A","T","Do / Thing of Actual","Hacer (Cosa de lo Actual)"],
  ["j","S","U","Signifier change / Idea","Idea / Cambio de Significante"],
  ["g","S","A","Document change / Message","Mensaje / Cambio de Documento"],
  ["s","S","S","Thought / Sign of Sign","Pensamiento (Signo del Signo)"],
  ["b","S","B","Language / Being of Sign","Lenguaje (Ser del Signo)"],
  ["t","S","T","Memory / Thing of Sign","Memoria (Cosa del Signo)"],
  ["h","B","U","Meaning change / Subject","Sujeto / Cambio de Significado"],
  ["c","B","A","Personal change / Individual","Persona / Cambio Personal"],
  ["k","B","S","Society / Sign of Being","Sociedad (Signo del Ser)"],
  ["m","B","B","Affect / Being of Being","Afecto (Ser del Ser)"],
  ["n","B","T","World / Thing of Being","Mundo (Cosa del Ser)"],
  ["p","T","U","Referent change / Object","Objeto / Cambio de Referente"],
  ["x","T","A","Material change / Body","Cuerpo / Cambio Material"],
  ["d","T","S","Truth / Sign of Thing","Verdad (Signo de la Cosa)"],
  ["f","T","B","Life / Being of Thing","Vida (Ser de la Cosa)"],
  ["l","T","T","Space / Thing of Thing","Espacio (Cosa de la Cosa)"]
];
export const ALPHABET = Object.freeze(RECORDS.map(([char,row,col,en,es]) => Object.freeze({
  char,row,col,en,es,
  vector:Object.freeze([...SEGMENTS[row].substance,...SEGMENTS[col].attribute])
})));
const BY_SYMBOL = new Map(ALPHABET.map(item => [item.char,item]));
const BY_COORDS = new Map(ALPHABET.map(item => [item.row+":"+item.col,item]));
export function getChar(symbol) {
  return BY_SYMBOL.get(String(symbol ?? "").toLowerCase()) ?? null;
}
export function getCharByCoords(row,col) {
  return BY_COORDS.get(row+":"+col) ?? null;
}
export function getAlphabetMatrix() {
  return AXES.map(row => AXES.map(col => getCharByCoords(row.key,col.key)));
}
export function cosineSimilarity(left,right) {
  const a=typeof left==="string"?getChar(left):left;
  const b=typeof right==="string"?getChar(right):right;
  if(!a||!b) return null;
  const dot=a.vector.reduce((s,v,i)=>s+v*b.vector[i],0);
  const an=Math.hypot(...a.vector),bn=Math.hypot(...b.vector);
  return an && bn ? dot/(an*bn) : 0;
}
export function nearestSymbols(symbol,count=5) {
  const target=getChar(symbol);
  if(!target) return [];
  return ALPHABET.filter(x=>x.char!==target.char)
    .map(x=>({char:x.char,score:cosineSimilarity(target,x)}))
    .sort((a,b)=>b.score-a.score||a.char.localeCompare(b.char))
    .slice(0,Math.max(0,Math.min(24,count)));
}
/** Only explicit alphabet tokens are read. Ordinary Spanish words are never
 * split into individual letters and misrepresented as IEML expressions. */
export function tokenizeSymbols(expression) {
  return String(expression ?? "").trim().toLowerCase()
    .split(/[\s,;→|>]+/u).filter(Boolean)
    .map(token=>({token,entry:getChar(token),valid:!!getChar(token)}));
}
