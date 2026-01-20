# Documentación del Proyecto: Sistema de Aparcamiento Autónomo en Webots

Este documento describe la arquitectura y el funcionamiento del código implementado para la simulación de un sistema de aparcamiento utilizando Webots y Python.

## 1. Visión General

El proyecto simula un entorno de aparcamiento con un pasillo central y plazas de aparcamiento situadas a la derecha. El sistema consta de dos componentes principales de control:

1.  **Supervisor (`control_parking.py`)**: Gestiona el entorno, conoce la ubicación "real" de las plazas y envía la información del mapa al coche.
2.  **Controlador del Coche (`parking_logger.py`)**: Controla el vehículo BMW X5, gestiona sus sensores (GPS, Lidar) y ejecuta la lógica de movimiento.

---

## 2. Supervisor (`control_parking.py`)

El supervisor actúa como la "infraestructura inteligente" del parking. No controla el robot físicamente, sino que facilita información.

### Funcionalidades Clave

*   **Definición de Plazas**: Mantiene una lista de coordenadas (X, Z) para las 6 plazas de aparcamiento (P1 a P6).
    *   **Coordenadas**: Se utiliza el sistema de coordenadas estándar de Webots donde **X** es el eje longitudinal (avance) y **Z** es el eje lateral.
*   **Mapa de Plazas**: Al inicio, envía un mensaje JSON al coche con el "Mapa" de las plazas.
    *   Formato: `{'type': 'SPOT_MAP', 'spots': [...]}`.
*   **Recepción de Mensajes**: Escucha mensajes del coche (aunque en la versión simplificada actual, el coche apenas envía datos).

### Estructura del Código

*   `SPOTS_CONFIG`: Lista constante con la configuración de las plazas (ID, Lado, X, Z).
*   `get_translation_xz(node)`: Función auxiliar para extraer las coordenadas reales de los nodos en el mundo.
*   **Bucle Principal**:
    *   Envía el mapa periódicamente hasta recibir confirmación (`ACK`).
    *   Procesa mensajes entrantes (`recv_all_json`).

---

## 3. Controlador del Coche (`parking_logger.py`)

Este es el script principal que gobierna el comportamiento del robot.

### Configuración del Vehículo

*   **Sensores**:
    *   **GPS**: Se utiliza para conocer la posición exacta (X, Z) del vehículo en el mundo.
    *   **Lidar**: (Habilitado pero no utilizado en la lógica de movimiento actual) Sensor láser para detectar obstáculos.
    *   **Receptor/Emisor**: Para comunicación con el Supervisor.
*   **Actuadores**:
    *   `Driver`: Interfaz de alto nivel de Webots para controlar dirección y velocidad.

### Lógica de Control (Versión Actual)

El comportamiento se ha simplificado para cumplir con el requisito de **movimiento recto y parada de seguridad**.

1.  **Inicialización**: Se activan los sensores y se establece el paso de tiempo (`timestep`).
2.  **Bucle de Control**:
    *   **Lectura de GPS**: Se obtienen las coordenadas `(x, z)`.
    *   **Comprobación de Seguridad (Muro)**:
        *   Se verifica si la coordenada X supera el límite de seguridad (`12.0`).
        *   Si `X > 12.0`: El coche detecta que se acerca al final del pasillo y se detiene (`Speed = 0`).
        *   Si `X <= 12.0`: El coche avanza a velocidad constante (`Speed = 5.0`) con dirección recta (`Steering = 0`).

### Notas sobre el Sistema de Coordenadas

*   **Eje X**: Dirección de avance del pasillo. El coche empieza en X negativo y avanza hacia X positivo.
*   **Eje Z**: Dirección lateral. El centro del pasillo es Z=0. Las plazas están en Z positivo (+3.5).
*   El código ha sido corregido para usar explícitamente `gps_vals[0]` (X) y `gps_vals[2]` (Z), ignorando la altura (Y).

---

## 4. Archivos del Proyecto

*   `controllers/control_parking/control_parking.py`: Código fuente del Supervisor.
*   `controllers/parking_logger/parking_logger.py`: Código fuente del Controlador del Coche.
*   `worlds/parking_v1.wbt`: Archivo del mundo de Webots.

## 5. Ejecución

Para ejecutar la simulación:
1.  Abrir `worlds/parking_v1.wbt` en Webots.
2.  Asegurarse de que el controlador del robot `BMW X5` está asignado a `parking_logger` y el `Robot` supervisor a `control_parking`.
3.  Pulsar **Play**.
