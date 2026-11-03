-------------------------------------------------------------------------------
-- SUBSISTEMA DE ESTUDIO: camas 223, 225, 226, 227 y 228 (+ quirófano en serie)
-- Requiere: datos_limpios (ver 1_limpieza_de_datos.sql)
--
-- Convención de la base: en un "Pase de cama", cama_id es la cama de DESTINO.
-- La cama de origen es la cama del movimiento inmediatamente anterior de la
-- misma internación.
--
-- Este script:
--   A) fija el subsistema y arma la tabla de movimientos de cada internación;
--   B) justifica la elección (relación con el quirófano, utilización);
--   C) clasifica las llegadas y salidas del subsistema según las definiciones
--      del modelo, y las visitas al quirófano;
--   D) mide la ocupación del subsistema.
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
-- A) Subsistema y movimientos
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS subsistema_camas;
CREATE TABLE subsistema_camas (cama_id INTEGER PRIMARY KEY);
INSERT INTO subsistema_camas VALUES (223), (225), (226), (227), (228);

-- Movimientos que ubican al paciente en una cama (Ingreso, Pase de cama, Egreso),
-- con la cama anterior, la anterior a esa, y el movimiento siguiente.
-- Se ignoran las altas médicas y las órdenes de internación.
DROP VIEW IF EXISTS movimientos;
CREATE VIEW movimientos AS
SELECT
    internacion_id,
    evento_id,
    tipo_evento,
    cama_id,
    fecha_hora_evento                     AS t,
    LAG(cama_id, 1)  OVER w               AS cama_prev,
    LAG(cama_id, 2)  OVER w               AS cama_prev2,
    LEAD(tipo_evento) OVER w              AS tipo_next,
    LEAD(cama_id)     OVER w              AS cama_next,
    LEAD(fecha_hora_evento) OVER w        AS t_next
FROM datos_limpios
WHERE tipo_evento IN ('Ingreso', 'Pase de cama', 'Egreso')
WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id);

-- Horizonte de la muestra (horas)
SELECT (julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24
           AS horas_muestra
FROM datos_limpios;

-------------------------------------------------------------------------------
-- B) Justificación de la elección del subsistema
-------------------------------------------------------------------------------
-- B1) Pases hacia el quirófano y retornos desde el quirófano, por cama regular
--     (ranking de las camas con mayor relación con el quirófano)
DROP TABLE IF EXISTS relacion_quirofano;
CREATE TABLE relacion_quirofano AS
WITH a_q AS (
    SELECT cama_prev AS cama_id, COUNT(*) AS pases_a_quirofano
    FROM movimientos
    WHERE tipo_evento = 'Pase de cama' AND cama_id = 241 AND cama_prev IS NOT NULL
    GROUP BY cama_prev
),
d_q AS (
    SELECT cama_id, COUNT(*) AS pases_desde_quirofano
    FROM movimientos
    WHERE tipo_evento = 'Pase de cama' AND cama_id <> 241 AND cama_prev = 241
    GROUP BY cama_id
),
camas AS (SELECT DISTINCT cama_id FROM datos_limpios WHERE cama_id <> 241)
SELECT c.cama_id,
       COALESCE(a.pases_a_quirofano, 0)    AS pases_a_quirofano,
       COALESCE(d.pases_desde_quirofano, 0) AS pases_desde_quirofano
FROM camas c
LEFT JOIN a_q a ON a.cama_id = c.cama_id
LEFT JOIN d_q d ON d.cama_id = c.cama_id;

SELECT * FROM relacion_quirofano
ORDER BY pases_a_quirofano DESC, cama_id
LIMIT 12;

-- B2) Participación del subsistema en el total de pases con quirófano
SELECT
    SUM(CASE WHEN cama_id IN (SELECT cama_id FROM subsistema_camas)
             THEN pases_a_quirofano END)                  AS pases_a_quirofano_subsistema,
    SUM(pases_a_quirofano)                                AS pases_a_quirofano_total,
    SUM(CASE WHEN cama_id IN (SELECT cama_id FROM subsistema_camas)
             THEN pases_desde_quirofano END)              AS pases_desde_quirofano_subsistema,
    SUM(pases_desde_quirofano)                            AS pases_desde_quirofano_total
FROM relacion_quirofano;

-- B3) Estadías en cama (tramos reales: del movimiento hasta el siguiente), de
--     todas las camas regulares; sirve para medir la utilización de cada cama.
--     Los tramos sin fin registrado se cierran al final de la muestra.
DROP TABLE IF EXISTS estadias_cama;
CREATE TABLE estadias_cama AS
SELECT
    internacion_id, cama_id, t AS t_inicio,
    COALESCE(t_next, (SELECT MAX(fecha_hora_evento) FROM datos_limpios)) AS t_fin
FROM movimientos
WHERE tipo_evento IN ('Ingreso', 'Pase de cama') AND cama_id <> 241;

