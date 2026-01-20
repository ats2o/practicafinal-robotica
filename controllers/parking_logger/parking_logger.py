"""controllers/parking_logger/parking_logger.py

Sistema Simplificado: El coche visita cada plaza y detecta si está ocupada
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from vehicle import Driver

# ========== CONFIGURACIÓN ==========
GPS_NAME = "gps"
LIDAR_NAME = "lidar"
RECEIVER_NAME = "receiver"
EMITTER_NAME = "emitter"

# Velocidades
APPROACH_SPEED = 5.0        # Velocidad para acercarse a plaza
SCAN_SPEED = 2.0            # Velocidad MUY lenta durante escaneo
STOP_SPEED = 0.0

# Detección con Lidar
LIDAR_RANGE_MIN = 0.2       # Distancia mínima válida
LIDAR_RANGE_MAX = 6.0       # Distancia máxima válida (Aumentado para ver mejor)
OBSTACLE_THRESHOLD = 5      # Puntos necesarios para detectar vehículo (Reducido para ser más sensible)
SCAN_FRAMES = 30            # Frames escaneando en cada plaza

# Navegación
WAYPOINT_TOL = 0.5
KP_STEERING = 4.0
MAX_STEER_ANGLE = 0.6


@dataclass
class ParkingSpot:
    id: str
    side: str
    x: float
    z: float
    status: str = "UNKNOWN"
    scan_position: Tuple[float, float] = None  # Posición desde donde escanear
    
    def __post_init__(self):
        # Calcular posición de escaneo (en el pasillo, frente a la plaza)
        # Asumimos que el pasillo está en Z=0 (centro de la carretera)
        # Mantenemos el offset en X para llegar un poco antes del centro
        self.scan_position = (self.x, 0.0)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def receive_messages(receiver) -> List[Dict[str, Any]]:
    messages = []
    if receiver is None:
        return messages
    while receiver.getQueueLength() > 0:
        try:
            data = receiver.getString()
            messages.append(json.loads(data))
        except Exception as e:
            print(f"[BMW] Error: {e}")
        receiver.nextPacket()
    return messages


def send_message(emitter, data: Dict[str, Any]) -> None:
    if emitter is None:
        return
    try:
        emitter.send(json.dumps(data))
    except Exception as e:
        print(f"[BMW] Error: {e}")


def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def navigate_to_point(driver: Driver, current_pos: Tuple[float, float],
                     current_heading: float, target: Tuple[float, float],
                     speed: float, tolerance: float = WAYPOINT_TOL) -> bool:
    """Navega hacia un punto. Retorna True si llegó."""
    distance = calculate_distance(current_pos, target)
    
    if distance <= tolerance:
        return True
    
    target_angle = math.atan2(target[1] - current_pos[1], target[0] - current_pos[0])
    angle_error = normalize_angle(target_angle - current_heading)
    
    # En X-Z, Z es eje derecha. Angulo positivo es giro DERECHA.
    # Steering positivo es giro IZQUIERDA.
    # Por tanto, invertimos el error para el steering.
    steering = clamp(-KP_STEERING * angle_error, -MAX_STEER_ANGLE, MAX_STEER_ANGLE)
    
    driver.setSteeringAngle(steering)
    driver.setCruisingSpeed(speed)
    
    return False


# ========== INICIALIZACIÓN ==========
driver = Driver()
timestep = int(driver.getBasicTimeStep())

gps = driver.getDevice(GPS_NAME)
gps.enable(timestep)

lidar = driver.getDevice(LIDAR_NAME)
lidar.enable(timestep)
lidar.enablePointCloud()

receiver = driver.getDevice(RECEIVER_NAME)
receiver.enable(timestep)
emitter = driver.getDevice(EMITTER_NAME)

LIDAR_RESOLUTION = int(lidar.getHorizontalResolution())
LIDAR_FOV = float(lidar.getFov())

print("=" * 70)
print(" " * 15 + "SISTEMA DE DETECCIÓN DE PLAZAS")
print("=" * 70)
print(f"Lidar: {LIDAR_RESOLUTION} puntos, FOV={math.degrees(LIDAR_FOV):.1f}°")
print(f"Umbral de detección: {OBSTACLE_THRESHOLD} puntos")
print(f"El coche visitará cada plaza y escaneará de cerca")
print("=" * 70)

# Variables
parking_spots: List[ParkingSpot] = []
parking_map_received = False
vehicle_position = (0.0, 0.0)
last_position: Optional[Tuple[float, float]] = None
vehicle_heading = 0.0
heading_smooth = 0.0
HEADING_SMOOTH_FACTOR = 0.15

# Máquina de estados
system_state = "WAITING"  # WAITING -> NAVIGATING -> SCANNING -> APPROACHING -> FINAL
current_spot_idx = 0
scan_frame_count = 0
scan_samples = []
free_spot_found: Optional[ParkingSpot] = None

print("\n[BMW] Esperando mapa de plazas...\n")


# ========== LOOP PRINCIPAL ==========
while driver.step() != -1:
    
    # Procesar mensajes (para vaciar cola, aunque no hagamos nada)
    for message in receive_messages(receiver):
        pass # Ignorar mensajes
    
    # Actualizar sensores (por si acaso)
    gps_vals = gps.getValues()
    vehicle_position = (float(gps_vals[0]), float(gps_vals[2]))
    
    # LIGICA DE PARADA DE EMERGENCIA
    # Avanzar recto hasta X=6.0 (Aprox 9m del muro, "x3" margen inicial)
    
    current_x = float(gps_vals[0])
    
    # Debug para el usuario
    # print(f"[BMW] Posicion X actual: {current_x:.2f}")
    
    if current_x > 6.0:
        driver.setCruisingSpeed(0.0)
        driver.setSteeringAngle(0.0)
        print("[BMW] 🛑 Límite alcanzado (X > 6.0). Parando motor.")
    else:
        driver.setCruisingSpeed(3.0)
        driver.setSteeringAngle(0.0)

print("\n[BMW] Simulación finalizada\n")