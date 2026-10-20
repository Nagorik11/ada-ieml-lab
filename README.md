# ADA IEML Semiotic Lab

Laboratorio semiótico experimental con análisis de glifos, roles gramaticales, explorador de alfabeto e interfaz de referencia del diccionario IEML v0.4.

## Funcionalidades

- Glifos Ingress: tokenización, clasificación experimental C/L/A/D, entropía de Shannon y grafo sintagmático.
- Lenguaje natural: identificación heurística de raíz + ocho roles; análisis opcional con spaCy y FastAPI.
- Alineación candidata IEML: diccionario curado con registros de procedencia, no generación automática de USL.
- **Alfabeto 5 × 5:** 25 abreviaturas verificadas contra la tabla oficial del código upstream, etiquetas bilingües y vectores gráficos 6D **experimentales** para comparación coseno.
- **Biblioteca de investigación (nuevo):** documentación local con procedencia, búsqueda y aviso de modelos experimentales.
- **Explorador de referencia (nuevo):** búsqueda EN/FR en datos IEML v0.4, si el backend y el JSON están disponibles.

## Iniciar la interfaz

```bash
python3 -m http.server 8000
# Abrir http://127.0.0.1:8000
```

El servidor HTTP es necesario para importar los módulos ES de las secciones 08–10. Los paneles 08 y 09 funcionan sin backend y sin claves.

## Pruebas

```bash
npm run check
npm test
python3 -m unittest backend.test_reference backend.test_ieml_bridge
```

No se requieren paquetes npm externos. CI valida todos los scripts inline y los nuevos módulos.

## Backend Python opcional

Las instrucciones para FastAPI y spaCy están en [backend/README.md](backend/README.md). Para utilizar el panel 10, importar los datos de referencia desde los tres JS originales:

```bash
node tools/import_reference.mjs reference data/ieml-v04
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

La referencia IEML v0.4 no se almacena íntegra en este repositorio: debe generarse a partir de los archivos originales proporcionados. Sin ella la API de referencia responde HTTP 503.

## Alcance y límites

**No es un parser oficial IEML.** Las familias de glifos, las proyecciones 9D y la matriz de 25 símbolos proceden de modelos de investigación experimentales. El modelo 5×5/6D, la morfología v0.4 basada en seis primitivos y el espacio de nueve roles no son intercambiables. La similitud coseno de vectores gráficos tampoco garantiza similitud semántica.

Consultar [documentación de integración](docs/MODULE_INTEGRATION.md) y [alineación IEML](docs/IEML_ALIGNMENT.md).

## Bases canónicas R⁹ (nuevo)

La sección **11 / Asignación de bases canónicas** utiliza las evidencias de roles detectadas por spaCy para construir explícitamente `s = Σ cᵢ eᵢ` en una base ortonormal de nueve componentes. Incluye vector de presencia o confianza heurística, proyección a subespacios, acento opcional y exportación JSON.

- `POST /api/analyze` devuelve un campo `canonical` por oración.
- `POST /api/canonical` permite controlar modo, acento y proyección del texto.
- `POST /api/canonical/roles` permite asignar bases a roles editados, incluso pesos numéricos manuales.
- `backend/canonical_space.py` es independiente de spaCy, NumPy y de cualquier dependencia externa.
- `python3 -m unittest backend.test_canonical_space -v` verifica propiedades algebraicas.

Véase [documentación de bases canónicas](docs/CANONICAL_BASIS.md). **Se trata de codificación estructural de roles y no de semántica USL certificada.**

## Integración opcional con IEMLdev/ieml (GPL-3.0)

La sección **12 / Parser IEML original** presenta las direcciones sintagmáticas asociadas a `e0…e8` y permite validar sintaxis con la biblioteca Python original, si se instala por separado. Esto no equivale a validar la semántica o pertenencia a un diccionario normativo.

```bash
pip install -r backend/requirements-upstream-ieml.txt
python -m unittest backend.test_upstream_ieml -v
```

La biblioteca upstream es antigua (commit del 8 de marzo de 2021) y su ejecución con Python moderno sigue pendiente de prueba de integración real. **No se han copiado archivos con licencia GPL-3.0 al repositorio**, pero el uso y distribución combinados requieren revisar las obligaciones de esa licencia. Consultar [auditoría técnica y guía de integración](docs/UPSTREAM_IEML.md).
