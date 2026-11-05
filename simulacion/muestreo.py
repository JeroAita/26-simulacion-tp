"""Muestreo por inversa empírica y flujos de números aleatorios.

Cada fuente de aleatoriedad del modelo tiene su propio flujo, derivado de
``numpy.random.SeedSequence``. No se usa el módulo ``random`` ni el estado
global de ``numpy.random``.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np


class FlujoAleatorio:
    """Envoltura de un ``numpy.random.Generator`` con opción antitética."""

    def __init__(self, generador: np.random.Generator, antitetico: bool = False) -> None:
        self.generador = generador
        self.antitetico = antitetico

    def random(self) -> float:
        """Devuelve un número U(0,1); con antitetico, devuelve ``1 - U``."""
        u = float(self.generador.random())
        return 1.0 - u if self.antitetico else u


def crear_flujos(
    semilla_base: int,
    replica: int,
    antitetico: bool = False,
) -> tuple[FlujoAleatorio, FlujoAleatorio, FlujoAleatorio, FlujoAleatorio]:
    """Crea los cuatro flujos independientes de una réplica.

    Orden: (1) interarribos exógenos, (2) servicio en camas, (3) destino,
    (4) servicio del quirófano.
    """
    secuencia = np.random.SeedSequence(
        entropy=semilla_base,
        spawn_key=(replica,),
    )
    hijos = secuencia.spawn(4)
    return tuple(  # type: ignore[return-value]
        FlujoAleatorio(np.random.Generator(np.random.PCG64(hijo)), antitetico)
        for hijo in hijos
    )


class InversaEmpirica:
    """Inversa de la distribución empírica por interpolación lineal.

    Dada la muestra ordenada ``x_(1) <= ... <= x_(n)`` se usan las
    probabilidades acumuladas ``p_i = (i - 0.5) / n``. Fuera del rango
    ``[p_1, p_n]`` la función satura en el mínimo o el máximo observado.
    """

    def __init__(self, muestra: object) -> None:
        valores = np.asarray(muestra, dtype=float).ravel()
        if valores.size == 0:
            raise ValueError("La muestra no puede estar vacía.")
        if not np.all(np.isfinite(valores)):
            raise ValueError("La muestra contiene valores no finitos.")
        self._x = np.sort(valores)
        n = self._x.size
        self._p = (np.arange(1, n + 1) - 0.5) / n

    @property
    def n(self) -> int:
        return int(self._x.size)

    @property
    def minimo(self) -> float:
        return float(self._x[0])

    @property
    def maximo(self) -> float:
        return float(self._x[-1])

    def inversa(self, u: float) -> float:
        """Evalúa ``F_n^{-1}(u)`` para un ``u`` explícito en ``[0, 1]``."""
        u = float(u)
        if not 0.0 <= u <= 1.0:
            raise ValueError(f"u debe estar en [0, 1]; se recibió {u!r}.")
        return float(np.interp(u, self._p, self._x))

    def muestra(self, flujo: FlujoAleatorio) -> float:
        """Sortea exactamente un ``U`` del flujo y lo transforma."""
        return self.inversa(flujo.random())


class DestinoCategorico:
    """Distribución categórica construida a partir de conteos observados."""

    def __init__(self, conteos: Mapping[str, int]) -> None:
        if not conteos:
            raise ValueError("Los conteos de destino no pueden estar vacíos.")
        categorias = list(conteos.keys())
        valores = np.asarray([conteos[c] for c in categorias], dtype=float)
        if np.any(valores < 0) or valores.sum() <= 0:
            raise ValueError("Los conteos de destino deben ser no negativos.")
        self.categorias = tuple(categorias)
        self.conteos = {c: int(conteos[c]) for c in categorias}
        self.probabilidades = valores / valores.sum()
        self.acumuladas = np.cumsum(self.probabilidades)

    def inversa(self, u: float) -> str:
        """Devuelve la categoría asociada a ``u`` (un solo número aleatorio)."""
        u = float(u)
        if not 0.0 <= u <= 1.0:
            raise ValueError(f"u debe estar en [0, 1]; se recibió {u!r}.")
        indice = int(np.searchsorted(self.acumuladas, u, side="right"))
        indice = min(indice, len(self.categorias) - 1)
        return self.categorias[indice]

    def muestra(self, flujo: FlujoAleatorio) -> str:
        return self.inversa(flujo.random())
