import os
import io
import base64
import pandas as pd
from flask import Flask, request, jsonify, render_template
from vectorizador_ia import VectorizadorCNC

# Inicializar aplicación Flask
app = Flask(__name__)

# Definir la ruta de la base de conocimientos
EXCEL_PATH = "dataset_de_cnc.xlsx"
vectorizador = VectorizadorCNC()

def cargar_base_conocimientos():
    """
    Carga los DataFrames desde el archivo Excel dataset_de_cnc.xlsx.
    """
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"No se encontró el archivo de base de datos {EXCEL_PATH} en el directorio actual.")
    
    df_figuras = pd.read_excel(EXCEL_PATH, sheet_name="figuras")
    df_parametros = pd.read_excel(EXCEL_PATH, sheet_name="parametros_experto")
    return df_figuras, df_parametros

def guardar_figura_en_dataset(resultado_vec):
    """
    Inserta o actualiza las coordenadas de la figura vectorizada directamente
    en el dataset Excel para su integración completa en el sistema CNC.
    """
    df_figuras, df_parametros = cargar_base_conocimientos()
    nombre_figura = resultado_vec["figura"]
    
    # Eliminar registros previos con el mismo nombre si existían
    df_figuras = df_figuras[df_figuras['Figura'].str.lower() != nombre_figura.lower()].copy()
    
    # Determinar nuevo ID de Pieza
    max_id = int(df_figuras['ID_Pieza'].max()) if not df_figuras.empty and 'ID_Pieza' in df_figuras else 0
    nuevo_id = max_id + 1
    
    # Asignar ID_Pieza a las nuevas filas
    nuevas_filas = []
    for fila in resultado_vec["filas_excel"]:
        fila_con_id = fila.copy()
        fila_con_id["ID_Pieza"] = nuevo_id
        nuevas_filas.append(fila_con_id)
        
    df_nuevas = pd.DataFrame(nuevas_filas)
    df_figuras_actualizado = pd.concat([df_figuras, df_nuevas], ignore_index=True)
    
    # Actualizar o insertar en parametros_experto si no existe regla para esta geometría
    nombre_norm = nombre_figura.strip().lower()
    df_parametros_filtrado = df_parametros[df_parametros['Material'].str.lower() != nombre_norm].copy()
    
    es_compleja_str = "si" if resultado_vec["es_compleja"] else "no"
    potencia_sug = "85% (Ajuste Curvas IA)" if resultado_vec["es_compleja"] else "75% (Corte óptimo)"
    velocidad_sug = "Precisión Fina (G01 - 800 mm/min)" if resultado_vec["es_compleja"] else "Rápida (G01 - 1800 mm/min)"
    
    fila_param = {
        "Material": nombre_norm,
        "Figura_Compleja": es_compleja_str,
        "Presion_Min_Gas": 4.0,
        "Potencia_Sugerida": potencia_sug,
        "Velocidad_Sugerida": velocidad_sug
    }
    df_parametros_actualizado = pd.concat([df_parametros_filtrado, pd.DataFrame([fila_param])], ignore_index=True)
    
    # Escribir en el archivo Excel
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_figuras_actualizado.to_excel(writer, sheet_name="figuras", index=False)
        df_parametros_actualizado.to_excel(writer, sheet_name="parametros_experto", index=False)
        
    return df_figuras_actualizado, df_parametros_actualizado

def planificar_dfs_iterativo(figura, df_figuras):
    """
    Planifica la secuencia de corte CNC de la figura utilizando un DFS iterativo (LIFO stack).
    Construye un grafo secuencial donde cada punto de la figura en el dataset se conecta al siguiente.
    """
    df_fig = df_figuras[df_figuras['Figura'].str.lower() == figura.lower()]
    if df_fig.empty:
        return None

    df_fig = df_fig.sort_values('Pasos_Acumulados')
    
    puntos = []
    for _, row in df_fig.iterrows():
        puntos.append({
            'secuencia': str(row['Vertice_Secuencia']),
            'x': int(row['Coordenada_X']),
            'y': int(row['Coordenada_Y']),
            'operacion': str(row['Operacion_CNC']),
            'paso': int(row['Pasos_Acumulados'])
        })
        
    n = len(puntos)
    if n == 0:
        return []
        
    grafo = {i: [i+1] for i in range(n-1)}
    
    pila = [(0, [0])]
    visitados = set()
    camino_final = []
    
    while pila:
        nodo, camino = pila.pop()
        
        if nodo == n - 1:
            camino_final = camino
            break
            
        if nodo not in visitados:
            visitados.add(nodo)
            vecinos = grafo.get(nodo, [])
            for vecino in vecinos:
                if vecino not in visitados:
                    pila.append((vecino, camino + [vecino]))
                    
    coordenadas_resultado = [puntos[idx] for idx in camino_final]
        
    listado_pasos = []
    for i in range(len(coordenadas_resultado)):
        pt = coordenadas_resultado[i]
        x, y = pt['x'], pt['y']
        op = pt['operacion']
        
        if i == 0:
            listado_pasos.append(f"Paso 0: Inicio en origen ({x},{y}) | [G00 - Posicionamiento Rápido]")
        else:
            prev_pt = coordenadas_resultado[i-1]
            px, py = prev_pt['x'], prev_pt['y']
            
            if op == 'Traslado_Apagado':
                listado_pasos.append(f"Paso {i}: ({px},{py}) -> ({x},{y}) | [G00 - Traslado Rápido (Soplete Apagado)]")
            elif op == 'Encender_Soplete':
                listado_pasos.append(f"Paso {i}: En ({x},{y}) | [M03 - Encendido de Soplete]")
            elif op == 'Corte_Lineal':
                listado_pasos.append(f"Paso {i}: ({px},{py}) -> ({x},{y}) | [G01 - Corte Lineal Activo]")
            elif op == 'Apagar_Soplete':
                listado_pasos.append(f"Paso {i}: En ({x},{y}) | [M05 - Apagado de Soplete]")
            else:
                listado_pasos.append(f"Paso {i}: ({px},{py}) -> ({x},{y}) | [{op}]")
                
    return {
        "coordenadas": coordenadas_resultado,
        "listado_pasos": listado_pasos
    }

