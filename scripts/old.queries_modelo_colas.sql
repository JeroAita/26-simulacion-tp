
-------------------------------------------------------------------------------
-- 1) Número de camas en el sistema
-------------------------------------------------------------------------------
SELECT COUNT(DISTINCT cama_id) FROM datos_crudos;
-- Existen 76 cama_id. El quirófano se trata como la cama 241: existen 75 camas + el quirófano.


-------------------------------------------------------------------------------
-- 2) Periodo entre llegadas al sistema (órdenes de internación)
-------------------------------------------------------------------------------
SELECT
    evento_id,
    tipo_evento,
    fecha_hora_evento,
    (julianday(fecha_hora_evento) -
     julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento))) * 24
        AS horas_desde_evento_anterior
FROM datos_crudos
WHERE tipo_evento = 'Orden Internacion'
ORDER BY fecha_hora_evento;

-------------------------------------------------------------------------------
-- 3) Periodo entre salidas del sistema (egresos)
-------------------------------------------------------------------------------
SELECT
    evento_id,
    tipo_evento,
    fecha_hora_evento,
    (julianday(fecha_hora_evento) -
     julianday(LAG(fecha_hora_evento) OVER (ORDER BY fecha_hora_evento))) * 24
        AS horas_desde_evento_anterior
FROM datos_crudos
WHERE tipo_evento = 'Egreso'
ORDER BY fecha_hora_evento;