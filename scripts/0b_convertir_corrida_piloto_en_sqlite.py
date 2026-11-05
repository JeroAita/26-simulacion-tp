import csv
import math
import re
import sqlite3
from pathlib import Path

DIR_CSV = Path("datos/corrida_piloto")
RUTA_DB = Path("datos/corrida_piloto.db")

NOMBRE_TABLA = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def abortar(mensaje):
    raise SystemExit(mensaje)


def ident(nombre):
    return '"' + nombre.replace('"', '""') + '"'


def leer_serie(ruta):
    filas = []
    with ruta.open(newline="", encoding="utf-8") as archivo:
        for numero, fila in enumerate(csv.reader(archivo), start=1):
            if not fila or all(not campo.strip() for campo in fila):
                continue
            if len(fila) != 2:
                abortar(f"{ruta}:{numero}: se esperaban 2 columnas, hay {len(fila)}.")
            try:
                tiempo, valor = float(fila[0]), float(fila[1])
            except ValueError:
                abortar(f"{ruta}:{numero}: valor no numérico: {fila!r}.")
            if not (math.isfinite(tiempo) and math.isfinite(valor)):
                abortar(f"{ruta}:{numero}: valor no finito: {fila!r}.")
            if filas and tiempo < filas[-1][0]:
                abortar(f"{ruta}:{numero}: el tiempo retrocede ({tiempo} < {filas[-1][0]}).")
            filas.append((tiempo, valor))
    if not filas:
        abortar(f"{ruta}: no contiene filas de datos.")
    return filas


def main():
    if not DIR_CSV.is_dir():
        abortar(f"No existe el directorio {DIR_CSV}.")
    archivos = sorted(DIR_CSV.glob("*.csv"))
    if not archivos:
        abortar(f"No se encontraron archivos .csv en {DIR_CSV}.")

    series = []
    for ruta in archivos:
        tabla = ruta.stem
        if not NOMBRE_TABLA.fullmatch(tabla):
            abortar(f"{ruta.name}: el nombre no es un identificador SQL válido.")
        filas = leer_serie(ruta)
        instantes = len({fila[0] for fila in filas})
        series.append((tabla, filas, len(filas) - instantes))

    RUTA_DB.parent.mkdir(parents=True, exist_ok=True)
    RUTA_DB.unlink(missing_ok=True)

    conn = sqlite3.connect(RUTA_DB)
    try:
        with conn:
            for tabla, filas, _ in series:
                conn.execute(
                    f"""
                    CREATE TABLE {ident(tabla)} (
                        id       INTEGER PRIMARY KEY,
                        tiempo_h REAL NOT NULL,
                        valor    REAL NOT NULL
                    )
                    """
                )
                conn.executemany(
                    f"INSERT INTO {ident(tabla)} (tiempo_h, valor) VALUES (?, ?)",
                    filas,
                )
                conn.execute(
                    f"CREATE INDEX {ident(f'idx_{tabla}_tiempo_h')} "
                    f"ON {ident(tabla)} (tiempo_h)"
                )
    finally:
        conn.close()

    print(f"OK: {len(series)} series importadas en {RUTA_DB}.")
    for tabla, filas, repetidos in series:
        detalle = f", {repetidos} instantes repetidos" if repetidos else ""
        print(f"  {tabla}: {len(filas)} filas ({filas[0][0]}..{filas[-1][0]} h{detalle})")


if __name__ == "__main__":
    main()
