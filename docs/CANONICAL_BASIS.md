# Asignación de bases canónicas de nueve dimensiones — ADA IEML Lab

## Fundamento y procedencia

El módulo `backend/canonical_space.py` implementa una **codificación estructural experimental** basada en las secciones 2–5 del documento proporcionado por el usuario: *Formal Algebraic Representation of the IEML Semantic Space: Orthonormal Canonical Basis, Vector Sums, Recursive Block Matrices, and Integration with Semantic Neural Networks* (Fernando Valenzuela, 11 de junio de 2026).

El documento propone el espacio `V ≅ R9`, la base estándar ortonormal `B={e0,...,e8}`, la ecuación `s=Σ c_i e_i`, la identidad `I9`, acento `cσ` y la composición recursiva `diag(I9,M)`.

| Coordenada | Rol |
|---|---|
| e0 | Raíz |
| e1 | Iniciador |
| e2 | Interactante |
| e3 | Destinatario |
| e4 | Causalidad |
| e5 | Tiempo |
| e6 | Lugar |
| e7 | Intención |
| e8 | Manera |

**No confundir estos vectores con representaciones semánticas IEML formalmente verificadas.** Una cadena de texto, lexema o USL no es por sí misma un escalar real. Para codificar contenido semántico hacen falta un diccionario validado y una función de asignación numérica con criterios explícitos.

## Modos numéricos

1. `presence`: cada rol con evidencia extraída se representa mediante un coeficiente 1; rol ausente → 0.
2. `confidence`: se utiliza la confianza heurística de la regla spaCy; una evidencia con confianza faltante da 0. Las puntuaciones **no están calibradas** como probabilidades.
3. `manual`: la persona usuaria suministra pesos reales finitos para **todos** los roles activos. No se permiten pesos distintos de cero en roles sin evidencia.

Con cualquiera de estos modos `s = Σ c_i e_i` es un vector de **roles**, no un embedding de la semántica de cada argumento.

## Operadores y contratos

- `basis_vector(i)` → vector unitario e_i.
- `identity_matrix()` → identidad 9×9.
- `projection_matrix([i,j,...])` → proyector diagonal de los roles seleccionados. Se garantiza `P² = P`.
- `dot(a,b)` y `norm(a)` → producto escalar y norma euclidiana.
- `assign_roles(roles, mode=..., manual_coefficients=..., accent_role=..., accent_scale=..., projection_roles=...)` → asignación trazable.
- `assign_analysis(extraction, **options)` → vectorización de cada oración.
- `recursive_block_matrix(M)` → matriz `diag(I9,M)` de 18×18; no infiere suboraciones a partir de texto por sí sola.

El acento es una **transformación opcional y explícita** que escala una coordenada sin modificar el vector original; un rol ausente no puede recibir acento.

## API FastAPI

`POST /api/analyze` devuelve los mismos roles y dependencias spaCy más un campo `canonical` por oración, en modo `presence`.

`POST /api/canonical` recibe el texto y configura modo, acento y subespacio:

```json
{
  "text": "María envió un informe a Pedro ayer.",
  "mode": "presence",
  "accent_role": 0,
  "accent_scale": 1.5,
  "projection_roles": [0, 1, 2, 3, 5]
}
```

Su respuesta contiene `schema: ada-ieml-canonical-analysis/v1`, `basis`, `identityMatrix`, y por oración: `vector`, `coefficients`, `activeRoleIndices`, `roles` con evidencia y regla, `norm`, `projection`, `accent` y `warnings`. Los roles reales detectados pueden variar según la segmentación de spaCy.

`POST /api/canonical/roles` permite vectorizar roles revisados manualmente, sin requerir extracción de texto en esa solicitud:

```json
{
  "roles": {
    "0": {"evidence": "enviar", "confidence": 0.98},
    "1": {"evidence": "María", "confidence": 0.88},
    "2": {"evidence": "informe", "confidence": 0.82},
    "3": {"evidence": "Pedro", "confidence": 0.60},
    "5": {"evidence": "ayer", "confidence": 0.87}
  },
  "mode": "manual",
  "manual_coefficients": {
    "0": 1.0, "1": 0.5, "2": 1.0, "3": 0.25, "5": 0.75
  }
}
```

Para este caso manual, el vector resultante es `[1, 0.5, 1, 0.25, 0, 0.75, 0, 0, 0]`.

## Interfaz web

La sección **11 / Asignación de bases canónicas** utiliza el texto existente de la sección 07. Permite:

- cambiar el modo `presence` / `confidence`;
- seleccionar las bases a proyectar;
- elegir coordenada y escala de acento;
- inspeccionar evidencias, coeficientes, vector, norma y proyección;
- exportar el resultado JSON.

Requiere servidor HTTP para los ES Modules del navegador y backend Python para spaCy:

```bash
python3 -m http.server 8000
# En una terminal adicional (tras instalar dependencias y el modelo spaCy):
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

## Verificación

```bash
python3 -m unittest backend.test_canonical_space -v
```

Las pruebas cubren ortonormalidad, presencia, confianza heurística, pesos manuales, proyección idempotente, identidad, acento, recursión y validación de entradas.

## Próximos hitos

Validar los roles contra un conjunto etiquetado en español y conectar términos IEML curados a cada rol de manera explícita; no mezclar similitud estructural con equivalencia semántica.
