-- Script SQL 3: llegadas
-- Identifica los eventos que constituyen una "llegada" al sub-sistema
-- seleccionado (camas 223, 225, 226, 227, 228) y calcula el periodo entre
-- llegadas sucesivas (en horas).
--
-- Una llegada al sub-sistema ocurre cuando:
--   a) Un evento "Ingreso" asigna al paciente a una cama del sub-sistema.
--   b) Un evento "Pase de cama" traslada al paciente desde una cama externa
--      (cama distinta a 223, 225, 226, 227, 228) hacia una cama del
--      sub-sistema. Esto incluye pases desde el quirófano (241) y desde
--      otras camas regulares.
-- Los pases de cama entre camas del sub-sistema NO se consideran nuevas
-- llegadas, ya que no modifican la cantidad de clientes en el sistema.
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
llegadas AS (
    -- a) Ingreso directo a una cama del sub-sistema
    SELECT fecha_hora_evento, evento_id, 'Ingreso' AS tipo_llegada
    FROM ev
    WHERE tipo_evento = 'Ingreso'
      AND cama_id IN (223, 225, 226, 227, 228)

    UNION ALL

    -- b) Pase de cama desde una cama externa hacia el sub-sistema
    SELECT fecha_hora_evento, evento_id, 'Pase desde externa' AS tipo_llegada
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id IN (223, 225, 226, 227, 228)
      AND cama_prev IS NOT NULL
      AND cama_prev NOT IN (223, 225, 226, 227, 228)
)
SELECT
    fecha_hora_evento,
    evento_id,
    tipo_llegada,
    LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id) AS llegada_anterior,
    ROUND(
        (julianday(fecha_hora_evento) - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id))) * 24,
        4
    ) AS horas_entre_llegadas
FROM llegadas
ORDER BY fecha_hora_evento, evento_id;

-- Cantidad total de llegadas y desglose por tipo
SELECT tipo_llegada, COUNT(*) AS n
FROM llegadas
GROUP BY tipo_llegada;

-- Estadísticos descriptivos del periodo entre llegadas (para elegir distribución)
SELECT
    COUNT(*) AS n_observaciones,
    ROUND(MIN(horas_entre_llegadas), 4) AS minimo,
    ROUND(MAX(horas_entre_llegadas), 4) AS maximo,
    ROUND(AVG(horas_entre_llegadas), 4) AS media,
    -- Varianza muestral para luego estimar lambda
    ROUND(AVG(horas_entre_llegadas * horas_entre_llegadas) - AVG(horas_entre_llegadas) * AVG(horas_entre_llegadas), 6) AS varianza
FROM (
    SELECT
        (julianday(fecha_hora_evento) - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id))) * 24 AS horas_entre_llegadas
    FROM llegadas
);