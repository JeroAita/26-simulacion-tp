---
title: 'Análisis de llegadas - Chi Cuadrado'
---

Se registraron $355$ llegadas de pacientes a alguna de las camas del sub-sistema, siendo el $86\%$ pases de cama desde una cama regular externa. Con ello, tenemos $n = 354$ periodos entre las llegadas:

$$
\bar x = \frac{\sum_{i=1}^{n}{ x_i }}{n} \approx 4,95 \frac{\text{horas}}{\text{paciente}}
\ , \qquad
s = \sqrt {\frac{\sum_{i=1}^{n}{ (x_i - \bar x)^2 }}{n-1}} \approx 5,84 \frac{\text{horas}}{\text{paciente}}
$$
Por ende, estimamos la **tasa de llegada** como $\lambda = \frac{1}{\bar x} \approx 0,2 \frac{\text{pacientes}}{\text{hora}}$.

Realizamos una **prueba de bondad de ajuste Chi Cuadrado** para comprobar si la distribución se ajusta a una exponencial.

Planteamos como hipótesis nula $H_0$ que las muestras provienen de una población distribuída exponencialmente con media $4,95$, y como hipótesis alternativa, que corresponden a otra distribución. Tomamos un nivel de confianza $1-\alpha = 0,90$.

Tomamos $k = \sqrt n \approx 19$ intervalos equiprobables, de frecuencias esperadas $F_e = \frac n k = 18,63$. Calculamos los límites de los intervalos a partir de la inversa de la función de probabilidad acumulada:

$$
\begin{aligned}
&F(x) = 1-e^{- \lambda x} \\
&\Rightarrow F^{-1}(x) = -\frac{1}{\lambda} \cdot \ln \left( 1 - \frac i k \right)\\
&\Rightarrow x_i = -4,95 \cdot \ln \left( 1 - \frac{i}{19} \right)
\end{aligned}
$$

Luego los intervalos: $[x_0; \ x_1) = [0; \ 0,010)\, \ [x_1; \ x_2) = [0,010; \ 0,022)\, ...$ . Realizamos un conteo de las muestras incluídas en cada intervalo; las frecuencias observadas $F_o$.

| Límite superior $x_i$ | $F_o$ |
| :-------------------: | :---: |
|0,010|42|
|0,022 |24|
|0,034|17|
|0,047|11|
|0,061|21|
|0,076|19|
|0,091|11|
|0,109|19|
|0,128|15|
|0,149|16|
|0,173|18|
|0,200|19|
|0,231|12|
|0,267|21|
|0,312|18|
|0,369|13|
|0,450|20|
|0,589|11|
|$\infty$|27|

Calculamos el estimador:

$$
\chi^2 = \sum{ \frac{(F_o - F_e)^2}{F_e}} \approx 49,21
$$

Poseemos $k-1-1 = 17$ grados de libertad; restamos uno al haber estimado la media a partir de la muestra. Luego el estimador tabulado:

$$
\chi^2_{\alpha, \, k-1-1} = \chi^2_{0,10, \ 17} \approx 24,77
$$

Vemos que el $\chi^2$ calculado es superior al $\chi^2$ tabulado, por lo que rechazamos la $H_0$ con un nivel de confianza del 90%; la distribución de entradas no es exponencial.