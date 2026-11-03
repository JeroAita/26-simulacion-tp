
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
- [ ] [Modelo de simulación](secciones/4_simulacion.md)
  - [ ] Medidas de rendimiento a estimar
  - [ ] Distribuciones elegidas
  - [ ] Implementación en MATLAB/SimEvents
  - [ ] Verificación y validación
- [ ] [Planeamiento táctico](secciones/5_tactico.md)
  - [ ] Método para reunir observaciones
  - [ ] Eliminación de transitorio
  - [ ] Número de corridas y longitud
- [ ] [Resultados y propuesta de optimización](secciones/6_resultados.md)
  - [ ] Resultados e IC
  - [ ] Comparación con lo analítico y test de hipótesis
  - [ ] Reducción de varianza
  - [ ] Modelo alternativo
  - [ ] Comparación
- [ ] [Conclusiones](secciones/7_conclusiones.md)
- [ ] Apéndices

## Archivos

Entregables:
- [Simulación: TP Final](entregables/simulacion_tp_final.md)
- [Apéndice: Análisis de entradas - Chi Cuadrado](analisis_entradas_chi_cuadrado.md)

~~~
secciones/   # Redacción de cada sección. Por separado para facilitar edición y avances.
entregables/ # Archivo acumulando las secciones + apéndices.

datos/       # CSV / base de datos SQLite con los datos de muestra.
scripts/     # SQL / Python para trabajar con los datos.

src/         # Multimedia; imágenes.