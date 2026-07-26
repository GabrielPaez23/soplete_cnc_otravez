import os
import pandas as pd
from flask import Flask, request, jsonify, render_template

# Inicializar aplicación Flask
app = Flask(__name__)

# Definir la ruta de la base de conocimientos
EXCEL_PATH = "dataset_de_cnc.xlsx"

def cargar_base_conocimientos():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"No se encontró el archivo de base de datos {EXCEL_PATH} en el directorio actual.")
    
    df_figuras = pd.read_excel(EXCEL_PATH, sheet_name="figuras")
    df_parametros = pd.read_excel(EXCEL_PATH, sheet_name="parametros_experto")
    return df_figuras, df_parametros

def planificar_dfs_iterativo(figura, df_figuras):
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
                listado_pasos.append(f"Paso {i}: ({px},{py}) ➔ ({x},{y}) | [G00 - Traslado Rápido (Soplete Apagado)]")
            elif op == 'Encender_Soplete':
                listado_pasos.append(f"Paso {i}: En ({x},{y}) | [M03 - Encendido de Soplete]")
            elif op == 'Corte_Lineal':
                listado_pasos.append(f"Paso {i}: ({px},{py}) ➔ ({x},{y}) | [G01 - Corte Lineal Activo]")
            elif op == 'Apagar_Soplete':
                listado_pasos.append(f"Paso {i}: En ({x},{y}) | [M05 - Apagado de Soplete]")
            else:
                listado_pasos.append(f"Paso {i}: ({px},{py}) ➔ ({x},{y}) | [{op}]")
                
    return {
        "coordenadas": coordenadas_resultado,
        "listado_pasos": listado_pasos
    }

def evaluar_sistema_experto(figura, material, presion_gas, df_parametros):
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
        "motivo": "Parámetros validados de forma segura por la base de reglas.",
        "potencia": potencia_sugerida,
        "velocidad": velocidad_sugerida,
        "geometria_compleja": es_compleja,
        "presion_min": presion_min,
        "presion_actual": presion_gas
    }

@app.route('/')
def home():
    return render_template('index.html')

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