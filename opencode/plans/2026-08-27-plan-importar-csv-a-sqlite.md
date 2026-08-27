# Plan: importar CSV a SQLite con claves primaria y foránea

Fecha: 2026-08-27

## Diagnóstico

`scripts/convertir_csv_en_sqlite.py` lee el CSV `datos/angeles-movimientos_internacion.csv` con
`pd.read_csv(...)` sin `sep`, y pandas usa por defecto la coma `,` como delimitador. Como el archivo
usa punto y coma `;` y no contiene comas, pandas interpreta cada línea completa como una única
columna: la tabla SQLite resultante tiene una sola columna `TEXT` cuyo nombre es la concatenación de
los encabezados y cada fila guarda la línea completa.

Además, `Evento ID` debe ser clave primaria y `Siguiente evento ID` referencia a otro registro
(clave foránea auto-referencial).

## Análisis de datos

- 9099 filas; `Evento ID` único y numérico en todas.
- `Siguiente evento ID`: 1996 vacíos; los 7103 valores existentes siempre referencian un evento
  presente y no hay ciclos (1997 raíces, cadenas de hasta 30 pasos).
- Anomalía: el evento `58646` es referenciado como "siguiente" por dos registros:
  - `58624` (Ingreso, persona 14200, cama 202)
  - `58645` (Alta médica, persona 14200, cama 202)
  Decisión: imponer `UNIQUE` sobre `siguiente_evento_id` y abortar el importe con mensaje claro
  mientras el dato fuente no se corrija.
- Columnas de la tabla en snake case (decisión tomada).

## Pasos

1. Crear `venv/` e instalar dependencias según `docs/REPO.md` (`venv/bin/pip install -r requirements.txt`).
2. Eliminar `datos/_datos.db` (base rota, sin trackear).
3. Reescribir `scripts/convertir_csv_en_sqlite.py`:
   - `pd.read_csv(..., sep=";")`.
   - Renombrar columnas a `evento_id`, `tipo_evento`, `siguiente_evento_id`, `persona_id`, `cama_id`,
     `fecha_hora_evento`.
   - Normalizar vacíos a `None` (NULL).
   - Validar antes de insertar: si un `siguiente_evento_id` no nulo se repite, abortar con mensaje que
     señala el conflicto.
   - Crear la tabla con esquema explícito:
     ```sql
     CREATE TABLE datos_crudos (
         evento_id INTEGER PRIMARY KEY,
         tipo_evento TEXT NOT NULL,
         siguiente_evento_id INTEGER UNIQUE REFERENCES datos_crudos(evento_id),
         persona_id INTEGER,
         cama_id INTEGER,
         fecha_hora_evento TEXT
     )
     ```
   - `PRAGMA foreign_keys = ON` y insertar en orden de cadena (padres antes que hijos) para que la
     clave foránea se satisfaga en tiempo de inserción.
4. Verificar:
   - 9099 filas.
   - Esquema con PK, `UNIQUE` y referencia auto.
   - `INSERT` con `siguiente_evento_id` duplicado falla por `UNIQUE`.
   - `DELETE` de un evento referenciado falla por `FOREIGN KEY`.

## Notas de implementación

- Pandas 3.x: `df.where(df.notna(), None)` sobre columnas `float64` re-coerciona el reemplazo a
  `NaN`; hace falta `df.astype(object).where(pd.notna(df), None)` para obtener `None` reales.
- La verificación end-to-end (esquema, UNIQUE, FK) se hizo sobre una copia corregida del CSV en
  `/tmp`; sobre el CSV original el script aborta a propósito señalando el evento `58646`.