-- Script SQL 6: ruteo, llegadas exógenas y ocupación observada
-- Insumos para el modelo de simulación del sub-sistema (camas 223, 225, 226,
-- 227, 228) y el quirófano (241).
--
--   a) Tabla bloques_servicio: una fila por estancia continua en el sub-sistema,
--      con su origen (cómo llegó), su destino (cómo salió) y su duración.
--   b) Matriz de ruteo: P(destino | origen) y P(destino) global.
--   c) Llegadas exógenas: llegadas al sub-sistema SIN contar los retornos del
--      quirófano de pacientes que salieron del sub-sistema hacia el quirófano
--      (esos retornos los genera el propio modelo: lazo de realimentación).
--   d) Ocupación observada de las 5 camas (valor de validación).
--
-- Requiere: datos_limpios

-------------------------------------------------------------------------------
-- a) bloques_servicio
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS bloques_servicio;

CREATE TABLE bloques_servicio AS
WITH ev AS (
    SELECT
        evento_id, tipo_evento, cama_id, fecha_hora_evento, internacion_id,
        LAG(cama_id) OVER w AS cama_prev
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
)
SELECT
    internacion_id,
    bloque_id,
    MIN(CASE WHEN tipo_movimiento = 'entrada' THEN cama_id END) AS cama_inicio,
    -- Origen: cómo llegó el paciente al sub-sistema
    MIN(CASE WHEN tipo_movimiento = 'entrada' THEN
            CASE WHEN tipo_evento = 'Ingreso' THEN 'ingreso'
                 WHEN cama_prev = 241         THEN 'quirofano'
                 ELSE 'externa' END
        END) AS origen,
    -- Destino: cómo salió
    MIN(CASE WHEN tipo_movimiento = 'salida' THEN
            CASE WHEN tipo_evento = 'Egreso' THEN 'egreso'
                 WHEN cama_id = 241          THEN 'quirofano'
                 ELSE 'externa' END
        END) AS destino,
    MIN(fecha_hora_evento) AS inicio_servicio,
    MAX(fecha_hora_evento) AS fin_servicio,
    ROUND((julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24, 4) AS horas_servicio
FROM bloques
GROUP BY internacion_id, bloque_id
HAVING MAX(CASE WHEN tipo_movimiento = 'salida' THEN 1 ELSE 0 END) = 1;

-------------------------------------------------------------------------------
-- b) Matriz de ruteo
-------------------------------------------------------------------------------
-- Destino global (debe sumar n = 350)
SELECT destino, COUNT(*) AS n,
       ROUND(1.0 * COUNT(*) / (SELECT COUNT(*) FROM bloques_servicio), 4) AS proporcion,
       ROUND(AVG(horas_servicio), 2) AS media_horas
FROM bloques_servicio
GROUP BY destino
ORDER BY n DESC;

-- Destino según origen
SELECT origen, destino, COUNT(*) AS n,
       ROUND(1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY origen), 4) AS proporcion
FROM bloques_servicio
GROUP BY origen, destino
ORDER BY origen, destino;

-------------------------------------------------------------------------------
-- c) Llegadas exógenas al sub-sistema
-------------------------------------------------------------------------------
-- Una llegada es endógena si es un retorno desde el quirófano de un paciente
-- cuyo evento anterior al quirófano fue una cama del sub-sistema.
WITH ev AS (
    SELECT
        evento_id, tipo_evento, cama_id, fecha_hora_evento, internacion_id,
        LAG(cama_id)    OVER w AS cama_prev,
        LAG(cama_id, 2) OVER w AS cama_prev2
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
llegadas AS (
    SELECT
        fecha_hora_evento, evento_id,
        CASE WHEN cama_prev = 241 AND cama_prev2 IN (223, 225, 226, 227, 228)
             THEN 1 ELSE 0 END AS endogena
    FROM ev
    WHERE (tipo_evento = 'Ingreso' AND cama_id IN (223, 225, 226, 227, 228))
       OR (tipo_evento = 'Pase de cama'
           AND cama_id IN (223, 225, 226, 227, 228)
           AND cama_prev IS NOT NULL
           AND cama_prev NOT IN (223, 225, 226, 227, 228))
),
exogenas AS (
    SELECT
        fecha_hora_evento,
        evento_id,
        ROUND((julianday(fecha_hora_evento)
             - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id))) * 24, 4)
            AS horas_entre_llegadas
    FROM llegadas
    WHERE endogena = 0
)
SELECT fecha_hora_evento, evento_id, horas_entre_llegadas
FROM exogenas
ORDER BY fecha_hora_evento, evento_id;

