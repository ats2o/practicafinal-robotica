# Resumen de Configuración - Día 1

## Estado del Proyecto
Se ha completado la estructura inicial y el mundo de simulación `parking_v1.wbt` cumpliendo los requisitos del Día 1.

### Estructura de Archivos
- `worlds/parking_v1.wbt`: Mundo de Webots con pasillo, 6 plazas (P1-P6), y 2 obstáculos (en P2 y P5). Incluye vehículo Ackermann con sensores.
- `controllers/parking_logger/parking_logger.py`: Controlador simple en Python para verificar sensores.
- `docs/plazas_parking_v1.md`: Tabla con las coordenadas lógicas de las plazas.

### Instrucciones para Verificación
1. **Abrir el Mundo**:
   - Inicia Webots y abre `worlds/parking_v1.wbt`.
   - Verifica que veas el pasillo, las líneas de las plazas y los obstáculos.

2. **Ejecutar la Simulación**:
   - El vehículo debería cargar el controlador `parking_logger`.
   - Dale a **Play**.
   - Abre la **Consola** de Webots (Panel inferior).
   - Deberías ver logs tipo: `ds_front=0.000 ds_right=5.000` (valores variarán según posición).

3. **Prueba de Sensores**:
   - Mueve manualmente un obstáculo frente al coche (en pausa o marcha) para ver cambiar `ds_front`.
   - El sensor lateral `ds_right` debería detectar las paredes y los huecos de las plazas al avanzar.

### Notas Técnicas
- El vehículo es un `AckermannVehicle` usando los PROTOS estándar de Webots R2023b.
- Se han añadido `EXTERNPROTO` al inicio del archivo `.wbt` para garantizar compatibilidad.
- El controlador usa `ds_front` y `ds_right` como nombres de dispositivo.

### Siguientes Pasos
- Implementar la lógica de detección de huecos usando los datos del sensor lateral.
- Implementar máquina de estados para la maniobra de aparcamiento.
