# Simulador de eventos discretos (SimPy)

Reproduce en Python el modelo de la sección 4 del informe: llegadas exógenas
empíricas, 5 camas en paralelo con prioridad para los retornos del quirófano,
un quirófano de un servidor y realimentación al sub-sistema de camas.

Tiempos en **horas**. El código y los comentarios están en español.

## Instalación

~~~bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
# o, si sólo se quieren las dependencias:
pip install -r scripts/requirements.txt simpy scipy matplotlib pytest
~~~

## Muestras empíricas

Los CSV de `datos/muestras/` se generan desde `datos/datos.db` con la lógica de
los scripts SQL 3, 4, 5 y 6:

~~~bash
python scripts/extraer_muestras.py
~~~

El script verifica los controles documentados (n, media, desvío, mediana, máximo
y conteos de destino) y aborta si no coinciden. Si falta `datos_limpios`, hay
que ejecutar antes `scripts/0_convertir_csv_en_sqlite.py` y
`scripts/1_limpieza_de_datos.sql`.

Camas del sub-sistema: **223, 225, 226, 227, 228**. Quirófano: **241**.

## Uso mínimo

~~~bash
python -m simulacion \
    --config configs/original.toml \
    --replicas 20 --T 30000 --warmup 1000 --semilla 12345 \
    --salida salida/ejemplo --procesos 4
~~~

Opciones:

| Opción | Descripción |
|:---|:---|
| `--config` | TOML de configuración (por defecto `configs/original.toml`). |
| `--replicas` | Cantidad de réplicas independientes. |
| `--T` | Longitud de cada corrida en horas. |
| `--warmup` | Transitorio descartado `d_T` en horas. |
| `--semilla` | Semilla base del experimento. |
| `--salida` | Directorio de resultados. |
| `--antitetico` | Usa `1-U` en los cuatro flujos (réplica antitética). |
| `--sin-trayectoria` | Omite los CSV de trayectoria de estados. |
| `--procesos` | Réplicas en paralelo; no cambia los resultados. |

Las réplicas se numeran desde **0**: `corrida_00`, `corrida_01`, etc. La misma
tupla `(semilla, réplica)` produce exactamente la misma trayectoria.

## Salidas

En `salida/<experimento>/`:

1. `corrida_<jj>_estado.csv`: una fila por cambio de estado con los valores
   posteriores, más una fila en `t=0` y otra en `t=T`.
2. `corrida_<jj>_visitas.csv`: una fila por visita, incluidas las incompletas.
3. `medidas.csv`: una fila por réplica con las medidas y los controles.
4. `config_usada.toml`: configuración efectiva y versiones de las librerías.

Los tiempos y las medidas se escriben con precisión completa (`repr` de
`float`), sin redondear.

## Definiciones y decisiones de implementación

- **Ventana de recolección:** `[d_T, T]`, con `T_c = T - d_T`. Las integrales
  temporales se calculan exactamente sobre la función escalón, no muestreando
  una grilla.
- **Visita completa en la ventana:** `t_llegada_cola >= d_T` **y**
  `t_fin_servicio <= T`. Las visitas en curso en cualquiera de los bordes se
  excluyen de `W_q`, `W_s` y de `lambda_eff`.
- **`W_q^(q)`:** se usan las visitas al quirófano con
  `t_llegada_quirofano >= d_T` y `t_fin_quirofano <= T`. Es el mismo criterio
  de no censurar los bordes.
- **Visitas incompletas:** se guardan igual en `visitas.csv` con
  `completa_en_ventana = False`. `servicio_h` es el valor sorteado para la
  visita aunque el servicio no haya terminado; `espera_h` queda vacío si la
  visita nunca llegó a tomar una cama.
- **`rho_q`:** media temporal de servidores del quirófano ocupados dividida por
  `c_quirofano`. Con `c_quirofano = 1` es la fracción de tiempo ocupado.
- **`lambda_eff`:** visitas completas en la ventana divididas por `T_c`.
- **`lambda_ext`:** llegadas exógenas con instante de llegada en `[d_T, T]`
  divididas por `T_c`.
- **Error de Little:** `(L - lambda_eff * W) / L`, con `L = L_s` o `L_q`.
  Vale `nan` si `L = 0`.
- **Trayectoria:** los cambios simultáneos generan varias filas con el mismo
  `tiempo_h` (duración cero), como es esperable.
- **Fin de corrida:** `env.run(until=T)` corta los pacientes en curso; sus
  visitas quedan registradas como incompletas.

## Números aleatorios

Cada réplica usa cuatro flujos independientes derivados de
`numpy.random.SeedSequence(entropy=semilla, spawn_key=(replica,))`: llegadas,
servicio en camas, destino y servicio del quirófano. Cada flujo consume
exactamente un `U` por variable mediante `random()`. No se usa el módulo
`random` ni el estado global de `numpy.random`.

Con `--antitetico` cada flujo devuelve `1-U`. Con la misma `(semilla, réplica)`
se obtiene la réplica antitética de la corrida normal. Esto deja preparados los
números aleatorios comunes y las variables antitéticas de las etapas siguientes.

## Tests

~~~bash
pytest
~~~

Incluyen: inversa empírica, determinismo, antitético, prioridad de retornos,
validación contra Erlang C (M/M/5), consistencia de integrales con la
trayectoria, ley de Little y conservación de pacientes.

## Análisis táctico

Todos los scripts leen `salida/<experimento>/` y escriben CSV/Markdown; las
figuras van a `src/` como PNG.

~~~bash
# Transitorio de Ws (piloto de 30 réplicas × 5000 h, sin trayectoria)
python -m analisis.transitorio_ws --entrada salida/transitorio-ws \
    --delta 50 --ventanas 5,10,20

# Transitorio de medidas temporales (piloto con trayectoria habilitada)
python -m analisis.transitorio --entrada salida/piloto \
    --delta 10 --ventanas 5,20,50

# Tamaño de muestra M, n por Chebyshev y longitud
python -m analisis.tamano_muestra --entrada salida/piloto \
    --precision 0.05 --absoluta Lq_q=0.01 --absoluta Wq_q=0.05

# Intervalos de confianza al 95 %
python -m analisis.intervalos --entrada salida/final \
    --precision 0.05 --absoluta Lq_q=0.01 --absoluta Wq_q=0.05
~~~

`analisis/transitorio.py` propone `d_T` como la primera entrada del promedio
móvil a una banda de ±5 % del nivel final. Si la serie es muy ruidosa, informa
también el primer instante desde el cual no vuelve a salir de la banda. La
decisión final de `d_T` queda en manos del usuario.

`analisis/transitorio_ws.py` hace lo mismo para `W_s` a partir de
`corrida_*_visitas.csv`, agrupando las visitas por instante de llegada y
descartando la cola censurada para estimar el nivel final. No necesita los CSV
de trayectoria, así que el piloto puede correrse con `--sin-trayectoria`.

## Nota sobre los valores esperados

Con la distribución empírica de servicios (`C^2 ≈ 2,7`) el modelo produce
`L_q` y `W_q` bastante mayores que los de una aproximación M/M/c. Los valores
`L_q ≈ 1,3` y `W_q ≈ 6,8` que aparecen como referencia corresponden a esa
aproximación markoviana, no al modelo con servicios empíricos. La comparación
se reporta en la sección de resultados; no es un error de implementación.
