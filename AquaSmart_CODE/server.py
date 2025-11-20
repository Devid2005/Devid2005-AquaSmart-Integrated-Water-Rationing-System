# -*- coding: utf-8 -*-
from flask import Flask, Response
from flask_cors import CORS
import subprocess
import re
import json

app = Flask(__name__)
CORS(app)  # Permite conexión desde el host web (localhost:8000, etc.)

@app.route('/')
def index():
    return "Servidor AquaSmart activo. Visita /run para iniciar el flujo de eventos."

@app.route('/run')
def run_process():
    """
    Ejecuta riego.py y retransmite su salida en tiempo real
    como Server-Sent Events (SSE) hacia el navegador.
    """
    def generate():
        try:
            # -u = unbuffered, para salida en tiempo real
            process = subprocess.Popen(
                ['python', '-u', 'riego.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                # Enviar el log textual a la web
                yield f"data: {json.dumps({'type': 'log', 'message': line})}\n\n"

                # Detectar eventos estructurados (día, zona)
                match_dia = re.search(r"D[ií]a\s+(\d+)", line)
                match_zona = re.search(r"Zona\s+(\d+)", line)

                if match_dia:
                    dia = int(match_dia.group(1))
                    estado = "completado" if "completado" in line.lower() else "en_progreso"
                    zona = int(match_zona.group(1)) if match_zona else None

                    data = {"type": "evento", "dia": dia, "zona": zona, "estado": estado}
                    yield f"data: {json.dumps(data)}\n\n"

            yield f"data: {json.dumps({'type': 'fin'})}\n\n"
            process.wait()

        except Exception as e:
            error_msg = f"Error en servidor: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

    # text/event-stream mantiene la conexión abierta para eventos en vivo
    return Response(generate(), mimetype='text/event-stream')


if __name__ == "__main__":
    print("Servidor Flask activo en http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)
