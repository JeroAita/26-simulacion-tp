## Planeamiento táctico

Con el modelo de simulación definido, falta decidir **cómo se experimenta** con él: qué tipo de corrida se usa, cómo se reúnen las observaciones, cuánto se descarta al inicio, qué precisión se busca y cuántas corridas y de qué longitud se realizan. En esta sección se fijan esas decisiones. 

> Los valores que dependen de las corridas piloto se indican como **pendientes** y se completarán una vez ejecutadas.

### Tipo de simulación

El hospital no tiene un evento natural de terminación: los pacientes llegan y egresan de forma indefinida, y lo que interesa no es el total acumulado hasta un instante fijo sino el comportamiento de largo plazo del sub-sistema (ocupación, congestión, esperas). Por eso la simulación es **no terminante** y se estudia en **régimen permanente**.

Como $\rho \approx 0,73 < 1$, el sistema tiende a estado estable. Aun así, la corrida debe ser suficientemente larga como para que las medidas no estén dominadas por el arranque, y el transitorio debe eliminarse antes de recolectar observaciones.

Las medidas de rendimiento se separan en dos grupos, según cómo se calcula el estimador dentro de cada corrida:

| Tipo | Medidas | Estimador por corrida |
|:---|:---|:---|
| Promedio temporal | $\bar C$, $\rho$, $L_s$, $L_q$, $\rho_q$ | $\frac{1}{T_c}\int_0^{T_c} X(t)\,dt$ (área bajo la curva / tiempo) |
| Promedio por observación | $W_q$, $W_s$ | $\frac{1}{n}\sum_{i=1}^{n} X_i$ (promedio sobre pacientes) |

En ambos casos, $T_c$ es la **ventana de recolección** que queda después de descartar el transitorio y $n$ es la cantidad de valores (visitas o muestras) incluidos en esa ventana. En las medidas por observación se consideran solo las visitas completas dentro de la ventana; las que quedan en curso al inicio o al final se excluyen para no censurar el tiempo. Cada corrida produce **una sola observación por medida**: el estadístico calculado sobre su ventana de recolección. Las $M$ corridas producen las $M$ observaciones que se usan para estimar el valor esperado y construir el intervalo de confianza.

La ley de Little se mantiene como control interno de cada corrida: $L_s \approx \lambda_{eff} W_s$ y $L_q \approx \lambda_{eff} W_q$.

### Método para reunir observaciones

Se adopta el **método de réplicas**. Cada réplica es una corrida independiente, con su propia semilla, las mismas condiciones iniciales y la misma longitud $T$. De cada una se obtiene una observación por medida, de modo que las $M$ observaciones son independientes **por construcción** y el teorema central del límite se aplica directamente a su media. No es necesario modelar la autocorrelación interna de una corrida para construir el intervalo de confianza: la independencia está garantizada entre réplicas, no dentro de ellas.

Esto también prepara las etapas siguientes. Las **variables antitéticas** requieren pares de corridas (una con $U$ y otra con $1-U$), y la **comparación entre modelos con números aleatorios comunes** requiere usar la misma semilla réplica a réplica. En ambos casos la estructura de réplicas es la que permite formar los pares y emparejar las observaciones.

El procedimiento es:

1. Elegir $M$ semillas independientes $s_1, \dots, s_M$ (o flujos de números aleatorios independientes).
2. Para cada réplica $j$, inicializar el sistema en el mismo estado, correr hasta $T$, descartar los primeros $d_T$ y recolectar las estadísticas en $T_c = T - d_T$.
3. Guardar el vector de medidas de la réplica $j$, con un valor por medida.
4. Estimar cada medida con la media de sus $M$ observaciones y construir el intervalo de confianza a partir de su desvío estándar.

No se agrupan los pacientes de todas las réplicas como si fueran una sola muestra: primero se calcula el estadístico de cada réplica y recién después se promedian las réplicas. De lo contrario se ignoraría la dependencia dentro de cada corrida y se subestimaría la varianza.

> Alternativa descartada: el método de lotes divide una única corrida larga en lotes y trata las medias de lote como observaciones. Sus observaciones están correlacionadas y la independencia es solo aproximada; además, obliga a una sola corrida larga, lo que dificulta el emparejamiento que necesitan las variables antitéticas y los números aleatorios comunes.

### Eliminación del transitorio

**Condiciones iniciales:** Todas las réplicas arrancan con el sistema vacío, sin pacientes en cola y con las $5$ camas y el quirófano libres. Es el estado más simple de inicializar, se reproduce igual en todas las réplicas y no introduce valores arbitrarios.

