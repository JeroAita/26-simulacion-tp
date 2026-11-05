"""Configuración del modelo y de las distribuciones de entrada."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from .muestreo import DestinoCategorico, FlujoAleatorio, InversaEmpirica


class Distribucion(Protocol):
    """Cualquier objeto capaz de generar una observación con un flujo dado."""

    def muestra(self, flujo: FlujoAleatorio) -> Any: ...


@dataclass
class Distribuciones:
    """Distribuciones inyectables en el núcleo de simulación."""

    llegadas: Distribucion
    servicio_camas: Distribucion
    servicio_quirofano: Distribucion
    destino: Distribucion


@dataclass
class ModeloConfig:
    """Parámetros estructurales del modelo.

    Las distribuciones se construyen desde ``rutas_muestras`` o se inyectan
    directamente en :class:`simulacion.modelo.SistemaSimulacion`. El modelo
    alternativo podrá reutilizar este mismo núcleo cambiando esta configuración
    o la disciplina/ruteo en una subclase.
    """

    nombre: str = "original"
    c_camas: int = 5
    c_quirofano: int = 1
    prioridad_retornos: int = 0
    prioridad_exogenas: int = 1
    rutas_muestras: dict[str, str] = field(default_factory=dict)
    destinos: dict[str, int] = field(default_factory=dict)
    raiz: Path = field(default_factory=Path.cwd)

    def __post_init__(self) -> None:
        if self.c_camas <= 0:
            raise ValueError("c_camas debe ser positivo.")
        if self.c_quirofano <= 0:
            raise ValueError("c_quirofano debe ser positivo.")
        if self.prioridad_retornos >= self.prioridad_exogenas:
            raise ValueError(
                "La prioridad de los retornos debe ser menor (más alta) que la "
                "de las llegadas exógenas."
            )
        self.raiz = Path(self.raiz)

    def _leer_muestra(self, clave: str) -> np.ndarray:
        if clave not in self.rutas_muestras:
            raise ValueError(f"Falta la muestra '{clave}' en la configuración.")
        ruta = self.raiz / self.rutas_muestras[clave]
        if not ruta.exists():
            raise FileNotFoundError(
                f"No existe la muestra {ruta}. Ejecutá scripts/extraer_muestras.py."
            )
        valores = np.loadtxt(ruta, delimiter=",", skiprows=1, ndmin=1)
        return np.asarray(valores, dtype=float)

    def crear_distribuciones(self) -> Distribuciones:
        """Construye las inversas empíricas y el ruteo del modelo original."""
        if not self.destinos:
            raise ValueError("Faltan los conteos de destino en la configuración.")
        return Distribuciones(
            llegadas=InversaEmpirica(self._leer_muestra("interarribos_exogenos")),
            servicio_camas=InversaEmpirica(self._leer_muestra("servicio_camas")),
            servicio_quirofano=InversaEmpirica(self._leer_muestra("servicio_quirofano")),
            destino=DestinoCategorico(self.destinos),
        )


def cargar_config(ruta: str | Path, raiz: str | Path | None = None) -> ModeloConfig:
    """Carga ``configs/*.toml``.

    Las rutas de las muestras se resuelven contra ``raiz``. Si no se indica,
    se usa el directorio padre del directorio que contiene el archivo de
    configuración (por ejemplo, la raíz del repositorio para
    ``configs/original.toml``).
    """
    ruta = Path(ruta).resolve()
    with ruta.open("rb") as archivo:
        datos = tomllib.load(archivo)

    modelo = datos.get("modelo", {})
    muestras = datos.get("muestras", {})
    destinos = datos.get("destinos", {})
    base = Path(raiz).resolve() if raiz is not None else ruta.parent.parent

    return ModeloConfig(
        nombre=str(modelo.get("nombre", "original")),
        c_camas=int(modelo.get("c_camas", 5)),
        c_quirofano=int(modelo.get("c_quirofano", 1)),
        prioridad_retornos=int(modelo.get("prioridad_retornos", 0)),
        prioridad_exogenas=int(modelo.get("prioridad_exogenas", 1)),
        rutas_muestras={str(k): str(v) for k, v in muestras.items()},
        destinos={str(k): int(v) for k, v in destinos.items()},
        raiz=base,
    )
