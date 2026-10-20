# Alineación de roles españoles con el diccionario IEML

## Fundamento

Pierre Lévy describe una función sintagmática de **nueve roles**, con raíz 0 y roles 1–8 (iniciador, interactante, destinatario, causa, tiempo, lugar, intención y manera).

Fuente: https://journals.sagepub.com/doi/10.1177/26339137231207634

Repositorio histórico del parser: https://github.com/IEMLdev/ieml

## Flujo

1. spaCy extrae candidatos por oración.
2. `backend/ieml_bridge.py` compara etiquetas españolas exactas con entradas curadas.
3. Cada correspondencia debe registrar `labels_es`, `ieml`, `source` y preferiblemente `dictionaryVersion`.
4. Opcionalmente, el parser histórico valida la sintaxis de la unidad.
5. Si no hay correspondencia, se devuelve `unmapped`. **Nunca se inventa una USL.**

## Formato del léxico

```json
{
  "schema": "ada-ieml-lexicon/v1",
  "entries": [
    {
      "labels_es": ["concepto español revisado"],
      "ieml": "EXPRESIÓN_IEML_VERIFICADA",
      "source": "URL del diccionario y registro exacto",
      "dictionaryVersion": "versión documentada"
    }
  ]
}
```

El ejemplo es una **plantilla**, no una entrada válida. El archivo real inicia sin entradas porque no se ha importado una exportación verificada.

## API

`POST /api/align`: recibe `{"text":"..." , "validate":false}` y devuelve candidatos por oración.

## Límites de interoperabilidad

La biblioteca `IEMLdev/ieml` documenta una gramática histórica de Word, Topic, Fact, Theory y Text. El artículo de 2023 describe otra notación sintagmática; **no se debe asumir que el parser histórico valida la notación de 2023**. Se necesita seleccionar una versión de gramática y diccionario y validar su compatibilidad antes de habilitar generación formal de oraciones.
