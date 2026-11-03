## Análisis

### Modelo

Para analizar este sistema, lo modelamos a partir de la **Teoría de colas** con las siguientes reglas:

- Un paciente es una entidad / cliente.
- Las camas con ID $223$, $225$, $226$, $227$ y $228$ son los $c = 5$ servidores en paralelo. Las consideraremos las camas "internas" o del "sub-sistema seleccionado".
- Entrada: Un evento "Orden de internación" es la llegada de un paciente al sistema. Queda encolado hasta que ocurre el evento "Ingreso", que lo ubica en una de las camas del sub-sistema. También puede ocurrir que se ubique a un paciente en una de estas camas a partir de un evento "Pase de cama" desde una cama regular externa. En ese caso, el tiempo del paciente encolado queda sujeto al tiempo que pasó en camas externas.
- Salida:  Un evento "Egreso" o un "Pase de cama" desde una de las camas del sub-sistema hacia una cama externa es la salida del paciente del sistema.
- Existe una cama especial llamada quirófano, en serie con todas las camas. Se llega al quirófano y se sale del quirófano mediante un evento "Pase de cama". Salir del quirófano implicaría volver a la cola original, pero siempre se retorna a una cama. Por lo tanto, se tiene una cola con prioridades.
- La llegada de un paciente es aleatoria, siguiendo una distribución desconocida.
- El egreso de un paciente es aleatorio, siguiendo una distribución desconocida.

Bajo la notación de Kendall, sería un modelo multi-servidor de cola infinita y fuente infinita: 

$$
(GD|GD|5):(GD|\infty|\infty)
$$

Con este modelo sabemos que:

- La tasa de llegada efectiva es igual a la tasa de llegada, porque la cola es infinita: $\lambda_{eff} = \lambda_n$
- La tasa de llegada no depende del estado del sistema: $\lambda_n = \lambda$
- El tiempo de servicio del sistema escala con el tiempo de servicio de los servidores y de la cantidad de servidores ocupados: $\mu_n = n \cdot \mu$ (si $n \leq c$) o $\mu_n = c \cdot \mu$ (si $n > c$, todos los servidores ocupados).

Ignoraremos los eventos de tipo "Pase de cama" que ocurran entre las camas del sub-sistema seleccionado, al no representar un cambio en la cantidad de clientes en el sistema. El tiempo de servicio a un paciente se calcularía entonces como la diferencia entre la fecha-hora de egreso, paso a quirófano o paso a cama externa, y la fecha-hora de ingreso o pase a cama interna. Esto se desarrollará con mayor detalle más adelante, cuando analicemos los tiempos de servicio.

Con estas bases definidas, el diagrama de modelo de colas:

![Diagrama de modelo de colas](../src/simulacion-tp_final-diagrama_modelo.png)

### Tasa de llegadas

Filtramos eventos cuyos destinos sean una de las camas seleccionadas, con el objetivo de analizar las llegadas al sistema y comprender el periodo entre ellas.

> Script SQL 3: llegadas

![](../src/llegadas.png)

Se registraron $355$ llegadas de pacientes a alguna de las camas del sub-sistema, siendo el $86\%$ pases de cama desde una cama regular externa. Con ello, tenemos $n = 354$ periodos entre las llegadas:

$$
\bar x = \frac{\sum_{i=1}^{n}{ x_i }}{n} \approx 4,95 \frac{\text{horas}}{\text{paciente}}
\ , \qquad
s = \sqrt {\frac{\sum_{i=1}^{n}{ (x_i - \bar x)^2 }}{n-1}} \approx 5,84 \frac{\text{horas}}{\text{paciente}}
$$
Por ende, estimamos la **tasa de llegada** como:

$$
\lambda = \frac{1}{\bar x} \approx 0,2 \frac{\text{pacientes}}{\text{hora}}
$$

Realizamos una **prueba de bondad de ajuste Chi Cuadrado** para comprobar si la distribución se ajusta a una exponencial. Obtuvimos un estimador $\chi^2 \approx 49,21$, mayor al valor crítico tabulado $\chi^2_{0,10, \ 17} \approx 24,77$, por lo que rechazamos la hipótesis nula: los datos no se ajustan a una exponencial.

> Ver apéndice: Análisis de llegadas - Chi Cuadrado

Si bien se rechazó la hipótesis de que las llegadas siguen una distribución exponencial, la media $\lambda = 0,2 \frac{\text{pacientes}}{\text{hora}}$ sigue siendo válida como estimador de la tasa de llegadas, ya que se deriva directamente de la media muestral. Para la simulación, se generarán valores a partir de la distribución empírica.

Como detalle, podemos ver que alrededor del $45\%$ de los periodos entre llegadas son menores a $3$ horas. El histograma:

![](../src/llegadas_histograma.png)

### Tasas de servicio

Similar al análisis de las llegadas al sistema, analizaremos ahora el tiempo que un paciente permanece en una de las camas seleccionadas; es decir, el tiempo de servicio.

