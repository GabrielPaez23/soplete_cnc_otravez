import urllib.request
import json
import time

url = "http://127.0.0.1:5000/api/planificar"

# Test cases
tests = [
    # 1. Acero + Cuadrado + Presión válida
    {
        "name": "Acero + Cuadrado + Presión válida (5.0 bar)",
        "payload": {"figura": "Cuadrado", "material": "acero", "presion_gas": 5.0}
    },
    # 2. Acero + Cuadrado + Presión baja (bloqueo)
    {
        "name": "Acero + Cuadrado + Presión baja (3.0 bar)",
        "payload": {"figura": "Cuadrado", "material": "acero", "presion_gas": 3.0}
    },
    # 3. Aluminio + Circulo (geometría compleja) + Presión válida
    {
        "name": "Aluminio + Circulo (inercia activa) (4.5 bar)",
        "payload": {"figura": "Circulo", "material": "aluminio", "presion_gas": 4.5}
    }
]

print("Esperando a que el servidor Flask termine de iniciar...")
time.sleep(2)

for test in tests:
    print(f"\nEjecutando: {test['name']}")
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(test['payload']).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("Resultado:", json.dumps(res_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error en la petición:", e)
