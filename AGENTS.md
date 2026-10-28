# AGENTS.md

## Contexto

- TP final de la asignatura Simulación (UTN FRD): Teoría de Colas aplicada a la internación de pacientes en un hospital.
- Es un informe académico en Markdown, no una aplicación. No hay tests, lint, CI ni build.
- La redacción, los nombres de archivos y los commits van en español.

## Comandos

~~~bash
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt

# Ejecutar SIEMPRE desde la raíz del repo: el script usa rutas relativas fijas.
python scripts/convertir_csv_en_sqlite.py

# Consultas de referencia
sqlite3 datos/datos.db < scripts/queries_modelo_colas.sql
~~~

## Pipeline de datos

- `datos/angeles-movimientos_internacion.csv` usa `;` como separador y encabezados en español; el script los renombra a `snake_case`.
- `scripts/convertir_csv_en_sqlite.py` hace `DROP TABLE` y recrea `datos_crudos` en `datos/datos.db` con PK y FK auto-referencial. `datos.db` está versionado y puede estar desactualizado respecto del CSV: si los conteos no coinciden, regenerarlo.
- El importe valida referencias inexistentes, `siguiente_evento_id` duplicado y ciclos; aborta con mensaje en vez de insertar datos inválidos. Si falla, corregir el CSV, no relajar las validaciones.
- El CSV contiene tipos de evento no mencionados en el modelo (p. ej. `Alta Anulada`, `Cancelacion Internacion`, `Reingreso`). El análisis filtra solo `Orden Internacion`, `Ingreso`, `Pase de cama`, `Alta médica` y `Egreso`.
- La cama `241` es el quirófano; el alcance del modelo usa solo las camas `200`, `203`, `225`, `236`, `281` más el quirófano. Se ignoran los pases entre camas regulares y las altas médicas para calcular tiempos de servicio.
- El ajuste exponencial de las llegadas fue rechazado; `lambda ≈ 1,09 pacientes/hora` se usa solo como estimador descriptivo.

## Organización

- `secciones/`: redacción de cada sección del informe (portada, introducción, análisis, experimentación, optimización, conclusiones).
- `src/`: imágenes referenciadas desde `secciones/*.md` con rutas `../src/...`.
- `calculos/`: desarrollos auxiliares; no forma parte de la entrega.
- `scripts/`: código Python y consultas SQL.
- `opencode/plans/`: planes de trabajo de agentes. En modo plan, documentar el diagnóstico/cambio como `opencode/plans/yyyy-mm-dd-plan-(titulo).md`; recién en modo build modificar archivos.