def evaluar_sistema_experto(figura, material, presion_gas, df_parametros):
    """
    Motor de Inferencia del Sistema Experto para validación de seguridad y parámetros.
    """
    figura_norm = figura.strip().lower()
    material_norm = material.strip().lower()
    
    row_material = df_parametros[df_parametros['Material'].str.lower() == material_norm]
    if row_material.empty:
        return {
            "aprobado": False,
            "motivo": f"El material '{material}' no existe en la base de conocimientos."
        }
        
    presion_min = float(row_material.iloc[0]['Presion_Min_Gas'])
    potencia_sugerida = str(row_material.iloc[0]['Potencia_Sugerida'])
    velocidad_sugerida = str(row_material.iloc[0]['Velocidad_Sugerida'])
    
    if presion_gas < presion_min:
        return {
            "aprobado": False,
            "motivo": f"PRESIÓN INSUFICIENTE: La presión ingresada ({presion_gas:.2f} bar) es menor al mínimo requerido para el {material} ({presion_min:.2f} bar). Bloqueo de seguridad activado por riesgo de retroceso de llama.",
            "presion_min": presion_min,
            "presion_actual": presion_gas
        }
        
    row_figura = df_parametros[df_parametros['Material'].str.lower() == figura_norm]
    es_compleja = False
    
    if not row_figura.empty:
        fig_compleja_val = str(row_figura.iloc[0]['Figura_Compleja']).strip().lower()
        if fig_compleja_val == 'si':
            es_compleja = True
            velocidad_sugerida = str(row_figura.iloc[0]['Velocidad_Sugerida'])
            
    return {
        "aprobado": True,
        "motivo": "Parámetros validados de forma segura por la base de reglas del HMI.",
        "potencia": potencia_sugerida,
        "velocidad": velocidad_sugerida,
        "geometria_compleja": es_compleja,
        "presion_min": presion_min,
        "presion_actual": presion_gas
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/figuras', methods=['GET'])
def obtener_figuras():
    """
    Retorna el listado de figuras disponibles en el dataset.
    """
    try:
        df_figuras, _ = cargar_base_conocimientos()
        figuras = list(df_figuras['Figura'].dropna().unique())
        return jsonify({"success": True, "figuras": figuras})
    except Exception as e:
        return jsonify({"success": False, "motivo": str(e)}), 500

@app.route('/api/vectorizar', methods=['POST'])
def vectorizar_imagen():
    """
    Endpoint para procesar una imagen mediante el módulo de red neuronal / visión,
    extraer los vectores poligonales, insertarlos en el dataset CNC y devolver
    las coordenadas listas para visualización en el plano cartesiano.
    """
    try:
        nombre_figura = "Figura_Vectorizada"
        img_bytes = None
        
        # 1. Comprobar si se envió archivo multipart
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo and archivo.filename != '':
                img_bytes = archivo.read()
                nombre_base = os.path.splitext(archivo.filename)[0]
                # Sanitizar nombre
                nombre_limpio = "".join(c for c in nombre_base if c.isalnum() or c in ('_', '-')).strip()
                if nombre_limpio:
                    nombre_figura = f"Vec_{nombre_limpio}"
        elif 'file' in request.files:
            archivo = request.files['file']
            if archivo and archivo.filename != '':
                img_bytes = archivo.read()
                nombre_base = os.path.splitext(archivo.filename)[0]
                nombre_limpio = "".join(c for c in nombre_base if c.isalnum() or c in ('_', '-')).strip()
                if nombre_limpio:
                    nombre_figura = f"Vec_{nombre_limpio}"
        else:
            # 2. Comprobar JSON (Base64 o figuras predefinidas)
            data = request.get_json(silent=True)
            if data:
                if 'nombre' in data and data['nombre']:
                    nombre_figura = str(data['nombre'])
                if 'imagen_base64' in data and data['imagen_base64']:
                    b64_str = data['imagen_base64']
                    if ',' in b64_str:
                        b64_str = b64_str.split(',', 1)[1]
                    img_bytes = base64.b64decode(b64_str)
                    
        if not img_bytes:
            return jsonify({
                "success": False,
                "motivo": "No se recibió ninguna imagen válida para vectorizar."
            }), 400
            
        # 3. Procesar imagen mediante el módulo de vectorización IA
        resultado_vec = vectorizador.procesar_imagen_bytes(img_bytes, nombre_figura=nombre_figura)
        
        # 4. Insertar las coordenadas directamente en el dataset de control de la máquina CNC
        guardar_figura_en_dataset(resultado_vec)
        
        return jsonify({
            "success": True,
            "figura": resultado_vec["figura"],
            "coordenadas": resultado_vec["coordenadas"],
            "num_vertices": resultado_vec["num_vertices"],
            "es_compleja": resultado_vec["es_compleja"],
            "dimensiones": resultado_vec["dimensiones"],
            "puntos_norm": resultado_vec.get("puntos_norm", []),
            "mensaje": "Figura vectorizada exitosamente e integrada en el dataset CNC."
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "motivo": f"Error en la vectorización de imagen: {str(e)}"
        }), 500

@app.route('/api/dataset/guardar', methods=['POST'])
def guardar_dataset():
    """
    Guarda la imagen original y sus coordenadas en formato YOLO Segmentación
    para reentrenar la IA y mejorar el modelo de forma continua.
    """
    try:
        data = request.get_json()
        if not data or 'imagen_base64' not in data or 'puntos_norm' not in data:
            return jsonify({"success": False, "motivo": "Faltan datos de imagen o coordenadas."}), 400
            
        b64_str = data['imagen_base64']
        if ',' in b64_str:
            b64_str = b64_str.split(',', 1)[1]
            
        img_bytes = base64.b64decode(b64_str)
        puntos_norm = data['puntos_norm']
        
        # Crear directorios
        ruta_images = os.path.join("dataset", "images")
        ruta_labels = os.path.join("dataset", "labels")
        os.makedirs(ruta_images, exist_ok=True)
        os.makedirs(ruta_labels, exist_ok=True)
        
        num_existentes = len([f for f in os.listdir(ruta_images) if f.endswith('.png')]) + 1
        id_muestra = f"muestra_{num_existentes:04d}"
        
        # 1. Guardar Imagen Original
        path_img = os.path.join(ruta_images, f"{id_muestra}.png")
        with open(path_img, "wb") as f:
            f.write(img_bytes)
            
        # 2. Guardar archivo .txt de etiquetas (Clase 0 + Polígono YOLO)
        path_lbl = os.path.join(ruta_labels, f"{id_muestra}.txt")
        linea_yolo = "0 " + " ".join([str(p) for p in puntos_norm]) + "\n"
        with open(path_lbl, "w") as f:
            f.write(linea_yolo)
            
        return jsonify({
            "success": True, 
            "mensaje": f"Muestra guardada exitosamente como {id_muestra}.",
            "id_muestra": id_muestra
        })
        
    except Exception as e:
        return jsonify({"success": False, "motivo": f"Error al guardar dataset: {str(e)}"}), 500

@app.route('/api/planificar', methods=['POST'])
def planificar():
    data = request.get_json()
    if not data:
        return jsonify({"aprobado": False, "motivo": "No se recibieron datos JSON válidos."}), 400
        
    figura = data.get("figura")
    material = data.get("material")
    presion_gas = data.get("presion_gas")
    
    if figura is None or material is None or presion_gas is None:
        return jsonify({"aprobado": False, "motivo": "Faltan parámetros de entrada requeridos."}), 400
        
    try:
        presion_gas = float(presion_gas)
    except ValueError:
        return jsonify({"aprobado": False, "motivo": "Presión de gas debe ser un valor numérico."}), 400
        
    try:
        df_figuras, df_parametros = cargar_base_conocimientos()
        
        resultado_experto = evaluar_sistema_experto(figura, material, presion_gas, df_parametros)
        
        if not resultado_experto["aprobado"]:
            return jsonify({
                "aprobado": False,
                "motivo": resultado_experto["motivo"]
            })
            
        resultado_cnc = planificar_dfs_iterativo(figura, df_figuras)
        if resultado_cnc is None:
            return jsonify({
                "aprobado": False,
                "motivo": f"No se encontraron coordenadas para la figura '{figura}' en el dataset."
            })
            
        return jsonify({
            "aprobado": True,
            "motivo": resultado_experto["motivo"],
            "potencia": resultado_experto["potencia"],
            "velocidad": resultado_experto["velocidad"],
            "geometria_compleja": resultado_experto["geometria_compleja"],
            "presion_min": resultado_experto["presion_min"],
            "presion_actual": resultado_experto["presion_actual"],
            "coordenadas": resultado_cnc["coordenadas"],
            "listado_pasos": resultado_cnc["listado_pasos"]
        })
        
    except Exception as e:
        return jsonify({
            "aprobado": False,
            "motivo": f"Error interno del servidor al procesar la planificación: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("Iniciando el servidor de HMI CNC en: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)