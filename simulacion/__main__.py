"""Interfaz de línea de comandos del simulador.

Ejemplo::

    python -m simulacion --config configs/original.toml \\
        --replicas 20 --T 30000 --warmup 0 --semilla 12345 \\
        --salida salida/piloto_01
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
from pathlib import Path
from typing import Any

from .config import ModeloConfig, cargar_config
from .modelo import simular_replica
from .salida import escribir_config_usada, escribir_estado, escribir_medidas, escribir_visitas


def _ejecutar_replica(tarea: tuple[ModeloConfig, int, dict[str, Any], str]) -> dict[str, Any]:
    config, replica, parametros, salida = tarea
    ruta_salida = Path(salida)

    resultado = simular_replica(
        config,
        T=parametros["T"],
        warmup=parametros["warmup"],
        semilla_base=parametros["semilla"],
        replica=replica,
        antitetico=parametros["antitetico"],
        sin_trayectoria=parametros["sin_trayectoria"],
    )

    if resultado.trayectoria is not None:
        escribir_estado(
            ruta_salida / f"corrida_{replica:02d}_estado.csv",
            replica,
            resultado.trayectoria,
        )
    escribir_visitas(
        ruta_salida / f"corrida_{replica:02d}_visitas.csv",
        replica,
        resultado.visitas,
    )

    fila: dict[str, Any] = {
        "corrida": replica,
        "semilla_base": parametros["semilla"],
        "T": parametros["T"],
        "d_T": parametros["warmup"],
        "antitetico": parametros["antitetico"],
    }
    fila.update(resultado.medidas)
    return fila


def _parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulador de eventos discretos del sub-sistema de internación."
    )
    parser.add_argument(
        "--config",
        default="configs/original.toml",
        help="Archivo TOML de configuración (por defecto: configs/original.toml).",
    )
    parser.add_argument("--replicas", type=int, default=1, help="Cantidad de réplicas.")
    parser.add_argument("--T", type=float, default=30000.0, help="Longitud de cada corrida (h).")
    parser.add_argument(
        "--warmup",
        type=float,
        default=0.0,
        help="Transitorio descartado d_T (h).",
    )
    parser.add_argument("--semilla", type=int, default=12345, help="Semilla base.")
    parser.add_argument("--salida", required=True, help="Directorio de salida.")
    parser.add_argument(
        "--antitetico",
        action="store_true",
        help="Usa 1-U en todos los flujos (réplica antitética).",
    )
    parser.add_argument(
        "--sin-trayectoria",
        action="store_true",
        help="Omite los CSV de trayectoria de estados.",
    )
    parser.add_argument(
        "--procesos",
        type=int,
        default=1,
        help="Cantidad de procesos para correr réplicas en paralelo.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parsear_argumentos()
    if args.replicas <= 0:
        raise SystemExit("--replicas debe ser positivo.")
    if args.procesos <= 0:
        raise SystemExit("--procesos debe ser positivo.")
    if args.T <= args.warmup:
        raise SystemExit("--T debe ser mayor que --warmup.")

    config = cargar_config(args.config)
    ruta_salida = Path(args.salida)
    ruta_salida.mkdir(parents=True, exist_ok=True)

    parametros = {
        "T": float(args.T),
        "warmup": float(args.warmup),
        "semilla": int(args.semilla),
        "antitetico": bool(args.antitetico),
        "sin_trayectoria": bool(args.sin_trayectoria),
    }
    tareas = [
        (config, replica, parametros, str(ruta_salida))
        for replica in range(args.replicas)
    ]

    if args.procesos == 1:
        filas = [_ejecutar_replica(tarea) for tarea in tareas]
    else:
        with mp.Pool(processes=args.procesos) as pool:
            filas = pool.map(_ejecutar_replica, tareas, chunksize=1)

    filas.sort(key=lambda fila: fila["corrida"])
    escribir_medidas(ruta_salida / "medidas.csv", filas)
    escribir_config_usada(
        ruta_salida / "config_usada.toml",
        config,
        replicas=args.replicas,
        T=args.T,
        warmup=args.warmup,
        semilla_base=args.semilla,
        antitetico=args.antitetico,
        sin_trayectoria=args.sin_trayectoria,
    )

    print(
        f"OK: {args.replicas} réplica(s) en {ruta_salida} "
        f"(T={args.T:g} h, d_T={args.warmup:g} h)."
    )


if __name__ == "__main__":
    main()
