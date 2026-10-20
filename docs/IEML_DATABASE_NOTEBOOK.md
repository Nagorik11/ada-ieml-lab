# IEMLDatabase.ipynb → ADA IEML Lab

## Análisis del notebook aportado

Notebook Python 3 de **16 celdas**, originalmente pensado para un entorno de desarrollo local de la biblioteca `IEMLdev/ieml`. La lógica válida se conserva, pero sus rutas absolutas, claves SSH, credenciales `pygit2.Keypair` y ejemplo de actualización remota `GitInterface.pull()` **NO se importan** a nuestro código.

Las API usadas en el notebook y verificadas en la revisión auditada del código fuente upstream son:

| Notebook | Código upstream comprobado | Adaptación ADA |
|---|---|---|
| `IEMLDatabase(folder=...)` | `ieml/ieml_database/ieml_database.py` | apertura local opcional |
| `iemldb.list()` | `IEMLDatabase.list(type=None,paradigm=None,parse=False)` | listado paginado |
| `iemldb.list(type='word',parse=True)` | parser `IEMLParser` | listado de strings; sin parse masivo |
| `iemldb.get_descriptors()` | `get_values_partial(ieml,language,descriptor)` | traducciones, comentarios y etiquetas |
| `iemldb.get_dictionary()` | `Dictionary(paradigms,structure)` | fuente local de tablas/relaciones |
| `dictionary.relations.object('wa.','child_attribute')` | objeto Script como índice de relaciones | consultamos con `script(term)` |
| `dictionary.tables['O:O:.'].cells` | celdas de tablas | serialización 2D hasta 20×20 |
| `dictionary.tables['M:'].parent.script` | enlace jerárquico de tablas | campo `parent` |

En los resultados *ya almacenados* en el notebook, `get_values_partial('wa.')` presenta traducciones EN `act`, `perform` y FR `agir`, `exercer`. Es evidencia **histórica del notebook**, no el resultado de una consulta en vivo de la base actual.

## Componentes incluidos

- `backend/upstream_database.py`: adaptador **de solo lectura**; nunca clona ni actualiza repositorios.
- `backend/test_upstream_database.py`: pruebas unitarias offline con simulaciones controladas.
- `backend/main.py`: API que responde 503 cuando la base local o biblioteca externa no está disponible.
- `src/ieml/database-ui.js` y sección 13 de `index.html`: explorador visual.
- `.github/workflows/ci.yml`: test de contrato y sintaxis (sin descarga de bibliotecas antiguas).

## Preparación en un entorno controlado

1. Instalar las dependencias básicas del backend según `backend/README.md`.
2. Revisar la compatibilidad y licencia GPL-3.0 del código upstream en `docs/UPSTREAM_IEML.md`; instalar el paquete opcional en un entorno aislado. Sus dependencias antiguas podrían requerir ajustes.
3. Clonar **únicamente mediante HTTPS**, sin archivos SSH de terceros:

```bash
git clone --depth 1 https://github.com/IEMLdev/ieml-language.git ./data/upstream-ieml-language
export IEML_DATABASE_PATH="$(pwd)/data/upstream-ieml-language"
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

**No** ejecutar automáticamente `git pull` desde peticiones HTTP. La aplicación solo lee una copia que el operador administra.

La base de datos y la biblioteca Python provienen de **repositorios diferentes**:
- https://github.com/IEMLdev/ieml-language (datos)
- https://github.com/IEMLdev/ieml (biblioteca Python, GPL-3.0)

Se debe revisar también el régimen de licencia de los **datos** antes de incluir exportaciones completas en artefactos redistribuidos.

## Endpoints

| Método y ruta | Descripción |
|---|---|
| `GET /api/upstream/database/status` | Estado de configuración y presencia de datos locales |
| `GET /api/upstream/database/terms?kind=word&limit=25&offset=0` | Listar cadenas IEML de la clase solicitada |
| `GET /api/upstream/database/descriptors?term=wa.&language=en` | Consultar traducciones y metadatos |
| `GET /api/upstream/database/relations?term=wa.&relation=child_attribute&limit=20` | Grafo estructural |
| `GET /api/upstream/database/table?term=O:O:.` | Matriz de tabla y relación jerárquica |

Las consultas tienen límites de resultados y parámetros autorizados; la construcción inicial del grafo upstream puede seguir consumiendo mucha RAM. Debe utilizarse localmente y, para uso público, aislarse en un proceso con cuota y tiempo máximo.

### Ejemplo de respuesta de descriptores

La siguiente respuesta es **ilustrativa**, basada en la salida histórica del notebook; no demuestra que se haya ejecutado el parser upstream:

```json
{
  "schema": "ada-ieml-database-descriptors/v1",
  "term": "wa.",
  "items": [
    {"ieml":"wa.","language":"en","category":"translations","values":["act","perform"]},
    {"ieml":"wa.","language":"fr","category":"translations","values":["agir","exercer"]}
  ]
}
```

## Limitaciones

1. La biblioteca upstream es antigua y **todavía no hemos ejecutado pruebas de integración con una copia real de `ieml-language`**. Las pruebas de GitHub Actions usan fixtures, sin descarga ni carga de Git.
2. La disponibilidad de etiquetas en EN/FR no genera traducciones españolas por sí sola.
3. El diccionario es una fuente de conceptos y relaciones, mientras que los vectores `e₀...e₈` de ADA representan **roles estructurales**. No son magnitudes semánticas equivalentes.
4. No se importó el notebook original a GitHub porque contiene rutas y configuración de autenticación específicas de otro equipo. Se reimplementaron solo sus operaciones de lectura relevantes.

## Próximo hito

Alinear cada evidencia gramatical detectada por spaCy con una entrada revisada del diccionario, conservando término IEML, traducción, versión de la base, regla, procedencia y estado de validación semántica.
