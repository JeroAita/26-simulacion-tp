## Planeamiento táctico

En esta sección se fijan las decisiones experimentales: tipo de simulación, método para reunir observaciones, transitorio, precisión, número de réplicas y longitud de cada corrida.

### Tipo de simulación

El hospital no tiene un evento de terminación: los pacientes llegan y egresan indefinidamente, y lo que interesa es el comportamiento de largo plazo del sub-sistema. La simulación es **no terminante** y se estudia en **régimen permanente**.

$T_c$ es la ventana de recolección (la corrida sin el transitorio) y $n$ la cantidad de visitas completas ocurridas dentro de ella; las visitas en curso al final de la ventana se excluyen. Cada corrida producirá una observación de la medida a analizar, ${W_s}_k$, que es una variable basada en promedio por observación:

$$
{W_s}_k = \frac{ \sum_{i=1}^{n}{{W_s}_i} }{ n }
$$

Utilizando el Teorema del Límite Central, sabemos que al ser una distribución de promedios, están normalmente distribuídos. Si obtenemos $M$ observaciones y las promediamos, obtenemos un estimador del valor esperado de $W_s$:

$$
\bar W_s = \frac{ \sum_{k=1}^{M}{{W_s}_k} }{ M }
$$

### Método para reunir observaciones

**Método de réplicas:** Se simulan $M$ corridas independientes, cada una con su propio flujo de números aleatorios, el sistema inicialmente vacío y la misma longitud $T$. De cada corrida se calcula un valor por medida sobre su ventana de recolección, y esos $M$ valores se promedian.

Se eligió este método porque las $M$ observaciones son independientes por construcción, de modo que se puede construir el intervalo de confianza con la distribución $t$ sin suponer nada sobre la dependencia dentro de cada corrida. Además, permite formar los pares necesarios para las variables antitéticas y para los números aleatorios comunes.

### Número de corridas y longitud

**Cantidad de visitas $n$:** Para las medidas por observación, la desigualdad de Chebyshev da la cantidad mínima de valores por observación sin suponer normalidad:

$$
n = \frac{1}{\alpha\,b^2}, \qquad b = d/\sigma
$$

Con $\alpha = 0,10$ y $b = 1/4$ se obtiene $n = 160$.

A partir de la tasa de llegada, tenemos que $\lambda \cdot T_c \approx n \Rightarrow T_c \approx \frac{n}{\lambda} = \frac{160}{0,205} = 780,5 \ h$ es el tiempo mínimo para la llegada de la cantidad de visitas necesarias. Para calcular la longitud total de las corridas, debemos considerar el tiempo que el sistema pasa en estado transitorio.

### Eliminación del transitorio

**Condiciones iniciales:** sistema vacío (sin cola, con las 5 camas y el quirófano libres). Es la inicialización más simple y es igual en todas las réplicas. Como un hospital real nunca arranca vacío, el período inicial no es representativo y se descarta.

**Método:** promedio móvil de ventana fija (Emshoff y Sisson, descrito en Shannon). Se corren $K = 30$ réplicas piloto de $T = 5.000$ h con la semilla base $12345$ y el sistema inicialmente vacío.

Las visitas se agrupan en intervalos de $\Delta = 50$ h según su **instante de llegada**, y no según su instante de salida, para no favorecer a las visitas cortas al comienzo. Para cada réplica $k$ e intervalo $i$ se calcula

$$
Y_{k,i} = \frac{1}{n_{k,i}}\sum_{v \in i} W_{s,v},
$$

donde $n_{k,i}$ es la cantidad de visitas de la réplica $k$ que llegan en el intervalo $i$ y terminan antes de $T$. Luego se promedia entre réplicas, $\bar Y_i = \frac{1}{K}\sum_k Y_{k,i}$, y se aplica el promedio móvil de ventana $w$:

$$
\bar Y_j(w) = \frac{1}{w}\sum_{i=j-w+1}^{j} \bar Y_i
$$

Se probaron ventanas de $w = 5$, $10$ y $20$ intervalos (250, 500 y 1.000 h). Con $\lambda_{eff} \approx 0{,}206$ visitas/h, cada intervalo de 50 h contiene unas 10 visitas por réplica y unas 300 al promediar las 30 réplicas, de modo que la media por intervalo no está dominada por el ruido. El nivel final se estima en la región central de la corrida, descartando la cola censurada (los últimos 1.000 h), para que las visitas incompletas no sesguen la banda. El punto en que la curva deja de tener tendencia y oscila alrededor de ese nivel define el transitorio.

Se eligió este método porque el promedio entre réplicas junto con el promedio móvil suavizan el ruido de una sola corrida, que en este sistema es grande por la cola pesada de los servicios.

![](../src/transitorio_Ws.png)

**Resultado:** las ventanas de 250 y 500 h entran en la banda de $\pm 5\%$ alrededor de su nivel final estimado a las $350$ h y $550$ h, respectivamente. La ventana de 1.000 h, que es la más conservadora y la que mejor filtra las fluctuaciones de largo plazo, entra a las $1.050$ h. Se adopta

$$
d_T = 1.000\ \text{h},
$$

redondeando ese valor, el mismo para todas las réplicas (Shannon recomienda no elegir un descarte distinto por corrida, para no seleccionar corridas favorables). El nivel final estimado es $\approx 28{,}5$ h, del mismo orden que la media de $W_s$ de las 30 réplicas ($28{,}98$ h). El transitorio representa el $20\%$ del piloto de $5.000$ h y deja $4.000$ h de ventana. La longitud total de las corridas será $T = T_c + d_T$, con $T_c$ fijado en la sección siguiente a partir de la precisión requerida para $W_s$.

<!--
Indicaciones para las secciones siguientes (pendientes de re-redacción):
- Recalcular M sólo para W_s. El piloto de 30×5000 h es sólo para d_T; no usarlo para M si T final es distinto.
- Fijar T_c a partir de n y λ_eff, y luego T = T_c + d_T con d_T = 1000 h.
- Revisar la inconsistencia n=160 vs d=10%: con σ_Ws≈37,7 h, n≈1.700 y T_c≈8.300 h.
- Eliminar las demás medidas y las cotas absolutas de Lq_q/Wq_q.
- Comando sugerido: python -m analisis.tamano_muestra --entrada <piloto-final> --precision-medida Ws=0.10 --alpha 0.10
-->

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