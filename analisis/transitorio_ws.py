"""Eliminación del transitorio de ``W_s`` por promedio móvil de ventana fija.

Lee las visitas de las réplicas piloto (``corrida_*_visitas.csv``), calcula
``W_s = t_fin_servicio - t_llegada_cola`` y agrupa las visitas por intervalo
según su instante de llegada. Luego promedia entre réplicas y aplica el
promedio móvil de ventana fija (Emshoff-Sisson, descrito en Shannon).

Uso::

    python -m analisis.transitorio_ws --entrada salida/transitorio-ws \\
        --delta 50 --ventanas 5,10,20

Las visitas que llegan cerca de ``T`` y no terminan se excluyen, por lo que
los últimos intervalos están censurados. El nivel final se estima con una
región central, descartando esa cola, para no sesgar la banda de estabilidad.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ._comun import guardar_tabla  # noqa: E402
from .transitorio import media_movil  # noqa: E402


def cargar_visitas(directorio: str | Path) -> tuple[list[pd.DataFrame], float]:
    """Carga las visitas de todas las réplicas y detecta ``T``."""
    directorio = Path(directorio)
    rutas = sorted(directorio.glob("corrida_*_visitas.csv"))
    if not rutas:
        raise SystemExit(
            f"No se encontraron corrida_*_visitas.csv en {directorio}. "
            "Corré el piloto sin --sin-trayectoria."
        )
    tablas = [pd.read_csv(ruta) for ruta in rutas]

    ruta_medidas = directorio / "medidas.csv"
    if ruta_medidas.exists():
        medidas = pd.read_csv(ruta_medidas)
        if "T" in medidas.columns:
            valores = medidas["T"].dropna()
            if not valores.empty:
                return tablas, float(valores.iloc[0])

    ruta_config = directorio / "config_usada.toml"
    if ruta_config.exists():
        import tomllib

        with ruta_config.open("rb") as archivo:
            datos = tomllib.load(archivo)
        T = datos.get("simulacion", {}).get("T")
        if T is not None:
            return tablas, float(T)

    maximos = [
        float(pd.to_numeric(tabla["t_fin_servicio"], errors="coerce").max())
        for tabla in tablas
    ]
    return tablas, max(maximos)


def _serie_ws_replica(
    tabla: pd.DataFrame,
    delta: float,
    T: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Media de ``W_s`` por intervalo de llegada para una réplica."""
    t_llegada = pd.to_numeric(tabla["t_llegada_cola"], errors="coerce")
    t_fin = pd.to_numeric(tabla["t_fin_servicio"], errors="coerce")
    validas = (
        t_llegada.notna()
        & t_fin.notna()
        & (t_llegada >= 0.0)
        & (t_llegada < T)
        & (t_fin <= T)
    )

    tiempos = t_llegada[validas].to_numpy(dtype=float)
    ws = (t_fin[validas] - t_llegada[validas]).to_numpy(dtype=float)

    n_intervalos = int(math.ceil(T / delta))
    if n_intervalos <= 0:
        raise SystemExit("T y delta deben ser positivos.")
    indices = np.clip(
        np.floor(tiempos / delta).astype(int),
        0,
        n_intervalos - 1,
    )
    sumas = np.bincount(indices, weights=ws, minlength=n_intervalos)
    conteos = np.bincount(indices, minlength=n_intervalos)
    medias = np.divide(
        sumas,
        conteos,
        out=np.full(n_intervalos, np.nan, dtype=float),
        where=conteos > 0,
    )
    return medias, conteos


