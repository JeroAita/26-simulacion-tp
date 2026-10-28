### Modelo

Para analizar este sistema, lo modelamos a partir de la **Teoría de colas** con las siguientes reglas:

- Un paciente es una entidad/cliente.
- El evento "Orden de internación" es la llegada de un paciente al sistema. Queda encolado hasta que ocurre el evento "Ingreso", que lo ubica en una cama.
- Una cama es un servidor.
- Existe una cama especial llamada quirófano, en serie con todas las camas. Se llega al quirófano y se sale del quirófano mediante un evento "Pase de cama". Salir del quirófano implicaría volver a la cola original, pero siempre se retorna a una cama. Por lo tanto, se tiene una cola con prioridades.
- La llegada de un paciente es aleatoria, siguiendo una distribución desconocida.
- El egreso de un paciente es aleatorio, siguiendo una distribución desconocida.

Bajo la notación de Kendall, sería un modelo multi-servidor de cola infinita y fuente infinita: 

$$
(GD|GD|c):(GD|\infty|\infty)
$$

Con este modelo sabemos que:

- La tasa de llegada efectiva es igual a la tasa de llegada, porque la cola es infinita: $\lambda_{eff} = \lambda_n$
- La tasa de llegada no depende del estado del sistema: $\lambda_n = \lambda$
- El tiempo de servicio del sistema escala con el tiempo de servicio de los servidores y de la cantidad de servidores ocupados: $\mu_n = n \cdot \mu$ (si $n \leq c$) o $\mu_n = c \cdot \mu$ (si $n > c$, todos los servidores ocupados). Aun así, contemplaremos que los servidores son heterogéneos; cada uno tendrá su tiempo de servicio.


Retomando de los datos disponibles: podríamos tomar $c = 74$ camas regulares en paralelo. Identificamos que la cama quirófano es aquella con `cama_id = 241` desde el sistema, reafirmado al ver que a esta cama en particular los pacientes llegan únicamente a través de pases de cama.

Aun así, para el alcance de este trabajo, necesitamos acotar la cantidad de servidores. **Tomaremos únicamente $c = 10$ camas**, seleccionando aquellas con mayor cantidad de eventos de tipo "Ingreso"  asociados:

| ID | Ingresos |
| :---: | :---: |
|201 |247 |
|202|183 |
|203 |163 |
|273|155 |
|230|87|
|275|82|
|231|79|
|232|71|
|200|67|
|243|67|

Estas camas representan casi el 70% de la actividad de las muestras; al acumular 1201 eventos de tipo Ingreso de los 1756 en total.

Ignoraremos los eventos de tipo "Pase de cama" que no involucren a la cama `241`, ya que al ser movimientos de entidades entre servidores en paralelo no modifican la cantidad de servidores ocupados. En consecuencia, consideraremos que el paciente continúa en la misma cama desde su ingreso hasta que ocurra un pase de cama al quirófano o hasta su egreso. El tiempo de servicio a un paciente se calcularía entonces como la diferencia entre la fecha-hora de egreso o paso a quirófano y la fecha-hora de ingreso. Esto se desarrollará con mayor detalle más adelante, cuando analicemos los tiempos de servicio.

Además, ignoraremos los eventos de tipo "Alta médica", ya que no implican un movimiento de entidad, sino que representan una etapa burocrática necesaria previa al evento de tipo "Egreso", que sí implica un movimiento de entidad.

Con estas bases definidas, presentamos el diagrama de modelo de colas:

![Diagrama de modelo de colas](../src/simulacion-tp_final-diagrama_modelo.png)

### Tasa de llegadas

Filtramos los eventos de tipo "Orden de internación" con el objetivo de analizar las llegadas al sistema y comprender el periodo entre ellas.

![Captura de registro de eventos](../src/simulacion-tp_final-muestras-2.png)

Teniendo $n = 1190$ eventos de tipo Orden de internación, calculamos la media muestral y el desvío estándar:

$$
\bar x = \frac{ \sum_{i=1}^{n}{ x_i } }{n} 
\approx 1,479 \frac{\text{horas}}{\text{paciente}} 
\, \qquad 
s = \sqrt{ \frac{ \sum_{i=1}^{n}{ (x_i - \bar x)^2 } }{n-1} } 
\approx 2,004 \frac{\text{horas}}{\text{paciente}}
$$

