from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analisis.transitorio import integral_escalon
from simulacion.modelo import simular_replica


def test_integrales_de_la_trayectoria_coinciden_con_el_acumulador(config_original) -> None:
    T = 2_000.0
    warmup = 200.0
    resultado = simular_replica(
        config_original,
        T=T,
        warmup=warmup,
        semilla_base=11,
        replica=0,
    )
    assert resultado.trayectoria is not None

    tabla = pd.DataFrame(
        resultado.trayectoria,
        columns=[
            "tiempo_h",
            "camas_n",
            "cola_cama_n",
            "quirofano_n",
            "cola_quirofano_n",
        ],
    )
    t = tabla["tiempo_h"].to_numpy(dtype=float)
    bordes = np.array([warmup, T], dtype=float)
    Tc = T - warmup

    series = {
        "C": tabla["camas_n"].to_numpy(dtype=float),
        "Lq": tabla["cola_cama_n"].to_numpy(dtype=float),
        "Ls": (tabla["camas_n"] + tabla["cola_cama_n"]).to_numpy(dtype=float),
        "rho_q": tabla["quirofano_n"].to_numpy(dtype=float),
        "Lq_q": tabla["cola_quirofano_n"].to_numpy(dtype=float),
    }
    for clave, valores in series.items():
        integral = integral_escalon(t, valores, bordes)
        recalculada = float(integral[1] - integral[0]) / Tc
        assert resultado.medidas[clave] == pytest.approx(
            recalculada, rel=1e-9, abs=1e-9
        )


def test_little_en_una_corrida_larga(config_original) -> None:
    resultado = simular_replica(
        config_original,
        T=30_000.0,
        warmup=1_000.0,
        semilla_base=12,
        replica=0,
        sin_trayectoria=True,
    )
    assert abs(resultado.medidas["little_Ls_err"]) < 0.05
    assert abs(resultado.medidas["little_Lq_err"]) < 0.10


def test_conservacion_de_pacientes(config_original) -> None:
    resultado = simular_replica(
        config_original,
        T=2_000.0,
        warmup=0.0,
        semilla_base=13,
        replica=0,
        sin_trayectoria=True,
    )
    ultimas = {
        visita["paciente_id"]: visita for visita in resultado.visitas
    }
    salieron = sum(
        1
        for visita in ultimas.values()
        if visita["destino"] != "quirofano"
        and visita["t_fin_servicio"] is not None
    )
    en_sistema = len(ultimas) - salieron

    assert len(ultimas) == resultado.medidas["n_pacientes_creados"]
    assert salieron == resultado.medidas["n_pacientes_salidos"]
    assert en_sistema == resultado.medidas["n_pacientes_en_sistema"]
