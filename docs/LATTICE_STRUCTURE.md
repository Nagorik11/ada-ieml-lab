# IEML LatticeStructure — jerarquía dirigida y contención (ADA 0.7)

## Procedencia

Este módulo es una adaptación del código **LatticeNode / LatticeStructure** proporcionado en la conversación. Conserva la distinción entre:

- `parents`: antecesores conocidos de un término.
- `child`: inversa de `parents`, con alias `children`.
- `contains`: unidades incluidas por un término.
- `contained_by`: inversa de `contains`.
- `roots`: términos sin padres **dentro del subgrafo seleccionado**, no necesariamente raíces de todo el léxico.

El código original importa `from ieml.lexicon.grammar import Word`, pero ese paquete no existe en la revisión auditada `b49d70bc8a9a548bf6a1066eef8cb975cbf95c91` (2021-03-08) de https://github.com/IEMLdev/ieml. La clase contemporánea `ieml.usl.word.Word` no garantiza los atributos `.ancestors` y `.singular_sequences` que exige el fragmento antiguo. Por ello no se realiza ese import en ADA: se aceptan **objetos con ambos atributos** o bien un **grafo de relaciones explícito**.

Aunque el código heredado utiliza la palabra *lattice*, **no prueba las propiedades matemáticas de retícula**: no calcula `meet` ni `join`, ni garantiza que cada par de elementos tenga ambos. Para evitar confusiones, la API declara que su resultado es un grafo jerárquico con relación de inclusión.

## Relaciones admitidas

Cada relación es una tripleta `[origen, tipo, destino]`.

| Tipo | Interpretación |
|---|---|
| `ancestor`, `parent`, `child_substance`, `child_attribute`, `child_mode` | origen es descendiente; destino es antecesor |
| `child`, `father_substance`, `father_attribute`, `father_mode` | origen es antecesor; destino es descendiente |
| `contains` | origen contiene destino |
| `contained`, `contained_by` | destino contiene origen |

Los nombres `father_*` y `child_*` y sus direcciones se verificaron consultando `ieml/dictionary/relation/relations.py` de IEMLdev/ieml; la relación `contains` puede incluir la identidad según su implementación. ADA omite los enlaces reflexivos para evitar convertir `A contains A` en una conexión visual engañosa.

Otras relaciones (`opposed`, `associated`, `twin`, `crossed`) **no** se convierten en ascendencia ni contención. Se informa qué tipos se descartaron.

No se añade una reducción transitiva: si el original entrega `A` y `B` como antecesores de `C`, ambos enlaces se conservan. Los ciclos de ascendencia se rechazan porque invalidarían la identificación de raíces.

## Uso Python sin biblioteca IEML externa

```python
from backend.lattice import LatticeStructure

g = LatticeStructure.from_edges(
    ["A", "B", "C"],
    [
        ("A", "father_substance", "B"),
        ("A", "contains", "C"),
    ],
)
assert [root.word for root in g.roots] == ["A", "C"]
assert g["B"].parents == ["A"]
assert g["A"].child == ["B"]
assert g["A"].contains == ["C"]
assert g["C"].contained_by == ["A"]
print(g.to_dict())
```

En este ejemplo las letras `A`, `B`, `C` son **identificadores sintéticos**, no expresiones IEML certificadas.

## Entrada desde objetos heredados

```python
from backend.lattice import LatticeStructure

# Requiere objetos cuyo str(word) sea una clave IEML estable y que tengan
# word.ancestors y word.singular_sequences.
lattice = LatticeStructure(old_words)
print(lattice.roots)
```

Una ausencia de esos atributos causa `TypeError` explicativo y **no** crea raíces artificiales.

## Entrada desde la referencia de términos previamente importada

```python
from backend.reference import reference
from backend.lattice import LatticeStructure

data = reference()  # Lee data/ieml-v04/reference.json
graph = LatticeStructure.from_reference(data, ["wa.", "we.", "wu."])
print(graph.to_dict())
```

Solo se incluyen las relaciones **entre los términos seleccionados**, hasta 300 nodos. Para la visualización SVG del navegador se recomienda usar a lo sumo 49 nodos.

**Importante:** los términos pedidos deben existir en `relations.terms` de esa versión de referencia. No se sustituye automáticamente ninguna grafía IEML por otra.

## API FastAPI

`POST /api/lattice/edges`:

```json
{
  "words": ["A", "B", "C"],
  "edges": [
    ["A", "father_substance", "B"],
    ["A", "contains", "C"]
  ]
}
```

`POST /api/lattice/reference`:

```json
{
  "terms": ["wa.", "we.", "wu."]
}
```

El segundo endpoint responde **503** cuando `reference.json` aún no está disponible, en lugar de inventar relaciones.

Ambos devuelven la forma `ada-ieml-lattice/v1`, con `nodes`, `edges`, `roots`, contadores, relaciones ignoradas y advertencias semánticas.

## Interfaz

La sección **14 / LatticeStructure** permite cargar términos desde la referencia o pegar relaciones explícitas. Dibuja aristas verdes de ascendencia y aristas ámbar discontinuas de contención; incluye una tabla con las relaciones inversas y exportación/inspección del JSON.

## Pruebas y compatibilidad

```bash
python -m unittest backend.test_lattice -v
npm run check
```

Las pruebas de contrato utilizan conjuntos pequeños construidos en memoria, por lo que no requieren importar el proyecto original (GPL-3.0). La prueba contra una copia histórica completa del diccionario, incluidos sus formatos de índices, sigue siendo un paso de integración pendiente.

## Relación con las bases canónicas R9

Las aristas de la retícula describen **relaciones entre conceptos/expresiones**, mientras `e0…e8` describe las **posiciones sintagmáticas de los participantes de una oración**.

Son dos dimensiones de información diferentes y complementarias. Una ampliación futura puede asignar a cada evidencia de rol un término IEML curado, y luego explorar su vecindad en esta jerarquía. Ninguno de esos pasos permite deducir coeficientes semánticos numéricos sin un modelo de codificación definido y validado.
