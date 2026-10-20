# Analizador morfosintáctico español

El motor spaCy extrae dependencias gramaticales y candidatos para raíz (0) y ocho roles (1–8) por oración.

## Instalar y ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m spacy download es_core_news_sm
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

Abrir `index.html` usando un servidor local en puerto 8000:

```bash
python -m http.server 8000
```

El frontend utiliza `http://127.0.0.1:8001/api/analyze` al presionar **Analizar con spaCy**. Si el backend no está ejecutándose, el analizador heurístico original sigue disponible.

## Alcance

El modelo NLP es probabilístico y puede confundir complementos. Las asignaciones a los ocho roles son **candidatos experimentales**, no una conversión formal certificada a IEML. La sintaxis IEML se puede verificar con un parser upstream **opcional**, no instalado por defecto. El diccionario IEML v0.4 requiere importación explícita.

## API

`POST /api/analyze` con `{"text":"María envió un informe a Pedro ayer."}`.

`GET /health` informa el modelo cargado.

## Parser original opcional IEMLdev/ieml

El parser externo usa **GPL-3.0**, y su revisión auditada de 2021 puede tener incompatibilidades con versiones modernas de Python. No se incluye en las dependencias básicas ni se copian sus archivos al repositorio.

```bash
pip install -r backend/requirements-upstream-ieml.txt
```

Para consultar el motor: `GET /api/upstream/status`, `GET /api/upstream/roles` y `POST /api/upstream/parse` con `{"kind":"script","expression":"wa."}`.

**Importante:** el README upstream indica imports de `ieml.grammar`, pero la revisión auditada usa `ieml.usl.usl` y `ieml.dictionary.script`. Revisa [UPSTREAM_IEML.md](../docs/UPSTREAM_IEML.md) para compatibilidad, licencia y limitaciones.
