"""ADA IEML — directed hierarchy/containment lattice adapter.

Adapted from the LatticeStructure snippet supplied by the user.
The legacy import `ieml.lexicon.grammar.Word` is intentionally absent.
Legacy Word-like objects can still be used *if* they expose .ancestors and
.singular_sequences. Modern IEMLdev/ieml scripts can instead be linked from
its typed dictionary graph via `from_edges` or `from_reference`.

Terminology: this is a finite directed hierarchy with two binary relations,
NOT proof of a mathematical lattice (joins and meets are not computed).
Parent edges are preserved exactly as supplied, including transitive ancestors;
we do not silently calculate a Hasse/transitive reduction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable, Mapping
from typing import Any

MAX_NODES = 300
# Original word.ancestors orientation: word -> each ancestor.
# Upstream dictionary RelationsGraph orientation:
# father_*: parent -> component; child_*: component -> parent.
_PARENT_INVERSE = frozenset({"parent", "ancestor", "child_substance",
                             "child_attribute", "child_mode"})
_PARENT_FORWARD = frozenset({"child", "father_substance",
                             "father_attribute", "father_mode"})
_CONTAINS_FORWARD = frozenset({"contains"})
_CONTAINS_INVERSE = frozenset({"contained", "contained_by"})
_SUPPORTED = _PARENT_INVERSE | _PARENT_FORWARD | _CONTAINS_FORWARD | _CONTAINS_INVERSE


@dataclass
class LatticeNode:
    word: str
    contains: list[str] = field(default_factory=list)
    contained_by: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)
    child: list[str] = field(default_factory=list)

    @property
    def children(self) -> list[str]:
        """Plural alias without changing the original snippet's .child."""
        return self.child

    def as_dict(self) -> dict[str, Any]:
        return {"word": self.word, "parents": self.parents,
                "child": self.child, "contains": self.contains,
                "contained_by": self.contained_by}


def _identifier(value: Any) -> str:
    if value is None:
        raise ValueError("A node cannot be None")
    name = str(value)
    if not name or not name.strip():
        raise ValueError("A node must have a nonempty string representation")
    if len(name) > 2048:
        raise ValueError("Node identifiers cannot exceed 2048 characters")
    return name


