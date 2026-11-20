"""Acumuladores y estimadores de las medidas de rendimiento por réplica.

Este módulo no depende de que el modelo sea el original: recibe la
trayectoria, las visitas y los contadores que produce cualquier núcleo de
simulación compatible.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np

CLAVES_INTEGRAL = ("C", "Nq", "Ls", "B", "Nqq")


@dataclass
class AcumuladorTemporal:
    """Integra funciones escalón sobre la ventana ``[inicio, fin]``.

    ``actualizar(t, valores)`` debe llamarse en cada cambio de estado con los
    valores *posteriores* al cambio. El intervalo transcurrido desde la
    llamada anterior se integra con los valores anteriores.
    """

    inicio: float
    fin: float
    ultimo_t: float = 0.0
    valores: dict[str, float] = field(
        default_factory=lambda: {clave: 0.0 for clave in CLAVES_INTEGRAL}
    )
    integrales: dict[str, float] = field(
        default_factory=lambda: {clave: 0.0 for clave in CLAVES_INTEGRAL}
    )

    def actualizar(self, t: float, valores: dict[str, float]) -> None:
        t = float(t)
        if t < self.ultimo_t:
            raise ValueError("El tiempo no puede retroceder en el acumulador.")
        if t > self.ultimo_t:
            desde = max(self.ultimo_t, self.inicio)
            hasta = min(t, self.fin)
            if hasta > desde:
                ancho = hasta - desde
                for clave in CLAVES_INTEGRAL:
                    self.integrales[clave] += self.valores[clave] * ancho
        self.ultimo_t = t
        self.valores = dict(valores)

    def cerrar(self, t: float) -> None:
        self.actualizar(t, self.valores)


@dataclass
class ResultadoReplica:
    medidas: dict[str, Any]
    trayectoria: list[tuple[float, int, int, int, int]] | None
    visitas: list[dict[str, Any]]


def _media(valores: list[float]) -> float:
    return float(np.mean(valores)) if valores else float("nan")


def calcular_medidas(
    *,
    acumulador: AcumuladorTemporal,
    visitas: list[dict[str, Any]],
    T: float,
    warmup: float,
    c_camas: int,
    c_quirofano: int,
    n_llegadas_exogenas: int,
    interarribos: list[float],
    servicios_camas: list[float],
    servicios_quirofano: list[float],
    n_pacientes_creados: int,
    n_pacientes_salidos: int,
) -> dict[str, Any]:
    """Calcula una observación por medida a partir de una réplica terminada."""
    Tc = float(T) - float(warmup)
    if Tc <= 0:
        raise ValueError("La ventana de recolección T - d_T debe ser positiva.")

    integ = acumulador.integrales
    C = integ["C"] / Tc
    Nq = integ["Nq"] / Tc
    Ls = integ["Ls"] / Tc
    B = integ["B"] / Tc
    Nqq = integ["Nqq"] / Tc

    completas = [v for v in visitas if v["completa_en_ventana"]]
    n_visitas = len(completas)
    esperas = [float(v["espera_h"]) for v in completas]
    tiempos_sistema = [
        float(v["t_fin_servicio"]) - float(v["t_llegada_cola"]) for v in completas
    ]
    Wq = _media(esperas)
    Ws = _media(tiempos_sistema)

    quirofano_completas = [
        v
        for v in visitas
        if v["destino"] == "quirofano"
        and v["t_llegada_quirofano"] is not None
        and float(v["t_llegada_quirofano"]) >= warmup
        and v["t_fin_quirofano"] is not None
        and float(v["t_fin_quirofano"]) <= T
    ]
    esperas_q = [
        float(v["t_inicio_quirofano"]) - float(v["t_llegada_quirofano"])
        for v in quirofano_completas
    ]
    Wq_q = _media(esperas_q)

    lambda_eff = n_visitas / Tc
    lambda_ext = n_llegadas_exogenas / Tc

    destinos = Counter(str(v["destino"]) for v in completas)
    if n_visitas:
        frac_egreso = destinos["egreso"] / n_visitas
        frac_cama_externa = destinos["cama_externa"] / n_visitas
        frac_quirofano = destinos["quirofano"] / n_visitas
    else:
        frac_egreso = frac_cama_externa = frac_quirofano = float("nan")

    little_Ls_err = (
        (Ls - lambda_eff * Ws) / Ls
        if Ls != 0.0 and not np.isnan(Ws)
        else float("nan")
    )
    little_Lq_err = (
        (Nq - lambda_eff * Wq) / Nq
        if Nq != 0.0 and not np.isnan(Wq)
        else float("nan")
    )

    return {
        "C": C,
        "rho": C / c_camas,
        "Lq": Nq,
        "Ls": Ls,
        "Wq": Wq,
        "Ws": Ws,
        "rho_q": B / c_quirofano,
        "Lq_q": Nqq,
        "Wq_q": Wq_q,
        "n_visitas": n_visitas,
        "lambda_eff": lambda_eff,
        "lambda_ext": lambda_ext,
        "little_Ls_err": little_Ls_err,
        "little_Lq_err": little_Lq_err,
        "n_visitas_totales": len(visitas),
        "n_visitas_quirofano": len(quirofano_completas),
        "frac_egreso": frac_egreso,
        "frac_cama_externa": frac_cama_externa,
        "frac_quirofano": frac_quirofano,
        "n_llegadas_exogenas": n_llegadas_exogenas,
        "n_interarribos": len(interarribos),
        "media_interarribo": _media(interarribos),
        "n_servicios_camas": len(servicios_camas),
        "media_servicio_camas": _media(servicios_camas),
        "n_servicios_quirofano": len(servicios_quirofano),
        "media_servicio_quirofano": _media(servicios_quirofano),
        "n_pacientes_creados": n_pacientes_creados,
        "n_pacientes_salidos": n_pacientes_salidos,
        "n_pacientes_en_sistema": n_pacientes_creados - n_pacientes_salidos,
    }
