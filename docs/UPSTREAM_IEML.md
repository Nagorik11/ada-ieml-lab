# Integración técnica con IEMLdev/ieml

## Proyecto original y procedencia

- Fuente oficial (código de terceros): https://github.com/IEMLdev/ieml
- Revisión auditada: `b49d70bc8a9a548bf6a1066eef8cb975cbf95c91` (2021-03-08)
- Licencia del código original: **GPL-3.0**
- Metadatos del paquete `setup.py`: versión **1.0.4**
- Dependencias declaradas: numpy, bidict, ply, scipy, cached-property, tqdm, appdirs, pygit2, pandas, pyyaml, pylatex.
- El repositorio no declara soporte comprobado para los Python modernos del backend ADA.

**Licencia:** no hemos incorporado copias del código GPL del upstream a `ada-ieml-lab`. El módulo `backend/upstream_ieml.py` es un adaptador nuevo escrito para usar una instalación externa, **opcional**. Instalar, enlazar, redistribuir o desplegar componentes del upstream requiere revisar las obligaciones GPL-3.0 aplicables al producto combinado; mantener el paquete separado no constituye por sí solo una exención garantizada. Conservar los avisos de copyright y el texto íntegro de la licencia upstream.

## Lo que aparece realmente en el árbol upstream

El README original muestra `from ieml.grammar import usl`; ese módulo **no existe** en el árbol de la revisión auditada. Se han verificado las rutas:

- `ieml/dictionary/script/operator.py`: función `script(arg, promote=False, factorize=False)`.
- `ieml/usl/usl.py`: función `usl(arg)`.
- `ieml/usl/parser/parser.py`: clase `IEMLParser`, método `parse`.
- `ieml/usl/constants.py`: direcciones sintagmáticas y scripts de valencia.
- `ieml/dictionary/dictionary.py`: constructor `Dictionary(paradigms, structure)`; **no** acepta el constructor sin parámetros del README desactualizado.
- `IEMLv2_SPECIFICATION.md`: especificación de interfaces; no debe asumirse que todos sus tipos o métodos están implementados.

Por tanto, el adaptador usa `ieml.dictionary.script.script` o `ieml.usl.usl.usl`, **no** las rutas antiguas del README.

## Correspondencias con nuestra base canónica

Fuente exacta: https://github.com/IEMLdev/ieml/blob/b49d70bc8a9a548bf6a1066eef8cb975cbf95c91/ieml/usl/constants.py

| Eje de ADA | Función | Script de dirección upstream |
|---|---|---|
| e0 | raíz/proceso | sin script único; valencias `E:S:.`, `E:T:.`, `E:B:.` |
| e1 | iniciador | `E:.n.-` |
| e2 | interactante | `E:.d.-` |
| e3 | destinatario | `E:.k.-` |
| e4 | causa | `E:.s.-` |
| e5 | tiempo | `E:.t.-` |
| e6 | lugar | `E:.l.-` |
| e7 | intención | `E:.m.-` |
| e8 | manera | `E:.f.-` |

Los scripts representan **direcciones gramaticales** dentro del formalismo del upstream. No describen directamente el contenido de un concepto español ni definen los coeficientes `cᵢ`. Nuestro vector `R⁹` es una codificación estructural adicional.

## Ejecución y límites

El frontend (sección 12) muestra estas correspondencias localmente, sin instalar el parser. Para activarlo con FastAPI:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m spacy download es_core_news_sm
# Instala la biblioteca GPL opcional (puede requerir ajustes de dependencias):
pip install -r backend/requirements-upstream-ieml.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

El archivo opcional fija el commit upstream y **no** se instala en las pruebas básicas de CI. Si la importación falla por incompatibilidad, el endpoint devuelve 503. La posibilidad de instalar el paquete en Python 3.11+ **no se ha verificado** con una prueba real en esta integración.

### API

- `GET /api/upstream/status`: instalación detectada (sin importar completamente el paquete).
- `GET /api/upstream/roles`: correspondencia de e0…e8 con scripts de dirección, procedencia y notas de cautela.
- `POST /api/upstream/parse`: petición `{"kind":"script","expression":"wa."}` o `{"kind":"usl","expression":"..."}`. Devuelve `syntaxValid`, cadena canónica y clase reconocida si el parser está disponible.
- `POST /api/align` con `validate:true` utiliza ahora la ruta correcta del parser upstream para cotejar sintaxis de candidatos curados, sin atribuirles automáticamente validez semántica.

**Códigos de respuesta:** 503 parser ausente o fallando al importar, 422 expresión rechazada sintácticamente, 400 configuración inválida. No se ejecutan programas suministrados por el usuario. El parser construye su AST interno al validar; para exponer este endpoint de forma pública se requieren límites de recursos, timeout de proceso, cuotas y revisión de seguridad adicional.

### Ejemplo Python

```python
from backend.upstream_ieml import parse_expression, role_addresses

print(role_addresses()["roleAddresses"][1])
print(parse_expression("wa.", "script"))
```

Si `parse_expression` devuelve `syntaxValid:true`, eso significa que se aceptó la sintaxis por **el paquete instalado**. No significa que el script aparezca en la base normativa de una versión concreta ni que se haya verificado su interpretación conceptual.

## Pruebas

```bash
python -m unittest backend.test_upstream_ieml -v
```

La suite básica valida el adaptador usando simulaciones de la API externa. **No** demuestra que la versión upstream antigua se ejecute sin problemas sobre Python 3.11. Se necesita una suite de integración ejecutada en un entorno con la dependencia real para declararlo compatible.

## Próximos pasos

1. Probar el parser real en un entorno reproducible y fijar versión de Python compatible.
2. Verificar una muestra conocida de scripts y USL, incluidos errores intencionales.
3. Separar sintaxis, pertenencia al diccionario y asignación de significados.
4. Si se distribuye upstream junto con ADA, completar la revisión de licencias y avisos.
5. Integrar la asignación de palabras española → léxicos IEML por diccionario curado, no por proyecciones numéricas inventadas.
