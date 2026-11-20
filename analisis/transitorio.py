"""Eliminación del transitorio por promedio móvil de ventana fija.

Implementa el método de Emshoff-Sisson (Shannon) sobre las réplicas piloto
corridas con ``d_T = 0`` y trayectoria de estados habilitada.

Uso::

    python -m analisis.transitorio --entrada salida/piloto \\
        --delta 10 --ventanas 5,20,50
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ._comun import guardar_tabla


def integral_escalon(t: np.ndarray, y: np.ndarray, bordes: np.ndarray) -> np.ndarray:
    """Integral exacta de una función escalón en los ``bordes`` indicados."""
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    bordes = np.asarray(bordes, dtype=float)
    if t.size == 0:
        return np.zeros_like(bordes)
    if t.size == 1:
        return y[0] * (bordes - t[0])
    acumulada = np.concatenate(([0.0], np.cumsum(y[:-1] * np.diff(t))))
    indice = np.searchsorted(t, bordes, side="right") - 1
    indice = np.clip(indice, 0, t.size - 1)
    return acumulada[indice] + y[indice] * (bordes - t[indice])


def cargar_trayectorias(directorio: str | Path) -> tuple[list[pd.DataFrame], float]:
    rutas = sorted(Path(directorio).glob("corrida_*_estado.csv"))
    if not rutas:
        raise SystemExit(
            f"No se encontraron corrida_*_estado.csv en {directorio}. "
            "Corré el piloto sin --sin-trayectoria."
        )
    tablas = [pd.read_csv(ruta) for ruta in rutas]
    T = min(float(tabla["tiempo_h"].max()) for tabla in tablas)
    return tablas, T


def medias_por_intervalo(
    tabla: pd.DataFrame,
    delta: float,
    T: float,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    t = tabla["tiempo_h"].to_numpy(dtype=float)
    series = {
        "N": (tabla["camas_n"] + tabla["cola_cama_n"]).to_numpy(dtype=float),
        "Nq": tabla["cola_cama_n"].to_numpy(dtype=float),
        "C": tabla["camas_n"].to_numpy(dtype=float),
    }
    n_intervalos = int(math.ceil(T / delta))
    if n_intervalos <= 0:
        raise SystemExit("T debe ser positivo.")
    bordes = np.array(
        [min(i * delta, T) for i in range(n_intervalos + 1)],
        dtype=float,
    )
    anchos = np.diff(bordes)
    medias: dict[str, np.ndarray] = {}
    for nombre, valores in series.items():
        integral = integral_escalon(t, valores, bordes)
        medias[nombre] = np.diff(integral) / anchos
    return medias, bordes[:-1]


def promediar_replicas(
    tablas: list[pd.DataFrame],
    delta: float,
    T: float,
    series: list[str],
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    acumulados: dict[str, np.ndarray] = {}
    tiempos: np.ndarray | None = None
    for tabla in tablas:
        medias, tiempos = medias_por_intervalo(tabla, delta, T)
        for nombre in series:
            if nombre not in acumulados:
                acumulados[nombre] = np.zeros_like(medias[nombre])
            acumulados[nombre] += medias[nombre]
    if tiempos is None:
        raise SystemExit("No hay réplicas para promediar.")
    return {nombre: acumulados[nombre] / len(tablas) for nombre in series}, tiempos


def media_movil(serie: np.ndarray, ventana: int) -> np.ndarray:
    resultado = np.full_like(serie, np.nan, dtype=float)
    if ventana <= 0:
        raise ValueError("La ventana debe ser positiva.")
    if serie.size >= ventana:
        resultado[ventana - 1 :] = np.convolve(
            serie, np.ones(ventana) / ventana, mode="valid"
        )
    return resultado


def proponer_dt(
    promedio_movil: np.ndarray,
    delta: float,
    banda: float,
) -> tuple[float, float, float]:
    """Propone un ``d_T`` a partir del promedio móvil.

    Devuelve ``(d_T_propuesto, nivel_final, d_T_estable)``. El propuesto es la
    primera entrada a la banda de ±``banda`` alrededor del nivel final. El
    tercer valor es el primer ``j`` desde el cual la serie ya no sale de la
    banda (``nan`` si eso no ocurre en la ventana).
    """
    validos = np.where(np.isfinite(promedio_movil))[0]
    if validos.size == 0:
        return float("nan"), float("nan"), float("nan")
    cola = validos[-max(1, validos.size // 10) :]
    nivel_final = float(np.mean(promedio_movil[cola]))
    tolerancia = max(abs(banda * nivel_final), 1e-12)

    primera_entrada: int | None = None
    estable: int | None = None
    for j in validos:
        if primera_entrada is None and abs(float(promedio_movil[j]) - nivel_final) <= tolerancia:
            primera_entrada = int(j)
        resto = promedio_movil[j:]
        resto = resto[np.isfinite(resto)]
        if estable is None and np.all(np.abs(resto - nivel_final) <= tolerancia):
            estable = int(j)
        if primera_entrada is not None and estable is not None:
            break

    if primera_entrada is None:
        return float(validos[-1] * delta), nivel_final, float("nan")
    dt_estable = float(estable * delta) if estable is not None else float("nan")
    return float(primera_entrada * delta), nivel_final, dt_estable


def _parsear_ventanas(texto: str) -> list[int]:
    ventanas = [int(parte) for parte in texto.split(",") if parte.strip()]
    if not ventanas or any(v <= 0 for v in ventanas):
        raise SystemExit("--ventanas debe ser una lista de enteros positivos.")
    return ventanas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, help="Directorio del piloto.")
    parser.add_argument("--delta", type=float, default=10.0, help="Ancho de intervalo (h).")
    parser.add_argument(
        "--ventanas",
        default="5,20,50",
        help="Ventanas del promedio móvil, separadas por coma.",
    )
    parser.add_argument(
        "--series",
        default="N,Nq,C",
        help="Series a analizar: N, Nq y/o C.",
    )
    parser.add_argument("--banda", type=float, default=0.05, help="Banda relativa (±).")
    parser.add_argument("--figuras", default="src", help="Directorio de figuras PNG.")
    parser.add_argument(
        "--tablas",
        default=None,
        help="Directorio de tablas (por defecto, <entrada>/analisis).",
    )
    args = parser.parse_args()

    ventanas = _parsear_ventanas(args.ventanas)
    series = [s.strip() for s in args.series.split(",") if s.strip()]
    invalidas = set(series) - {"N", "Nq", "C"}
    if invalidas:
        raise SystemExit(f"Series desconocidas: {sorted(invalidas)}")

    tablas, T = cargar_trayectorias(args.entrada)
    promedios, tiempos = promediar_replicas(tablas, args.delta, T, series)

    directorio_tablas = Path(args.tablas or (Path(args.entrada) / "analisis"))
    directorio_figuras = Path(args.figuras)
    directorio_figuras.mkdir(parents=True, exist_ok=True)

    resumen: list[dict[str, object]] = []

    for nombre in series:
        promedio = promedios[nombre]
        moviles = {ventana: media_movil(promedio, ventana) for ventana in ventanas}

        figura, eje = plt.subplots(figsize=(10, 5))
        eje.plot(
            tiempos,
            promedio,
            color="0.65",
            linewidth=0.8,
            label="media entre réplicas",
        )
        for ventana, movil in moviles.items():
            eje.plot(tiempos, movil, label=f"promedio móvil w={ventana}")
            dt, nivel_final, dt_estable = proponer_dt(
                movil, args.delta, args.banda
            )
            eje.axvline(dt, linestyle="--", alpha=0.6, label=f"d_T w={ventana}")
            if np.isfinite(dt_estable) and dt_estable != dt:
                eje.axvline(dt_estable, linestyle=":", alpha=0.4)
            resumen.append(
                {
                    "serie": nombre,
                    "ventana": ventana,
                    "d_T_propuesto_h": dt,
                    "nivel_final": nivel_final,
                    "banda_relativa": args.banda,
                    "d_T_estable_h": dt_estable,
                }
            )
        eje.set_title(f"Transitorio de la serie {nombre} (K={len(tablas)} réplicas)")
        eje.set_xlabel("tiempo (h)")
        eje.set_ylabel(nombre)
        eje.grid(alpha=0.3)
        eje.legend()
        figura.savefig(
            directorio_figuras / f"transitorio_{nombre}.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(figura)

        filas = []
        for i, tiempo in enumerate(tiempos):
            fila: dict[str, object] = {
                "intervalo": i,
                "tiempo_h": float(tiempo),
                "media": float(promedio[i]),
            }
            for ventana in ventanas:
                fila[f"mm_w{ventana}"] = float(moviles[ventana][i])
            filas.append(fila)
        columnas = ["intervalo", "tiempo_h", "media"] + [
            f"mm_w{ventana}" for ventana in ventanas
        ]
        guardar_tabla(
            filas,
            columnas,
            directorio_tablas / f"transitorio_{nombre}.csv",
            directorio_tablas / f"transitorio_{nombre}.md",
        )

    guardar_tabla(
        resumen,
        [
            "serie",
            "ventana",
            "d_T_propuesto_h",
            "nivel_final",
            "banda_relativa",
            "d_T_estable_h",
        ],
        directorio_tablas / "transitorio_resumen.csv",
        directorio_tablas / "transitorio_resumen.md",
    )
    print(
        f"OK: {len(tablas)} réplicas, T={T:g} h. "
        f"Tablas en {directorio_tablas}, figuras en {directorio_figuras}."
    )


if __name__ == "__main__":
    main()
