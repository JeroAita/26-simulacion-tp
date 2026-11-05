"""Extrae las muestras empíricas usadas por el simulador.

Genera, a partir de ``datos/datos.db`` y de la lógica de los scripts SQL 3, 4,
5 y 6, los archivos de ``datos/muestras/``:

- ``interarribos_exogenos.csv``
- ``servicio_camas.csv``
- ``servicio_quirofano.csv``

Si los valores de control no coinciden con los documentados en la
especificación, el script aborta sin escribir resultados.
"""

from __future__ import annotations

import csv
import shutil
import sqlite3
import statistics
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RUTA_DB = RAIZ / "datos" / "datos.db"
RUTA_SALIDA = RAIZ / "datos" / "muestras"
RUTA_SCRIPT_6 = RAIZ / "scripts" / "6_ruteo_y_llegadas_exogenas.sql"

# Lógica del Script SQL 6, sección c) (llegadas exógenas al sub-sistema).
SQL_INTERARRIBOS = """
WITH ev AS (
    SELECT
        evento_id, tipo_evento, cama_id, fecha_hora_evento, internacion_id,
        LAG(cama_id)    OVER w AS cama_prev,
        LAG(cama_id, 2) OVER w AS cama_prev2
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
llegadas AS (
    SELECT
        fecha_hora_evento, evento_id,
        CASE WHEN cama_prev = 241 AND cama_prev2 IN (223, 225, 226, 227, 228)
             THEN 1 ELSE 0 END AS endogena
    FROM ev
    WHERE (tipo_evento = 'Ingreso' AND cama_id IN (223, 225, 226, 227, 228))
       OR (tipo_evento = 'Pase de cama'
           AND cama_id IN (223, 225, 226, 227, 228)
           AND cama_prev IS NOT NULL
           AND cama_prev NOT IN (223, 225, 226, 227, 228))
),
exogenas AS (
    SELECT
        fecha_hora_evento,
        evento_id,
        ROUND((julianday(fecha_hora_evento)
             - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id))) * 24, 4)
            AS horas
    FROM llegadas
    WHERE endogena = 0
)
SELECT horas
FROM exogenas
WHERE horas IS NOT NULL
ORDER BY fecha_hora_evento, evento_id
"""

# Lógica del Script SQL 5: servicio del quirófano.
SQL_SERVICIO_QUIROFANO = """
WITH ev AS (
    SELECT
        evento_id,
        tipo_evento,
        cama_id,
        fecha_hora_evento,
        internacion_id,
        LAG(cama_id) OVER w AS cama_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
entradas AS (
    SELECT
        evento_id AS evento_entrada,
        fecha_hora_evento AS fecha_entrada,
        internacion_id,
        cama_prev AS cama_origen
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id = 241
      AND cama_prev IN (223, 225, 226, 227, 228)
),
salidas AS (
    SELECT
        evento_id AS evento_salida,
        fecha_hora_evento AS fecha_salida,
        internacion_id,
        cama_id AS cama_destino
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id IN (223, 225, 226, 227, 228)
      AND cama_prev = 241
),
con_siguiente_salida AS (
    SELECT
        e.evento_entrada,
        e.fecha_entrada,
        s.fecha_salida,
        ROW_NUMBER() OVER (
            PARTITION BY e.internacion_id, e.evento_entrada
            ORDER BY s.fecha_salida
        ) AS rn
    FROM entradas e
    LEFT JOIN salidas s ON s.internacion_id = e.internacion_id
                       AND s.fecha_salida > e.fecha_entrada
)
SELECT ROUND((julianday(fecha_salida) - julianday(fecha_entrada)) * 24, 4) AS horas
FROM con_siguiente_salida
WHERE rn = 1
  AND fecha_salida IS NOT NULL
ORDER BY fecha_entrada
"""


def abortar(mensaje: str) -> None:
    raise SystemExit(f"ERROR: {mensaje}")


def preparar_bloques_servicio(conn: sqlite3.Connection) -> None:
    """Ejecuta la parte del Script SQL 6 que crea ``bloques_servicio``."""
    if not RUTA_SCRIPT_6.exists():
        abortar(f"No existe {RUTA_SCRIPT_6}.")
    texto = RUTA_SCRIPT_6.read_text(encoding="utf-8")
    marca = "-- b) Matriz de ruteo"
    if marca not in texto:
        abortar("No se encontró la sección b) en el Script SQL 6.")
    conn.executescript(texto.split(marca)[0])


