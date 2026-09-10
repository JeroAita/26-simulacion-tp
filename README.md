
# Simulación: TP Final

Equipo:

- Aita Jerónimo
- Mactavish Tomás
- Rojas Francis

Docentes:

- Franco Lorena
- Bonesi Matías

---

## Trabajo en el repositorio

Documentado en [REPO](REPO.md)

---

## Consigna

Seleccionar un modelo o sistema que tenga varios servidores, que estén conectados en serie y en paralelo. Tendrán que contextualizar y explicar su funcionamiento.

El sistema considerado debe ser un sistema real del cual puedan demostrar y obtener los datos de las variables exógenas o bien obtener la información a través de alguna fuente pública de internet.

Antes de continuar con el resto del trabajo la idea deberá ser presentada y aprobada por la cátedra.

Fecha máxima de presentación de tema a aprobar 10-09-26.

La idea clave del trabajo integrador es que puedan aplicar todo lo que vamos a ir viendo en la materia de Simulación. Por lo tanto, a medida que avancemos en los temas, van a tener que ir presentando los avances.

## Sistema

Nuestro equipo propone trabajar sobre **la internación de pacientes en un hospital**.

Bajo el contexto de un centro de salud que presta servicio de hospitalización, las instalaciones poseen un determinado conjunto finito de **camas**.

Cuando un médico considera que un paciente requiere hospitalización, genera una **orden de internación** para ese paciente. Esto habilita al personal de enfermería para asignarlo a una cama entre las disponibles.

**De no haber camas disponibles**, el paciente retendría la orden de internación hasta que sea liberada una cama.

Los pacientes ocupan la cama a la que fueron asignados por un cierto periodo de tiempo, pudiendo ser horas o días.
También pueden ocurrir **pases de cama**, en caso de ser necesario trasladar al paciente de una habitación a otra.

Luego de cierto tiempo, el médico responsable emite un **alta**, que habilita al personal de enfermería registrar el **egreso** del paciente, dejando libre la cama que ocupaba.

Además, según el cuadro clínico del paciente, el médico puede indicar la necesidad de realizar una operación.
La misma requiere pasar al paciente de una cama (periodo de preparación pre-quirúrgica) al **quirófano**; una sala especial en la cual el paciente podría pasar entre minutos y horas.

Luego de la operación, el paciente volvería a una cama (periodo de reposo post-quirúrgico) hasta recibir el alta.

## Modelo

Para analizar este sistema, podemos modelarlo utilizando la **Teoría de colas** con las siguientes reglas:

- Un paciente es una entidad/cliente.
- El evento "Orden de internación" es la llegada de un paciente al sistema. Queda encolado hasta que ocurre el evento "Ingreso", que lo ubica en una cama.
- Una cama es un servidor.
- Existe una cama especial llamada quirófano, en serie con todas las camas. Se llega al quirófano y se sale del quirófano mediante un evento "Pase de cama". Salir del quirófano implicaría volver a la cola original, pero siempre se retorna a una cama. Por lo tanto, se tiene una cola con prioridades.
- La llegada de un paciente es aleatoria, siguiendo una distribución desconocida.
- El egreso de un paciente es aleatorio, siguiendo una distribución desconocida.
- Desestimaremos los eventos "Pase de cama" que sean entre camas regulares, ya que este tipo de evento no altera la cantidad total de servidores en paralelo ocupados.

Bajo la notación de Kendall, sería un modelo multi-servidor de cola infinita y fuente infinita: 

$$
(GD|GD|c):(GD|\infty|\infty)
$$

![](docs/simulacion-tp_final-diagrama_modelo.png)

Con este modelo sabemos que:

- La tasa de llegada efectiva es igual a la tasa de llegada, porque la cola es infinita: $\lambda_{eff} = \lambda_n$
- La tasa de llegada no depende del estado del sistema: $\lambda_n = \lambda$
- La tasa de salida del sistema escala con la tasa de salida de los servidores y de la cantidad de servidores ocupados: $\mu_n = n \cdot \mu$ (si $n \leq c$) o $\mu_n = c \cdot \mu$ (si $n > c$, todos los servidores ocupados).

## Muestras y análisis preliminar

Tomamos 9016 registros de base de datos del centro de salud, descartando datos personales y sensibles. Cada registro corresponde a un **evento** que relaciona a un paciente con un tipo de evento, una cama y una fecha-hora. Existen los eventos de tipos:

- Orden de internación
- Ingreso
- Pase de cama
- Alta médica
- Egreso

![](docs/simulacion-tp_final-muestras.png)

