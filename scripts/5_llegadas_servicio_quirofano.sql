-- Script SQL 5: llegadas al quirófano
-- Identifica los eventos que constituyen una "llegada" al quirófano (cama 241)
-- desde las camas del sub-sistema seleccionado (223, 225, 226, 227, 228) y
-- calcula el periodo entre llegadas sucesivas (en horas).
--
-- Una llegada al quirófano ocurre cuando un "Pase de cama" tiene como destino
-- la cama 241 y como origen una cama del sub-sistema.
--
-- Requiere: datos_limpios

WITH ev AS (
    SELECT
        evento_id,
        tipo_evento,
        cama_id,
        fecha_hora_evento,
        internacion_id,
        LAG(cama_id) OVER w AS cama_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
llegadas_quirofano AS (
    SELECT
        fecha_hora_evento,
        evento_id,
        internacion_id,
        cama_prev AS cama_origen
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id = 241
      AND cama_prev IN (223, 225, 226, 227, 228)
)
SELECT
    fecha_hora_evento,
    evento_id,
    internacion_id,
    cama_origen,
    LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id) AS llegada_anterior,
    ROUND(
        (julianday(fecha_hora_evento) - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id))) * 24,
        4
    ) AS horas_entre_llegadas
FROM llegadas_quirofano
ORDER BY fecha_hora_evento, evento_id;

-- --------------------------------------------------------

-- Estadísticos descriptivos del periodo entre llegadas al quirófano
WITH ev AS (
    SELECT
        evento_id,
        tipo_evento,
        cama_id,
        fecha_hora_evento,
        internacion_id,
        LAG(cama_id) OVER w AS cama_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
llegadas_quirofano AS (
    SELECT fecha_hora_evento
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id = 241
      AND cama_prev IN (223, 225, 226, 227, 228)
),
periodos AS (
    SELECT
        (julianday(fecha_hora_evento) - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento))) * 24 AS horas_entre_llegadas
    FROM llegadas_quirofano
)
SELECT
    COUNT(*) AS n_observaciones,
    ROUND(MIN(horas_entre_llegadas), 4) AS minimo,
    ROUND(MAX(horas_entre_llegadas), 4) AS maximo,
    ROUND(AVG(horas_entre_llegadas), 4) AS media,
    ROUND(
        AVG(horas_entre_llegadas * horas_entre_llegadas) - AVG(horas_entre_llegadas) * AVG(horas_entre_llegadas),
        6
    ) AS varianza
FROM periodos;

-- -------------------------------------------------------

-- -------------------------------------------------------

-- Script SQL 6: tiempos de servicio del quirófano
-- Calcula el tiempo de servicio (en horas) de cada estancia de un paciente
-- en el quirófano (cama 241), considerando únicamente los pases originados
-- desde las camas del sub-sistema seleccionado.
--
-- Un "bloque de servicio" en el quirófano comienza cuando un paciente es
-- trasladado desde una cama del sub-sistema hacia el quirófano, y termina
-- cuando es trasladado desde el quirófano hacia una cama del sub-sistema.
--
-- Requiere: datos_limpios

WITH ev AS (
    SELECT
        evento_id,
        tipo_evento,
        cama_id,
        fecha_hora_evento,
        internacion_id,
        LAG(cama_id) OVER w AS cama_prev,
        LAG(tipo_evento) OVER w AS tipo_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
-- Entrada al quirófano desde cama del sub-sistema
entradas AS (
    SELECT
        evento_id AS evento_entrada,
        fecha_hora_evento AS fecha_entrada,
        internacion_id,
        cama_prev AS cama_origen
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id = 241
      AND cama_prev IN (223, 225, 226, 227, 228)
),
-- Salida del quirófano hacia cama del sub-sistema
salidas AS (
    SELECT
        evento_id AS evento_salida,
        fecha_hora_evento AS fecha_salida,
        internacion_id,
        cama_id AS cama_destino,
        cama_prev AS cama_origen_quirofano
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id IN (223, 225, 226, 227, 228)
      AND cama_prev = 241
),
-- Emparejar entradas y salidas por internación
-- Cada entrada se empareja con la siguiente salida de la misma internación
con_siguiente_salida AS (
    SELECT
        e.evento_entrada,
        e.fecha_entrada,
        e.internacion_id,
        e.cama_origen,
        s.evento_salida,
        s.fecha_salida,
        s.cama_destino,
        ROW_NUMBER() OVER (PARTITION BY e.internacion_id, e.evento_entrada ORDER BY s.fecha_salida) AS rn
    FROM entradas e
    LEFT JOIN salidas s ON s.internacion_id = e.internacion_id
                       AND s.fecha_salida > e.fecha_entrada
)
SELECT
    internacion_id,
    evento_entrada,
    fecha_entrada,
    cama_origen,
    evento_salida,
    fecha_salida,
    cama_destino,
    ROUND(
        (julianday(fecha_salida) - julianday(fecha_entrada)) * 24,
        4
    ) AS horas_servicio_quirofano
FROM con_siguiente_salida
WHERE rn = 1
  AND fecha_salida IS NOT NULL
ORDER BY fecha_entrada;

-- --------------------------------------------------------

-- Estadísticos descriptivos del tiempo de servicio del quirófano
WITH ev AS (
    SELECT
        evento_id,
        tipo_evento,
        cama_id,
        fecha_hora_evento,
        internacion_id,
        LAG(cama_id) OVER w AS cama_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
entradas AS (
    SELECT
        evento_id AS evento_entrada,
        fecha_hora_evento AS fecha_entrada,
        internacion_id
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id = 241
      AND cama_prev IN (223, 225, 226, 227, 228)
),
salidas AS (
    SELECT
        evento_id AS evento_salida,
        fecha_hora_evento AS fecha_salida,
        internacion_id
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id IN (223, 225, 226, 227, 228)
      AND cama_prev = 241
),
con_siguiente_salida AS (
    SELECT
        e.internacion_id,
        e.fecha_entrada,
        s.fecha_salida,
        ROW_NUMBER() OVER (PARTITION BY e.internacion_id, e.evento_entrada ORDER BY s.fecha_salida) AS rn
    FROM entradas e
    LEFT JOIN salidas s ON s.internacion_id = e.internacion_id
                       AND s.fecha_salida > e.fecha_entrada
),
tiempos AS (
    SELECT
        ROUND((julianday(fecha_salida) - julianday(fecha_entrada)) * 24, 4) AS horas_servicio
    FROM con_siguiente_salida
    WHERE rn = 1 AND fecha_salida IS NOT NULL
)
SELECT
    COUNT(*) AS n_observaciones,
    ROUND(MIN(horas_servicio), 4) AS minimo,
    ROUND(MAX(horas_servicio), 4) AS maximo,
    ROUND(AVG(horas_servicio), 4) AS media,
    ROUND(
        AVG(horas_servicio * horas_servicio) - AVG(horas_servicio) * AVG(horas_servicio),
        6
    ) AS varianza
FROM tiempos;