# Importación IEML v0.4

Copiar `groundTruth.js`, `descriptors.generated.js` y `relations.generated.js` desde los archivos originales a la carpeta `reference/`.

Ejecutar:

```bash
node tools/import_reference.mjs reference data/ieml-v04
python -m unittest backend.test_reference
```

El importador ejecuta módulos JavaScript; utilizar únicamente archivos de confianza.

Endpoints disponibles tras importar los datos:

- `GET /api/reference/search?q=actual&language=en`
- `GET /api/reference/term?term=A%3A`
- `GET /api/reference/neighbors?term=A%3A`

Conteos comprobados de los archivos recibidos: 5227 términos, 5222 descriptores, 5227 nodos y 45246 relaciones codificadas como 135738 enteros. Son datos de la referencia aportada, no el total universal de IEML.

Los demás módulos JS se conservan para pruebas independientes. No se ha implementado traducción automática al español ni generación formal de oraciones USL. Si faltan los datos importados, la API responde HTTP 503.
