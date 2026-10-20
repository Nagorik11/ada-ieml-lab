# Implementación P0/P1 · Alfabeto y corpus documental

## Fuentes
- `ieml-alphabet.js` (aportado por el usuario): 25 caracteres, matriz de 5×5, etiquetas ES/EN y vectors gráficos de seis dimensiones.
- `ieml-docs.js` (aportado por el usuario): dos notas de investigación, una sobre representación 9D y otra sobre alfabeto 5×5.
- PDFs «Linear Algebraic Representation of the IEML Semantic Space» (aportados por el usuario): hipótesis de base canónica e₀…e₈, recursión y conexiones neuronales.

## Reutilización real
- `src/ieml/alphabet.js` conserva las 25 correspondencias y vectores del archivo original.
- `src/ieml/docs.js` condensa dos entradas y las etiqueta como documentos de investigación, con procedencia; no se presenta como un parser ni una transcripción literal.
- `src/ieml/ui.js` ofrece matriz accesible, inspección de caracteres, vecinos por coseno de vectores 6D, tokenización explícita y búsqueda de notas.
- `index.html` añade las secciones 08–10 sin sustituir la interfaz anterior.
- `tests/ieml-alphabet.test.mjs` verifica todas las celdas, ejemplos, distancias y tokenización explícita.

## Compatibilidad y fronteras metodológicas
El modelo 5×5 **no es equivalente** al parser morfológico IEML v0.4 basado en seis primitivos `E,U,A,S,B,T`, ni al modelo de nueve roles `R⁹`. Son capas analíticas distintas. El índice 5×5 no valida expresiones USL. La proximidad coseno 6D mide similitud de patrones gráficos según la fuente original: no prueba equivalencia semántica. Las notas documentales contienen propuestas, no resultados cuantitativos de evaluación.

`ieml-semantic.js` depende de `glyph-catalog.js` externo a los archivos recibidos y `ieml-quantum.js` depende de `quantum-sim.js`. No se importan hasta tener implementaciones y pruebas de esas dependencias.

## Ejecutar
```bash
python3 -m http.server 8000
# visitar http://127.0.0.1:8000
npm test
npm run check
```
Los paneles 08 y 09 funcionan sin backend Python; requieren un servidor HTTP local para importar módulos ES.

El panel 10 necesita `reference.json`, generado desde los JS originales:
```bash
node tools/import_reference.mjs reference data/ieml-v04
# otra terminal (instalar dependencias y modelo spaCy: backend/README.md)
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```
La API de referencia permite coincidencias de etiquetas EN/FR pero aún **no** alinea automáticamente español con códigos IEML formalmente certificados.

## Próximas fases
1. Importar y validar los datos completos con verificación de integridad y pruebas con los 5.227 términos.
2. Alinear candidatos morfosintácticos ES → etiquetas EN/FR de manera revisable, con procedencia de traducciones.
3. Adaptar `ieml-semantic.js` al catálogo interno de glifos (reglas declaradas experimentales).
4. Implementar y probar el puente vectorial 9D separado de códigos morfológicos.
5. Mantener el simulador de 9 qubits como plugin de investigación opcional.
