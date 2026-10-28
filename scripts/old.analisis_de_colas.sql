-- =====================================================================
-- ANALISIS DE COLAS - INTERNACION HOSPITALARIA
-- Tabla asumida: eventos(evento_id, tipo_evento, siguiente_evento_id,
--                         persona_id, cama_id, fecha_hora_evento)
--
-- Nota: usa sintaxis de PostgreSQL (EXTRACT(EPOCH FROM ...)).
-- Si usás SQLite: reemplazar por
--   (julianday(fecha_siguiente) - julianday(fecha_hora_evento)) * 24
-- Si usás MySQL: TIMESTAMPDIFF(MINUTE, fecha_hora_evento, fecha_siguiente)
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1) NUMERO DE CAMAS (total, incluye quirófano hasta que lo descartes)
-- ---------------------------------------------------------------------
SELECT COUNT(DISTINCT cama_id) AS total_camas
FROM datos_crudos;


-- ---------------------------------------------------------------------
-- 2) CANDIDATO A QUIROFANO
--    Heurística: duración de ocupación muy corta + entra/sale
--    predominantemente por "Pase de cama" (no por Ingreso/Alta-Egreso)
-- ---------------------------------------------------------------------
WITH ordenado AS (
    SELECT
        e.cama_id,
        e.tipo_evento                                            AS evento_entrada,
        e.fecha_hora_evento,
        LEAD(e.tipo_evento) OVER (
            PARTITION BY e.persona_id ORDER BY e.fecha_hora_evento
        )                                                         AS evento_salida,
        LEAD(e.fecha_hora_evento) OVER (
            PARTITION BY e.persona_id ORDER BY e.fecha_hora_evento
        )                                                         AS fecha_siguiente
    FROM datos_crudos e
    WHERE e.tipo_evento IN ('Ingreso', 'Pase de cama')
),
duraciones AS (
    SELECT
        cama_id,
        evento_entrada,
        evento_salida,
        (julianday(fecha_siguiente) - julianday(fecha_hora_evento)) * 24 / 60.0 AS duracion_min
    FROM ordenado
    WHERE fecha_siguiente IS NOT NULL
)
SELECT
    cama_id,
    COUNT(*)                                                          AS episodios,
    AVG(duracion_min)                                                 AS duracion_media_min,
    AVG(CASE WHEN evento_entrada = 'Pase de cama' THEN 1.0 ELSE 0 END) AS pct_entra_por_pase,
    AVG(CASE WHEN evento_salida  = 'Pase de cama' THEN 1.0 ELSE 0 END) AS pct_sale_por_pase
FROM duraciones
GROUP BY cama_id
ORDER BY duracion_media_min ASC;
-- Mirá las primeras filas (menor duración media): si además tienen
-- pct_entra_por_pase y pct_sale_por_pase cercanos a 1, esa es tu(s)
-- cama(s) quirófano. Anotá el/los cama_id resultante(s) y usalos abajo
-- en lugar de :quirofano_id.


-- ---------------------------------------------------------------------
-- 3) TASA DE LLEGADA AL SISTEMA (lambda) -> eventos "Orden Internacion"
-- ---------------------------------------------------------------------
WITH llegadas AS (
    SELECT
        fecha_hora_evento,
        LEAD(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento) - fecha_hora_evento AS intervalo
    FROM eventos
    WHERE tipo_evento = 'Orden Internacion'
)
SELECT
    COUNT(*)                                                              AS n_llegadas,
    AVG(EXTRACT(EPOCH FROM intervalo)) / 3600.0                           AS intervalo_medio_horas,
    1.0 / (AVG(EXTRACT(EPOCH FROM intervalo)) / 3600.0)                   AS lambda_por_hora
FROM llegadas
WHERE intervalo IS NOT NULL;


-- ---------------------------------------------------------------------
-- 4) TASA DE SERVICIO POR CAMA (mu) - excluyendo el quirófano
--    Reemplazar :quirofano_id por el/los ID hallado(s) en el paso 2
-- ---------------------------------------------------------------------
WITH ordenado AS (
    SELECT
        e.cama_id, e.tipo_evento AS evento_entrada, e.fecha_hora_evento,
        LEAD(e.fecha_hora_evento) OVER (
            PARTITION BY e.persona_id ORDER BY e.fecha_hora_evento
        ) AS fecha_siguiente
    FROM eventos e
    WHERE e.tipo_evento IN ('Ingreso', 'Pase de cama')
),
duraciones AS (
    SELECT cama_id,
           EXTRACT(EPOCH FROM (fecha_siguiente - fecha_hora_evento)) / 3600.0 AS duracion_h
    FROM ordenado
    WHERE fecha_siguiente IS NOT NULL
)
SELECT
    AVG(duracion_h)          AS estadia_media_horas,
    1.0 / AVG(duracion_h)    AS mu_por_hora
FROM duraciones
WHERE cama_id <> :quirofano_id;   -- ajustar si hay más de un quirófano


-- ---------------------------------------------------------------------
-- 5) TASA DE SALIDA DEL SISTEMA (mu_n empirico) -> eventos "Egreso"
--    Sirve para validar: debería aproximarse a n_promedio_ocupado * mu
-- ---------------------------------------------------------------------
WITH egresos AS (
    SELECT
        fecha_hora_evento,
        LEAD(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento) - fecha_hora_evento AS intervalo
    FROM eventos
    WHERE tipo_evento = 'Egreso'
)
SELECT
    COUNT(*)                                                    AS n_egresos,
    AVG(EXTRACT(EPOCH FROM intervalo)) / 3600.0                 AS intervalo_medio_horas,
    1.0 / (AVG(EXTRACT(EPOCH FROM intervalo)) / 3600.0)         AS mu_n_por_hora
FROM egresos
WHERE intervalo IS NOT NULL;


-- ---------------------------------------------------------------------
-- 6) lambda_q y mu_q DEL QUIROFANO
--    Reemplazar :quirofano_id por el ID hallado en el paso 2
-- ---------------------------------------------------------------------
WITH ordenado AS (
    SELECT
        e.cama_id, e.fecha_hora_evento,
        LEAD(e.fecha_hora_evento) OVER (
            PARTITION BY e.persona_id ORDER BY e.fecha_hora_evento
        ) AS fecha_siguiente
    FROM eventos e
    WHERE e.tipo_evento IN ('Ingreso', 'Pase de cama')
),
quirofano AS (
    SELECT cama_id, fecha_hora_evento,
           EXTRACT(EPOCH FROM (fecha_siguiente - fecha_hora_evento)) / 3600.0 AS duracion_h
    FROM ordenado
    WHERE cama_id = :quirofano_id AND fecha_siguiente IS NOT NULL
)
SELECT
    COUNT(*)                                                           AS n_cirugias,
    AVG(duracion_h)                                                    AS estadia_media_horas,
    1.0 / AVG(duracion_h)                                              AS mu_q_por_hora,
    COUNT(*) / (
        EXTRACT(EPOCH FROM (
            (SELECT MAX(fecha_hora_evento) FROM eventos) -
            (SELECT MIN(fecha_hora_evento) FROM eventos)
        )) / 3600.0
    )                                                                   AS lambda_q_por_hora
FROM quirofano;