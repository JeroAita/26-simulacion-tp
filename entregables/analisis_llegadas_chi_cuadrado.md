---
title: 'Análisis de llegadas - Chi Cuadrado'
---

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

Las frecuencias observadas $F_o$ en cada intervalo:

| Límite superior $x_i$ | $F_o$ |
| :-------------------: | :---: |
| $0,043$ | 219 |
| $0,087$ | 41 |
| $0,133$ | 32 |
| $0,179$ | 25 |
| $0,228$ | 25 |
| $0,278$ | 29 |
| $0,330$ | 22 |
| $0,384$ | 25 |
| $0,440$ | 26 |
| $0,498$ | 30 |
| $0,558$ | 24 |
| $0,621$ | 22 |
| $0,687$ | 34 |
| $0,756$ | 31 |
| $0,828$ | 24 |
| $0,904$ | 17 |
| $0,983$ | 35 |
| $1,068$ | 25 |
| $1,158$ | 17 |
| $1,253$ | 31 |
| $1,355$ | 31 |
| $1,465$ | 27 |
| $1,583$ | 33 |
| $1,712$ | 23 |
| $1,853$ | 35 |
| $2,009$ | 24 |
| $2,183$ | 29 |
| $2,380$ | 26 |
| $2,608$ | 31 |
| $2,878$ | 18 |
| $3,208$ | 26 |
| $3,634$ | 29 |
| $4,233$ | 21 |
| $\infty$ | 103 |

Calculamos el estimador:

$$
\chi^2 = \sum{ \frac{(F_o - F_e)^2}{F_e}} \approx 1183
$$

Poseemos $k-1-1 = 32$ grados de libertad; restamos uno al haber estimado la media a partir de la muestra. Luego el estimador tabulado:

$$
\chi^2_{\alpha, \, k-1-1} = \chi^2_{0,10, \, 32} \approx 42,58
$$

Vemos que el $\chi^2$ calculado es ampliamente superior al $\chi^2$ tabulado, por lo que rechazamos la $H_0$ con un nivel de confianza del 90%; la distribución de entradas no es exponencial.