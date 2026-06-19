
# Simulación: TP Final

Equipo:

- Aita Jerónimo
- Mactavish Tomás
- Francis Rojas

Docentes:

- Franco Lorena
- Bonesi Matías

## Trabajo en el repositorio

Documentado en [REPO](REPO.md)

## Consigna

~~~
Seleccionar un modelo o sistema que tenga varios servidores, que estén conectados en serie y en paralelo. Tendrán que contextualizar y explicar su funcionamiento.

El sistema considerado debe ser un sistema real del cual puedan demostrar y obtener los datos de las variables exógenas o bien obtener la información a través de alguna fuente pública de internet.

Antes de continuar con el resto del trabajo la idea deberá ser presentada y aprobada por la cátedra.

Fecha máxima de presentación de tema a aprobar 10-09-26.

La idea clave del trabajo integrador es que puedan aplicar todo lo que vamos a ir viendo en la materia de Simulación. Por lo tanto, a medida que avancemos en los temas, van a tener que ir presentando los avances.
~~~

## Sistema

Nuestro equipo trabajará sobre **la internación de pacientes en un hospital**.

Bajo el contexto de un centro de salud que presta hospitalización, el mismo posee un determinado conjunto finito de camas.

Cuando un médico considera que un paciente requiere hospitalización, genera una **orden de internación** para ese paciente. Esto habilita al personal de enfermería asignarlo a una **cama** entre las disponibles.

**De no haber camas disponibles**, el paciente retendría la orden de internación, pudiendo optar por atenderse en otro centro de salud.

Los pacientes ocupan la cama a la que fueron asignados por un cierto periodo de tiempo, pudiendo ser horas o días.
También pueden ocurrir **pases de cama**, en caso de ser necesario trasladar al paciente de una habitación a otra.

Luego de cierto tiempo, el médico responsable emite un **alta**, que habilita al personal de enfermería registrar el **egreso** del paciente, dejando libre la cama que ocupaba.

> [!note] Extra: Quirófano
>
> Además, según el cuadro clínico del paciente, el médico puede indicar la necesidad de realizar una operación.
> La misma requiere pasar al paciente de una cama (periodo de preparación pre-quirúrgica) al quirófano; una sala especial en la que el paciente podría pasar entre minutos y horas.
> Luego de la operación, el paciente volvería a una cama (periodo de reposo post-quirúrgico) hasta recibir el alta.

## Modelo

Para analizar este sistema, podemos modelarlo utilizando la **Teoría de colas** con las siguientes reglas:

- Un paciente es una entidad - cliente.
- La orden de internación de un paciente es su llegada al sistema.
- Una cama es un servidor.
- La llegada de un paciente es aleatoria, siguiendo una distribución exponencial en el tiempo (en cuanto avance el tiempo, la probabilidad de llegada de un paciente crece exponencialmente).
- El egreso de un paciente es aleatorio, siguiendo una distribución exponencial.

Bajo la notación de Kendall, sería un modelo multi-servidor de cola infinita y fuente infinita: `(M|M|c):(GD|\infty|\infty)`.

