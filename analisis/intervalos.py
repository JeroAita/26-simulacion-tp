"""Intervalos de confianza al 95 % por medida (t de Student).

Uso::

    python -m analisis.intervalos --entrada salida/final --precision 0.05
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
import numpy as np
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, help="Directorio de la corrida.")
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

    filas: list[dict[str, object]] = []
    for clave, _nombre in MEDIDAS:
        if clave not in medidas.columns:
            continue
        valores = medidas[clave].dropna().to_numpy(dtype=float)
        M = int(valores.size)
        if M < 2:
            continue
        media = float(np.mean(valores))
        desvio = float(np.std(valores, ddof=1))
        cuantil = float(t_student.ppf(1.0 - args.alpha / 2.0, df=M - 1))
        semianchura = cuantil * desvio / math.sqrt(M)
        d = absolutas.get(clave, precisiones.get(clave, args.precision) * media)
        filas.append(
            {
                "medida": clave,
                "M": M,
                "media": media,
                "S": desvio,
                "semianchura": semianchura,
                "li": media - semianchura,
                "ls": media + semianchura,
                "semianchura_relativa": (
                    semianchura / abs(media) if media != 0.0 else float("nan")
                ),
                "d": d,
                "cumple": bool(semianchura <= d),
            }
        )

    columnas = [
        "medida",
        "M",
        "media",
        "S",
        "semianchura",
        "li",
        "ls",
        "semianchura_relativa",
        "d",
        "cumple",
    ]
    guardar_tabla(
        filas,
        columnas,
        directorio / "intervalos.csv",
        directorio / "intervalos.md",
    )

    validos_figura = [
        fila
        for fila in filas
        if np.isfinite(float(fila["semianchura"]))
        and float(fila["d"]) > 0.0
    ]
    if validos_figura:
        figuras = Path(args.figuras)
        figuras.mkdir(parents=True, exist_ok=True)
        etiquetas = [str(fila["medida"]) for fila in validos_figura]
        ratios = [
            float(fila["semianchura"]) / float(fila["d"])
            for fila in validos_figura
        ]
        figura, eje = plt.subplots(figsize=(8.0, 4.5))
        eje.bar(etiquetas, ratios, color="#55A868")
        eje.axhline(1.0, color="#C44E52", linestyle="--", label="tolerancia")
        eje.set_yscale("log")
        eje.set_ylabel("semianchura / tolerancia")
        eje.set_title("Precisión alcanzada por medida (≤ 1 cumple)")
        eje.grid(axis="y", alpha=0.3)
        eje.legend()
        for indice, valor in enumerate(ratios):
            eje.text(
                indice,
                valor,
                f"{valor:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        figura.tight_layout()
        ruta_figura = figuras / "intervalos_precision.png"
        figura.savefig(ruta_figura, dpi=150)
        plt.close(figura)
        print(f"Figura: {ruta_figura}.")

    print(f"OK: {len(filas)} medidas con IC en {directorio}.")


if __name__ == "__main__":
    main()