class LatticeStructure:
    """Finite hierarchy indexed by stable canonical IEML identifier strings."""

    def __init__(self, words: Iterable[Any]):
        # Backward-compatible entrypoint for the original Word-like objects.
        self.words_to_latticeNode, self.roots = self._build_hierarchie(words)
        self.source = "legacy-word-properties"
        self.ignored_reflexive = 0
        self.ignored_relation_kinds: list[str] = []

    def __getitem__(self, item: Any) -> LatticeNode:
        return self.words_to_latticeNode[_identifier(item)]

    def __len__(self) -> int:
        return len(self.words_to_latticeNode)

    @staticmethod
    def _build_hierarchie(words: Iterable[Any]) -> tuple[dict[str, LatticeNode], list[LatticeNode]]:
        """Original algorithm: ancestors, inverse child, singular containment.

        Missing required attributes are errors, never silently treated as
        empty sets (otherwise a version mismatch invents root nodes).
        """
        objects: dict[str, Any] = {}
        for word in words:
            key = _identifier(word)
            if key in objects:
                raise ValueError(f"Duplicate term representation: {key}")
            if not hasattr(word, "ancestors") or not hasattr(word, "singular_sequences"):
                raise TypeError(
                    "Legacy word must expose .ancestors and .singular_sequences. "
                    "Use LatticeStructure.from_edges with modern IEML relations."
                )
            objects[key] = word
        _check_size(objects)
        edges: list[tuple[str, str, str]] = []
        for word_id, word in objects.items():
            for ancestor in word.ancestors:
                edges.append((word_id, "ancestor", _identifier(ancestor)))
            for singular in word.singular_sequences:
                edges.append((word_id, "contains", _identifier(singular)))
        # Only relations among the selected words are included, as in source.
        structure = LatticeStructure.from_edges(objects, edges)
        return structure.words_to_latticeNode, structure.roots

    @classmethod
    def from_edges(
        cls, words: Iterable[Any], edges: Iterable[tuple[Any, str, Any]], *,
        source: str = "supplied-relations",
    ) -> "LatticeStructure":
        """Build from (source, relation_name, target) triples.

        For ancestor/parent/child_*: source is the descendant and target
        its parent. For child/father_*: source is parent, target is descendant.
        For contains: source contains target. For contained: target contains
        source. Other relations are ignored, not misrepresented as hierarchy.
        """
        ids = [_identifier(x) for x in words]
        _check_size(ids)
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate IEML identifiers")
        nodes = set(ids)
        parents = {w: set() for w in ids}
        contains = {w: set() for w in ids}
        ignored_reflexive = 0
        ignored_relations: set[str] = set()
        for triple in edges:
            if len(triple) != 3:
                raise ValueError("Each relation must be (source, kind, target)")
            source_id, kind, target_id = triple
            source_id, target_id = _identifier(source_id), _identifier(target_id)
            if not isinstance(kind, str):
                raise ValueError("Relation kind must be a string")
            if kind not in _SUPPORTED:
                ignored_relations.add(kind)
                continue
            if source_id not in nodes or target_id not in nodes:
                continue  # Only the induced graph on selected words.
            if source_id == target_id:
                ignored_reflexive += 1
                continue  # Upstream contains may explicitly contain identity.
            if kind in _PARENT_INVERSE:
                parents[source_id].add(target_id)
            elif kind in _PARENT_FORWARD:
                parents[target_id].add(source_id)
            elif kind in _CONTAINS_FORWARD:
                contains[source_id].add(target_id)
            elif kind in _CONTAINS_INVERSE:
                contains[target_id].add(source_id)

        _check_parent_acyclic(parents)
        children = {w: set() for w in ids}
        contained_by = {w: set() for w in ids}
        for child_id, ancestors in parents.items():
            for parent_id in ancestors:
                children[parent_id].add(child_id)
        for container, members in contains.items():
            for member in members:
                contained_by[member].add(container)

        entries = {
            key: LatticeNode(
                word=key,
                parents=sorted(parents[key]),
                child=sorted(children[key]),
                contains=sorted(contains[key]),
                contained_by=sorted(contained_by[key]),
            ) for key in sorted(ids)
        }
        instance = cls.__new__(cls)
        instance.words_to_latticeNode = entries
        instance.roots = [entries[k] for k in sorted(ids) if not parents[k]]
        instance.source = source
        instance.ignored_reflexive = ignored_reflexive
        instance.ignored_relation_kinds = sorted(ignored_relations)
        return instance

    @classmethod
    def from_reference(
        cls,
        reference_data: Mapping[str, Any],
        terms: Iterable[str],
    ) -> "LatticeStructure":
        """Build an induced graph from ADA's imported reference.json.

        The reference's triples are stored as flattened [source_index,
        relation_kind_index, target_index, ...]. The term registry and relation
        registry are distinct: use relations.terms to resolve edge indexes.
        """
        if reference_data.get("schema") != "ada-ieml-reference/v04":
            raise ValueError("Unsupported IEML reference data schema")
        relation_data = reference_data.get("relations", {})
        rel_terms = relation_data.get("terms")
        kinds = relation_data.get("kinds")
        triples = relation_data.get("triples")
        if not isinstance(rel_terms, list) or not isinstance(kinds, list) or not isinstance(triples, list):
            raise ValueError("Invalid relation terms/kinds/triples")
        if len(triples) % 3:
            raise ValueError("Reference relation triples must have length divisible by three")
        requested = [_identifier(t) for t in terms]
        _check_size(requested)
        known = set(rel_terms)
        missing = sorted(set(requested) - known)
        if missing:
            raise ValueError("Unknown reference term(s): " + ", ".join(missing[:5]))
        selected = set(requested)
        edges = []
        # The full index may hold many thousands of edges; only materialize
        # the selected induced graph, bounded to MAX_NODES.
        for i in range(0, len(triples), 3):
            a, k, b = triples[i:i+3]
            if (not all(isinstance(v, int) and not isinstance(v, bool)
                        for v in (a, k, b))
                or not (0 <= a < len(rel_terms) and 0 <= b < len(rel_terms)
                        and 0 <= k < len(kinds))):
                raise ValueError("Invalid reference graph index")
            if rel_terms[a] in selected and rel_terms[b] in selected:
                edges.append((rel_terms[a], kinds[k], rel_terms[b]))
        return cls.from_edges(
            requested, edges,
            source="IEML v0.4 imported reference, induced graph",
        )

    def to_dict(self) -> dict[str, Any]:
        nodes = [node.as_dict() for node in self.words_to_latticeNode.values()]
        links = []
        for node in nodes:
            for p in node["parents"]:
                links.append({"source": p, "target": node["word"], "relation": "parent"})
            for member in node["contains"]:
                links.append({"source": node["word"], "target": member, "relation": "contains"})
        return {
            "schema": "ada-ieml-lattice/v1",
            "source": self.source,
            "nodeCount": len(nodes),
            "roots": [n.word for n in self.roots],
            "parentEdgeCount": sum(len(n["parents"]) for n in nodes),
            "containmentEdgeCount": sum(len(n["contains"]) for n in nodes),
            "nodes": nodes, "edges": links,
            "ignoredReflexiveEdges": self.ignored_reflexive,
            "ignoredRelationKinds": self.ignored_relation_kinds,
            "warnings": [
                "Hierarchical graph only: mathematical meet/join lattice properties are not established.",
                "Parent edges are supplied relationships, not necessarily immediate Hasse covers.",
                "Only selected terms and links between them are displayed.",
            ],
        }


def _check_size(values: Any) -> None:
    if len(values) > MAX_NODES:
        raise ValueError(f"Too many nodes ({len(values)}); maximum is {MAX_NODES}")


def _check_parent_acyclic(parents: Mapping[str, set[str]]) -> None:
    """Reject loops: roots are meaningless in a cyclic ancestry graph."""
    state: dict[str, int] = {}
    for start in parents:
        if state.get(start, 0):
            continue
        state[start] = 1
        stack = [(start, iter(sorted(parents[start])))]
        while stack:
            current, iterator = stack[-1]
            try:
                predecessor = next(iterator)
            except StopIteration:
                state[current] = 2
                stack.pop()
                continue
            status = state.get(predecessor, 0)
            if status == 1:
                raise ValueError(
                    f"Parent hierarchy contains a cycle involving {predecessor}"
                )
            if status == 0:
                state[predecessor] = 1
                stack.append((predecessor, iter(sorted(parents[predecessor]))))
