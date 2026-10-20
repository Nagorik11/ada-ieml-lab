# Integración auditada: siete archivos de la gramática IEML

## Identidad de los archivos

Se analizaron siete archivos Python aportados durante la conversación y se
contrastaron con el **árbol Git de una revisión fija**:

- Proyecto: https://github.com/IEMLdev/ieml
- Commit: `b49d70bc8a9a548bf6a1066eef8cb975cbf95c91` (8 de marzo de 2021).
- Licencia del código original: **GPL-3.0**.
- Integridad: se calculó el Git Blob SHA-1 de cada archivo cargado y se
  comparó con el SHA del mismo archivo en ese commit. **Los siete coinciden**.
- Las rutas, tamaños, SHA-256 completos y SHA-1 Git están en
  [UPSTREAM_SOURCE_MANIFEST.json](UPSTREAM_SOURCE_MANIFEST.json).

| Original cargado | Ruta exacta del proyecto IEMLdev | Integración en ADA |
|---|---|---|
| `lexer.py` | `ieml/dictionary/script/parser/lexer.py` | Tokenización estricta y trazable |
| `parser.py` | `ieml/dictionary/script/parser/parser.py` | AST opcional del parser real |
| `script.py` | `ieml/dictionary/script/script.py` | Inspección de capa, cardinalidad, hijos, tipo, paradigma |
| `operator.py` | `ieml/dictionary/script/operator.py` | Constructor `script()` como punto de integración |
| `tools.py` | `ieml/dictionary/script/tools.py` | Identificados `factor`, `factorize`, `promote` (ejecución no expuesta a HTTP) |
| `dictionary.py` | `ieml/dictionary/dictionary.py` | Reutiliza el adaptador de `IEMLDatabase` |
| `relations.py` | `ieml/dictionary/relation/relations.py` | Ampliación de tipos de relaciones consultables |

Los archivos originales **no se copiaron a este repositorio**. El import
opcional del upstream se mantiene encapsulado en
`backend/upstream_ieml.py` y `backend/upstream_database.py`; el módulo
`backend/script_inspector.py` es código nuevo, independiente de PLY/NumPy
para la fase léxica.

## Modelo gramatical comprobado en la fuente

El lexer original declara exactamente:

- **6 primitivas:** `E,U,A,S,B,T`.
- **4 adiciones notables:** `O,M,F,I`.
- **25 multiplicaciones notables:** `wo,wa,y,o,e,wu,we,u,a,i,j,g,s,b,t,h,c,k,m,n,p,x,d,f,l`.
- **7 marcadores de nivel:** capa 0 `:`, 1 `.`, 2 `-`, 3 `'` o `’`, 4 `,`, 5 `_`, 6 `;`.
- **Operador aditivo:** `+`.

`parser.py` define `ScriptParser` con reglas PLY explícitas para las capas
0 y 1 y genera reglas desde la capa 2 hasta la 6. El archivo
`script.py` construye `AdditiveScript`, `MultiplicativeScript`,
`NullScript`, expone `singular_sequences`, `layer`, `cardinal`,
`grammatical_class`, `empty` y `paradigm`. Estas son propiedades del
objeto Script, **no coeficientes del espacio vectorial R9**.

## Decisiones de ingeniería y compatibilidad

1. **No omitir caracteres desconocidos.** El lexer histórico, al entrar en
   `t_error`, registra el error y avanza un carácter. La API nueva
   `/api/upstream/script/lex` los informa explícitamente en `errors`;
   rechaza analizarlos como si fueran válidos.
2. **Separar tokens de sintaxis.** Que todos los caracteres sean reconocibles
   no garantiza una derivación gramatical. La validación real se solicita a
   `/api/upstream/script/inspect`, que importa opcionalmente la función
   `ieml.dictionary.script.script`.
3. **No expandir paradigmas grandes por defecto.** `cardinal` y
   `singular_sequences` pueden alcanzar volúmenes considerables. La
   inspección expone metadatos y hasta 4 niveles de hijos, sin enumerar todas
   las secuencias.
4. **No ejecutar factorización libre por HTTP.** `tools.py` incluye un
   algoritmo combinatorio, pero su complejidad y seguridad no están validadas
   para entradas arbitrarias. Permanece accesible a través del paquete
   externo para ensayos controlados, no desde una ruta pública de ADA.
5. **No densificar matrices por defecto.** En `relations.py`,
   `RelationsGraph.__init__` aplica `todense()` para la matriz global;
   el consumo potencial de memoria es cuadrático en el tamaño del diccionario.
   Además se usa `np.bool`, retirado de NumPy moderno, por lo que el
   upstream podría requerir correcciones de compatibilidad. No se afirma
   soporte de Python 3.11+ hasta ejecutar una prueba con la dependencia real.
6. **No inferir equivalencias semánticas.** Los operandos *substance*,
   *attribute*, *mode* no son los nueve roles sintagmáticos
   `e0…e8`; una traducción de expresión formal a texto natural necesita
   un diccionario, correspondencias explícitas y procedencia.

## Endpoints nuevos

### `GET /api/upstream/script/lex?expression=wa.`

Ejemplo orientativo de respuesta:

```json
{
  "schema": "ada-ieml-script-lex/v1",
  "input": "wa.",
  "lexicallyValid": true,
  "grammarValidated": false,
  "tokens": [
    {"type":"REMARKABLE_MULTIPLICATION","value":"wa","position":0,"line":1,"column":1},
    {"type":"LAYER1_MARK","value":".","position":2,"line":1,"column":3}
  ],
  "errors": []
}
```

La respuesta incluye además fuente, commit verificado y advertencia sobre
la diferencia entre lexicografía y gramática.

### `POST /api/upstream/script/inspect`

```json
{"expression":"wa."}
```

Requiere una instalación funcional de `IEMLdev/ieml`; retorna una
representación acotada del AST con `layer`, `cardinal`, `children`,
`character`, `grammaticalClass` y `paradigm`.
La respuesta marca `dictionaryVerified:false`. Si falta la biblioteca,
responde HTTP 503; si rechaza la expresión, HTTP 422; entradas lexicalmente
inválidas devuelven HTTP 400.

### `GET /api/upstream/database/relations`

El adaptador ahora reconoce además las relaciones `identity` y
`table_0`…`table_5`, correspondientes a las matrices calculadas por
`RelationsGraph` en el archivo cargado.

## Comprobar hashes de los archivos originales

Si se conservan los siete archivos en la misma carpeta:

```bash
python tools/verify_upstream_sources.py /ruta/a/archivos
```

El verificador comprueba el tamaño y ambos hashes por archivo, indica
`OK`/`FAIL` y finaliza con código distinto de cero si falta alguno o su
contenido es diferente. El script **no ejecuta ni instala** el código GPL.

## Ejecutar pruebas y aplicación

```bash
python -m unittest backend.test_script_inspector backend.test_upstream_sources -v
npm run check
npm test
# Instalar la dependencia GPL-3.0 solo para inspección del AST:
pip install -r backend/requirements-upstream-ieml.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8001
python -m http.server 8000
```

La interfaz presenta estas operaciones en la **sección 15 / Gramática IEML**.

### Estado de validación

Las pruebas básicas del lexer, respuestas JSON, contratos AST simulados,
verificación SHA y validación de sintaxis del código están en GitHub Actions.
**No se ha validado todavía el parser original instalado con sus dependencias
en un entorno Python moderno**; la evaluación de integración real es un
trabajo separado. La redistribución del upstream o distribución conjunta
requiere evaluar cumplimiento GPL-3.0 y conservar avisos de licencia.
