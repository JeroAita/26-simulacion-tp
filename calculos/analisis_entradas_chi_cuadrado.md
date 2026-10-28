Teniendo $n = 1922$ eventos de tipo Orden de internación, calculamos la media muestral y el desvío estándar:

$$
\bar x = \frac{ \sum_{i=1}^{n}{ x_i } }{n} 
\approx 0,917 \frac{\text{horas}}{\text{paciente}} 
\, \qquad 
s = \sqrt{ \frac{ \sum_{i=1}^{n}{ (x_i - \bar x)^2 } }{n-1} } 
\approx 1,422 \frac{\text{horas}}{\text{paciente}}
$$

Por ende, estimamos la **tasa de llegada** como $\lambda = \frac{1}{\bar x} \approx 1,09 \frac{\text{pacientes}}{\text{hora}}$

Analizamos la distribución a la que se ajustan los periodos entre llegadas. Al ser la variable aleatoria la cantidad de tiempo entre evento y evento, sabemos que es no-negativa. Realizamos una **prueba de bondad de ajuste Chi Cuadrado** para probar si la distribución se ajusta a una exponencial. Utilizamos Chi Cuadrado en lugar de Kolmogorov-Smirnov porque poseemos una gran cantidad de muestras.

Planteamos como hipótesis nula $H_0$ que las muestras corresponden a una distribución exponencial con media $0,917$, y como hipótesis alternativa, que corresponden a otra distribución. Tomamos un nivel de confianza $1 - \alpha = 0,90$.

Tomamos $k = \sqrt{n} \approx  43$ intervalos equiprobables, de frecuencias esperadas $F_e = \frac{n}{k} \approx 44,7$. Calculamos los límites de los intervalos a partir de la inversa de la función de probabilidad acumulada:

$$
\begin{aligned}
&F(x) = 1-e^{- \lambda x} \\
&\Rightarrow F^{-1}(x) = -\frac{1}{\lambda} \cdot \ln \left( 1 - \frac i k \right)\\
&\Rightarrow x_i = -0,917 \cdot \ln \left( 1 - \frac{i}{43} \right)
\end{aligned}
$$

Luego los intervalos: $[x_0; \ x_1) = [0; \ 0,022)$, $[x_1; \ x_2) = [0,022; \ 0,044)$, ...

Las frecuencias observadas $F_o$ en cada intervalo:

| Límite superior $x_i$ | $F_o$ |
| :-------------------: | :---: |
| $0,022$ | 376 |
| $0,044$ | 82 |
| $0,066$ | 58 |
| $0,090$ | 50 |
| $0,113$ | 42 |
| $0,138$ | 34 |
| $0,163$ | 38 |
| $0,189$ | 45 |
| $0,215$ | 42 |
| $0,243$ | 31 |
| $0,271$ | 26 |
| $0,300$ | 26 |
| $0,330$ | 33 |
| $0,361$ | 31 |
| $0,393$ | 32 |
| $0,427$ | 30 |
| $0,461$ | 33 |
| $0,497$ | 36 |
| $0,535$ | 29 |
| $0,574$ | 39 |
| $0,615$ | 30 |
| $0,657$ | 28 |
| $0,702$ | 34 |
| $0,749$ | 30 |
| $0,799$ | 31 |
| $0,851$ | 29 |
| $0,907$ | 29 |
| $0,966$ | 38 |
| $1,029$ | 28 |
| $1,097$ | 28 |
| $1,170$ | 33 |
| $1,250$ | 36 |
| $1,338$ | 26 |
| $1,434$ | 21 |
| $1,542$ | 35 |
| $1,665$ | 26 |
| $1,806$ | 32 |
| $1,973$ | 41 |
| $2,178$ | 37 |
| $2,442$ | 38 |
| $2,813$ | 36 |
| $3,449$ | 45 |
| $\infty$ | 98 |

Calculamos el estimador:

$$
\chi^2 = \sum{ \frac{(F_o - F_e)^2}{F_e}} \approx 2695,5
$$

Poseemos $k-1-1 = 41$ grados de libertad restamos uno por haber estimado la media a partir de la muestra. Luego el estimador tabulado:

$$
\chi^2_{\alpha, \, k-1-1} = \chi^2_{0,10, \, 41} \approx 52,95
$$

Vemos que el $\chi^2$ calculado es ampliamente superior al $\chi^2$ tabulado, por lo que rechazamos la $H_0$ con un nivel de confianza del 90%; la distribución de entradas no es exponencial.