Por ende, estimamos la **tasa de llegada** como $\lambda = \frac{1}{\bar x} \approx 0,676 \frac{\text{pacientes}}{\text{hora}}$

Analizamos la distribución a la que se ajustan los periodos entre llegadas. Al ser la variable aleatoria la cantidad de tiempo entre evento y evento, sabemos que es no-negativa. Realizamos una **prueba de bondad de ajuste Chi Cuadrado** para probar si la distribución se ajusta a una exponencial. Utilizamos Chi Cuadrado en lugar de Kolmogorov-Smirnov porque poseemos una gran cantidad de muestras.

Planteamos como hipótesis nula $H_0$ que las muestras corresponden a una distribución exponencial con media $1,479$, y como hipótesis alternativa, que corresponden a otra distribución. Tomamos un nivel de confianza $1 - \alpha = 0,90$.

Tomamos $k = \sqrt{n} \approx  34$ intervalos equiprobables, de frecuencias esperadas $F_e = \frac{n}{k} = 35$. Calculamos los límites de los intervalos a partir de la inversa de la función de probabilidad acumulada:

$$
\begin{aligned}
&F(x) = 1-e^{- \lambda x} \\
&\Rightarrow F^{-1}(x) = -\frac{1}{\lambda} \cdot \ln \left( 1 - \frac i k \right)\\
&\Rightarrow x_i = -1,479 \cdot \ln \left( 1 - \frac{i}{35} \right)
\end{aligned}
$$

Luego los intervalos: $[x_0; \ x_1) = [0; \ 0,043)\, \ [x_1; \ x_2) = [0,022; \ 0,087)\, ...$ . Realizamos un conteo de las muestras incluídas en cada intervalo; las frecuencias observadas $F_o$.

Calculamos el estimador:

$$
\chi^2 = \sum{ \frac{(F_o - F_e)^2}{F_e}} \approx 1183
$$

Poseemos $k-1-1 = 32$ grados de libertad; restamos uno al haber estimado la media a partir de la muestra. Luego el estimador tabulado:

$$
\chi^2_{\alpha, \ k-1-1} = \chi^2_{0,10, \, 32} \approx 42,58
$$
> Ver apéndice: Análisis de llegadas - Chi Cuadrado

Vemos que el $\chi^2$ calculado es ampliamente superior al $\chi^2$ tabulado, por lo que rechazamos la $H_0$ con un nivel de confianza del 90%; la distribución de entradas no es exponencial.

Detalles a considerar:

- El primer intervalo, $[0; \ 0,043)$ (periodos de menos de 2,5 minutos entre entradas) aporta $\frac{(F_o - F_e)^2}{F_e} = 967$ al estadístico, es decir, casi la totalidad del peso de los resultados.
- El último intervalo, $[4,233; \ \infty)$ (entradas cada más de 4,2 horas) son el siguiente gran aporte al estadístico: $132$.
- Los intervalos intermedios respetan una alineación equilibrada más próxima a la distribución esperada.

Esto sugiere que el proceso de llegadas al sistema no es homogéneo, sino que podría ser una mezcla entre:

- Llegadas "reales" de pacientes, espaciadas, más similares a una exponencial.
- Órdenes de internación cargadas en conjunto, casi simultáneamente, quizás por el mismo usuario o al inicio de determinado turno.
- Periodos de más de 4 horas sin cargas de internaciones, quizás por caídas del sistema, parálisis administrativa de la institución o demás factores externos.

Si bien se rechazó la hipótesis de que las llegadas siguen una distribución exponencial, la media $\lambda = 0,676 \frac{\text{pacientes}}{\text{hora}}$ sigue siendo válida como estimador de la tasa de llegadas, ya que se deriva directamente de la media muestral. La misma será utilizada como parámetro descriptivo del proceso GD en el modelo de colas.

### Tasas de servicio

Similar al análisis de las llegadas al sistema, analizaremos ahora el tiempo que cada paciente permanece en una cama; es decir, el tiempo de servicio.

Siguiendo las reglas del modelo, el tiempo de servicio de un paciente es la diferencia entre la fecha-hora de su egreso (o de su pase de cama al quirófano, lo que ocurra primero) y la fecha-hora de su evento ingreso. Se ignoran los pases de cama entre camas regulares y las altas médicas.