Aquí vemos que existen $75$ camas distintas (75 `cama_id`s distintos, por más que los IDs estén en el orden de los doscientos). De aquí podemos tomar $c = 74$ camas regulares en paralelo.
Identificamos que la cama quirófano es aquella con `cama_id` `241` desde el sistema, pero además puede verse que a esta cama en particular los pacientes llegan únicamente a través de pases de cama.

### Llegadas

Filtramos los eventos de tipo Orden de internación con el objetivo de analizar las llegadas al sistema y comprender el periodo entre ellas:

![](docs/simulacion-tp_final-muestras-2.png)

Teniendo $n = 1922$ eventos de tipo Orden de internación, calculamos la media muestral y el desvío estándar:

- $$\bar x = \frac{ \sum_{i=1}^{n}{ x_i } }{n} \approx 0,917 \frac{\text{horas}}{\text{paciente}}$$
- $$s = \sqrt{ \frac{ \sum_{i=1}^{n}{ (x_i - \bar x)^2 } }{n-1} } \approx 1,422 \frac{\text{horas}}{\text{paciente}}$$

Esto nos da paso a estimar la **tasa de llegada** como $\lambda = \frac{1}{\bar x} \approx 1,09 \frac{\text{pacientes}}{\text{hora}}$

Al ser la variable aleatoria la cantidad de tiempo entre evento y evento, sabemos que es no-negativa. Por lo tanto, no correspondería a una distribución normal.
Realizamos la **prueba de bondad de ajuste Xi Cuadrado** para analizar si las muestras se ajustan a una distribución exponencial.

> *Nota conceptual*
> Utilizamos la prueba de Xi Cuadrado en lugar de la prueba de Kolmogorov-Smirnov porque poseemos una gran cantidad de muestras. La alternativa mencionada se utiliza en situación de poseer menos o cerca de 30 muestras.

Planteamos como hipótesis nula $H_0$ que las muestras corresponden a una distribución exponencial con media $0,917$, y como hipótesis alternativa, que corresponden a otra distribución. Tomamos un nivel de significancia $1 - \alpha = 90\%$.
Tomamos $k = \sqrt{n} \approx  43$ intervalos equiprobables, de frecuencias esperadas $F_e = \frac{n}{k} \approx 44,7$. Calculamos los límites de los intervalos a partir de la función de probabilidad acumulada:

$$
\begin{aligned}
F(x) &= 1-e^{- \lambda x} \\
\frac{1}{x_i} &= 1-e^{- \lambda x} \\
x_i &= -\frac{1}{\lambda} \cdot \ln \left( 1 - \frac i k \right) \\
x_i &= -0,917 \cdot \ln \left( 1 - \frac{i}{43} \right)
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
| $\inf$ | 98 |

Calculamos el estimador:

$$
\chi^2 = \sum{ \frac{(F_o - F_e)^2}{F_e}} \approx 2695,5
$$

Comparamos con el estimador tabulado: $\chi^2_{\alpha, k} = \chi^2_{0,10, 42} \approx 52,95$

Vemos que el $\chi^2$ calculado es ampliamente superior al $\chi^2$ tabulado, por lo que rechazamos la $H_0$ con un nivel de confianza del 90%; la distribución de entradas no es exponencial.

Detalles a considerar:

- El primer intervalo, $(0; \ 0,022)$ (periodos de menos de 1,3 minutos entre entradas) aporta $(F_o - F_e)^2}{F_e} = 2455,6$ al estadístico, es decir, casi la totalidad del peso de los resultados.
- Los intervalos intermedios respetan una alineación equilibrada más próxima a la distribución esperada.
- El último intervalo, $(3,449; \ \inf)$ (entradas cada más de 3,5 horas) son el siguiente gran aporte al estadístico.

Esto sugiere que el proceso de llegadas al sistema no es homogéneo, sino que podría ser una mezcla entre:

- Llegadas "reales" de pacientes, espaciadas, más similares a una exponencial.
- Órdenes de internación cargadas en conjunto, casi simultáneamente, quizás por el mismo usuario o al inicio de determinado turno.
- Periodos de más de 3,5 horas sin cargas de internaciones, quizás por caídas del sistema, parálisis administrativa de la institución o demás factores externos.

Si bien se rechazó la hipótesis de que las llegadas siguen una distribución exponencial, la media $\lambda = 1,09 \frac{\text{pacientes}}{\text{hora}}$ sigue siendo válida como estimador de la tasa de llegadas, ya que se deriva directamente de la media muestral. La misma será utilizada como parámetro descriptivo del proceso GD en el modelo de colas.

### Salidas

(Repetimos el procedimiento para analizar las salidas del sistema...)

## Análisis de modelo de colas

(...)

## Simulación

(...)