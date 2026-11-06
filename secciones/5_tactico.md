## Planeamiento táctico

En esta sección se fijan las decisiones experimentales: tipo de simulación, método para reunir observaciones, transitorio, precisión, número de réplicas y longitud de cada corrida.

### Tipo de simulación

El hospital no tiene un evento de terminación: los pacientes llegan y egresan indefinidamente, y lo que interesa es el comportamiento de largo plazo del sub-sistema. La simulación es **no terminante** y se estudia en **régimen permanente**. Como $\rho \approx 0,73 < 1$, el sistema tiende a estado estable.

Las medidas se calculan de dos maneras:

| Tipo | Medidas | Estimador por corrida |
|:---|:---|:---|
| Promedio temporal | $\bar C$, $\rho$, $L_s$, $L_q$, $\rho_q$, $L_q^{(q)}$ | $\frac{1}{T_c}\int_0^{T_c} X(t)\,dt$ |
| Promedio por observación | $W_q$, $W_s$, $W_q^{(q)}$ | $\frac{1}{n}\sum_{i=1}^{n} X_i$ |

$T_c$ es la ventana de recolección (la corrida sin el transitorio) y $n$ es la cantidad de visitas completas que caen dentro de ella; las visitas en curso al inicio o al final de la ventana se excluyen. Cada corrida produce **una sola observación por medida**.

### Método para reunir observaciones

**Método de réplicas.** Se simulan $M$ corridas independientes, cada una con su propio flujo de números aleatorios, el sistema inicialmente vacío y la misma longitud $T$. De cada corrida se calcula un valor por medida sobre su ventana de recolección, y esos $M$ valores se promedian.

Se eligió este método porque las $M$ observaciones son independientes por construcción, de modo que se puede construir el intervalo de confianza con la distribución $t$ sin suponer nada sobre la dependencia dentro de cada corrida. Además, permite formar los pares necesarios para las variables antitéticas y para los números aleatorios comunes. Se descartó el método de subintervalos (lotes) porque las corridas son instantáneas, de modo que las réplicas no tienen costo adicional y evitan tener que estimar la autocorrelación entre lotes.

### Eliminación del transitorio

**Condiciones iniciales:** sistema vacío (sin cola, con las 5 camas y el quirófano libres). Es la inicialización más simple y es igual en todas las réplicas. Como un hospital real nunca arranca vacío, el período inicial no es representativo y se descarta.

**Método:** promedio móvil de ventana fija (Emshoff y Sisson, descrito en Shannon). Se corren $K = 20$ réplicas piloto de $T = 30.000$ h con la semilla base $12345$. Para cada instante se promedia la medida entre réplicas, $\bar Y_i = \frac{1}{K}\sum_k Y_{k,i}$, y se grafica el promedio móvil de ventana $w$:

$$
\bar Y_j(w) = \frac{1}{w}\sum_{i=j-w+1}^{j} \bar Y_i
$$

El punto en que la curva deja de tener tendencia y oscila alrededor de un nivel define el transitorio. Se aplicó a las medidas $C(t)$ y $N_q(t)$; esta última es la que más tarda en estabilizarse. Se eligió este método porque aprovecha las réplicas piloto que de todos modos hacen falta para calcular $M$, y porque el promedio entre réplicas junto con el promedio móvil suavizan el ruido de una sola corrida, que en este sistema es grande.

![](../src/transitorio_C.png)
![](../src/transitorio_Nq.png)

**Resultado:** $d_T = 1.000$ h, el mismo valor para todas las réplicas (Shannon recomienda no elegir un descarte distinto por corrida, para no seleccionar corridas favorables). Equivale al $3,3\%$ de la corrida y deja una ventana $T_c = 29.000$ h.

### Precisión y confianza

Se fija $\alpha = 0,10$ (intervalos del $90\%$). La precisión de cada medida $k$ se define relativa a su media:

$$
d_k = p_k \, \bar X_k, \qquad p_k = 10\%
$$

Se usa precisión relativa porque las medidas tienen escalas muy distintas (no es lo mismo exigir media hora de precisión en $W_q$ que en $L_q$). El intervalo con $M$ réplicas es:

$$
\bar X_k \pm t_{\alpha/2;\,M-1}\,\frac{S_k}{\sqrt{M}}, \qquad \text{con semianchura} \le d_k
$$

