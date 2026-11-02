-------------------------------------------------------------------------------
-- PASO 2) Ingresos por cama y selección de las 10 camas con más ingresos
-- Se cuentan solo eventos "Ingreso" (coherente con el modelo: el paciente
-- permanece en la cama de su ingreso; los pases entre camas regulares se
-- ignoran). Con esta tabla (y con el total de eventos por cama) el top 10 es
-- el mismo. En caso de empate se desempata por cama_id.
-------------------------------------------------------------------------------
SELECT
    cama_id,
    COUNT(*) AS ingresos
FROM datos_limpios
WHERE tipo_evento = 'Ingreso'
GROUP BY cama_id
ORDER BY ingresos DESC, cama_id;

-- Tabla con las camas seleccionadas (se reutiliza en los pasos siguientes)
DROP TABLE IF EXISTS camas_seleccionadas;

CREATE TABLE camas_seleccionadas AS
SELECT
    cama_id,
    COUNT(*) AS ingresos
FROM datos_limpios
WHERE tipo_evento = 'Ingreso'
GROUP BY cama_id
ORDER BY ingresos DESC, cama_id
LIMIT 10;

SELECT * FROM camas_seleccionadas ORDER BY ingresos DESC, cama_id;


-------------------------------------------------------------------------------
-- PASO 3) Tasa de llegadas única, a partir de las 10 camas seleccionadas
-- Llegada = "Orden Internacion" de las internaciones cuyo Ingreso ocurre en
-- una de las camas seleccionadas.
-------------------------------------------------------------------------------
DROP VIEW IF EXISTS llegadas_seleccion;

CREATE VIEW llegadas_seleccion AS
SELECT o.evento_id, o.fecha_hora_evento
FROM datos_limpios o
JOIN datos_limpios i
  ON i.internacion_id = o.internacion_id
 AND i.tipo_evento = 'Ingreso'
WHERE o.tipo_evento = 'Orden Internacion'
  AND i.cama_id IN (SELECT cama_id FROM camas_seleccionadas);

-- 3a) Periodos entre llegadas (horas), para el análisis de distribución
SELECT
    evento_id,
    fecha_hora_evento,
    (julianday(fecha_hora_evento) -
     julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento))) * 24
        AS horas_desde_llegada_anterior
FROM llegadas_seleccion
ORDER BY horas_desde_llegada_anterior;
--ORDER BY fecha_hora_evento;

-- 3b) Resumen: n, media, desvío muestral y tasa de llegada
WITH x AS (
    SELECT
        (julianday(fecha_hora_evento) -
         julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento))) * 24 AS h
    FROM llegadas_seleccion
)
SELECT
    COUNT(h)                                                          AS n_intervalos,
    AVG(h)                                                            AS media_horas,
    SQRT((SUM(h * h) - COUNT(h) * AVG(h) * AVG(h)) / (COUNT(h) - 1))  AS desvio_horas,
    1.0 / AVG(h)                                                      AS lambda_pacientes_por_hora
FROM x
WHERE h IS NOT NULL;
