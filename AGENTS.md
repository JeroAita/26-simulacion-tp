
# AGENTS.md

## Contexto

Este repositorio es para trabajar sobre el trabajo práctico final de una asignatura universitaria llamada Simulación.

En la misma, vemos Teoría de Colas y su aplicación.

## Repositorio

### Convenciones

Las convenciones de desarrollo se documentan en `docs/REPO.md`.

### Skills

`./opencode/skills/`

En este directorio se almacenan *skills*: archivos escritos en Markdown que funcionan como "programas" para los agentes de IA.

### Planes

`./opencode/plans/`

En este directorio se almacenan *planes*: archivos escritos en Markdown que describen diagnósticos sobre el código y/o planes de modificación de archivos del repositorio, a ejecutar por agentes de IA.

La convención principal es que los agentes de IA operen en modo "plan" al diagnosticar y planficar cambios, los escriban en este directorio como un archivo `yyyy-mm-dd-plan-(titulo).md` y luego pasen a modo "build".
Únicamente en modo "build" deben modificar archivos, generalmente siguiendo las indicaciones del plan.

### Scripts

`scripts/`

En este directorio se almacenan scripts, inicialmente en Python.

