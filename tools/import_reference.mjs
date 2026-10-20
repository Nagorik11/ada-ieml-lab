#!/usr/bin/env node
/** Convert the user's trusted v0.4 JS exports to portable JSON assets.
 * Run only against source files you trust: dynamic imports execute JS.
 */
import { pathToFileURL } from "node:url";
import { resolve, join } from "node:path";
import { mkdir, writeFile } from "node:fs/promises";

const source = resolve(process.argv[2] || "reference");
const output = resolve(process.argv[3] || "data/ieml-v04");
const load = async (name) => import(pathToFileURL(join(source, name)).href);
const { IEML_TRUTH } = await load("groundTruth.js");
const { DESCRIPTORS } = await load("descriptors.generated.js");
const { RELATION_KINDS, RELATION_TERMS, RELATION_TRIPLES, RELATION_OFFSETS } =
  await load("relations.generated.js");
const assert = (condition, msg) => { if (!condition) throw Error(msg); };
assert(Array.isArray(IEML_TRUTH) && IEML_TRUTH.length > 0, "No reference terms");
assert(new Set(IEML_TRUTH.map(t => t.term)).size === IEML_TRUTH.length, "Duplicate terms");
assert(RELATION_KINDS.length === 6, "Unexpected relation types");
assert(RELATION_TERMS.length === RELATION_OFFSETS.length - 1 ||
       RELATION_TERMS.length === RELATION_OFFSETS.length,
       "Unexpected offsets shape");
const data = {
  schema: "ada-ieml-reference/v04",
  source: "user-provided IEML v0.4 JS reference exports",
  terms: IEML_TRUTH,
  descriptors: DESCRIPTORS,
  relations: { kinds: RELATION_KINDS, terms: RELATION_TERMS,
               triples: RELATION_TRIPLES, offsets: RELATION_OFFSETS }
};
await mkdir(output, { recursive: true });
await writeFile(join(output, "reference.json"), JSON.stringify(data));
await writeFile(join(output, "manifest.json"), JSON.stringify({
  schema: data.schema, termCount: IEML_TRUTH.length,
  descriptorCount: Object.keys(DESCRIPTORS).length,
  relationKinds: RELATION_KINDS,
  relationTermCount: RELATION_TERMS.length,
  relationTripleCount: RELATION_TRIPLES.length
}, null, 2) + "\n");
console.log("Imported", IEML_TRUTH.length, "terms into", output);