Siguiendo las reglas del modelo, el tiempo de servicio de un paciente es la diferencia entre la fecha-hora de su egreso de su pase de cama al quirófano o una cama externa, y la fecha-hora del evento ingreso o pase de cama con el que llegó a la cama. Se ignoran los pases de cama entre camas dentro del sub-sistema y las altas médicas al no representar un movimiento de entidades dentro del sistema.

> Script SQL 4: tiempos de servicio

![](../src/servicios.png)

Observamos $n=350$ servicios completos, con un tiempo de servicio medio global de $18,1 \frac{\text{ horas }}{\text{ paciente }}$, desvío $7,48$. Esto implicaría una **tasa de servicio del sistema**: 

$$
\mu \approx 0,05  \frac{\text{ pacientes }}{\text{ hora }}
$$

Separando por cama de inicio de servicio,

| Cama | n | Media de horas |  Tasa de servicio |
|:---:|:---:|:---:|:---:|
|223|81|16,88|$\mu_{223} = 0,059$
|226|75|18,01|$\mu_{226} = 0,056$
|228|68|18,63|$\mu_{228} = 0,054$
|225|64|22,23|$\mu_{225} = 0,045$
|227|62|14,78|$\mu_{227} = 0,068$

Por simplicidad, trabajaremos con servidores homogéneos tomando la tasa de servicio del sistema, que es el valor promedio de las tasas de servicios de los servidores.

Además, vemos que el $49\%$ de las internaciones fueron primeras instancias, es decir, primera vez que el paciente circuló por el sub-sistema antes de egresar o pasar de cama. $29\%$ de las internaciones fueron segundas veces que los pacientes circularon por el sub-sistema, como en situaciones en las que retornan del quirófano. $14\%$ fueron terceras instancias, $5\%$ fueron cuartas instancias, $0,2\%$ quintas instancias y hubo una única sexta instancia.

### Llegadas y tiempos de servicio del quirófano

Analizamos ahora el quirófano, la cama $241$, que está en serie con el resto de camas. Consideramos como llegadas los pases de cama dirigidos hacia la $241$ originados desde alguna de las camas del sub-sistema.

> Script SQL 5: Llegadas y tiempos de servicio del quirófano

Tenemos $68$ observaciones, una media de $26,07 \frac{\text{ horas }}{\text{ paciente }}$ y desvío estándar $31,59$.

Calculamos los tiempos de servicio como las diferencias entre los pases de cama originados desde la cama $241$ destinados a alguna cama del sub-sistema, y los pases de cama originados desde una cama del sub-sistema destinados a la cama quirófano.

Tenemos  $65$ observaciones, una media de $1,51 \frac{\text{ horas }}{\text{ paciente }}$ y desvío estándar $2,07$.

Por lo tanto, las tasas de llegada y tiempos de servicio del quirófano:

$$
\lambda_q = 0,04  \frac{\text{ pacientes }}{\text{ hora }}
, \qquad
\mu_q = 0,66  \frac{\text{ pacientes }}{\text{ hora }}
$$

### Medidas de rendimiento analíticas

El análisis de medidas de rendimiento sólo es válido si el sistema tiende a estado estable. Calculamos el **factor de utilización**:

$$
\rho = \frac{\lambda}{c \cdot \mu} = \frac{0,2}{5 \cdot 0,06} \approx 0,73
$$

Como $\rho < 1$, el sistema tiende a estado estable. Para el quirófano, $\rho_q = \frac{0,04}{0,66} \approx 0,06$.

El **número esperado de servidores ocupados**, por su fórmula de Little:

$$
\bar C = \frac{\lambda_{eff}}{\mu} = \frac{\lambda}{\mu} \approx 3,66 \ \text{camas}
$$

Si bien trabajamos sobre un modelo G/G/c, las siguientes medidas de rendimiento las calculamos utilizando a partir de la fórmula de probabilidad de $n$ clientes en el sistema del modelo M/M/c como marco de referencia. Las mismas son aproximaciones de referencia; la simulación por software proveerá medidas más fieles al modelo.

Con $a = \lambda / \mu$,
$$
P_0 = \left[ 
\sum_{n=0}^{c-1}{ \frac{a^n}{n!} } + \frac{ a^c }{ c! (1 - \rho) }
\right] \approx 0,02
$$

Luego:

$$
P(n \geq c) = \frac{ a^c }{ c! (1 - \rho) } \cdot P_0 \approx 0,43
$$

El **número esperado de clientes en la cola**:

$$
L_q = 0,43 \cdot \frac{\rho}{1-\rho} \approx 1,17 \ \text{pacientes}
$$

El **tiempo esperado de espera en la cola**:

$$
W_q = \frac{L_q}{\lambda} \approx 5,8 \ \text{h}
$$

El **tiempo esperado de espera en el sistema**:

$$
W_s = W_q + \frac{1}{\mu} \approx 23,9 \ \text{h}
$$

El **número esperado de clientes en el sistema**:

$$
L_s = L_q + \frac{\lambda}{\mu} \approx 4,8 \ \text{pacientes}
$$
