import urllib.request
import json
import time

url = "http://127.0.0.1:5000/api/planificar"

payload = {"figura": "Circulo", "material": "aluminio", "presion_gas": 4.5}

try:
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        # Print keys and some contents safely
        print("Aprobado:", res_data.get("aprobado"))
        print("Motivo:", res_data.get("motivo"))
        print("Potencia:", res_data.get("potencia"))
        print("Velocidad:", res_data.get("velocidad"))
        print("Geometria Compleja:", res_data.get("geometria_compleja"))
        print("Cant Pasos:", len(res_data.get("listado_pasos", [])))
        print("Cant Coordenadas:", len(res_data.get("coordenadas", [])))
        print("\nPrimeros pasos:")
        for paso in res_data.get("listado_pasos", [])[:4]:
            print(paso.encode('ascii', 'replace').decode('ascii'))
except Exception as e:
    print("Error:", e)
