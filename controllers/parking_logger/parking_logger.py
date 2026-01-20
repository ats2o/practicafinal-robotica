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
LIDAR_RANGE_MAX = 5.0       # Distancia máxima válida
OBSTACLE_THRESHOLD = 25     # Puntos necesarios para detectar vehículo
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
    
    # Procesar mensajes
    for message in receive_messages(receiver):
        msg_type = message.get("type")
        
        if msg_type == "SPOT_MAP":
            spots_data = message.get("spots", [])
            parking_spots = [
                ParkingSpot(
                    id=spot["id"],
                    side=spot["side"],
                    x=float(spot["x"]),
                    z=float(spot["z"])
                )
                for spot in spots_data
            ]
            
            print(f"[BMW] ✓ Mapa recibido: {len(parking_spots)} plazas")
            print("-" * 70)
            for idx, spot in enumerate(parking_spots, 1):
                scan_x, scan_z = spot.scan_position
                print(f"  {idx}. {spot.id:20s} [{spot.side}] en ({spot.x:6.2f}, {spot.z:6.2f})")
                print(f"      → Posición de escaneo: ({scan_x:6.2f}, {scan_z:6.2f})")
            print("-" * 70)
            
            send_message(emitter, {"type": "ACK_SPOT_MAP", "count": len(parking_spots)})
            parking_map_received = True
            
            if parking_spots:
                system_state = "NAVIGATING"
                current_spot_idx = 0
                print(f"\n[BMW] 🚗 Navegando hacia plaza 1: {parking_spots[0].id}\n")
    
    if not parking_map_received:
        continue
    
    # Actualizar posición (Webots: X, Z plano suelo)
    gps_vals = gps.getValues()
    vehicle_position = (float(gps_vals[0]), float(gps_vals[2]))
    
    # Calcular heading
    if last_position is not None:
        dx = vehicle_position[0] - last_position[0]
        dy = vehicle_position[1] - last_position[1]
        if abs(dx) + abs(dy) > 0.002:
            # En plano X-Z de Webots (X forward, Z right):
            # atan2(dz, dx) nos da el ángulo.
            instant_heading = math.atan2(dy, dx)
            heading_smooth = (HEADING_SMOOTH_FACTOR * instant_heading +
                            (1 - HEADING_SMOOTH_FACTOR) * heading_smooth)
            vehicle_heading = heading_smooth
    last_position = vehicle_position
    
    # Leer Lidar
    lidar_ranges = lidar.getRangeImage()
    
    # ========== MÁQUINA DE ESTADOS ==========
    
    if system_state == "NAVIGATING":
        # Ir hacia la posición de escaneo de la plaza actual
        if current_spot_idx >= len(parking_spots):
            system_state = "FINAL"
            continue
        
        spot = parking_spots[current_spot_idx]
        target = spot.scan_position
        
        reached = navigate_to_point(driver, vehicle_position, vehicle_heading,
                                   target, APPROACH_SPEED, tolerance=0.7)
        
        if reached:
            print(f"\n[BMW] 📍 Llegué a posición de escaneo de {spot.id}")
            print(f"[BMW] 🔍 Escaneando plaza (lado {spot.side})...\n")
            
            # Cambiar a modo escaneo
            driver.setCruisingSpeed(SCAN_SPEED)
            system_state = "SCANNING"
            scan_frame_count = 0
            scan_samples = []
    
    elif system_state == "SCANNING":
        spot = parking_spots[current_spot_idx]
        
        # Moverse MUY lento mientras escaneamos
        driver.setCruisingSpeed(SCAN_SPEED)
        driver.setSteeringAngle(0.0)
        
        # Determinar qué sector del Lidar mirar según el lado
        if spot.side == "R":
            # Plaza a la DERECHA: miramos hacia la derecha (90° a la derecha)
            # Sector: 10% - 40% del array (derecha del vehículo)
            sector_start = int(0.10 * LIDAR_RESOLUTION)
            sector_end = int(0.40 * LIDAR_RESOLUTION)
        else:
            # Plaza a la IZQUIERDA: miramos hacia la izquierda (90° a la izquierda)
            # Sector: 60% - 90% del array (izquierda del vehículo)
            sector_start = int(0.60 * LIDAR_RESOLUTION)
            sector_end = int(0.90 * LIDAR_RESOLUTION)
        
        sector_data = lidar_ranges[sector_start:sector_end]
        
        # Contar obstáculos válidos en el rango
        valid_points = [r for r in sector_data if math.isfinite(r)]
        obstacles = [r for r in valid_points if LIDAR_RANGE_MIN <= r <= LIDAR_RANGE_MAX]
        
        obstacle_count = len(obstacles)
        scan_samples.append(obstacle_count)
        scan_frame_count += 1
        
        # Debug cada 10 frames
        if scan_frame_count % 10 == 0:
            avg = sum(scan_samples) / len(scan_samples) if scan_samples else 0
            print(f"[SCAN] Frame {scan_frame_count}/{SCAN_FRAMES}: {obstacle_count} puntos (promedio: {avg:.1f})")
        
        # ¿Terminamos de escanear?
        if scan_frame_count >= SCAN_FRAMES:
            # Calcular promedio
            avg_obstacles = sum(scan_samples) / len(scan_samples) if scan_samples else 0
            max_obstacles = max(scan_samples) if scan_samples else 0
            
            # DECIDIR: ¿Hay vehículo o no?
            if avg_obstacles >= OBSTACLE_THRESHOLD:
                spot.status = "OCCUPIED"
                result = "❌ OCUPADA"
            else:
                spot.status = "FREE"
                result = "✅ LIBRE"
                free_spot_found = spot
            
            print("\n" + "=" * 70)
            print(f"[RESULTADO] {spot.id} → {result}")
            print(f"  Promedio de obstáculos: {avg_obstacles:.1f} puntos")
            print(f"  Máximo detectado: {max_obstacles} puntos")
            print(f"  Umbral: {OBSTACLE_THRESHOLD} puntos")
            print("=" * 70 + "\n")
            
            # Enviar resultado
            send_message(emitter, {
                "type": "SCAN_RESULT",
                "spot_id": spot.id,
                "status": spot.status,
                "score": avg_obstacles,
                "min_dist": min(obstacles) if obstacles else None
            })
            
            if spot.status == "FREE":
                # ENCONTRAMOS PLAZA LIBRE -> DEJAMOS DE ESCANEAR Y VAMOS A ELLA
                print(f"[BMW] 🎯 ¡Plaza libre encontrada! ({spot.id})")
                print(f"[BMW] 🛑 Cancelando resto de escaneos. Iniciando aproximación...")
                system_state = "APPROACHING"
            else:
                # Siguiente plaza
                current_spot_idx += 1
                
                if current_spot_idx >= len(parking_spots):
                    # Terminamos todas las plazas
                    system_state = "FINAL"
                else:
                    # Ir a la siguiente plaza
                    next_spot = parking_spots[current_spot_idx]
                    print(f"[BMW] 🚗 Navegando hacia plaza {current_spot_idx + 1}: {next_spot.id}\n")
                    system_state = "NAVIGATING"

    elif system_state == "APPROACHING":
        if free_spot_found:
             # Navegar hacia la plaza encontrada
             # Target: (spot.x, spot.z)
             target = (free_spot_found.x, free_spot_found.z)
             
             # Usamos una tolerancia generosa para "llegar"
             reached = navigate_to_point(driver, vehicle_position, vehicle_heading,
                                        target, APPROACH_SPEED, tolerance=1.0)
             
             if reached:
                 print(f"\n[BMW] 🏁 Llegada a la plaza {free_spot_found.id}")
                 system_state = "FINAL"
    
    elif system_state == "FINAL":
        # Detener el vehículo
        driver.setCruisingSpeed(STOP_SPEED)
        driver.setSteeringAngle(0.0)
        
        # Mostrar resumen
        free_spots = [s for s in parking_spots if s.status == "FREE"]
        occupied_spots = [s for s in parking_spots if s.status == "OCCUPIED"]
        
        print("\n" + "=" * 70)
        print(" " * 20 + "ESCANEO COMPLETADO")
        print("=" * 70)
        print(f"Total plazas escaneadas: {len(parking_spots)}")
        print(f"Plazas LIBRES: {len(free_spots)}")
        print(f"Plazas OCUPADAS: {len(occupied_spots)}")
        print("-" * 70)
        
        if free_spots:
            print("PLAZAS LIBRES:")
            for s in free_spots:
                print(f"  ✅ {s.id}")
        
        if occupied_spots:
            print("\nPLAZAS OCUPADAS:")
            for s in occupied_spots:
                print(f"  ❌ {s.id}")
        
        print("=" * 70)
        
        if free_spot_found:
            print(f"\n[BMW] 🎯 Primera plaza libre encontrada: {free_spot_found.id}")
            print(f"[BMW] 📍 Me quedo aquí, junto a la plaza libre")
            print(f"[BMW] ✓ Posición final: ({vehicle_position[0]:.2f}, {vehicle_position[1]:.2f})")
            
            send_message(emitter, {
                "type": "FREE_SPOT_FOUND",
                "spot_id": free_spot_found.id
            })
        else:
            print("\n[BMW] ⚠️ No se encontraron plazas libres")
            send_message(emitter, {"type": "NO_FREE_SPOTS"})
        
        print("\n" + "=" * 70)
        print(" " * 22 + "PROYECTO COMPLETADO")
        print("=" * 70 + "\n")
        
        send_message(emitter, {"type": "SCAN_COMPLETE"})
        
        # Cambiar a estado final permanente
        system_state = "STOPPED"
    
    elif system_state == "STOPPED":
        # Mantener detenido
        driver.setCruisingSpeed(STOP_SPEED)
        driver.setSteeringAngle(0.0)

print("\n[BMW] Simulación finalizada\n")