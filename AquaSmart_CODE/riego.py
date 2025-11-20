# -*- coding: utf-8 -*-
import sys
import time

# ========= CONFIGURACIÓN DE SALIDA =========
# Asegura que los prints se envíen inmediatamente (sin buffering)
# y que los caracteres especiales (acentos, flechas, etc.) salgan bien
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# ========= CONEXIÓN CON ARDUINO =========
try:
    import serial
    arduino = serial.Serial('COM7', 9600, timeout=1)
    time.sleep(2)
    print("[PYTHON] Conectado al Arduino en modo riego diario.\n")
    SIMULADO = False
except Exception as e:
    print(f"[PYTHON] No se pudo conectar al Arduino ({e}). Se usará modo simulado.\n")

    # Arduino simulado (para pruebas sin hardware)
    class FakeArduino:
        def write(self, msg):
            print(f"[SIMULADO] Enviando → {msg.strip()}")
        def readline(self):
            # Devuelve mensajes simulados con un poco de espera
            time.sleep(1.5)
            return "Día completado\n"

    arduino = FakeArduino()
    SIMULADO = True


# ========= DATOS DE PRUEBA =========
racionamiento = {
    0: [3, 9],  # Zona 0 sin agua esos días
    1: [2]      # Zona 1 sin agua ese día
}

c = [
  [
    [0.00, 4016825.89, 93721755.85],
    [0.00, 2295153.41, 81068113.39],
    [0.00, 4790279.00, 77134270.11],
    [0.00, 2837293.80, 98841109.58],
    [0.00, 4211348.86, 97783088.95],
    [0.00, 3645511.50, 85894666.86],
    [0.00, 3698092.86, 84205941.70],
    [0.00, 3989200.15, 86816367.62],
    [0.00, 3108222.04, 87507996.49],
    [0.00, 2336000.75, 102494227.54],
  ],
  [
    [246971.50, 5216644.95, 133857958.17],
    [297511.17, 4589884.49, 135546705.00],
    [358712.60, 5672608.45, 146403248.19],
    [265122.20, 5230658.85, 129650906.85],
    [248945.10, 4030982.30, 97081577.14],
    [300664.83, 4392695.97, 141528153.15],
    [328343.40, 2461523.14, 125759855.20],
    [315085.05, 3776862.48, 127814850.20],
    [255875.00, 4895663.70, 105469795.51],
    [197067.52, 4068632.15, 113574871.70],
  ],
]


# ========= FUNCIONES =========
def hay_racionamiento(zona, dia):
    return dia in racionamiento.get(zona, [])


def volumen_dia_ml(zona, dia):
    """Suma los valores del día (fila) y convierte a ml."""
    valores = sum(c[zona][dia - 1])  
    return int(valores * 0.00001)  


def esperar_confirmacion(dia_actual):
    """Espera hasta que Arduino confirme que completó el día actual."""
    print(f"[PYTHON] Esperando confirmación de finalización del Día {dia_actual}...\n")
    while True:
        linea = arduino.readline().decode(errors="ignore").strip()
        if not linea:
            continue
        print(f"[ARDUINO] {linea}")
        if "Día" in linea and "completado" in linea:
            print(f"[PYTHON] Confirmado: Día {dia_actual} completado.\n")
            break


# ========= LÓGICA PRINCIPAL =========
dia = 1
total_dias = len(c[0])

print("[PYTHON] Presiona el joystick para avanzar los días.\n")
if SIMULADO:
    print("[SIMULADO] En este modo, los días avanzan automáticamente cada 2 segundos.\n")

while True:
    if SIMULADO:
        line = "CLICK"
        time.sleep(2)
    else:
        line = arduino.readline().decode(errors="ignore").strip()

    # Mostrar mensajes del Arduino mientras no haya CLICK
    if line and line not in ("CLICK",):
        print(f"[ARDUINO] {line}")
        continue

    # Cuando se detecta un click del joystick (o simulación)
    if line == "CLICK":
        print(f"\n=== Día {dia} ===")

        # Zona 0
        if hay_racionamiento(0, dia):
            V1 = 0
            print("Zona 0 -> RACIONAMIENTO (sin agua)")
        else:
            V1 = volumen_dia_ml(0, dia)
            print(f"Zona 0 -> Se entregan {V1:,} ml")

        # Zona 1
        if hay_racionamiento(1, dia):
            V2 = 0
            print("Zona 1 -> RACIONAMIENTO (sin agua)")
        else:
            V2 = volumen_dia_ml(1, dia)
            print(f"Zona 1 -> Se entregan {V2:,} ml")

        # Enviar orden al Arduino
        orden = f"{dia},{V1},{V2}\n"
        arduino.write(orden.encode())
        print(f"[PYTHON] Enviado → {orden.strip()}")

        # Esperar confirmación
        esperar_confirmacion(dia)

        dia += 1
        if dia > total_dias:
            print("\n>>> Simulación completada. Todos los días procesados.")
            break
