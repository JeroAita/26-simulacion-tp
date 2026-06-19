import pandas as pd
import sqlite3

# Leer el CSV
df = pd.read_csv("datos/angeles-movimientos_internacion.csv")

# Crear la base de datos SQLite
conn = sqlite3.connect("datos/datos.db")

# Guardar el DataFrame en SQLite
df.to_sql("tabla_datos", conn, if_exists="replace", index=False)

# Cerrar la conexión
conn.close()
