from __future__ import annotations

import math

import numpy as np
from scipy.stats import t as t_student

from simulacion.config import Distribuciones, ModeloConfig
from simulacion.modelo import simular_replica


class Exponencial:
    def __init__(self, tasa: float) -> None:
        self.tasa = tasa

    def muestra(self, flujo) -> float:  # noqa: ANN001
        return -math.log(1.0 - flujo.random()) / self.tasa


class DestinoFijo:
    def __init__(self, valor: str) -> None:
        self.valor = valor

    def muestra(self, flujo) -> str:  # noqa: ANN001
        return self.valor


def _erlang_c(lam: float, mu: float, c: int) -> tuple[float, float, float]:
    a = lam / mu
    rho = a / c
    terminos = sum(a**k / math.factorial(k) for k in range(c))
    ultimo = a**c / math.factorial(c) / (1.0 - rho)
    probabilidad_espera = ultimo / (terminos + ultimo)
    Lq = probabilidad_espera * rho / (1.0 - rho)
    Wq = Lq / lam
    return a, Lq, Wq


def _ic95(valores: list[float]) -> tuple[float, float, float]:
    datos = np.asarray(valores, dtype=float)
    media = float(np.mean(datos))
    desvio = float(np.std(datos, ddof=1))
    cuantil = float(t_student.ppf(0.975, df=datos.size - 1))
    semianchura = cuantil * desvio / math.sqrt(datos.size)
    return media, media - semianchura, media + semianchura


def test_mmc_contra_erlang_c() -> None:
    lam = 0.2
    mu = 0.055
    c = 5
    config = ModeloConfig(nombre="mmc", c_camas=c, c_quirofano=1)
    distribuciones = Distribuciones(
        llegadas=Exponencial(lam),
        servicio_camas=Exponencial(mu),
        servicio_quirofano=Exponencial(1.0),
        destino=DestinoFijo("egreso"),
    )

    resultados = [
        simular_replica(
            config,
            T=200_000.0,
            warmup=2_000.0,
            semilla_base=2026,
            replica=replica,
            sin_trayectoria=True,
            distribuciones=distribuciones,
        ).medidas
        for replica in range(10)
    ]

    Cbar_teoria, Lq_teoria, Wq_teoria = _erlang_c(lam, mu, c)

    for clave, teoria in (
        ("C", Cbar_teoria),
        ("Lq", Lq_teoria),
        ("Wq", Wq_teoria),
    ):
        media, li, ls = _ic95([float(fila[clave]) for fila in resultados])
        assert li <= teoria <= ls, (
            f"{clave}: teoría={teoria:.4f}, IC95%=({li:.4f}, {ls:.4f}), "
            f"media={media:.4f}"
        )
