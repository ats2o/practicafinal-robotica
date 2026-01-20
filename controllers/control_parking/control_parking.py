"""controllers/control_parking/control_parking.py

Supervisor simplificado para el sistema de detección
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Tuple

from controller import Supervisor

# CONFIG
RECEIVER_NAME = "receiver"
EMITTER_NAME = "emitter"
LIDAR_DEF = "lidar"

SPOT_DEFS: List[Tuple[str, str]] = [
    ("LineaParking1R", "R"),
    ("LineaParking2L", "L"),
    ("LineaParking3R", "R"),
    ("LineaParking4L", "L"),
]

# Plazas inicialmente ocupadas
INITIAL_OCCUPIED = {"LineaParking1R", "LineaParking3R"}


def recv_all_json(rx) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if rx is None:
        return out
    while rx.getQueueLength() > 0:
        try:
            packet = rx.getString()
            out.append(json.loads(packet))
        except Exception as e:
            print(f"[Supervisor] Error: {e}")
        rx.nextPacket()
    return out


def send_json(tx, payload: Dict[str, Any]) -> None:
    if tx is None:
        return
    try:
        tx.send(json.dumps(payload))
    except Exception as e:
        print(f"[Supervisor] Error: {e}")


def get_translation_xy(node) -> Tuple[float, float]:
    f = node.getField("translation")
    v = f.getSFVec3f()
    return float(v[0]), float(v[1])


# Inicialización
sup = Supervisor()
timestep = int(sup.getBasicTimeStep())

rx = sup.getDevice(RECEIVER_NAME)
rx.enable(timestep)
tx = sup.getDevice(EMITTER_NAME)

print(f"[Supervisor] Inicializado con timestep={timestep}ms")

# Construir lista de plazas
spots = []
for spot_def, side in SPOT_DEFS:
    node = sup.getFromDef(spot_def)
    if node is None:
        print(f"[Supervisor] ERROR: No se encuentra '{spot_def}'")
        continue
    x, y = get_translation_xy(node)
    spots.append({
        "id": spot_def,
        "side": side,
        "x": x,
        "y": y,
        "node": node,
    })
    print(f"[Supervisor] Plaza: {spot_def} ({side}) en ({x:.2f}, {y:.2f})")

# Ocultar líneas del Lidar
lidar_node = sup.getFromDef(LIDAR_DEF)
if lidar_node is None:
    print(f"[Supervisor] WARN: No se encuentra Lidar")
else:
    for s in spots:
        try:
            s["node"].setVisibility(lidar_node, False)
        except Exception as e:
            print(f"[Supervisor] Error ocultando {s['id']}: {e}")

# Estado inicial
occupied: Dict[str, bool] = {s["id"]: (s["id"] in INITIAL_OCCUPIED) for s in spots}
print(f"\n[Supervisor] Estado REAL inicial:")
for sid, occ in occupied.items():
    status = "OCUPADA" if occ else "LIBRE"
    print(f"  {sid}: {status}")

# Mensaje de mapa
spot_map = {
    "type": "SPOT_MAP",
    "spots": [{"id": s["id"], "side": s["side"], "x": s["x"], "y": s["y"]} for s in spots],
}

last_send = 0.0
acked = False
scan_completed = False

print("\n[Supervisor] Esperando BMW...\n")

# Loop principal
while sup.step(timestep) != -1:
    now = time.time()
    
    if not acked and (now - last_send) > 0.5:
        send_json(tx, spot_map)
        last_send = now
    
    for msg in recv_all_json(rx):
        msg_type = msg.get("type")
        
        if msg_type == "ACK_SPOT_MAP":
            if not acked:
                acked = True
                print(f"[Supervisor] ✓ BMW confirmó recepción de {msg.get('count')} plazas\n")
        
        elif msg_type == "SCAN_RESULT":
            sid = msg.get("spot_id")
            status = msg.get("status")
            score = msg.get("score", 0)
            min_dist = msg.get("min_dist")
            
            real_status = "OCUPADA" if occupied.get(sid, False) else "LIBRE"
            detected_status = "OCUPADA" if status == "OCCUPIED" else "LIBRE"
            
            # Verificar si la detección es correcta
            is_correct = (real_status == detected_status)
            icon = "✓" if is_correct else "✗"
            
            print(f"[Supervisor] {icon} {sid}: Detectado={detected_status}, Real={real_status}, Score={score:.1f}")
        
        elif msg_type == "FREE_SPOT_FOUND":
            sid = msg.get("spot_id")
            print(f"\n[Supervisor] 🎯 BMW encontró plaza libre: {sid}")
        
        elif msg_type == "NO_FREE_SPOTS":
            print(f"\n[Supervisor] ⚠️ BMW no encontró plazas libres")
        
        elif msg_type == "SCAN_COMPLETE":
            if not scan_completed:
                scan_completed = True
                print("\n[Supervisor] ═══════════════════════════════════════")
                print("[Supervisor] ESCANEO COMPLETADO")
                print("[Supervisor] ═══════════════════════════════════════\n")

print("[Supervisor] Simulación terminada")