-- Estadísticos de las llegadas exógenas (reemplazar la consulta anterior por
-- este SELECT para obtener n, media, desvío y coeficiente de variación)
-- (misma CTE 'exogenas'; se repite para poder ejecutarlo de forma independiente)
WITH ev AS (
    SELECT
        evento_id, tipo_evento, cama_id, fecha_hora_evento, internacion_id,
        LAG(cama_id)    OVER w AS cama_prev,
        LAG(cama_id, 2) OVER w AS cama_prev2
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
llegadas AS (
    SELECT
        fecha_hora_evento, evento_id,
        CASE WHEN cama_prev = 241 AND cama_prev2 IN (223, 225, 226, 227, 228)
             THEN 1 ELSE 0 END AS endogena
    FROM ev
    WHERE (tipo_evento = 'Ingreso' AND cama_id IN (223, 225, 226, 227, 228))
       OR (tipo_evento = 'Pase de cama'
           AND cama_id IN (223, 225, 226, 227, 228)
           AND cama_prev IS NOT NULL
           AND cama_prev NOT IN (223, 225, 226, 227, 228))
),
periodos AS (
    SELECT
        (julianday(fecha_hora_evento)
       - julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento, evento_id))) * 24
            AS h
    FROM llegadas
    WHERE endogena = 0
)
SELECT
    COUNT(h) AS n_periodos,
    ROUND(AVG(h), 4) AS media,
    ROUND(SQRT(AVG(h * h) - AVG(h) * AVG(h)) * SQRT(1.0 * COUNT(h) / (COUNT(h) - 1)), 4) AS desvio_muestral
FROM periodos;

-- Cantidad de llegadas por tipo (exógenas vs. endógenas); total esperado: 355
SELECT endogena, COUNT(*) AS n FROM (
    WITH ev AS (
        SELECT tipo_evento, cama_id,
               LAG(cama_id)    OVER w AS cama_prev,
               LAG(cama_id, 2) OVER w AS cama_prev2
        FROM datos_limpios
        WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
    )
    SELECT CASE WHEN cama_prev = 241 AND cama_prev2 IN (223, 225, 226, 227, 228)
                THEN 1 ELSE 0 END AS endogena
    FROM ev
    WHERE (tipo_evento = 'Ingreso' AND cama_id IN (223, 225, 226, 227, 228))
       OR (tipo_evento = 'Pase de cama'
           AND cama_id IN (223, 225, 226, 227, 228)
           AND cama_prev IS NOT NULL
           AND cama_prev NOT IN (223, 225, 226, 227, 228))
) GROUP BY endogena;

-------------------------------------------------------------------------------
-- d) Ocupación observada (valor de referencia para la validación)
-------------------------------------------------------------------------------
-- Camas ocupadas en promedio = (horas-cama de servicios completos) / ventana.
-- Subestima levemente: se ignoran los servicios incompletos en los bordes.
SELECT
    ROUND((julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24, 1) AS ventana_horas,
    ROUND((SELECT SUM(horas_servicio) FROM bloques_servicio), 1) AS horas_cama,
    ROUND((SELECT SUM(horas_servicio) FROM bloques_servicio)
          / ((julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24), 3) AS camas_ocupadas_prom,
    ROUND((SELECT SUM(horas_servicio) FROM bloques_servicio)
          / ((julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24) / 5, 3) AS utilizacion_observada
FROM datos_limpios;

-------------------------------------------------------------------------------
-- Exportación de las muestras empíricas para MATLAB (desde el cliente sqlite3):
--   .mode csv
--   .headers on
--   .output servicio.csv
--   SELECT horas_servicio, origen, destino FROM bloques_servicio;
--   .output stdout
-- (análogo para las llegadas exógenas y los tiempos de servicio del quirófano)
-------------------------------------------------------------------------------
