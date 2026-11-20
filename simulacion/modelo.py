"""Núcleo de simulación SimPy del sub-sistema de internación.

La disciplina de cola y el ruteo están en métodos sobrescribibles
(``paciente``, ``pasar_por_quirofano`` y ``sortear_destino``) para facilitar
el modelo alternativo de etapas futuras.
"""

from __future__ import annotations

from typing import Any

import simpy

from .config import Distribuciones, ModeloConfig
from .medidas import AcumuladorTemporal, ResultadoReplica, calcular_medidas
from .muestreo import FlujoAleatorio, crear_flujos


class SistemaSimulacion:
    """Estado y procesos del modelo original."""

    def __init__(
        self,
        env: simpy.Environment,
        config: ModeloConfig,
        *,
        distribuciones: Distribuciones | None = None,
        semilla_base: int = 0,
        replica: int = 0,
        antitetico: bool = False,
        T: float = 1.0,
        warmup: float = 0.0,
        sin_trayectoria: bool = False,
        iniciar_llegadas: bool = True,
    ) -> None:
        self.env = env
        self.config = config
        self.dist = distribuciones or config.crear_distribuciones()
        self.T = float(T)
        self.warmup = float(warmup)
        self.semilla_base = int(semilla_base)
        self.replica = int(replica)
        self.antitetico = bool(antitetico)

        (
            self.flujo_llegadas,
            self.flujo_servicio_camas,
            self.flujo_destino,
            self.flujo_servicio_quirofano,
        ) = crear_flujos(semilla_base, replica, antitetico)

        self.camas = simpy.PriorityResource(env, capacity=config.c_camas)
        self.quirofano = simpy.Resource(env, capacity=config.c_quirofano)

        self.c_camas = 0
        self.nq_camas = 0
        self.c_quirofano = 0
        self.nq_quirofano = 0

        self.trayectoria: list[tuple[float, int, int, int, int]] | None = (
            None if sin_trayectoria else []
        )
        self.visitas: list[dict[str, Any]] = []
        self.acumulador = AcumuladorTemporal(inicio=self.warmup, fin=self.T)

        self.n_pacientes_creados = 0
        self.n_pacientes_salidos = 0
        self.n_llegadas_exogenas_ventana = 0
        self.interarribos: list[float] = []
        self.servicios_camas: list[float] = []
        self.servicios_quirofano: list[float] = []

        self.registrar_estado()

        if iniciar_llegadas:
            env.process(self.proceso_llegadas())

    # ------------------------------------------------------------------
    # Registro de estado
    # ------------------------------------------------------------------
    def registrar_estado(self) -> None:
        """Registra el estado posterior a un cambio y actualiza integrales."""
        valores = {
            "C": float(self.c_camas),
            "Nq": float(self.nq_camas),
            "Ls": float(self.c_camas + self.nq_camas),
            "B": float(self.c_quirofano),
            "Nqq": float(self.nq_quirofano),
        }
        self.acumulador.actualizar(self.env.now, valores)
        if self.trayectoria is not None:
            self.trayectoria.append(
                (
                    float(self.env.now),
                    self.c_camas,
                    self.nq_camas,
                    self.c_quirofano,
                    self.nq_quirofano,
                )
            )

    # ------------------------------------------------------------------
    # Procesos
    # ------------------------------------------------------------------
    def proceso_llegadas(self):
        """Genera llegadas exógenas con la inversa empírica configurada."""
        while True:
            interarribo = float(
                self.dist.llegadas.muestra(self.flujo_llegadas)
            )
            self.interarribos.append(interarribo)
            yield self.env.timeout(interarribo)

            self.n_pacientes_creados += 1
            if self.warmup <= self.env.now <= self.T:
                self.n_llegadas_exogenas_ventana += 1
            self.env.process(
                self.paciente(
                    clase=self.config.prioridad_exogenas,
                    paciente_id=self.n_pacientes_creados,
                )
            )

    def paciente(self, clase: int, paciente_id: int):
        """Proceso de un paciente: visitas sucesivas hasta el egreso."""
        visita_no = 1
        while True:
            servicio = float(
                self.dist.servicio_camas.muestra(self.flujo_servicio_camas)
            )
            self.servicios_camas.append(servicio)
            destino = self.sortear_destino()

            t_cola = float(self.env.now)
            visita: dict[str, Any] = {
                "paciente_id": paciente_id,
                "visita_no": visita_no,
                "clase": clase,
                "t_llegada_cola": t_cola,
                "t_inicio_servicio": None,
                "t_fin_servicio": None,
                "servicio_h": servicio,
                "espera_h": None,
                "destino": destino,
                "t_llegada_quirofano": None,
                "t_inicio_quirofano": None,
                "t_fin_quirofano": None,
                "completa_en_ventana": False,
            }
            self.visitas.append(visita)

            self.nq_camas += 1
            self.registrar_estado()

            req = self.camas.request(priority=clase)
            yield req

            t_inicio = float(self.env.now)
            visita["t_inicio_servicio"] = t_inicio
            visita["espera_h"] = t_inicio - t_cola
            self.nq_camas -= 1
            self.c_camas += 1
            self.registrar_estado()

            yield self.env.timeout(servicio)

            t_fin = float(self.env.now)
            visita["t_fin_servicio"] = t_fin
            self.c_camas -= 1
            self.registrar_estado()
            self.camas.release(req)

            if destino != "quirofano":
                self.n_pacientes_salidos += 1
                return

            yield from self.pasar_por_quirofano(visita)

            clase = self.config.prioridad_retornos
            visita_no += 1

    def pasar_por_quirofano(self, visita: dict[str, Any]):
        """Espera, servicio y registro del paso por el quirófano."""
        visita["t_llegada_quirofano"] = float(self.env.now)
        self.nq_quirofano += 1
        self.registrar_estado()

        req = self.quirofano.request()
        yield req

        visita["t_inicio_quirofano"] = float(self.env.now)
        self.nq_quirofano -= 1
        self.c_quirofano += 1
        self.registrar_estado()

        servicio = float(
            self.dist.servicio_quirofano.muestra(self.flujo_servicio_quirofano)
        )
        self.servicios_quirofano.append(servicio)
        yield self.env.timeout(servicio)

        visita["t_fin_quirofano"] = float(self.env.now)
        self.c_quirofano -= 1
        self.registrar_estado()
        self.quirofano.release(req)

    def sortear_destino(self) -> str:
        """Sortea el destino al terminar el servicio en cama."""
        return str(self.dist.destino.muestra(self.flujo_destino))

    # ------------------------------------------------------------------
    # Cierre y resultados
    # ------------------------------------------------------------------
    def finalizar(self, T: float | None = None) -> None:
        """Cierra la ventana, agrega la fila final y marca visitas completas."""
        T = float(self.T if T is None else T)
        self.acumulador.cerrar(T)
        if self.trayectoria is not None:
            self.trayectoria.append(
                (
                    T,
                    self.c_camas,
                    self.nq_camas,
                    self.c_quirofano,
                    self.nq_quirofano,
                )
            )
        for visita in self.visitas:
            visita["completa_en_ventana"] = bool(
                visita["t_llegada_cola"] is not None
                and float(visita["t_llegada_cola"]) >= self.warmup
                and visita["t_fin_servicio"] is not None
                and float(visita["t_fin_servicio"]) <= T
            )

    def resultado(self) -> ResultadoReplica:
        medidas = calcular_medidas(
            acumulador=self.acumulador,
            visitas=self.visitas,
            T=self.T,
            warmup=self.warmup,
            c_camas=self.config.c_camas,
            c_quirofano=self.config.c_quirofano,
            n_llegadas_exogenas=self.n_llegadas_exogenas_ventana,
            interarribos=self.interarribos,
            servicios_camas=self.servicios_camas,
            servicios_quirofano=self.servicios_quirofano,
            n_pacientes_creados=self.n_pacientes_creados,
            n_pacientes_salidos=self.n_pacientes_salidos,
        )
        return ResultadoReplica(
            medidas=medidas,
            trayectoria=self.trayectoria,
            visitas=self.visitas,
        )


def simular_replica(
    config: ModeloConfig,
    *,
    T: float,
    warmup: float = 0.0,
    semilla_base: int = 0,
    replica: int = 0,
    antitetico: bool = False,
    sin_trayectoria: bool = False,
    distribuciones: Distribuciones | None = None,
    iniciar_llegadas: bool = True,
) -> ResultadoReplica:
    """Corre una réplica independiente y devuelve sus resultados."""
    env = simpy.Environment()
    sistema = SistemaSimulacion(
        env,
        config,
        distribuciones=distribuciones,
        semilla_base=semilla_base,
        replica=replica,
        antitetico=antitetico,
        T=T,
        warmup=warmup,
        sin_trayectoria=sin_trayectoria,
        iniciar_llegadas=iniciar_llegadas,
    )
    env.run(until=T)
    sistema.finalizar(T)
    return sistema.resultado()
