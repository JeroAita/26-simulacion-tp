
# Simulación: TP Final

Repositorio para organizar la redacción del trabajo práctico final de la asignatura Simulación, año 2026.

## Secciones

Un índice + barra de progreso del trabajo.

- [x] [Portada](secciones/portada.md)
  - [x] Autores
  - [x] Cátedra
  - [x] índice
  - [x] Consigna
- [x] [Introducción](secciones/introduccion.md)
  - [x] Sistema elegido
  - [x] Datos
- [ ] [Análisis](secciones/analisis.md)
  - [x] Modelo
  - [x] Llegadas
  - [x] Tasas de servicio
  - [x] Llegadas y tiempos de servicio del quirófano
  - [ ] Medidas de rendimiento analíticas
- [ ] Modelo de simulación
  - [ ] Variables de estado
  - [ ] Eventos
  - [ ] Lista de eventos
  - [ ] Diagrama de flujo
  - [ ] Implementación en MATLAB
  - [ ] Validación
- [ ] [Experimentación: planeamiento táctico](secciones/experimentacion.md)
  - [ ] Medidas de rendimiento elegidas
  - [ ] Transitorio
  - [ ] Número de observaciones
  - [ ] Número y longitud de corridas
  - [ ] Resultados, IC y tests de hipótesis
  - [ ] Reducción de varianza
- [ ] [Optimización](secciones/optimizacion.md)
  - [ ] Modelo alternativo
  - [ ] Comparación
- [ ] [Conclusiones](secciones/conclusiones.md)
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