Excepto para $L_q^{(q)}$ y $W_q^{(q)}$: se usan cotas absolutas ($d = 0,01$ pacientes y $d = 0,05$ h). Con $\rho_q \approx 0,06$ estas medidas son casi cero, y exigirles $10\%$ de una media tan pequeña no tiene sentido práctico.

### Número de corridas y longitud

**Número de réplicas $M$:** Con las $m = 20$ réplicas piloto (con el transitorio descartado) se obtiene el desvío $S_{\bar X}$ de las medias observadas, y se despeja $M$ de la condición de precisión:

$$
M = \left(\frac{t_{\alpha/2;\,m-1}\,S_{\bar X}}{d}\right)^2, \qquad t_{0,05;\,19} \approx 1,73
$$

| Medida | $\bar X$ | $S_{\bar X}$ | $d$ | $M$ |
|:---|:---:|:---:|:---:|:---:|
| $\bar C$ | 3,721 | 0,110 | 0,372 | 1 |
| $\rho$ | 0,744 | 0,022 | 0,074 | 1 |
| $L_s$ | 5,924 | 0,684 | 0,593 | 4 |
| $L_q$ | 2,203 | 0,600 | 0,220 | 23 |
| $W_q$ | 10,722 | 2,928 | 1,072 | 23 |
| $W_s$ | 28,857 | 3,282 | 2,886 | 4 |
| $rho_q$ | 0,060 | 0,003 | 0,006 | 1 |
| $L_q^{(q)}$ | 0,008 | 0,001 | 0,01 (abs.) | 1 |
| $W_q^{(q)}$ | 0,171 | 0,029 | 0,05 (abs.) | 2 |
$L_q^{(q)}$ | 0.008 | 0.001 | 0.01 | 1|
$W_q^{(q)}$ | 0.171 | 0.029 | 0.05 | 2|

Cuando hay varias medidas manda la de mayor variabilidad relativa, así que se adopta **$M = 23$** ($L_q$ y $W_q$). Como $23 > m = 20$, se completan 3 réplicas más con la misma semilla base. El resto de las medidas queda con precisión holgada. Con $p = 10\%$, $M$ depende del coeficiente de variación entre réplicas, $M \approx (t \cdot CV / p)^2$: $L_q$ y $W_q$ tienen $CV \approx 27\%$, mientras que $\bar C$ tiene $3\%$. Esa variabilidad se debe a los servicios de cola pesada ($C^2 \approx 2,7$) y a una utilización alta, que producen congestión persistente.

**Longitud de la corrida:** Se mantiene $T = 30.000$ h, la misma con la que se hizo el piloto, ya que $S_{\bar X}$ y por lo tanto $M$ dependen de $T_c$. Es la misma en todas las réplicas, para que las observaciones sean idénticamente distribuidas. El esfuerzo total es $23 \times 30.000$ h simuladas. Una vez completadas las $M$ réplicas, se verifica que la semianchura de cada intervalo cumpla $\le d_k$; de no ser así, se agregan réplicas.

**Verificación del tamaño de la muestra $n$:** Para las medidas por observación, la desigualdad de Chebyshev da la cantidad mínima de valores por observación sin suponer normalidad:

$$
n = \frac{1}{\alpha\,b^2}, \qquad b = d/\sigma
$$

Con $\alpha = 0,10$ y $b = 1/4$ se obtiene $n = 160$. En $T_c = 29.000$ h hay unas $0,205 \times 29.000 \approx 5.900$ visitas por réplica, muy por encima de ese mínimo. Las esperas de visitas consecutivas están autocorrelacionadas, por lo que $160$ es una cota inferior optimista.

### Resumen de decisiones

| Parámetro | Valor |
|:---|:---|
| Tipo de simulación | no terminante, régimen permanente |
| Método de observaciones | réplicas independientes, semilla base $12345$ con flujos independientes |
| Condiciones iniciales | sistema vacío |
| Transitorio | promedio móvil de ventana fija; $d_T = 1.000$ h en todas las réplicas |
| $\alpha$ | $0,10$ |
| Precisión $d$ | $10\%$ relativo; absoluto en $L_q^{(q)}$ ($0,01$) y $W_q^{(q)}$ ($0,05$ h) |
| Réplicas $M$ | $23$ |
| Longitud $T$ | $30.000$ h ($T_c = 29.000$ h) |