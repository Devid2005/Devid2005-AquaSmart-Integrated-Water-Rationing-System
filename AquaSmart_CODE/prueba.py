import re
import serial
import time

# === CONFIG SERIAL ===
arduino = serial.Serial('COM7', 9600)  # Cambia COM7 por el puerto real
time.sleep(2)

# === LEER ARCHIVO TXT ORIGINAL ===
with open("path/parametros_simulados.txt", "r") as f:
    content = f.read()

# Extraer matriz c
pattern_c = re.compile(r"c\s*=\s*\[(.*?)\];", re.S)
match_c = pattern_c.search(content)
if not match_c:
    raise ValueError("No se encontró la matriz c en el archivo")
c = eval("[" + match_c.group(1) + "]")

# Extraer r
pattern_r = re.compile(r"r\s*=\s*\[(.*?)\];", re.S)
match_r = pattern_r.search(content)
r = [float(x) for x in match_r.group(1).replace("\n", "").split(",")]

# Extraer h
pattern_h = re.compile(r"h\s*=\s*\[(.*?)\];", re.S)
match_h = pattern_h.search(content)
h = [float(x) for x in match_h.group(1).replace("\n", "").split(",")]

# Extraer p, n0, e, m
pattern_params = re.compile(r"p\s*=\s*(.*?);.*?n_0\s*=\s*(.*?);.*?e\s*=\s*(.*?);.*?m\s*=\s*(.*?);", re.S)
match_params = pattern_params.search(content)
p = float(match_params.group(1))
n_0 = float(match_params.group(2))
e = float(match_params.group(3))
m = float(match_params.group(4))

# === CALCULAR TOTALES POR ZONA Y DIA ===
num_zonas = len(c)
num_dias = len(c[0])

totales = []
for dia in range(num_dias):
    valores = []
    for z in range(num_zonas):
        total = sum(c[z][dia])
        valores.append(total)
    totales.append((dia+1, valores))

print(f" Archivo leído: {num_zonas} zonas × {num_dias} días")


# === FUNCION PARA GUARDAR ARCHIVOS ===
def guardar_parametros(c, r, h, p, n_0, e, m, ultimo_dia, archivo):
    with open(archivo, "w") as f:
        f.write("// Parámetros simulados para modelo de racionamiento de agua\n\n")

        f.write("c = [\n")
        for zona in c:
            f.write("  [\n")
            for dia in zona[:ultimo_dia]:
                f.write("    [" + ", ".join(f"{val:.2f}" for val in dia) + "],\n")
            f.write("  ],\n")
        f.write("];\n\n")

        f.write(f"p = {p};\n")
        f.write(f"n_0 = {n_0};\n")
        f.write(f"e = {e};\n")
        f.write(f"m = {m};\n\n")

        f.write("r = [" + ", ".join(f"{val:.2f}" for val in r[:ultimo_dia]) + "];\n")
        f.write("h = [" + ", ".join(f"{val:.2f}" for val in h) + "];\n")

    print(f" Archivo generado: {archivo} (hasta día {ultimo_dia})")


# === ENVIAR DATOS A ARDUINO DIA A DIA ===
interrumpido = False
dia_interrupcion = None

for dia, valores in totales:
    valores_ml = [int(v * 0.000001) for v in valores]

    msg = f"{dia}," + ",".join(map(str, valores_ml)) + "\n"
    arduino.write(msg.encode())
    print(f" Enviado: {msg.strip()}")

    # Escuchar hasta que Arduino diga COMPLETADO o PARADA
    while True:
        if arduino.in_waiting > 0:
            resp = arduino.readline().decode(errors="ignore").strip()
            if resp:
                print(f" {resp}")

            if "COMPLETADO" in resp:
                break  # Termina el ciclo de este día
            elif "PARADA" in resp:
                interrumpido = True
                dia_interrupcion = dia
                break

    if interrumpido:
        break


# === GUARDAR ARCHIVOS ===
if interrumpido:
    guardar_parametros(c, r, h, p, n_0, e, m,
                       ultimo_dia=dia_interrupcion,
                       archivo="path/parametros_truncados.txt")
    guardar_parametros(c, r, h, p, n_0, e, m,
                       ultimo_dia=num_dias,
                       archivo="path/parametros_completo.txt")
else:
    guardar_parametros(c, r, h, p, n_0, e, m,
                       ultimo_dia=num_dias,
                       archivo="path/parametros_completo.txt")