Sin embargo, un hospital real nunca comienza vacío: Shannon usa justamente el ejemplo de un hospital que, al abrir, tarda en alcanzar su ocupación habitual. Por eso el período inicial no representa el régimen permanente y debe descartarse; de lo contrario se subestiman la cola, la espera y la ocupación.

**Método:** Se usa el **promedio móvil de ventana fija** (Emshoff y Sisson, descrito por Shannon). Se ejecutan $K$ réplicas piloto y, para cada instante $t$, se promedia la medida entre réplicas:

$$
\bar Y(t) = \frac{1}{K}\sum_{k=1}^{K} Y_k(t)
$$

Luego se calcula el promedio móvil de ventana $w$:

$$
\bar Y_j(w) = \frac{1}{w}\sum_{i=j-w+1}^{j} \bar Y_i
$$

y se grafica $\bar Y_j(w)$ en función de $j$. El punto $j^{*}$ a partir del cual la serie se estabiliza alrededor de un nivel, sin tendencia, define el descarte $d_T = j^{*}$. Se monitorea la medida más variable, $L_q$ o $N(t)$, porque es la que más tarda en estabilizarse; si esa se estabiliza, las menos variables deberían hacerlo antes. De todos modos, se verifica el criterio sobre cada medida.

Shannon recomienda descartar **la misma cantidad** $d_T$ en todas las corridas, y no elegir un mínimo distinto para cada una. Así se evita seleccionar corridas afortunadas y se mantiene la comparabilidad. En consecuencia, la ventana de recolección es la misma $T_c$ para todas las réplicas.

No existe un método infalible para fijar el transitorio: la elección de $w$ y el punto de estabilización son juicios sobre una gráfica, y distintas ventanas pueden sugerir valores algo distintos de $d_T$. Se reportarán la ventana usada y el criterio adoptado, y se verificará que un cambio razonable de $w$ no altere sustancialmente las conclusiones. El valor definitivo de $d_T$ queda **pendiente** de las corridas piloto.

Para el modelo alternativo que se planteará más adelante se usarán **las mismas condiciones iniciales** (sistema vacío) y el mismo criterio de truncamiento que en el modelo original. De ese modo, la comparación entre ambos modelos no queda contaminada por un arranque distinto.

### Precisión y confianza

Se fija un nivel de significación $\alpha = 0,05$, es decir, intervalos de confianza del $95\%$. Para cada medida $k$, la precisión deseada se expresa como un porcentaje de su propia media:

$$
d_k = p_k \, \bar X_k
$$

donde $p_k$ es la precisión relativa buscada ($0,05$ para un $5\%$, por ejemplo) y $\bar X_k$ es la media estimada de la medida en el piloto. Trabajar con $d$ relativo es necesario porque las medidas tienen escalas muy distintas: no es lo mismo exigir media hora de precisión en $W_q$ que en $L_q$.

Con $M$ réplicas, el intervalo de confianza para la media de la medida $k$ es:

$$
\bar X_k \pm t_{\alpha/2;\,M-1}\,\frac{S_k}{\sqrt{M}}
$$

donde $S_k$ es el desvío estándar de las $M$ observaciones. La semianchura del intervalo debe cumplir:

$$
t_{\alpha/2;\,M-1}\,\frac{S_k}{\sqrt{M}} \le d_k
$$

Los valores de $p_k$ se proponen inicialmente en $5\%$ para todas las medidas y se ajustan después del piloto según la variabilidad observada. En particular, si $L_q$ resulta muy variable, puede convenir relajar su precisión relativa o fijarle una cota absoluta mínima. La precisión definitiva de cada medida queda **pendiente** hasta conocer el piloto.

### Número de corridas y longitud

El planeamiento distingue dos tamaños de muestra: $n$, la cantidad de valores que componen cada observación, y $M$, la cantidad de observaciones independientes (réplicas).

**Cálculo de $n$.** Al no conocer la distribución de la población ni su desvío, se usa la desigualdad de **Chebyshev**, que no requiere normalidad. Para la media de $n$ valores independientes, con desvío $\sigma$:

$$
P\left(|\bar X - \mu| \ge d\right) \le \frac{\sigma^2}{n\,d^2}
$$

Si se escribe $d = b\,\sigma$, la cota queda $1/(n b^2)$. Igualando a $\alpha$:

$$
n = \frac{1}{\alpha\,b^2}
$$

Por ejemplo, con $\alpha = 0,05$ y $b = 1/4$ se obtiene $n = 320$, el mismo valor que en la tabla 5.1 de Shannon. La siguiente tabla resume la relación:

| $b$ | $n$ con $\alpha = 0,05$ |
|:---:|:---:|
| $1/2$ | $80$ |
| $1/3$ | $180$ |
| $1/4$ | $320$ |
| $1/5$ | $500$ |

Como $\sigma$ es desconocido, en la práctica se estima con el desvío del piloto y se fija $b = d/\hat\sigma$. Si $d$ es relativo, $b = p\,\bar X/\hat\sigma = p/\widehat{CV}$: cuanto mayor sea el coeficiente de variación, más valores se necesitan para la misma precisión relativa. El valor final de $n$ queda **pendiente** del piloto.

La interpretación de $n$ depende de la medida: para $W_q$ y $W_s$ es la cantidad de visitas incluidas en la ventana de recolección; para las medidas temporales es la cantidad de muestras o lotes de tiempo con que se aproxima la integral. En las medidas temporales, la independencia que supone Chebyshev es aproximada, por lo que conviene usar muestras suficientemente separadas o lotes lo bastante largos como para que la autocorrelación sea despreciable.

**Cálculo de $M$.** Con una corrida piloto de $m$ réplicas (es decir, $m$ observaciones independientes) se obtiene $S_{\bar X}$, el desvío estándar de las medias observadas. Despejando $M$ de la condición de precisión:

$$
M = \left(\frac{t_{\alpha/2;\,m-1}\,S_{\bar X}}{d}\right)^2
$$

Si $M > m$, se ejecutan las réplicas adicionales hasta completar $M$; si $M \le m$, el piloto ya alcanza, aunque lo habitual es completar el número calculado. Como $d$ es relativo, la medida que exige más réplicas es la de mayor variabilidad relativa $S_{\bar X}/(p\,\bar X)$; si las medidas arrojan valores distintos de $M$, se toma el máximo. Shannon señala que, cuando hay varias medidas, manda la de mayor variabilidad. Los valores de $M$ por medida quedan **pendientes** del piloto:

| Medida | $\bar X$ piloto | $S_{\bar X}$ piloto | $d$ | $M$ |
|:---|:---:|:---:|:---:|:---:|
| $\bar C$ | pendiente | pendiente | pendiente | pendiente |
| $\rho$ | pendiente | pendiente | pendiente | pendiente |
| $L_s$ | pendiente | pendiente | pendiente | pendiente |
| $L_q$ | pendiente | pendiente | pendiente | pendiente |
| $W_q$ | pendiente | pendiente | pendiente | pendiente |
| $W_s$ | pendiente | pendiente | pendiente | pendiente |
| $\rho_q$ | pendiente | pendiente | pendiente | pendiente |

**Longitud de la corrida.** La longitud total es $T = d_T + T_c$, con $d_T$ el transitorio descartado y $T_c$ la ventana de recolección. La ventana debe ser lo bastante larga como para contener los $n$ valores que exige cada observación. Para $W_q$ y $W_s$, una estimación preliminar es:

$$
T_c \approx \frac{n}{\lambda_{eff}} = \frac{320}{0,205} \approx 1.560 \ \text{h} \approx 65 \ \text{días}
$$

valor que se ajustará con el $n$ definitivo del piloto. Para las medidas temporales, $T_c$ debe contener además suficientes muestras o lotes; la resolución temporal $\Delta t$ se elige de modo que el error de discretización de la integral sea despreciable. La longitud $T$ debe ser **la misma en todas las réplicas** para que las observaciones sean idénticamente distribuidas. El esfuerzo total de simulación es del orden de $M \times T$; tanto $T_c$ como $T$ quedan **pendientes** de las corridas piloto.

Como resumen, las decisiones experimentales son:

| Parámetro | Valor o expresión | Estado |
|:---|:---|:---|
| Tipo de simulación | no terminante, régimen permanente | definido |
| Método de observaciones | réplicas independientes | definido |
| Transitorio | promedio móvil de ventana fija; descarte igual en todas las réplicas | método definido, $d_T$ pendiente |
| Condiciones iniciales | sistema vacío | definido |
| $\alpha$ | $0,05$ | definido |
| $d$ | $p\,\bar X$, con $p$ relativo | $p$ pendiente |
| $n$ | $1/(\alpha b^2)$ | $b$ pendiente |
| $M$ | $\left(t_{\alpha/2;m-1} S_{\bar X}/d\right)^2$ | pendiente |
| $T$ | $d_T + T_c$, con $T_c \approx n/\lambda_{eff}$ | pendiente |