def consultar(conn: sqlite3.Connection, sql: str) -> list[float]:
    return [float(fila[0]) for fila in conn.execute(sql).fetchall()]


def escribir_csv(ruta: Path, valores: list[float]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["horas"])
        for valor in valores:
            escritor.writerow([repr(float(valor))])


def verificar(
    nombre: str,
    valores: list[float],
    n: int,
    media: float,
    desvio: float,
    mediana: float | None = None,
    maximo: float | None = None,
    tolerancia: float = 0.02,
) -> None:
    problemas: list[str] = []
    if len(valores) != n:
        problemas.append(f"n={len(valores)} (esperado {n})")
    if abs(statistics.fmean(valores) - media) > tolerancia:
        problemas.append(
            f"media={statistics.fmean(valores):.4f} (esperado {media:.4f})"
        )
    if abs(statistics.stdev(valores) - desvio) > tolerancia:
        problemas.append(
            f"desvío={statistics.stdev(valores):.4f} (esperado {desvio:.4f})"
        )
    if mediana is not None and abs(statistics.median(valores) - mediana) > tolerancia:
        problemas.append(
            f"mediana={statistics.median(valores):.4f} (esperado {mediana:.4f})"
        )
    if maximo is not None and abs(max(valores) - maximo) > tolerancia:
        problemas.append(f"máximo={max(valores):.4f} (esperado {maximo:.4f})")
    if problemas:
        abortar(f"Control fallido para {nombre}: " + "; ".join(problemas))


def main() -> None:
    if not RUTA_DB.exists():
        abortar(
            f"No existe {RUTA_DB}. Ejecutá primero "
            "scripts/0_convertir_csv_en_sqlite.py y scripts/1_limpieza_de_datos.sql."
        )

    with tempfile.TemporaryDirectory(prefix="simulacion_muestras_") as tmp:
        ruta_tmp = Path(tmp) / "datos.db"
        shutil.copy2(RUTA_DB, ruta_tmp)
        conn = sqlite3.connect(ruta_tmp)
        try:
            tablas = {
                fila[0]
                for fila in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "datos_limpios" not in tablas:
                abortar(
                    "No existe la tabla datos_limpios. Ejecutá "
                    "scripts/1_limpieza_de_datos.sql sobre datos/datos.db."
                )

            preparar_bloques_servicio(conn)

            interarribos = consultar(conn, SQL_INTERARRIBOS)
            servicio_camas = consultar(
                conn,
                "SELECT horas_servicio FROM bloques_servicio ORDER BY inicio_servicio",
            )
            servicio_quirofano = consultar(conn, SQL_SERVICIO_QUIROFANO)
            destinos = dict(
                conn.execute(
                    "SELECT destino, COUNT(*) FROM bloques_servicio GROUP BY destino"
                ).fetchall()
            )
        finally:
            conn.close()

    verificar(
        "interarribos_exogenos",
        interarribos,
        n=289,
        media=6.03,
        desvio=6.47,
    )
    verificar(
        "servicio_camas",
        servicio_camas,
        n=350,
        media=18.07,
        desvio=29.88,
        mediana=7.99,
        maximo=290.7,
    )
    verificar(
        "servicio_quirofano",
        servicio_quirofano,
        n=65,
        media=1.51,
        desvio=2.08,
        mediana=0.06,
        maximo=6.9,
    )

    esperados = {"egreso": 143, "externa": 139, "quirofano": 68}
    if destinos != esperados:
        abortar(f"Destinos observados {destinos}; se esperaban {esperados}.")

    escribir_csv(RUTA_SALIDA / "interarribos_exogenos.csv", interarribos)
    escribir_csv(RUTA_SALIDA / "servicio_camas.csv", servicio_camas)
    escribir_csv(RUTA_SALIDA / "servicio_quirofano.csv", servicio_quirofano)

    print("Muestras generadas correctamente:")
    print(f"  interarribos_exogenos: n={len(interarribos)}")
    print(f"  servicio_camas:        n={len(servicio_camas)}")
    print(f"  servicio_quirofano:    n={len(servicio_quirofano)}")
    print(f"  destinos:              {destinos}")


if __name__ == "__main__":
    main()
