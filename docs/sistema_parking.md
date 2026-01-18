# Sistema de aparcamiento autónomo (Webots)

Este proyecto está implementado **íntegramente en Webots** (sin ROS). Todo el comportamiento se define con un mundo `.wbt` y un controlador (Python o C). La lógica es **determinista**, basada en **sensores de distancia** y una **máquina de estados finitos (FSM)**.

## Componentes principales

### Mundo Webots (`.wbt`)

- **Vehículo:** un coche con ruedas, dirección tipo Ackermann y motores controlados por el controlador.
- **Sensores:** varios `DistanceSensor` ubicados para:
  - Detectar obstáculos frontales (seguridad de frenado).
  - Leer huecos laterales en las plazas (detección de ocupación).
- **Entorno:** plazas de parking y obstáculos simples (cajas/cilindros) que simulan coches estacionados.
- **Archivo base:** `worlds/parking.wbt` (creado en Webots y versionado en el repositorio).

### Controlador (Python o C)

El controlador ejecuta el bucle de control en cada `timestep` y gestiona:

1. **Lecturas de sensores**.
2. **Detección de ocupación de plazas** mediante umbrales de distancia.
3. **Selección de plaza objetivo**.
4. **Maniobra de aparcamiento automático** con FSM.

## Lógica de sensores

La ocupación de una plaza se decide por **umbral de distancia**:

- Si el sensor lateral detecta distancia **menor** que `UMBRAL_OCUPADO`, la plaza se considera **ocupada**.
- Si detecta distancia **mayor** que `UMBRAL_LIBRE`, la plaza se considera **libre**.
- Valores intermedios pueden tratarse como **zona gris** (mantener estado previo o usar histéresis).

> Recomendación: usar histéresis para evitar parpadeos por ruido, por ejemplo:
> - `UMBRAL_OCUPADO = 0.7 m`
> - `UMBRAL_LIBRE = 1.0 m`

## Escaneo de plazas

Durante la fase de escaneo:

1. El vehículo avanza por el pasillo.
2. Se toman lecturas laterales en cada zona de plaza.
3. Se etiqueta cada plaza como **libre** u **ocupada**.
4. Se guarda una lista con el estado de cada plaza.

## Selección de plaza objetivo

Una vez finalizado el escaneo:

- Se elige la **primera plaza libre** encontrada (estrategia simple).
- Alternativamente, se puede usar la plaza libre más cercana a la posición actual.

## FSM de aparcamiento automático

Ejemplo de estados mínimos:

1. **SCAN**: avanzar y escanear plazas.
2. **ALIGN**: posicionarse frente a la plaza objetivo.
3. **ENTER**: iniciar maniobra de giro hacia la plaza.
4. **PARK**: ajustar posición dentro de la plaza.
5. **STOP**: detener motores y finalizar.

Transiciones basadas en:

- Distancias medidas por sensores.
- Distancia al punto de entrada de la plaza.
- Ángulo de orientación del vehículo.

## Resultados esperados

- El coche identifica correctamente plazas libres/ocupadas.
- Selecciona una plaza libre.
- Realiza la maniobra de aparcamiento sin colisiones.
- No usa ML, visión ni planificadores externos: todo es **determinista**.
