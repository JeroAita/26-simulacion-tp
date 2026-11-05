from __future__ import annotations

import simpy

from simulacion.config import Distribuciones, ModeloConfig
from simulacion.modelo import SistemaSimulacion


class ValorFijo:
    def __init__(self, valor: float) -> None:
        self.valor = valor

    def muestra(self, flujo) -> float:  # noqa: ANN001
        return self.valor


class DestinoFijo:
    def __init__(self, valor: str) -> None:
        self.valor = valor

    def muestra(self, flujo) -> str:  # noqa: ANN001
        return self.valor


def _lanzar_en(env: simpy.Environment, sistema: SistemaSimulacion, t: float, clase: int, pid: int):
    def proceso():
        yield env.timeout(t)
        yield from sistema.paciente(clase=clase, paciente_id=pid)

    env.process(proceso())


def test_prioridad_de_retornos_y_fifo_entre_nuevos() -> None:
    config = ModeloConfig(nombre="prioridad", c_camas=1, c_quirofano=1)
    distribuciones = Distribuciones(
        llegadas=ValorFijo(1e9),
        servicio_camas=ValorFijo(10.0),
        servicio_quirofano=ValorFijo(1.0),
        destino=DestinoFijo("egreso"),
    )
    env = simpy.Environment()
    sistema = SistemaSimulacion(
        env,
        config,
        distribuciones=distribuciones,
        T=100.0,
        warmup=0.0,
        iniciar_llegadas=False,
    )

    env.process(sistema.paciente(clase=1, paciente_id=1))
    _lanzar_en(env, sistema, 1.0, clase=1, pid=2)
    _lanzar_en(env, sistema, 2.0, clase=0, pid=3)
    _lanzar_en(env, sistema, 3.0, clase=1, pid=4)

    env.run(until=100.0)
    sistema.finalizar(100.0)

    inicios = {v["paciente_id"]: v["t_inicio_servicio"] for v in sistema.visitas}
    assert inicios[1] == 0.0
    assert inicios[3] == 10.0
    assert inicios[2] == 20.0
    assert inicios[4] == 30.0

    primera = next(v for v in sistema.visitas if v["paciente_id"] == 1)
    assert primera["t_fin_servicio"] == 10.0