def promediar_replicas(
    tablas: list[pd.DataFrame],
    delta: float,
    T: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Promedia ``W_s`` por intervalo entre réplicas."""
    series = []
    conteos_totales = None
    for tabla in tablas:
        medias, conteos = _serie_ws_replica(tabla, delta, T)
        series.append(medias)
        conteos_totales = (
            conteos if conteos_totales is None else conteos_totales + conteos
        )

    matriz = np.vstack(series)
    finitos = np.isfinite(matriz)
    suma = np.nansum(matriz, axis=0)
    cuenta = finitos.sum(axis=0)
    promedio = np.divide(
        suma,
        cuenta,
        out=np.full(matriz.shape[1], np.nan, dtype=float),
        where=cuenta > 0,
    )
    return promedio, conteos_totales, matriz


def nivel_final_robusto(
    promedio_movil: np.ndarray,
    tiempos: np.ndarray,
    T: float,
    margen: float,
    inicio_relativo: float = 0.5,
) -> float:
    """Nivel final estimado en la región central, sin la cola censurada."""
    inicio = max(0.0, inicio_relativo * T)
    fin = max(inicio, T - margen)
    mascara = (
        np.isfinite(promedio_movil)
        & (tiempos >= inicio)
        & (tiempos <= fin)
    )
    if not mascara.any():
        mascara = np.isfinite(promedio_movil) & (tiempos <= T - margen)
    if not mascara.any():
        mascara = np.isfinite(promedio_movil)
    return float(np.nanmean(promedio_movil[mascara]))


def proponer_dt(
    promedio_movil: np.ndarray,
    tiempos: np.ndarray,
    nivel: float,
    banda: float,
    fin: float,
    racha_minima: int,
) -> tuple[float, float, float]:
    """Devuelve ``(d_T_entrada, d_T_racha, d_T_estable)``.

    ``entrada`` es el primer intervalo dentro de la banda; ``racha`` exige
    mantenerse dentro durante ``racha_minima`` intervalos consecutivos;
    ``estable`` exige no volver a salir hasta ``fin``.
    """
    validos = np.where(np.isfinite(promedio_movil) & (tiempos <= fin))[0]
    if validos.size == 0:
        return float("nan"), float("nan"), float("nan")

    tolerancia = max(abs(banda * nivel), 1e-12)
    dentro = np.abs(promedio_movil - nivel) <= tolerancia

    entrada = next((j for j in validos if dentro[j]), None)
    estable = next(
        (
            j
            for j in validos
            if np.all(dentro[j : validos[-1] + 1])
        ),
        None,
    )
    racha = None
    for j in validos:
        tramo = dentro[j : j + racha_minima]
        if tramo.size == racha_minima and np.all(tramo):
            racha = j
            break

    return (
        float(tiempos[entrada]) if entrada is not None else float("nan"),
        float(tiempos[racha]) if racha is not None else float("nan"),
        float(tiempos[estable]) if estable is not None else float("nan"),
    )


def _parsear_ventanas(texto: str) -> list[int]:
    ventanas = [int(parte) for parte in texto.split(",") if parte.strip()]
    if not ventanas or any(ventana <= 0 for ventana in ventanas):
        raise SystemExit("--ventanas debe ser una lista de enteros positivos.")
    return ventanas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, help="Directorio del piloto.")
    parser.add_argument(
        "--delta",
        type=float,
        default=50.0,
        help="Ancho de intervalo en horas (por defecto: 50).",
    )
    parser.add_argument(
        "--ventanas",
        default="5,10,20",
        help="Ventanas del promedio móvil en intervalos, separadas por coma.",
    )
    parser.add_argument(
        "--banda",
        type=float,
        default=0.05,
        help="Banda relativa alrededor del nivel final (por defecto: 0.05).",
    )
    parser.add_argument(
        "--margen",
        type=float,
        default=None,
        help=(
            "Horas de la cola censurada que se descartan para el nivel final. "
            "Por defecto: max(500, max(ventanas)*delta)."
        ),
    )
    parser.add_argument(
        "--T",
        type=float,
        default=None,
        help="Sobrescribe T (útil para probar con un prefijo de otra corrida).",
    )
    parser.add_argument(
        "--figuras",
        default="src",
        help="Directorio de figuras PNG.",
    )
    parser.add_argument(
        "--nombre-figura",
        default="transitorio_Ws.png",
        help="Nombre del PNG de salida.",
    )
    parser.add_argument(
        "--tablas",
        default=None,
        help="Directorio de tablas (por defecto, <entrada>/analisis).",
    )
    args = parser.parse_args()

    if args.delta <= 0.0:
        raise SystemExit("--delta debe ser positivo.")
    if not 0.0 < args.banda < 1.0:
        raise SystemExit("--banda debe estar entre 0 y 1.")

    ventanas = _parsear_ventanas(args.ventanas)
    tablas, T_detectado = cargar_visitas(args.entrada)
    T = float(args.T) if args.T is not None else T_detectado
    if T <= 0.0:
        raise SystemExit("T debe ser positivo.")

    margen = (
        float(args.margen)
        if args.margen is not None
        else max(500.0, max(ventanas) * args.delta)
    )
    if margen >= T:
        raise SystemExit("El margen de censura debe ser menor que T.")

    promedio, conteos, _matriz = promediar_replicas(tablas, args.delta, T)
    n_intervalos = promedio.size
    tiempos = np.arange(n_intervalos, dtype=float) * args.delta
    fin_nivel = T - margen

    moviles: dict[int, np.ndarray] = {}
    resumen: list[dict[str, object]] = []
    for ventana in ventanas:
        movil = media_movil(promedio, ventana)
        moviles[ventana] = movil
        nivel = nivel_final_robusto(movil, tiempos, T, margen)
        dt_entrada, dt_racha, dt_estable = proponer_dt(
            movil,
            tiempos,
            nivel,
            args.banda,
            fin_nivel,
            racha_minima=max(3, ventana),
        )
        resumen.append(
            {
                "ventana": ventana,
                "ventana_h": ventana * args.delta,
                "delta_h": args.delta,
                "d_T_entrada_h": dt_entrada,
                "d_T_racha_h": dt_racha,
                "d_T_estable_h": dt_estable,
                "nivel_final_h": nivel,
                "banda_relativa": args.banda,
                "margen_censura_h": margen,
                "T_h": T,
                "K": len(tablas),
            }
        )

    directorio_tablas = Path(args.tablas or (Path(args.entrada) / "analisis"))
    directorio_figuras = Path(args.figuras)
    directorio_figuras.mkdir(parents=True, exist_ok=True)

    figura, eje = plt.subplots(figsize=(10, 5))
    eje.plot(
        tiempos,
        promedio,
        color="0.65",
        linewidth=0.8,
        label="media entre réplicas",
    )
    colores = [
        plt.cm.tab10(indice / max(len(ventanas) - 1, 1))
        for indice in range(len(ventanas))
    ]
    for (ventana, movil), color, fila in zip(
        moviles.items(), colores, resumen
    ):
        eje.plot(
            tiempos,
            movil,
            color=color,
            label=f"promedio móvil w={ventana} ({ventana * args.delta:g} h)",
        )
        dt_racha = float(fila["d_T_racha_h"])
        if np.isfinite(dt_racha):
            eje.axvline(
                dt_racha,
                color=color,
                linestyle="--",
                alpha=0.6,
                label=f"d_T w={ventana}: {dt_racha:g} h",
            )

    nivel_referencia = float(resumen[-1]["nivel_final_h"])
    eje.axhline(
        nivel_referencia,
        color="black",
        linestyle=":",
        linewidth=0.9,
        label=f"nivel final ≈ {nivel_referencia:.2f} h",
    )
    eje.axhspan(
        nivel_referencia * (1.0 - args.banda),
        nivel_referencia * (1.0 + args.banda),
        color="gray",
        alpha=0.12,
        label=f"banda ±{args.banda:.0%}",
    )
    eje.axvspan(
        T - margen,
        T,
        color="tab:red",
        alpha=0.08,
        label="cola censurada",
    )
    eje.set_xlim(0.0, T)
    eje.set_title(
        f"Transitorio de $W_s$ (K={len(tablas)}, T={T:g} h, "
        f"$\\Delta$={args.delta:g} h)"
    )
    eje.set_xlabel("tiempo (h)")
    eje.set_ylabel("$W_s$ (h)")
    eje.grid(alpha=0.3)
    eje.legend(fontsize=8, ncol=2)
    figura.tight_layout()
    ruta_figura = directorio_figuras / args.nombre_figura
    figura.savefig(ruta_figura, dpi=150, bbox_inches="tight")
    plt.close(figura)

    filas_serie: list[dict[str, object]] = []
    for i, tiempo in enumerate(tiempos):
        fila: dict[str, object] = {
            "intervalo": i,
            "tiempo_h": float(tiempo),
            "ws_medio_h": float(promedio[i]),
            "n_visitas": int(conteos[i]),
        }
        for ventana in ventanas:
            fila[f"mm_w{ventana}"] = float(moviles[ventana][i])
        filas_serie.append(fila)

    columnas_serie = ["intervalo", "tiempo_h", "ws_medio_h", "n_visitas"] + [
        f"mm_w{ventana}" for ventana in ventanas
    ]
    guardar_tabla(
        filas_serie,
        columnas_serie,
        directorio_tablas / "transitorio_Ws.csv",
        directorio_tablas / "transitorio_Ws.md",
    )
    guardar_tabla(
        resumen,
        [
            "ventana",
            "ventana_h",
            "delta_h",
            "d_T_entrada_h",
            "d_T_racha_h",
            "d_T_estable_h",
            "nivel_final_h",
            "banda_relativa",
            "margen_censura_h",
            "T_h",
            "K",
        ],
        directorio_tablas / "transitorio_resumen.csv",
        directorio_tablas / "transitorio_resumen.md",
    )

    print(
        f"OK: {len(tablas)} réplicas, T={T:g} h, delta={args.delta:g} h, "
        f"margen de censura={margen:g} h."
    )
    for fila in resumen:
        print(
            f"  w={fila['ventana']:>2} ({fila['ventana_h']:>4g} h): "
            f"d_T entrada={fila['d_T_entrada_h']!s:>8} h, "
            f"d_T racha={fila['d_T_racha_h']!s:>8} h, "
            f"nivel={fila['nivel_final_h']:.3f} h"
        )
    print(f"Figura: {ruta_figura}. Tablas: {directorio_tablas}.")


if __name__ == "__main__":
    main()
