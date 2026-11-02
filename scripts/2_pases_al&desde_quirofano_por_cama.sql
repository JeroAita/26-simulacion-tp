-------------------------------------------------------------------------------
-- Pases de cama hacia el quirófano (cama 241), por cama de origen
-- Requiere: datos_limpios
--
-- En un evento "Pase de cama", cama_id es la cama de DESTINO. Por lo tanto, la
-- cama de origen de un pase al quirófano es la cama del evento inmediatamente
-- anterior de la misma internación.
--
-- Devuelve un registro por cada cama regular (todas las camas distintas
-- de 241), incluso las que no tuvieron pases al quirófano (0).
-------------------------------------------------------------------------------
WITH ev AS (
    SELECT
        internacion_id,
        tipo_evento,
        cama_id,
        LAG(cama_id) OVER (
            PARTITION BY internacion_id
            ORDER BY fecha_hora_evento, evento_id
        ) AS cama_origen
    FROM datos_limpios
),
pases AS (
    SELECT cama_origen, COUNT(*) AS pases_a_quirofano
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id = 241
      AND cama_origen IS NOT NULL
    GROUP BY cama_origen
),
camas AS (
    SELECT DISTINCT cama_id
    FROM datos_limpios
    WHERE cama_id <> 241
)
SELECT
    c.cama_id,
    COALESCE(p.pases_a_quirofano, 0) AS pases_a_quirofano
FROM camas c
LEFT JOIN pases p ON p.cama_origen = c.cama_id
ORDER BY pases_a_quirofano DESC, c.cama_id;

-------------------------------------------------------------------------------
-- Pases de cama desde el quirófano (cama 241) hacia cada cama regular
-- Requiere: datos_limpios
--
-- En un evento "Pase de cama", cama_id es la cama de DESTINO. Un pase desde el
-- quirófano es un "Pase de cama" a una cama regular (cama_id <> 241) cuyo evento
-- inmediatamente anterior, dentro de la misma internación, es el pase hacia la
-- cama 241 (la cama del evento anterior es 241).
--
-- Devuelve un registro por cada cama regular (todas las camas distintas de 241),
-- incluso las que no recibieron pacientes desde el quirófano (0).
-------------------------------------------------------------------------------
WITH ev AS (
    SELECT
        internacion_id,
        tipo_evento,
        cama_id,
        LAG(tipo_evento) OVER w AS tipo_prev,
        LAG(cama_id)     OVER w AS cama_prev
    FROM datos_limpios
    WINDOW w AS (PARTITION BY internacion_id ORDER BY fecha_hora_evento, evento_id)
),
pases AS (
    SELECT cama_id AS cama_destino, COUNT(*) AS pases_desde_quirofano
    FROM ev
    WHERE tipo_evento = 'Pase de cama'
      AND cama_id <> 241
      AND tipo_prev = 'Pase de cama'
      AND cama_prev = 241
    GROUP BY cama_id
),
camas AS (
    SELECT DISTINCT cama_id
    FROM datos_limpios
    WHERE cama_id <> 241
)
SELECT
    c.cama_id,
    COALESCE(p.pases_desde_quirofano, 0) AS pases_desde_quirofano
FROM camas c
LEFT JOIN pases p ON p.cama_destino = c.cama_id
ORDER BY pases_desde_quirofano DESC, c.cama_id;