Poseemos $1201$ internaciones que ingresan por alguna de las 10 camas seleccionadas. De ellas, $10$ no tienen un fin registrado porque los datos de la muestra terminan antes de que esos pacientes egresen, por lo que las descartamos. Nos quedan $n = 1191$ tiempos de servicio: $1145$ terminan en un egreso y $46$ en un pase al quirófano.

Las estadías posteriores al quirófano (cuando el paciente vuelve a una cama) se analizan junto con el quirófano, en la próxima sección.

Calculando la media y el desvío globales,

$$
\bar x \approx 11,746 \frac{\text{horas}}{\text{paciente}} 
\, \qquad 
s \approx 26,512 \frac{\text{horas}}{\text{paciente}}
$$

Estimamos la **tasa de servicio** como $\mu = \frac{1}{\bar x} \approx 0,085 \frac{\text{pacientes}}{\text{hora}}$ por cama.

Calculamos la media muestral y el desvío estándar de tiempo de servicio para cada una de las camas seleccionadas:

| Cama | $n$ | Media (h) | Desvío (h) | $\mu$ ($\frac{\text{pacientes}}{\text{hora}}$) |
| :--: | :-: | :-------: | :--------:  | :-----------: |
| `201` | 246 | 11,89 | 29,26 | 0,084 |
| `202` | 180 | 11,21 | 19,42 | 0,089 |
| `203` | 162 | 9,51 | 16,11 | 0,105 |
| `273` | 153 | 11,41 | 28,53 | 0,088 |
| `230` | 87 | 6,85 | 5,43 | 0,146 |
| `275` | 82 | 32,44 | 52,51 | 0,031 |
| `231` | 78 | 5,96 | 4,61 | 0,168 |
| `232` | 70 | 5,62 | 4,02 | 0,178 |
| `200` | 67 | 17,83 | 41,54 | 0,056 |
| `243` | 66 | 6,87 | 7,73 | 0,146 |

Vemos que los servidores son claramente heterogéneos: las medias van desde $5,6$ hasta $32,4$ horas de tiempo de servicio.

Pueden identificarse dos grupos claramente diferenciados: las camas `230`, `231`, `232` y `243` con mayor tasa de servicio y menor variabilidad, y el resto con menor tasa de servicio y mayor variabilidad. El primer grupo mencionado representa alrededor del $33\%$ de la cantidad de internaciones acumuladas entre ambos grupos.

La tasa $\mu$ de cada cama se utilizará como parámetro descriptivo del proceso GD en el modelo de colas.

### Llegadas y tiempos de servicio del quirófano

Analizamos ahora el quirófano, la cama `241`, que está en serie con el resto de camas. Consideramos únicamente a los pacientes cuya internación comenzó en alguna de las 10 camas seleccionadas.

Cada evento "Pase de cama" hacia la cama `241` es una llegada al quirófano. La salida del quirófano es el primer evento posterior a que sea un pase a otra cama o un "Egreso". Poseemos $83$ visitas al quirófano, por lo que $n=82$ periodos entre llegadas. Calculamos la media muestral y el desvío estándar de los periodos entre las llegadas:

$$
\bar x \approx 20,878 \frac{\text{horas}}{\text{paciente}} 
\, \qquad 
s \approx 32,316 \frac{\text{horas}}{\text{paciente}}
$$

Por ende, estimamos la **tasa de llegada al quirófano** como $\lambda_q = \frac{1}{\bar x} \approx 0,048 \frac{\text{pacientes}}{\text{hora}}$.

$83$ de los $1268$ servicios completos (considerando todas las camas, no sólo las seleccionadas) pasan al quirófano, es decir, alrededor del $6,5\%$.

Todas las visitas al quirófano poseen una salida registrada. Analizamos el periodo entre las salidas del quirófano:

$$
\bar x \approx 1,923 \frac{\text{horas}}{\text{paciente}} 
\, \qquad 
s \approx 2,194 \frac{\text{horas}}{\text{paciente}}
$$

Obtenemos que la **tasa de servicio del quirófano** es $\mu_q = \frac{1}{\bar x} \approx 0,520 \frac{\text{pacientes}}{\text{hora}}$.

### Medidas de rendimiento analíticas

(...)







