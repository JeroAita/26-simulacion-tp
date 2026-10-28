import sqlite3

import pandas as pd

RUTA_CSV = "datos/angeles-movimientos_internacion.csv"
RUTA_DB = "datos/datos.db"
TABLA = "datos_crudos"

COLUMNAS = [
    "evento_id",
    "tipo_evento",
    "siguiente_evento_id",
    "persona_id",
    "cama_id",
    "fecha_hora_evento",
]

NOMBRES_LEGIBLES = {
    "evento_id": "Evento ID",
    "tipo_evento": "Tipo evento",
    "siguiente_evento_id": "Siguiente evento ID",
    "persona_id": "Persona ID",
    "cama_id": "Cama ID",
    "fecha_hora_evento": "Fecha-Hora evento",
}


def abrir(mensaje):
    raise SystemExit(mensaje)


def main():
    df = pd.read_csv(RUTA_CSV, sep=";")
    df.columns = COLUMNAS

    # Vacíos ("") pasan a None para que SQLite guarde NULL.
    df = df.astype(object).where(pd.notna(df), None)

    eventos = {int(e) for e in df["evento_id"].dropna()}
    siguientes = df.loc[df["siguiente_evento_id"].notna(), "siguiente_evento_id"].astype(int)

    # Validación 1: toda referencia debe apuntar a un evento existente.
    faltantes = sorted(set(siguientes) - eventos)
    if faltantes:
        abrir(
            "Referencias inexistentes en 'Siguiente evento ID': "
            + ", ".join(str(e) for e in faltantes[:10])
            + "\nCorregí el CSV y volvé a ejecutar."
        )

    # Validación 2: un evento no puede tener dos predecesores (la cadena no se bifurca),
    # porque 'siguiente_evento_id' es UNIQUE.
    duplicados = sorted(set(siguientes[siguientes.duplicated()]))
    if duplicados:
        detalle = []
        for d in duplicados:
            predecesores = df.loc[
                df["siguiente_evento_id"].astype(float) == float(d), "evento_id"
            ].tolist()
            detalle.append(f"  {d}: predecesores {predecesores}")
        abrir(
            "El campo 'Siguiente evento ID' se repite y violaría la restricción UNIQUE.\n"
            "Eventos referenciados más de una vez:\n"
            + "\n".join(detalle)
            + "\nCorregí el CSV y volvé a ejecutar."
        )

    # Orden de inserción: cada evento debe insertarse después de aquel al que apunta
    # su 'Siguiente evento ID', para satisfacer la clave foránea (PRAGMA foreign_keys = ON).
    filas = df.to_dict("records")
    insertados = set()
    orden = []
    pendientes = list(filas)
    intentos = 0
    while pendientes:
        salida = []
        progreso = False
        for fila in pendientes:
            siguiente = fila["siguiente_evento_id"]
            if siguiente is None or int(siguiente) in insertados:
                evento = int(fila["evento_id"])
                insertados.add(evento)
                orden.append(fila)
                progreso = True
            else:
                salida.append(fila)
        if not progreso:
            abrir(
                "No se pudo ordenar la inserción: hay un ciclo "
                "o una referencia pendiente en el CSV."
            )
        intentos += 1
        if intentos > len(filas):
            abrir("No se pudo ordenar la inserción: límite de pasadas superado.")
        pendientes = salida

    if len(orden) != len(df):
        abrir(f"Faltan filas por insertar: {len(df) - len(orden)}.")

    mm = {c: NOMBRES_LEGIBLES[c] for c in COLUMNAS}
    conn = sqlite3.connect(RUTA_DB)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute(f'DROP TABLE IF EXISTS "{TABLA}"')
    conn.execute(
        f"""
        CREATE TABLE "{TABLA}" (
            evento_id           INTEGER PRIMARY KEY,
            tipo_evento         TEXT NOT NULL,
            siguiente_evento_id INTEGER UNIQUE
                                REFERENCES "{TABLA}"(evento_id),
            persona_id          INTEGER,
            cama_id             INTEGER,
            fecha_hora_evento   TEXT
        )
        """
    )

    columnas_sql = ", ".join(f'"{c}"' for c in COLUMNAS)
    marcadores = ", ".join("?" for _ in COLUMNAS)
    valores = [
        tuple(
            int(fila[c]) if fila[c] is not None and c != "tipo_evento" and c != "fecha_hora_evento"
            else fila[c]
            for c in COLUMNAS
        )
        for fila in orden
    ]
    conn.executemany(
        f'INSERT INTO "{TABLA}" ({columnas_sql}) VALUES ({marcadores})', valores
    )
    conn.commit()
    conn.close()

    print(
        f"OK: {len(valores)} filas insertadas en '{TABLA}' ({RUTA_DB}). "
        f"Columnas: {', '.join(mm[c] for c in COLUMNAS)}."
    )


if __name__ == "__main__":
    main()