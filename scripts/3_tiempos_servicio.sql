-------------------------------------------------------------------------------
-- TIEMPOS DE SERVICIO
-- Requiere: datos_limpios y camas_seleccionadas
--
-- Una fila por "estadía en cama regular" de las internaciones que ingresan por
-- una de las camas seleccionadas:
--   etapa 1  : desde el Ingreso hasta el primer pase al quirófano (241) o el
--              Egreso, lo que ocurra primero.
--   etapa >=2: desde que el paciente vuelve del quirófano a una cama regular
--              hasta el siguiente pase al quirófano o el Egreso.
-- Los pases entre camas regulares se ignoran (el paciente "sigue" en la misma
-- cama del modelo hasta salir al quirófano o egresar).
--
-- motivo_fin = 'censurado' cuando la muestra termina antes del fin del servicio
-- (horas queda en NULL): estas filas no deben usarse para ajustar distribuciones.
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS servicios;

CREATE TABLE servicios AS
WITH ev AS (
    SELECT
        internacion_id, evento_id, tipo_evento, cama_id, fecha_hora_evento,
        LAG(tipo_evento) OVER w AS tipo_prev,
        LAG(cama_id)     OVER w AS cama_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento)
),

-- Eventos que abren o cierran una estadía en cama regular
relevantes AS (
    SELECT
        internacion_id, cama_id, fecha_hora_evento,
        CASE
            WHEN tipo_evento = 'Ingreso'
                THEN 'inicio'
            WHEN tipo_evento = 'Pase de cama' AND cama_id <> 241
                 AND tipo_prev = 'Pase de cama' AND cama_prev = 241
                THEN 'inicio'                      -- vuelta del quirófano
            WHEN tipo_evento = 'Pase de cama' AND cama_id = 241
                THEN 'fin_quirofano'
            WHEN tipo_evento = 'Egreso'
                THEN 'fin_egreso'
        END AS rol
    FROM ev
),

secuencia AS (
    SELECT
        internacion_id, cama_id, fecha_hora_evento, rol,
        LEAD(rol)               OVER w AS rol_sig,
        LEAD(fecha_hora_evento) OVER w AS t_sig
    FROM relevantes
    WHERE rol IS NOT NULL
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento)
)

SELECT
    internacion_id,
    ROW_NUMBER() OVER w AS etapa,
    FIRST_VALUE(cama_id) OVER w AS cama_ingreso,
    cama_id AS cama_inicio,
    fecha_hora_evento AS t_inicio,
    CASE WHEN rol_sig IN ('fin_quirofano', 'fin_egreso') THEN t_sig END AS t_fin,
    CASE rol_sig
        WHEN 'fin_quirofano' THEN 'quirofano'
        WHEN 'fin_egreso'    THEN 'egreso'
        ELSE 'censurado'
    END AS motivo_fin,
    CASE WHEN rol_sig IN ('fin_quirofano', 'fin_egreso')
         THEN (julianday(t_sig) - julianday(fecha_hora_evento)) * 24
    END AS horas
FROM secuencia
WHERE rol = 'inicio'
  AND internacion_id IN (
        SELECT internacion_id
        FROM datos_limpios
        WHERE tipo_evento = 'Ingreso'
          AND cama_id IN (SELECT cama_id FROM camas_seleccionadas)
  )
WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento);

CREATE INDEX idx_serv_etapa ON servicios (etapa, cama_ingreso);


-------------------------------------------------------------------------------
-- Verificaciones
-------------------------------------------------------------------------------
-- Cantidad de servicios por etapa y motivo de fin
SELECT
    CASE WHEN etapa = 1 THEN '1 (ingreso)' ELSE '2+ (post-quirófano)' END AS etapa,
    motivo_fin,
    COUNT(*) AS n
FROM servicios
GROUP BY 1, 2
ORDER BY 1, 2;

-- Duraciones no positivas: debe devolver 0
SELECT COUNT(*) AS duraciones_no_positivas FROM servicios WHERE horas <= 0;


-------------------------------------------------------------------------------
-- Descriptiva de la etapa 1 por cama de ingreso (solo servicios completos)
-------------------------------------------------------------------------------
SELECT
    cama_ingreso,
    COUNT(*)                                                           AS n,
    AVG(horas)                                                         AS media_h,
    SQRT((SUM(horas * horas) - COUNT(*) * AVG(horas) * AVG(horas))
         / (COUNT(*) - 1))                                             AS desvio_h,
    MIN(horas)                                                         AS min_h,
    MAX(horas)                                                         AS max_h,
    SUM(motivo_fin = 'quirofano')                                      AS terminan_en_quirofano
FROM servicios
WHERE etapa = 1 AND horas IS NOT NULL
GROUP BY cama_ingreso
ORDER BY n DESC;

-- Descriptiva agregada (las 10 camas juntas)
SELECT
    COUNT(*)                                                           AS n,
    AVG(horas)                                                         AS media_h,
    SQRT((SUM(horas * horas) - COUNT(*) * AVG(horas) * AVG(horas))
         / (COUNT(*) - 1))                                             AS desvio_h,
    MIN(horas)                                                         AS min_h,
    MAX(horas)                                                         AS max_h
FROM servicios
WHERE etapa = 1 AND horas IS NOT NULL;