-- Utilización por cama (horas ocupada / horas de la muestra)
DROP TABLE IF EXISTS utilizacion_cama;
CREATE TABLE utilizacion_cama AS
SELECT
    cama_id,
    SUM((julianday(t_fin) - julianday(t_inicio)) * 24) /
    (SELECT (julianday(MAX(fecha_hora_evento)) - julianday(MIN(fecha_hora_evento))) * 24
     FROM datos_limpios)                                       AS utilizacion
FROM estadias_cama
GROUP BY cama_id;

-- Utilización media: hospital completo (74 camas) vs. subsistema
SELECT
    (SELECT COUNT(*) FROM utilizacion_cama)                               AS camas_con_uso,
    (SELECT SUM(utilizacion) / 74.0 FROM utilizacion_cama)                AS utilizacion_hospital_74_camas,
    (SELECT AVG(utilizacion) FROM utilizacion_cama
     WHERE cama_id IN (SELECT cama_id FROM subsistema_camas))             AS utilizacion_subsistema;

-- Utilización de cada cama del subsistema
SELECT * FROM utilizacion_cama
WHERE cama_id IN (SELECT cama_id FROM subsistema_camas)
ORDER BY cama_id;

-- Máximo de pacientes simultáneos por cama del subsistema (debe ser 1: la cama
-- se comporta como un servidor)
WITH mov AS (
    SELECT cama_id, t_inicio AS t,  1 AS d FROM estadias_cama
    UNION ALL
    SELECT cama_id, t_fin,         -1      FROM estadias_cama
),
acum AS (
    SELECT cama_id,
           SUM(d) OVER (PARTITION BY cama_id ORDER BY t, d ROWS UNBOUNDED PRECEDING) AS ocupados
    FROM mov
)
SELECT cama_id, MAX(ocupados) AS max_simultaneos
FROM acum
WHERE cama_id IN (SELECT cama_id FROM subsistema_camas)
GROUP BY cama_id;

-------------------------------------------------------------------------------
-- C) Definiciones del modelo aplicadas a los datos
-------------------------------------------------------------------------------
-- C1) Estadías en una cama del subsistema, con su forma de entrada y de salida.
--
--   ENTRADA (cómo llega el paciente a la cama):
--     ingreso                  : evento Ingreso a una cama del subsistema.
--     pase_otra_cama           : pase desde una cama que no es del subsistema ni la 241.
--     desde_quirofano_externo  : pase desde la 241 de un paciente que NO venía del subsistema.
--     retorno_quirofano        : pase desde la 241 de un paciente que SÍ salió del subsistema
--                                (no es una llegada: el cliente nunca dejó el sistema).
--     pase_interno             : pase desde otra cama del subsistema (continúa el mismo servicio).
--
--   SALIDA (cómo termina la estadía en la cama):
--     egreso            : sale del sistema.
--     pase_otra_cama    : pase a una cama que no es del subsistema ni la 241: sale del sistema.
--     a_quirofano       : pase a la 241: el servidor se libera y el paciente pasa al quirófano.
--     pase_interno      : pase a otra cama del subsistema (continúa el mismo servicio).
--     censurada         : la muestra termina antes del fin.
DROP TABLE IF EXISTS estadias_subsistema;
CREATE TABLE estadias_subsistema AS
SELECT
    internacion_id,
    cama_id,
    t      AS t_inicio,
    t_next AS t_fin,
    CASE
        WHEN tipo_evento = 'Ingreso'                                      THEN 'ingreso'
        WHEN cama_prev IN (SELECT cama_id FROM subsistema_camas)          THEN 'pase_interno'
        WHEN cama_prev = 241
             AND cama_prev2 IN (SELECT cama_id FROM subsistema_camas)     THEN 'retorno_quirofano'
        WHEN cama_prev = 241                                              THEN 'desde_quirofano_externo'
        ELSE                                                                   'pase_otra_cama'
    END AS entrada,
    CASE
        WHEN tipo_next IS NULL                                            THEN 'censurada'
        WHEN tipo_next = 'Egreso'                                         THEN 'egreso'
        WHEN cama_next IN (SELECT cama_id FROM subsistema_camas)          THEN 'pase_interno'
        WHEN cama_next = 241                                              THEN 'a_quirofano'
        ELSE                                                                   'pase_otra_cama'
    END AS salida,
    CASE WHEN t_next IS NOT NULL
         THEN (julianday(t_next) - julianday(t)) * 24 END AS horas
FROM movimientos
WHERE tipo_evento IN ('Ingreso', 'Pase de cama')
  AND cama_id IN (SELECT cama_id FROM subsistema_camas);

-- C2) Formas de entrada (llegadas externas = ingreso + pase_otra_cama + desde_quirofano_externo)
SELECT entrada, COUNT(*) AS n
FROM estadias_subsistema
GROUP BY entrada
ORDER BY n DESC;

-- C3) Formas de salida
SELECT salida, COUNT(*) AS n
FROM estadias_subsistema
GROUP BY salida
ORDER BY n DESC;

