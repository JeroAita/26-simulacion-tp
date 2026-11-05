from __future__ import annotations

from simulacion.modelo import simular_replica
from simulacion.muestreo import crear_flujos


def test_misma_semilla_y_replica_da_la_misma_trayectoria(config_original) -> None:
    primera = simular_replica(
        config_original,
        T=300.0,
        warmup=0.0,
        semilla_base=7,
        replica=0,
    )
    segunda = simular_replica(
        config_original,
        T=300.0,
        warmup=0.0,
        semilla_base=7,
        replica=0,
    )
    assert primera.trayectoria == segunda.trayectoria
    assert primera.visitas == segunda.visitas
    assert primera.medidas == segunda.medidas


def test_replicas_distintas_dan_trayectorias_distintas(config_original) -> None:
    primera = simular_replica(
        config_original,
        T=300.0,
        warmup=0.0,
        semilla_base=7,
        replica=0,
    )
    segunda = simular_replica(
        config_original,
        T=300.0,
        warmup=0.0,
        semilla_base=7,
        replica=1,
    )
    assert primera.trayectoria != segunda.trayectoria


def test_antitetico_usa_exactamente_uno_menos_u() -> None:
    flujos = crear_flujos(99, 3, antitetico=False)
    flujos_antiteticos = crear_flujos(99, 3, antitetico=True)

    for flujo, flujo_antitetico in zip(flujos, flujos_antiteticos):
        for _ in range(100):
            u = flujo.random()
            u_antitetico = flujo_antitetico.random()
            assert u_antitetico == 1.0 - u
