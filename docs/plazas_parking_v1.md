# Definición de Plazas de Aparcamiento - Parking V1

Esta tabla define las coordenadas lógicas de las plazas de aparcamiento en el mundo `parking_v1.wbt`.
Las coordenadas están en el sistema de referencia global del mundo Webots (X, Y, Z).

**Eje Longitudinal (X)**: A lo largo del pasillo.
**Eje Lateral (Z)**: Profundidad de la plaza. El pasillo está en Z < 3.5. Las plazas están en Z > 3.5.
**Altura (Y)**: ~0.0 (Suelo).

| Plaza | X Min | X Max | X Centro | Z Min | Z Max | Punto de Entrada (Target) | Estado Inicial |
|-------|-------|-------|----------|-------|-------|--------------------------|----------------|
| **P1**| -12.0 | -8.0  | -10.0    | 3.5   | 5.5   | (-10.0, 2.0)             | Libre          |
| **P2**| -8.0  | -4.0  | -6.0     | 3.5   | 5.5   | (-6.0, 2.0)              | **Ocupado** (Obstáculo) |
| **P3**| -4.0  | 0.0   | -2.0     | 3.5   | 5.5   | (-2.0, 2.0)              | Libre          |
| **P4**| 0.0   | 4.0   | 2.0      | 3.5   | 5.5   | (2.0, 2.0)               | Libre          |
| **P5**| 4.0   | 8.0   | 6.0      | 3.5   | 5.5   | (6.0, 2.0)               | **Ocupado** (Obstáculo) |
| **P6**| 8.0   | 12.0  | 10.0     | 3.5   | 5.5   | (10.0, 2.0)              | Libre          |

## Notas de Implementación
- **Sensor Lateral**: Debe leer distancias en el rango Z positivo (derecha del vehículo).
- **Detección**:
    - Si `distancia` < 2.0m (aprox) -> Obstáculo detectado.
    - Si `distancia` > 3.0m (o max range) -> Plaza libre.
- **Vehículo**:
    - Inicio: x=-13.0, z=0.0.
    - Orientación: 0 rad (mirando hacia X positivo).