-- C4) Llegadas externas (total) y llegadas con orden de internación registrada
SELECT
    COUNT(*) AS llegadas_externas,
    SUM(entrada = 'ingreso') AS ingresos,
    SUM(entrada = 'ingreso' AND EXISTS (
        SELECT 1 FROM datos_limpios o
        WHERE o.internacion_id = e.internacion_id
          AND o.tipo_evento = 'Orden Internacion')) AS ingresos_con_orden
FROM estadias_subsistema e
WHERE entrada IN ('ingreso', 'pase_otra_cama', 'desde_quirofano_externo');

-- C5) Visitas al quirófano originadas en el subsistema y cómo terminan.
--     Una visita empieza con el pase 241 desde una cama del subsistema y termina
--     en el movimiento siguiente (retorno, otra cama o egreso).
DROP TABLE IF EXISTS visitas_quirofano_subsistema;
CREATE TABLE visitas_quirofano_subsistema AS
SELECT
    internacion_id,
    t      AS t_llegada,
    t_next AS t_salida,
    CASE
        WHEN tipo_next IS NULL                                   THEN 'censurada'
        WHEN tipo_next = 'Egreso'                                THEN 'egreso'
        WHEN cama_next IN (SELECT cama_id FROM subsistema_camas) THEN 'retorno_al_subsistema'
        ELSE                                                          'pase_otra_cama'
    END AS salida,
    CASE WHEN t_next IS NOT NULL
         THEN (julianday(t_next) - julianday(t)) * 24 END AS horas
FROM movimientos
WHERE tipo_evento = 'Pase de cama'
  AND cama_id = 241
  AND cama_prev IN (SELECT cama_id FROM subsistema_camas);

SELECT salida, COUNT(*) AS n FROM visitas_quirofano_subsistema GROUP BY salida;

SELECT COUNT(horas) AS n, AVG(horas) AS media_h, MIN(horas) AS min_h, MAX(horas) AS max_h,
       SUM(horas < 5.0 / 60) AS menores_a_5_min
FROM visitas_quirofano_subsistema;

-- C6) Durante un viaje al quirófano, ¿otro paciente ocupó la cama liberada?
SELECT COUNT(*) AS viajes,
       SUM(EXISTS (
           SELECT 1 FROM estadias_cama c
           WHERE c.cama_id = prev.cama_prev
             AND c.internacion_id <> v.internacion_id
             AND c.t_inicio > v.t_llegada
             AND c.t_inicio < COALESCE(v.t_salida, '9999'))) AS viajes_con_otro_paciente_en_la_cama
FROM visitas_quirofano_subsistema v
JOIN movimientos prev
  ON prev.internacion_id = v.internacion_id
 AND prev.t = v.t_llegada
 AND prev.cama_id = 241;

-------------------------------------------------------------------------------
-- D) Ocupación del subsistema (cantidad de camas ocupadas en el tiempo)
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS ocupacion_subsistema;
CREATE TABLE ocupacion_subsistema AS
WITH mov AS (
    SELECT t_inicio AS t,  1 AS d FROM estadias_cama
    WHERE cama_id IN (SELECT cama_id FROM subsistema_camas)
    UNION ALL
    SELECT t_fin,         -1      FROM estadias_cama
    WHERE cama_id IN (SELECT cama_id FROM subsistema_camas)
),
acum AS (
    SELECT t, SUM(d) OVER (ORDER BY t, d ROWS UNBOUNDED PRECEDING) AS ocupadas
    FROM mov
)
SELECT t, ocupadas, LEAD(t) OVER (ORDER BY t) AS t_sig FROM acum;

-- Porcentaje de tiempo con 0, 1, ..., 5 camas ocupadas: toda la muestra y
-- desde el día 29 (las primeras semanas son el transitorio: la muestra empieza
-- sin pacientes previos).
SELECT
    ocupadas,
    SUM(julianday(t_sig) - julianday(t)) /
        (SELECT SUM(julianday(t_sig) - julianday(t)) FROM ocupacion_subsistema WHERE t_sig IS NOT NULL)
        AS fraccion_tiempo_toda_la_muestra,
    SUM(CASE WHEN t >= datetime((SELECT MIN(fecha_hora_evento) FROM datos_limpios), '+28 days')
             THEN julianday(t_sig) - julianday(t) END) /
        (SELECT SUM(julianday(t_sig) - julianday(t)) FROM ocupacion_subsistema
         WHERE t_sig IS NOT NULL
           AND t >= datetime((SELECT MIN(fecha_hora_evento) FROM datos_limpios), '+28 days'))
        AS fraccion_tiempo_desde_dia_29
FROM ocupacion_subsistema
WHERE t_sig IS NOT NULL
GROUP BY ocupadas
ORDER BY ocupadas;

-- Utilización semanal del subsistema (muestra el periodo transitorio)
SELECT
    strftime('%Y-%W', t) AS semana,
    SUM(ocupadas * (julianday(t_sig) - julianday(t))) / SUM(julianday(t_sig) - julianday(t)) / 5.0
        AS utilizacion
FROM ocupacion_subsistema
WHERE t_sig IS NOT NULL
GROUP BY semana
ORDER BY semana;