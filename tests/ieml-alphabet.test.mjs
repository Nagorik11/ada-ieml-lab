import test from "node:test";
import assert from "node:assert/strict";
import {
  AXES, ALPHABET, getChar, getCharByCoords,
  getAlphabetMatrix, cosineSimilarity, nearestSymbols, tokenizeSymbols
} from "../src/ieml/alphabet.js";
import { IEML_DOCS, findDocs } from "../src/ieml/docs.js";

test("5×5 matrix has 25 distinct symbols and exactly five rows",()=>{
  assert.equal(AXES.length,5);
  assert.equal(ALPHABET.length,25);
  assert.equal(new Set(ALPHABET.map(x=>x.char)).size,25);
  const m=getAlphabetMatrix();
  assert.equal(m.length,5);
  for(const row of m)assert.equal(row.length,5);
  for(const ch of ALPHABET) {
    assert.equal(getCharByCoords(ch.row,ch.col)?.char,ch.char);
    assert.equal(getChar(ch.char)?.char,ch.char);
    assert.equal(ch.vector.length,6);
    assert.ok(ch.vector.every(v=>Number.isFinite(v)&&v>=0&&v<=1));
  }
});
test("source alphabet coordinate and vector examples",()=>{
  assert.deepEqual(getChar("wo").vector,[0.5,0,0.5,0,0,0]);
  assert.deepEqual(getChar("l").vector,[0,0,1,0,0,1]);
  assert.equal(getChar("invalid"),null);
});
test("cosine similarity is symmetric, normalized and not artificially boosted",()=>{
  assert.equal(cosineSimilarity("wo","wo"),1);
  assert.equal(cosineSimilarity("wo","UNKNOWN"),null);
  for(const a of ALPHABET)for(const b of ALPHABET) {
    const ab=cosineSimilarity(a,b),ba=cosineSimilarity(b,a);
    assert.ok(ab>=-1e-12&&ab<=1+1e-12);
    assert.ok(Math.abs(ab-ba)<1e-12);
  }
  assert.equal(nearestSymbols("wo",4).length,4);
});
test("symbol parser does not split Spanish words",()=>{
  const tokens=tokenizeSymbols("wo → wa, y casa");
  assert.deepEqual(tokens.map(x=>x.valid),[true,true,true,false]);
  assert.equal(tokens[3].token,"casa");
});
test("research note provenance and filtering",()=>{
  assert.equal(IEML_DOCS.length,2);
  assert.equal(findDocs("ALFABETO").length,1);
  assert.equal(findDocs("NO_EXISTE").length,0);
  assert.ok(IEML_DOCS.every(doc=>doc.source&&doc.id&&doc.category));
});
