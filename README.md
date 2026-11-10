
# Simulación: TP Final

Repositorio para organizar la redacción del trabajo práctico final de la asignatura Simulación, año 2026.

## Secciones

Un índice + barra de progreso del trabajo.

- [x] [Portada](secciones/1_portada.md)
  - [x] Autores
  - [x] Cátedra
  - [x] índice
  - [x] Consigna
- [x] [Introducción](secciones/2_introduccion.md)
  - [x] Sistema elegido
  - [x] Datos
- [x] [Análisis](secciones/3_analisis.md)
  - [x] Modelo
  - [x] Llegadas
  - [x] Tasas de servicio
  - [x] Llegadas y tiempos de servicio del quirófano
  - [x] Medidas de rendimiento analíticas
- [x] [Modelo de simulación](secciones/4_simulacion.md)
  - [x] Medidas de rendimiento a estimar
  - [x] Distribuciones elegidas
  - [x] Implementación en MATLAB/SimEvents
- [x] [Planeamiento táctico](secciones/5_tactico.md)
  - [x] Método para reunir observaciones
  - [x] Eliminación de transitorio
  - [x] Número de corridas y longitud
- [ ] [Resultados y propuesta de optimización](secciones/6_resultados.md)
  - [x] Resultados e IC
  - [ ] Reducción de varianza
  - [x] Modelo alternativo, resultados
  - [x] Test de hipótesis
- [ ] [Conclusiones](secciones/7_conclusiones.md)
- [ ] Apéndices


## Archivos

Entregables:
- [Simulación: TP Final](entregables/simulacion_tp_final.md)
- [Apéndice: Análisis de entradas - Chi Cuadrado](entregables/analisis_entradas_chi_cuadrado.md)
- [Apéndice: Distribuciones empíricas](entregables/distribuciones_empiricas.md)

~~~
secciones/   # Redacción de cada sección. Por separado para facilitar edición y avances.
entregables/ # Archivo acumulando las secciones + apéndices.

datos/       # CSV / base de datos SQLite con los datos de muestra.
scripts/     # SQL / Python para trabajar con los datos.

simulacion/  # Simulador SimPy del modelo (ver simulacion/README.md).
analisis/    # Scripts de transitorio, tamaño de muestra e intervalos.
configs/     # Configuración del modelo original.
tests/       # Pruebas del simulador.

src/         # Multimedia; imágenes.
~~~

## Simulador en Python

El modelo de la sección 4 está implementado con SimPy. Instrucciones completas
en [`simulacion/README.md`](simulacion/README.md).

~~~bash
python3 -m venv venv
source venv/bin/activate
pip install -e .

python scripts/extraer_muestras.py
python -m simulacion --config configs/original.toml \
    --replicas 20 --T 30000 --warmup 1000 --semilla 2026 \
    --salida salida/ejemplo --procesos 4
pytest
~~~