## Resultados y propuesta de optimización

### Resultados e IC

Habiendo determinado el número y longitud de corridas, se ejecutan y se extraen los datos.

Corrida | $W_s$ | Corrida | $W_s$
--- | --- | --- | ---
1 | 21,052 | 24 | 72,456
2 | 17,738 | 25 | 32,940
3 | 16,470 | 26 | 21,217
4 | 38,222 | 27 | 17,846
5 | 21,760 | 28 | 23,305
6 | 21,782 | 29 | 18,436
7 | 17,546 | 30 | 15,306
8 | 30,132 | 31 | 35,613
9 | 30,124 | 32 | 13,543
10 | 24,155 | 33 | 15,910
11 | 23,949 | 34 | 19,706
12 | 39,570 | 35 | 20,472
13 | 26,748 | 36 | 15,747
14 | 40,501 | 37 | 14,348
15 | 15,610 | 38 | 27,344
16 | 63,488 | 39 | 43,019
17 | 40,195 | 40 | 39,283
18 | 21,006 | 41 | 58,299
19 | 19,936 | 42 | 19,041
20 | 35,530 | 43 | 45,374
21 | 19,419 | 44 | 20,301 
22 | 17,710 | 45 | 18,121
23 | 22,870 | 46 | 18,077


Luego:

$$
\bar {W_s} = 27,2\ h \ , \qquad S_{\bar {W_s}} = 13,4
$$
Intervalo de confianza con $\alpha = 10\%$:

$$
IC
= \bar{W_s} \pm \frac{ z_{\alpha / 2} \cdot S_{\bar{W_s}} }{ \sqrt{46} }
= (23,89; \ 30,51)h
$$

### Modelo alternativo

Proponemos añadir dos servidores en paralelo ($c=7$ en total) al modelo con el objeto de medir su efecto sobre el sistema.

Realizamos simulaciones con el sistema modificado y con las mismas semillas réplica a réplica (método de **números aleatorios comunes**). Luego, pondremos a prueba si esta modificación resulta en una reducción del tiempo esperado de los clientes en el sistema.

Resultados:

Corrida | $W_s$ | Corrida | $W_s$
--- | --- | --- | ---
1 | 16,42 | 24 | 18,94
2 | 16,33 | 25 | 19,41
3 | 14,69 | 26 | 16,65
4 | 19,61 | 27 | 14,71
5 | 16,47 | 28 | 17,30
6 | 17,38 | 29 | 16,10
7 | 16,11 | 30 | 14,95
8 | 16,98 | 31 | 21,12
9 | 19,64 | 32 | 13,25
10 | 18,35 | 33 | 14,49
11 | 18,49 | 34 | 18,00
12 | 21,35 | 35 | 18,47
13 | 18,09 | 36 | 14,11
14 | 22,42 | 37 | 14,06
15 | 14,56 | 38 | 17,40
16 | 23,65 | 39 | 17,19
17 | 21,63 | 40 | 21,63
18 | 17,17 | 41 | 17,55
19 | 17,17 | 42 | 16,88
20 | 21,94 | 43 | 20,96
21 | 16,80 | 44 | 15,47
22 | 16,52 | 45 | 15,79
23 | 15,95 | 46 | 16,08

$$
\bar {W_s^A} = 17,57\ h \ , \qquad S_{\bar {W_s^A}} = 2,48
$$
$$
IC^A
= \bar{W_s^A} \pm \frac{ z_{\alpha / 2} \cdot S_{\bar{W_s^A}} }{ \sqrt{46} }
= (16,95; \ 18,18)h
$$

A priori, vemos una reducción del $35\%$ en la esperanza de tiempo que los clientes pasan en el sistema.

### Test de hipótesis

Para validar estadísticamente la diferencia observada entre el modelo original y la alternativa propuesta, hacemos un test sobre las diferencias $D_i = W_{s,\ i} - W_{s,\ i}^A$. Definimos $\mu_D = E[W_s - W_s^A]$ y planteamos las hipótesis:

- $H_0: \ \mu_D \leq 0 \ (W_s^A \geq W_s)$ 
- $H_1: \ \mu_D > 0$

Utilizamos $\alpha = 5\%$.

$$
\bar D = 27,20 - 17,57 = 9,63\ h, \qquad S_D = 11,69
$$
El estadístico de prueba:

$$
z = \frac{\bar D}{S_D / \sqrt{46}} = 5,59
$$

El valor crítico:

$$
z_\alpha = z_{0,05} = 1,645
$$

Como el estadístico es mayor que el valor crítico, **se rechaza $H_0$**.

En conclusión, existe evidencia suficiente para determinar que **añadir dos servidores al sistema reduce el tiempo esperado de los clientes en el sistema**.

---

## Conclusión

El sub-sistema actual funciona cerca de su capacidad, y la variabilidad real de llegadas y estadías hace que los tiempos en el sistema sean más altos e irregulares de lo que predice la teoría clásica de colas. Agregar dos camas reduce de forma estadísticamente significativa y consistente el tiempo esperado en el sistema, al punto de eliminar prácticamente la espera, a costa de una menor utilización. La decisión final sobre la cantidad de camas debería sopesar este beneficio contra el costo de la capacidad adicional.

---

## Bibliografía

- Simulación, Sheldon M. Ross
- Investigación de Operaciones, Hamdy A. Taha