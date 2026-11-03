-- Script SQL 4: tiempos de servicio
-- Calcula el tiempo de servicio (en horas) de cada estancia continua de un
-- paciente en el sub-sistema de camas seleccionado (223, 225, 226, 227, 228).
--
-- Un "bloque de servicio" comienza cuando el paciente entra al sub-sistema
-- (Ingreso o Pase desde cama externa/quirófano) y termina cuando sale
-- (Egreso, Pase a quirófano, o Pase a cama externa).
-- Los pases entre camas del sub-sistema NO interrumpen el bloque.
-- El tiempo en quirófano NO cuenta como tiempo de servicio de las camas.
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
-- Clasificar cada evento según su relación con el sub-sistema
clasificado AS (
    SELECT
        *,
        CASE
            -- Entrada: Ingreso directo a cama del sub-sistema
            WHEN tipo_evento = 'Ingreso' 
                 AND cama_id IN (223, 225, 226, 227, 228) 
            THEN 'entrada'
            
            -- Entrada: Pase desde cama externa (o quirófano) hacia sub-sistema
            WHEN tipo_evento = 'Pase de cama' 
                 AND cama_id IN (223, 225, 226, 227, 228)
                 AND cama_prev IS NOT NULL 
                 AND cama_prev NOT IN (223, 225, 226, 227, 228) 
            THEN 'entrada'
            
            -- Salida: Egreso desde cama del sub-sistema
            WHEN tipo_evento = 'Egreso' 
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            
            -- Salida: Pase desde cama del sub-sistema hacia quirófano
            WHEN tipo_evento = 'Pase de cama' 
                 AND cama_id = 241
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            
            -- Salida: Pase desde cama del sub-sistema hacia cama externa
            WHEN tipo_evento = 'Pase de cama'
                 AND cama_id NOT IN (223, 225, 226, 227, 228, 241)
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            
            -- Interno: Pase entre camas del sub-sistema (no interrumpe bloque)
            WHEN tipo_evento = 'Pase de cama'
                 AND cama_id IN (223, 225, 226, 227, 228)
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'interno'
            
            ELSE 'externo'
        END AS tipo_movimiento
    FROM ev
),
-- Asignar número de bloque usando suma acumulativa de entradas
con_bloque AS (
    SELECT
        *,
        SUM(CASE WHEN tipo_movimiento = 'entrada' THEN 1 ELSE 0 END) 
            OVER (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id) AS bloque_id
    FROM clasificado
),
-- Filtrar solo eventos dentro del sub-sistema (bloques con entrada)
bloques AS (
    SELECT *
    FROM con_bloque
    WHERE tipo_movimiento IN ('entrada', 'interno', 'salida')
      AND bloque_id > 0
)
-- Para cada bloque, calcular tiempo de servicio
SELECT
    internacion_id,
    bloque_id,
    MIN(fecha_hora_evento) AS inicio_servicio,
    MAX(fecha_hora_evento) AS fin_servicio,
    ROUND(
        (julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24,
        4
    ) AS horas_servicio
FROM bloques
GROUP BY internacion_id, bloque_id
-- Solo bloques completos (con evento de salida)
HAVING MAX(CASE WHEN tipo_movimiento = 'salida' THEN 1 ELSE 0 END) = 1
ORDER BY inicio_servicio;

-- ---------------------------------------------------

-- Estadísticos descriptivos del tiempo de servicio
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
clasificado AS (
    SELECT
        *,
        CASE
            WHEN tipo_evento = 'Ingreso' 
                 AND cama_id IN (223, 225, 226, 227, 228) 
            THEN 'entrada'
            WHEN tipo_evento = 'Pase de cama' 
                 AND cama_id IN (223, 225, 226, 227, 228)
                 AND cama_prev IS NOT NULL 
                 AND cama_prev NOT IN (223, 225, 226, 227, 228) 
            THEN 'entrada'
            WHEN tipo_evento = 'Egreso' 
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            WHEN tipo_evento = 'Pase de cama' 
                 AND cama_id = 241
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            WHEN tipo_evento = 'Pase de cama'
                 AND cama_id NOT IN (223, 225, 226, 227, 228, 241)
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            WHEN tipo_evento = 'Pase de cama'
                 AND cama_id IN (223, 225, 226, 227, 228)
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'interno'
            ELSE 'externo'
        END AS tipo_movimiento
    FROM ev
),
con_bloque AS (
    SELECT
        *,
        SUM(CASE WHEN tipo_movimiento = 'entrada' THEN 1 ELSE 0 END) 
            OVER (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id) AS bloque_id
    FROM clasificado
),
bloques AS (
    SELECT *
    FROM con_bloque
    WHERE tipo_movimiento IN ('entrada', 'interno', 'salida')
      AND bloque_id > 0
),
tiempos_servicio AS (
    SELECT
        internacion_id,
        bloque_id,
        ROUND(
            (julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24,
            4
        ) AS horas_servicio
    FROM bloques
    GROUP BY internacion_id, bloque_id
    HAVING MAX(CASE WHEN tipo_movimiento = 'salida' THEN 1 ELSE 0 END) = 1
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
FROM tiempos_servicio;

-- ---------------------------------------------------

-- Distribución por cama de inicio del servicio
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
clasificado AS (
    SELECT
        *,
        CASE
            WHEN tipo_evento = 'Ingreso' 
                 AND cama_id IN (223, 225, 226, 227, 228) 
            THEN 'entrada'
            WHEN tipo_evento = 'Pase de cama' 
                 AND cama_id IN (223, 225, 226, 227, 228)
                 AND cama_prev IS NOT NULL 
                 AND cama_prev NOT IN (223, 225, 226, 227, 228) 
            THEN 'entrada'
            WHEN tipo_evento = 'Egreso' 
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            WHEN tipo_evento = 'Pase de cama' 
                 AND cama_id = 241
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            WHEN tipo_evento = 'Pase de cama'
                 AND cama_id NOT IN (223, 225, 226, 227, 228, 241)
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'salida'
            WHEN tipo_evento = 'Pase de cama'
                 AND cama_id IN (223, 225, 226, 227, 228)
                 AND cama_prev IN (223, 225, 226, 227, 228) 
            THEN 'interno'
            ELSE 'externo'
        END AS tipo_movimiento
    FROM ev
),
con_bloque AS (
    SELECT
        *,
        SUM(CASE WHEN tipo_movimiento = 'entrada' THEN 1 ELSE 0 END) 
            OVER (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id) AS bloque_id
    FROM clasificado
),
bloques AS (
    SELECT *
    FROM con_bloque
    WHERE tipo_movimiento IN ('entrada', 'interno', 'salida')
      AND bloque_id > 0
),
tiempos_servicio AS (
    SELECT
        internacion_id,
        bloque_id,
        MIN(CASE WHEN tipo_movimiento = 'entrada' THEN cama_id END) AS cama_inicio,
        ROUND(
            (julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24,
            4
        ) AS horas_servicio
    FROM bloques
    GROUP BY internacion_id, bloque_id
    HAVING MAX(CASE WHEN tipo_movimiento = 'salida' THEN 1 ELSE 0 END) = 1
)
SELECT
    cama_inicio,
    COUNT(*) AS n,
    ROUND(AVG(horas_servicio), 4) AS media_horas,
    ROUND(MIN(horas_servicio), 4) AS min_horas,
    ROUND(MAX(horas_servicio), 4) AS max_horas
FROM tiempos_servicio
GROUP BY cama_inicio
ORDER BY n DESC;

-- -----------------------------------