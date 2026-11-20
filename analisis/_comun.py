"""Utilidades compartidas por los scripts de análisis."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd


def leer_medidas(directorio: str | Path) -> pd.DataFrame:
    ruta = Path(directorio) / "medidas.csv"
    if not ruta.exists():
        raise SystemExit(f"No existe {ruta}. Corré primero el simulador.")
    return pd.read_csv(ruta)


def _formatear(valor: Any, formato: str | None) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, float) and math.isnan(valor):
        return "—"
    if formato:
        return format(valor, formato)
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, float):
        return f"{valor:.4f}"
    return str(valor)


def tabla_markdown(
    filas: list[dict[str, Any]],
    columnas: list[str],
    *,
    formatos: dict[str, str] | None = None,
    resaltar: set[int] | None = None,
) -> str:
    """Arma una tabla Markdown simple, sin depender de ``tabulate``."""
    formatos = formatos or {}
    resaltar = resaltar or set()
    lineas = [
        "| " + " | ".join(columnas) + " |",
        "| " + " | ".join("---" for _ in columnas) + " |",
    ]
    for indice, fila in enumerate(filas):
        celdas = []
        for columna in columnas:
            texto = _formatear(fila.get(columna), formatos.get(columna))
            if indice in resaltar:
                texto = f"**{texto}**"
            celdas.append(texto)
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas) + "\n"


def guardar_tabla(
    filas: list[dict[str, Any]],
    columnas: list[str],
    ruta_csv: str | Path,
    ruta_md: str | Path,
    *,
    formatos: dict[str, str] | None = None,
    resaltar: set[int] | None = None,
) -> None:
    ruta_csv = Path(ruta_csv)
    ruta_md = Path(ruta_md)
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas, columns=columnas).to_csv(ruta_csv, index=False)
    ruta_md.write_text(
        tabla_markdown(
            filas,
            columnas,
            formatos=formatos,
            resaltar=resaltar,
        ),
        encoding="utf-8",
    )
