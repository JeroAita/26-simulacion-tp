-------------------------------------------------------------------------------
-- PASO 1) Tabla datos_limpios
--
-- Criterios:
--   a) Se eliminan los eventos con cama_id NULL (órdenes sin ingreso y
--      cancelaciones de internación).
--   b) "Alta Anulada" y "Reingreso" se disuelven como eventos: el paciente
--      nunca dejó la cama (no hay Egreso entre medio), así que el evento
--      anterior se enlaza directamente con el siguiente evento válido.
--   c) Se eliminan las internaciones completas cuyo Ingreso es directo a la
--      cama 241 (quirófano).
--
-- Se agrega la columna internacion_id (= evento_id del primer evento de la
-- cadena), útil para agrupar los eventos de una misma internación.
-- siguiente_evento_id se recalcula para que no quede apuntando a eventos
-- eliminados (ni a eventos fuera de la muestra: quedan en NULL).
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS datos_limpios;

CREATE TABLE datos_limpios AS
WITH RECURSIVE
-- Eventos que se conservan como nodos de la cadena
validos AS (
    SELECT *
    FROM datos_crudos
    WHERE cama_id IS NOT NULL
      AND tipo_evento NOT IN ('Alta Anulada', 'Reingreso')
),

-- Para cada evento válido, avanza por siguiente_evento_id saltando los
-- eventos disueltos hasta encontrar el próximo evento válido (o el final).
camino(evento_id, cursor_id) AS (
    SELECT evento_id, siguiente_evento_id FROM validos
    UNION ALL
    SELECT c.evento_id, d.siguiente_evento_id
    FROM camino c
    JOIN datos_crudos d ON d.evento_id = c.cursor_id
    WHERE c.cursor_id NOT IN (SELECT evento_id FROM validos)
),

-- Enlaces definitivos evento -> siguiente evento válido
enlaces AS (
    SELECT evento_id, cursor_id AS sig
    FROM camino
    WHERE cursor_id IN (SELECT evento_id FROM validos)
),

-- Primer evento de cada internación (sin predecesor válido)
raices AS (
    SELECT evento_id
    FROM validos
    WHERE evento_id NOT IN (SELECT sig FROM enlaces)
),

-- Asigna a cada evento el id de su internación
cadena(evento_id, internacion_id) AS (
    SELECT evento_id, evento_id FROM raices
    UNION ALL
    SELECT e.sig, c.internacion_id
    FROM cadena c
    JOIN enlaces e ON e.evento_id = c.evento_id
),

-- Internaciones con ingreso directo al quirófano
excluidas AS (
    SELECT DISTINCT c.internacion_id
    FROM cadena c
    JOIN validos v ON v.evento_id = c.evento_id
    WHERE v.cama_id = 241
      AND v.tipo_evento IN ('Orden Internacion', 'Ingreso')
)

SELECT
    v.evento_id,
    v.tipo_evento,
    n.sig AS siguiente_evento_id,
    v.persona_id,
    v.cama_id,
    v.fecha_hora_evento,
    c.internacion_id
FROM validos v
JOIN cadena c ON c.evento_id = v.evento_id
LEFT JOIN enlaces n ON n.evento_id = v.evento_id
WHERE c.internacion_id NOT IN (SELECT internacion_id FROM excluidas);

CREATE INDEX idx_dl_evento ON datos_limpios (evento_id);
CREATE INDEX idx_dl_internacion ON datos_limpios (internacion_id);
CREATE INDEX idx_dl_cama_tipo ON datos_limpios (cama_id, tipo_evento);


-------------------------------------------------------------------------------
-- Verificaciones (opcionales)
-------------------------------------------------------------------------------
-- Eventos por tipo (no debe haber Alta Anulada, Reingreso ni Cancelacion)
SELECT tipo_evento, COUNT(*) AS n FROM datos_limpios GROUP BY tipo_evento;

-- Enlaces rotos: debe devolver 0
SELECT COUNT(*) AS enlaces_rotos
FROM datos_limpios
WHERE siguiente_evento_id IS NOT NULL
  AND siguiente_evento_id NOT IN (SELECT evento_id FROM datos_limpios);

-- Cantidad de camas: debe devolver 75 (74 + quirófano)
SELECT COUNT(DISTINCT cama_id) AS camas FROM datos_limpios;