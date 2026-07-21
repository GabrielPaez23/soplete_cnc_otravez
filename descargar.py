import os
import urllib.request

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# -----------------------------------------------------------------------------
# Ruta relativa (se adapta automáticamente a la carpeta donde esté tu proyecto)
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_DESTINO = os.path.join(DIRECTORIO_BASE, "static", "js")

# Si deseas usar la ruta absoluta exacta de tu equipo, puedes descomentar la siguiente línea:
# CARPETA_DESTINO = r"C:\Users\Miriam\Documents\universidad\proyecto 2\simulacion\prueba_inicial\static\js"

# Crear la estructura de carpetas si no existe
if not os.path.exists(CARPETA_DESTINO):
    os.makedirs(CARPETA_DESTINO)
    print(f">> Carpeta creada exitosamente: {CARPETA_DESTINO}")
else:
    print(f">> Carpeta de destino localizada: {CARPETA_DESTINO}")

# -----------------------------------------------------------------------------
# ARCHIVOS A DESCARGAR (LIBRERÍAS THREE.JS)
# -----------------------------------------------------------------------------
librerias = {
    "three.min.js": "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "GLTFLoader.js": "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js",
    "OrbitControls.js": "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"
}

# Encabezado para simular una petición de navegador estándar (necesario en Windows 7)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}

# -----------------------------------------------------------------------------
# PROCESO DE DESCARGA
# -----------------------------------------------------------------------------
print("\n>> Iniciando descarga de librerías para visualización 3D...\n")

for nombre_archivo, url in librerias.items():
    ruta_archivo = os.path.join(CARPETA_DESTINO, nombre_archivo)
    print(f"Descargando: {nombre_archivo}...")
    
    try:
        solicitud = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(solicitud) as respuesta, open(ruta_archivo, 'wb') as archivo_salida:
            archivo_salida.write(respuesta.read())
        print(f"   [ÉXITO] Guardado en: {ruta_archivo}\n")
    except Exception as error:
        print(f"   [ERROR] No se pudo descargar {nombre_archivo}: {error}\n")

print(">> Process completado. Abre la carpeta static/js en tu explorador para verificar los archivos.")