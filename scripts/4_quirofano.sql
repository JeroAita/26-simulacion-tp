-------------------------------------------------------------------------------
-- QUIRÓFANO (cama 241)
-- Requiere: datos_limpios, camas_seleccionadas y servicios
--           (ver limpieza_y_llegadas.sql y tiempos_servicio.sql)
--
-- Una fila por visita al quirófano de las internaciones que ingresan por una
-- de las camas seleccionadas.
--   t_llegada : evento "Pase de cama" hacia la cama 241.
--   t_salida  : primer evento posterior que sea un pase a otra cama o el Egreso
--               (las altas médicas se ignoran, igual que en las camas).
--   horas     : permanencia en el quirófano; NULL si la muestra termina antes.
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS servicios_quirofano;

CREATE TABLE servicios_quirofano AS
WITH visitas AS (
    SELECT
        e.internacion_id,
        e.fecha_hora_evento AS t_llegada,
        (SELECT MIN(s.fecha_hora_evento)
         FROM datos_limpios s
         WHERE s.internacion_id = e.internacion_id
           AND s.fecha_hora_evento > e.fecha_hora_evento
           AND ((s.tipo_evento = 'Pase de cama' AND s.cama_id <> 241)
                OR s.tipo_evento = 'Egreso')) AS t_salida
    FROM datos_limpios e
    WHERE e.tipo_evento = 'Pase de cama'
      AND e.cama_id = 241
      AND e.internacion_id IN (SELECT internacion_id FROM servicios)
)
SELECT
    v.internacion_id,
    ROW_NUMBER() OVER (PARTITION BY v.internacion_id ORDER BY v.t_llegada) AS visita,
    v.t_llegada,
    v.t_salida,
    CASE
        WHEN v.t_salida IS NULL THEN 'censurado'
        WHEN (SELECT s.tipo_evento FROM datos_limpios s
              WHERE s.internacion_id = v.internacion_id
                AND s.fecha_hora_evento = v.t_salida) = 'Egreso' THEN 'egreso'
        ELSE 'vuelta_a_cama'
    END AS motivo_salida,
    CASE WHEN v.t_salida IS NOT NULL
         THEN (julianday(v.t_salida) - julianday(v.t_llegada)) * 24
    END AS horas
FROM visitas v;


-------------------------------------------------------------------------------
-- Verificaciones
-------------------------------------------------------------------------------
SELECT motivo_salida, COUNT(*) AS n FROM servicios_quirofano GROUP BY motivo_salida;


-------------------------------------------------------------------------------
-- 1) Periodo entre llegadas al quirófano (horas)
-------------------------------------------------------------------------------
SELECT
    internacion_id,
    t_llegada,
    (julianday(t_llegada) -
     julianday(LAG(t_llegada) OVER (ORDER BY t_llegada))) * 24
        AS horas_desde_llegada_anterior
FROM servicios_quirofano
ORDER BY t_llegada;


-------------------------------------------------------------------------------
-- 2) Tiempo de servicio en el quirófano: resumen
-------------------------------------------------------------------------------
SELECT
    COUNT(horas)                                                       AS n,
    AVG(horas)                                                         AS media_h,
    SQRT((SUM(horas * horas) - COUNT(horas) * AVG(horas) * AVG(horas))
         / (COUNT(horas) - 1))                                         AS desvio_h,
    MIN(horas)                                                         AS min_h,
    MAX(horas)                                                         AS max_h
FROM servicios_quirofano
WHERE horas IS NOT NULL;


-------------------------------------------------------------------------------
-- 3) Probabilidad de derivación al quirófano al terminar un servicio en cama
-------------------------------------------------------------------------------
SELECT
    SUM(motivo_fin = 'quirofano') AS terminan_en_quirofano,
    COUNT(*)                      AS servicios_completos
FROM servicios
WHERE horas IS NOT NULL;
