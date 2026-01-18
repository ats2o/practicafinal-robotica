# Verificación de sensores (Día 1 + inicio Día 2)

Objetivo: poder afirmar **"detecta obstáculos y los valores cambian de manera lógica"** con un setup mínimo y repetible.

## Sensores mínimos para esta fase

- **Lateral derecho (plazas):** 1 sensor tipo `DistanceSensor`.
- **Frontal (seguridad):** 1 sensor tipo `DistanceSensor`.

## Colocación correcta

### Lateral derecho

- **Altura:** 0.2–0.5 m (evita ir pegado al suelo).
- **Orientación:** 90° hacia la derecha del coche.
- **Rango:** 3–5 m (suficiente para ver dentro de la plaza).

### Frontal

- **Orientación:** hacia delante.
- **Rango:** 5–10 m (margen para frenado/seguridad).

> Si un sensor “ve el suelo” y da valores raros, revisa:
> - Está demasiado inclinado hacia abajo.
> - Está demasiado bajo.
> - El “ray” intersecta el suelo antes que el obstáculo.

## Test mínimo (controlador temporal)

En el controlador, por cada `timestep`:

1. Leer el sensor lateral derecho.
2. Leer el sensor frontal.
3. Imprimir ambos valores (opcional: posición del coche).

Ejemplo de salida esperada (formato libre):

```
t=12.3s | lateral=2.15m | frontal=6.80m | pos=(x=1.25, z=8.0)
```

### Prueba de coherencia

- **Coche quieto:** valores estables.
- **Acerca un obstáculo delante:** el valor del frontal disminuye de manera clara.
- **Acerca un obstáculo al lateral:** el valor del lateral disminuye de manera clara.

**Checkpoint:** hay relación clara distancia ↔ valor.
