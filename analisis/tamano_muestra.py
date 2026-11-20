"""Cálculo de M (réplicas), n (valores por observación) y longitud.

Uso::

    python -m analisis.tamano_muestra --entrada salida/piloto \\
        --precision 0.05 --absoluta "Lq_q=0.01" --absoluta "Wq_q=0.05"
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import t as t_student

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ._comun import guardar_tabla, leer_medidas

MEDIDAS = [
    ("C", "Camas ocupadas"),
    ("rho", "Utilización de camas"),
    ("Ls", "Pacientes en el sistema"),
    ("Lq", "Pacientes en cola"),
    ("Wq", "Espera en cola"),
    ("Ws", "Tiempo en el sistema"),
    ("rho_q", "Utilización del quirófano"),
    ("Lq_q", "Cola del quirófano"),
    ("Wq_q", "Espera en el quirófano"),
]
SIMBOLOS = {clave for clave, _ in MEDIDAS}


def _parsear_pares(items: list[str] | None) -> dict[str, float]:
    resultado: dict[str, float] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Formato inválido: {item!r}. Usá MEDIDA=valor.")
        clave, valor = item.split("=", 1)
        clave = clave.strip()
        if clave not in SIMBOLOS:
            raise SystemExit(f"Medida desconocida: {clave!r}.")
        resultado[clave] = float(valor)
    return resultado


def _a_bool(serie: pd.Series) -> pd.Series:
    if serie.dtype == bool:
        return serie
    return serie.astype(str).str.lower().isin(["true", "1", "sí", "si"])


def _leer_visitas(directorio: Path) -> pd.DataFrame | None:
    rutas = sorted(directorio.glob("corrida_*_visitas.csv"))
    if not rutas:
        return None
    tablas = [pd.read_csv(ruta) for ruta in rutas]
    return pd.concat(tablas, ignore_index=True)


def _estadistico_m(
    valores: np.ndarray,
    precision: float,
    alpha: float,
) -> tuple[float, float, float, float, float]:
    m = int(valores.size)
    if m == 0:
        return (float("nan"),) * 5
    media = float(np.mean(valores))
    if m < 2:
        return media, float("nan"), float("nan"), float("nan"), float("nan")
    desvio = float(np.std(valores, ddof=1))
    cv = desvio / media if media != 0.0 else float("nan")
    d = precision * media
    if d <= 0.0 or not np.isfinite(d):
        return media, desvio, cv, d, float("nan")
    cuantil = float(t_student.ppf(1.0 - alpha / 2.0, df=m - 1))
    M = float(math.ceil((cuantil * desvio / d) ** 2))
    return media, desvio, cv, d, M


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, help="Directorio del piloto.")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--precision", type=float, default=0.05)
    parser.add_argument(
        "--precision-medida",
        action="append",
        default=[],
        help="Precisión relativa por medida, p. ej. Wq=0.10.",
    )
    parser.add_argument(
        "--absoluta",
        action="append",
        default=[],
        help="Cota absoluta por medida, p. ej. Lq_q=0.01.",
    )
    parser.add_argument(
        "--salida",
        default=None,
        help="Directorio de tablas (por defecto, <entrada>/analisis).",
    )
    parser.add_argument(
        "--figuras",
        default="src",
        help="Directorio de figuras (por defecto, src).",
    )
    args = parser.parse_args()

    if not 0.0 < args.alpha < 1.0:
        raise SystemExit("--alpha debe estar entre 0 y 1.")

    precisiones = _parsear_pares(args.precision_medida)
    absolutas = _parsear_pares(args.absoluta)

    entrada = Path(args.entrada)
    medidas = leer_medidas(entrada)
    directorio = Path(args.salida or (entrada / "analisis"))
    directorio.mkdir(parents=True, exist_ok=True)

    filas_m: list[dict[str, object]] = []
    for clave, _nombre in MEDIDAS:
        if clave not in medidas.columns:
            continue
        valores = medidas[clave].dropna().to_numpy(dtype=float)
        if valores.size == 0:
            continue
        p = precisiones.get(clave, args.precision)
        if clave in absolutas:
            media = float(np.mean(valores))
            desvio = (
                float(np.std(valores, ddof=1))
                if valores.size > 1
                else float("nan")
            )
            cv = desvio / media if media != 0.0 else float("nan")
            d = absolutas[clave]
            if d > 0 and np.isfinite(desvio):
                cuantil = float(t_student.ppf(1.0 - args.alpha / 2.0, df=valores.size - 1))
                M = float(math.ceil((cuantil * desvio / d) ** 2))
            else:
                M = float("nan")
        else:
            media, desvio, cv, d, M = _estadistico_m(valores, p, args.alpha)
        filas_m.append(
            {
                "medida": clave,
                "Xbar": media,
                "S_Xbar": desvio,
                "CV": cv,
                "d": d,
                "M": M,
            }
        )

    columnas_m = ["medida", "Xbar", "S_Xbar", "CV", "d", "M"]
    indices_validos = [
        i for i, fila in enumerate(filas_m) if np.isfinite(float(fila["M"]))
    ]
    resaltar: set[int] = set()
    if indices_validos:
        indice_max = max(indices_validos, key=lambda i: float(filas_m[i]["M"]))
        resaltar = {indice_max}
    guardar_tabla(
        filas_m,
        columnas_m,
        directorio / "tamano_muestra.csv",
        directorio / "tamano_muestra.md",
        resaltar=resaltar,
    )

    visitas = _leer_visitas(entrada)
    filas_n: list[dict[str, object]] = []
    if visitas is not None and not visitas.empty:
        completas = visitas[_a_bool(visitas["completa_en_ventana"])].copy()
        lambda_eff = float(medidas["lambda_eff"].dropna().mean())
        d_T = float(medidas["d_T"].dropna().iloc[0])

        valores_individuales = {
            "Wq": completas["espera_h"].dropna().to_numpy(dtype=float),
            "Ws": (
                completas["espera_h"] + completas["servicio_h"]
            ).dropna().to_numpy(dtype=float),
        }
        for clave, valores in valores_individuales.items():
            fila_m = next((f for f in filas_m if f["medida"] == clave), None)
            if fila_m is None or valores.size < 2:
                continue
            d = float(fila_m["d"])
            sigma = float(np.std(valores, ddof=1))
            b = d / sigma if sigma > 0.0 else float("nan")
            if b > 0.0 and np.isfinite(b):
                n = float(math.ceil(1.0 / (args.alpha * b**2)))
                Tc = n / lambda_eff if lambda_eff > 0.0 else float("nan")
                T = d_T + Tc
            else:
                n = float("nan")
                Tc = float("nan")
                T = float("nan")
            filas_n.append(
                {
                    "medida": clave,
                    "d": d,
                    "sigma_individual": sigma,
                    "b": b,
                    "n": n,
                    "lambda_eff": lambda_eff,
                    "Tc_h": Tc,
                    "T_h": T,
                }
            )
    else:
        print("Aviso: no hay corrida_*_visitas.csv; no se calcula n ni la longitud.")

    columnas_n = [
        "medida",
        "d",
        "sigma_individual",
        "b",
        "n",
        "lambda_eff",
        "Tc_h",
        "T_h",
    ]
    guardar_tabla(
        filas_n,
        columnas_n,
        directorio / "longitud.csv",
        directorio / "longitud.md",
    )

    if filas_m:
        M_max = max(
            (float(f["M"]) for f in filas_m if np.isfinite(float(f["M"]))),
            default=float("nan"),
        )
        validos_figura = [
            fila
            for fila in filas_m
            if np.isfinite(float(fila["M"])) and float(fila["M"]) > 0.0
        ]
        if validos_figura:
            figuras = Path(args.figuras)
            figuras.mkdir(parents=True, exist_ok=True)
            etiquetas = [str(fila["medida"]) for fila in validos_figura]
            valores = [float(fila["M"]) for fila in validos_figura]
            figura, eje = plt.subplots(figsize=(8.0, 4.5))
            eje.bar(etiquetas, valores, color="#4C72B0")
            eje.set_yscale("log")
            eje.set_ylabel("M (réplicas)")
            eje.set_title("Tamaño de muestra M por medida")
            eje.grid(axis="y", alpha=0.3)
            for indice, valor in enumerate(valores):
                eje.text(
                    indice,
                    valor,
                    f"{valor:g}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
            figura.tight_layout()
            ruta_figura = figuras / "tamano_muestra_M.png"
            figura.savefig(ruta_figura, dpi=150)
            plt.close(figura)
            print(f"Figura: {ruta_figura}.")
        print(f"OK: tablas en {directorio}. M máximo = {M_max:g}.")
    else:
        print(f"OK: tablas en {directorio}.")


if __name__ == "__main__":
    main()
