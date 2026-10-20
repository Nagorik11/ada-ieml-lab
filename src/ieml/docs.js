/**
 * Curated offline documentation from the user-supplied ieml-docs.js.
 * Research notes are *not* official IEML grammar specifications or verified
 * results of a neural/quantum benchmark.
 */
export const IEML_DOCS = Object.freeze([
  Object.freeze({
    id:"ieml_semantic_space_001",
    title:"Representación algebraica del espacio semántico IEML",
    author:"Fernando Valenzuela",
    date:"2026-06-11",
    source:"User-provided PDF: Linear Algebraic Representation of the IEML Semantic Space",
    category:"modelo matemático propuesto",
    tags:["ieml","semantic_space","vector_space","neuro_symbolic","recursive","block_matrix"],
    text:"Modelo propuesto: V ≅ R⁹ con base canónica e₀…e₈. Roles: raíz, iniciador, interactante, destinatario, causalidad, tiempo, lugar, intención y manera. Una oración se expresa formalmente como s = Σ cᵢeᵢ una vez que se hayan definido sus coeficientes numéricos. Se estudian identidad I₉, composición recursiva en bloques, redes neuronales recursivas, GNN y arquitecturas neuro-simbólicas. Estas aplicaciones son propuestas teóricas, no medidas experimentales de rendimiento."
  }),
  Object.freeze({
    id:"ieml_alphabet_001",
    title:"Alfabeto experimental IEML 5 × 5",
    author:"IEML Master (atribución del archivo proporcionado)",
    date:"2026",
    source:"User-provided JavaScript: ieml-alphabet.js and ieml-docs.js",
    category:"modelo de alfabeto experimental",
    tags:["ieml","alphabet","5x5_matrix","semantic_primitives","6d_vector"],
    text:"Una matriz 5 × 5 relaciona cinco ejes U (Virtual), A (Actual), S (Sign), B (Being) y T (Thing), con filas de sustancia y columnas de atributo. Hay 25 caracteres: U [wo,wa,y,o,e], A [wu,we,u,a,i], S [j,g,s,b,t], B [h,c,k,m,n] y T [p,x,d,f,l]. Se asocia a cada carácter un vector gráfico de seis segmentos. Esta construcción no debe confundirse con los seis primitivos del parser de términos IEML v0.4, que también incluye E (vacío)."
  })
]);
export function findDocs(term) {
  const needle=String(term??"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim();
  if(!needle) return [...IEML_DOCS];
  return IEML_DOCS.filter(doc=>{
    const haystack=[doc.title,doc.author,doc.category,doc.text,...doc.tags].join(" ")
      .normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
    return haystack.includes(needle);
  });
}
