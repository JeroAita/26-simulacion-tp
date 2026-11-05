"""Escritura de los CSV y de la configuración efectiva de una corrida."""

from __future__ import annotations

import csv
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .config import ModeloConfig

COLUMNAS_ESTADO = [
    "corrida",
    "tiempo_h",
    "camas_n",
    "cola_cama_n",
    "quirofano_n",
    "cola_quirofano_n",
]

COLUMNAS_VISITAS = [
    "corrida",
    "paciente_id",
    "visita_no",
    "clase",
    "t_llegada_cola",
    "t_inicio_servicio",
    "t_fin_servicio",
    "servicio_h",
    "espera_h",
    "destino",
    "t_llegada_quirofano",
    "t_inicio_quirofano",
    "t_fin_quirofano",
    "completa_en_ventana",
]

COLUMNAS_MEDIDAS = [
    "corrida",
    "semilla_base",
    "T",
    "d_T",
    "antitetico",
    "C",
    "rho",
    "Lq",
    "Ls",
    "Wq",
    "Ws",
    "rho_q",
    "Lq_q",
    "Wq_q",
    "n_visitas",
    "lambda_eff",
    "lambda_ext",
    "little_Ls_err",
    "little_Lq_err",
    "n_visitas_totales",
    "n_visitas_quirofano",
    "frac_egreso",
    "frac_cama_externa",
    "frac_quirofano",
    "n_llegadas_exogenas",
    "n_interarribos",
    "media_interarribo",
    "n_servicios_camas",
    "media_servicio_camas",
    "n_servicios_quirofano",
    "media_servicio_quirofano",
    "n_pacientes_creados",
    "n_pacientes_salidos",
    "n_pacientes_en_sistema",
]


def _formatear(valor: Any) -> Any:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "True" if valor else "False"
    if isinstance(valor, float):
        return repr(valor)
    return valor


def _escribir_csv(ruta: Path, columnas: list[str], filas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(columnas)
        for fila in filas:
            escritor.writerow([_formatear(fila.get(columna)) for columna in columnas])


def escribir_estado(
    ruta: Path,
    corrida: int,
    trayectoria: list[tuple[float, int, int, int, int]],
) -> None:
    filas = [
        {
            "corrida": corrida,
            "tiempo_h": tiempo,
            "camas_n": camas,
            "cola_cama_n": cola_cama,
            "quirofano_n": quirofano,
            "cola_quirofano_n": cola_quirofano,
        }
        for tiempo, camas, cola_cama, quirofano, cola_quirofano in trayectoria
    ]
    _escribir_csv(ruta, COLUMNAS_ESTADO, filas)


def escribir_visitas(
    ruta: Path,
    corrida: int,
    visitas: list[dict[str, Any]],
) -> None:
    filas = []
    for visita in visitas:
        fila = dict(visita)
        fila["corrida"] = corrida
        filas.append(fila)
    _escribir_csv(ruta, COLUMNAS_VISITAS, filas)


def escribir_medidas(ruta: Path, filas: list[dict[str, Any]]) -> None:
    _escribir_csv(ruta, COLUMNAS_MEDIDAS, filas)


def versiones_librerias() -> dict[str, str]:
    versiones = {"python": sys.version.split()[0]}
    for nombre in ("simpy", "numpy", "pandas", "scipy", "matplotlib"):
        try:
            versiones[nombre] = version(nombre)
        except PackageNotFoundError:
            versiones[nombre] = "desconocida"
    return versiones


def _toml_valor(valor: Any) -> str:
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, str):
        return json.dumps(valor, ensure_ascii=False)
    return repr(valor)


def escribir_config_usada(
    ruta: Path,
    config: ModeloConfig,
    *,
    replicas: int,
    T: float,
    warmup: float,
    semilla_base: int,
    antitetico: bool,
    sin_trayectoria: bool,
) -> None:
    lineas = [
        "# Configuración efectiva de la corrida.",
        "",
        "[modelo]",
        f"nombre = {_toml_valor(config.nombre)}",
        f"c_camas = {config.c_camas}",
        f"c_quirofano = {config.c_quirofano}",
        f"prioridad_retornos = {config.prioridad_retornos}",
        f"prioridad_exogenas = {config.prioridad_exogenas}",
        "",
        "[muestras]",
    ]
    for clave, valor in config.rutas_muestras.items():
        lineas.append(f"{clave} = {_toml_valor(valor)}")
    lineas.extend(["", "[destinos]"])
    for clave, valor in config.destinos.items():
        lineas.append(f"{clave} = {valor}")
    lineas.extend(
        [
            "",
            "[simulacion]",
            f"replicas = {replicas}",
            f"T = {_toml_valor(float(T))}",
            f"warmup = {_toml_valor(float(warmup))}",
            f"semilla_base = {semilla_base}",
            f"antitetico = {_toml_valor(antitetico)}",
            f"sin_trayectoria = {_toml_valor(sin_trayectoria)}",
            "",
            "[versiones]",
        ]
    )
    for clave, valor in versiones_librerias().items():
        lineas.append(f"{clave} = {_toml_valor(valor)}")
    lineas.append("")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas), encoding="utf-8")
