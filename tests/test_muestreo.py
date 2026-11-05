from __future__ import annotations

import numpy as np
import pytest

from simulacion.muestreo import InversaEmpirica, crear_flujos


def test_inversa_en_los_puntos_empiricos() -> None:
    muestra = [4.0, 1.0, 3.0, 2.0]
    inversa = InversaEmpirica(muestra)
    ordenada = np.sort(muestra)
    n = len(ordenada)
    probabilidades = (np.arange(1, n + 1) - 0.5) / n

    for probabilidad, valor in zip(probabilidades, ordenada):
        assert inversa.inversa(float(probabilidad)) == pytest.approx(float(valor))

    assert inversa.inversa(0.0) == pytest.approx(1.0)
    assert inversa.inversa(1.0) == pytest.approx(4.0)


def test_inversa_satura_y_no_sale_del_rango() -> None:
    muestra = [2.0, 5.0, 9.0, 20.0]
    inversa = InversaEmpirica(muestra)
    flujo = crear_flujos(123, 0)[0]

    valores = np.array([inversa.muestra(flujo) for _ in range(50_000)])
    assert valores.min() >= 2.0
    assert valores.max() <= 20.0
    assert np.mean(valores) == pytest.approx(np.mean(muestra), rel=0.02)
    assert np.median(valores) == pytest.approx(np.median(muestra), abs=0.5)


def test_inversa_rechaza_u_fuera_de_rango() -> None:
    inversa = InversaEmpirica([1.0, 2.0])
    with pytest.raises(ValueError):
        inversa.inversa(-0.01)
    with pytest.raises(ValueError):
        inversa.inversa(1.01)
