import os
import sys
import pandas as pd
from flask import Flask, request, jsonify, render_template_string

# Inicializar aplicación Flask
app = Flask(__name__)

# Definir la ruta de la base de conocimientos
EXCEL_PATH = "dataset_de_cnc.xlsx"

def cargar_base_conocimientos():
    """
    Carga y retorna los datos de las pestañas figuras y parametros_experto del archivo Excel.
    """
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"No se encontró el archivo de base de datos {EXCEL_PATH} en el directorio actual.")
    
    # Cargar figuras y parámetros expertos utilizando pandas
    df_figuras = pd.read_excel(EXCEL_PATH, sheet_name="figuras")
    df_parametros = pd.read_excel(EXCEL_PATH, sheet_name="parametros_experto")
    return df_figuras, df_parametros

def planificar_dfs_iterativo(figura, df_figuras):
    """
    Planifica la secuencia de corte del CNC de la figura utilizando un DFS iterativo (LIFO stack).
    Construye un grafo secuencial donde cada punto de la figura en el Excel se conecta al siguiente.
    """
    # Filtrar coordenadas para la figura seleccionada
    df_fig = df_figuras[df_figuras['Figura'].str.lower() == figura.lower()]
    if df_fig.empty:
        return None

    # Asegurar orden secuencial de los puntos en el dataset original
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
        
    # Grafo de adyacencia que conecta linealmente los puntos de la figura (0 -> 1 -> 2 -> ... -> n-1)
    # representados como nodos indexados del 0 al n-1.
    grafo = {i: [i+1] for i in range(n-1)}
    
    # Estructura del DFS Iterativo con una Pila LIFO: cada elemento contiene (nodo_actual, camino_acumulado)
    pila = [(0, [0])]
    visitados = set()
    camino_final = []
    
    while pila:
        nodo, camino = pila.pop()  # Pop LIFO
        
        # Si llegamos al nodo final (cierre de la trayectoria)
        if nodo == n - 1:
            camino_final = camino
            break
            
        if nodo not in visitados:
            visitados.add(nodo)
            vecinos = grafo.get(nodo, [])
            for vecino in vecinos:
                if vecino not in visitados:
                    pila.append((vecino, camino + [vecino]))
                    
    # Construir la lista ordenada de coordenadas resultantes de la búsqueda DFS
    coordenadas_resultado = []
    for idx in camino_final:
        coordenadas_resultado.append(puntos[idx])
        
    # Generar la secuencia cronológica detallada de instrucciones de corte CNC
    listado_pasos = []
    for i in range(len(coordenadas_resultado)):
        pt = coordenadas_resultado[i]
        x, y = pt['x'], pt['y']
        op = pt['operacion']
        seq = pt['secuencia']
        
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
    """
    Motor de Inferencia del Sistema Experto.
    Valida la presión del gas frente a la presión mínima y evalúa reglas de geometría compleja.
    """
    # Normalizar valores para la comparación case-insensitive
    figura_norm = figura.strip().lower()
    material_norm = material.strip().lower()
    
    # Buscar parámetros del material en la base de conocimientos
    row_material = df_parametros[df_parametros['Material'].str.lower() == material_norm]
    if row_material.empty:
        return {
            "aprobado": False,
            "motivo": f"El material '{material}' no existe en la base de conocimientos."
        }
        
    presion_min = float(row_material.iloc[0]['Presion_Min_Gas'])
    potencia_sugerida = str(row_material.iloc[0]['Potencia_Sugerida'])
    velocidad_sugerida = str(row_material.iloc[0]['Velocidad_Sugerida'])
    
    # Regla 1: Validar si la presión actual es inferior al mínimo requerido
    if presion_gas < presion_min:
        return {
            "aprobado": False,
            "motivo": f"PRESIÓN INSUFICIENTE: La presión ingresada ({presion_gas:.2f} bar) es menor al mínimo requerido para el {material} ({presion_min:.2f} bar). Bloqueo de seguridad activado por riesgo de retroceso de llama.",
            "presion_min": presion_min,
            "presion_actual": presion_gas
        }
        
    # Regla 2: Detectar Geometría Compleja (círculo o estrella) para mitigar inercia
    # Se consulta la fila que corresponde a la figura dentro del parámetro experto
    row_figura = df_parametros[df_parametros['Material'].str.lower() == figura_norm]
    es_compleja = False
    
    if not row_figura.empty:
        fig_compleja_val = str(row_figura.iloc[0]['Figura_Compleja']).strip().lower()
        if fig_compleja_val == 'si':
            es_compleja = True
            # Sobrescribir la velocidad a velocidad de precisión fina para compensar curvas
            velocidad_sugerida = str(row_figura.iloc[0]['Velocidad_Sugerida'])
            
    return {
        "aprobado": True,
        "motivo": "Luz verde: Parámetros validados de forma segura por la base de reglas del HMI.",
        "potencia": potencia_sugerida,
        "velocidad": velocidad_sugerida,
        "geometria_compleja": es_compleja,
        "presion_min": presion_min,
        "presion_actual": presion_gas
    }

# ----------------- PLANTILLA FRONTEND INTEGRADA -----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMI CNC - Panel de Control Industrial</title>
    <!-- Importación de Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f0f13;
            --bg-secondary: #171721;
            --card-bg: rgba(28, 28, 40, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent-blue: #00f0ff;
            --accent-green: #00ff88;
            --accent-red: #ff3366;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --font-sans: 'Outfit', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            background-image: 
                radial-gradient(at 0% 0%, rgba(0, 102, 255, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(0, 255, 136, 0.04) 0px, transparent 50%);
            color: var(--text-primary);
            font-family: var(--font-sans);
            min-height: 100vh;
            padding: 20px;
            overflow-x: hidden;
        }

        /* Contenedor Principal */
        .container {
            max-width: 1350px;
            margin: 0 auto;
        }

        /* Encabezado */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 25px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }

        .header-title h1 {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-title p {
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        .machine-status {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 255, 136, 0.08);
            border: 1px solid rgba(0, 255, 136, 0.2);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: var(--accent-green);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 15px var(--accent-green); }
            100% { transform: scale(0.9); opacity: 0.6; }
        }

        /* Grid de la HMI */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 20px;
            align-items: start;
        }

        /* Paneles */
        .panel {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            backdrop-filter: blur(10px);
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
            transition: border-color 0.3s;
        }

        .panel:hover {
            border-color: rgba(255, 255, 255, 0.12);
        }

        .panel-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Formularios y Inputs */
        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }

        select {
            width: 100%;
            background: rgba(15, 15, 19, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            padding: 12px;
            font-family: var(--font-sans);
            font-size: 14px;
            outline: none;
            cursor: pointer;
            transition: all 0.3s;
        }

        select:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.15);
        }

        /* Estilizado del Range Slider */
        .slider-container {
            background: rgba(15, 15, 19, 0.6);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .slider-header {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .slider-value {
            color: var(--accent-blue);
            font-family: var(--font-mono);
        }

        input[type=range] {
            -webkit-appearance: none;
            width: 100%;
            background: transparent;
        }

        input[type=range]:focus {
            outline: none;
        }

        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 6px;
            cursor: pointer;
            background: #27273a;
            border-radius: 3px;
        }

        input[type=range]::-webkit-slider-thumb {
            height: 18px;
            width: 18px;
            border-radius: 50%;
            background: var(--accent-blue);
            cursor: pointer;
            -webkit-appearance: none;
            margin-top: -6px;
            box-shadow: 0 0 8px var(--accent-blue);
            transition: transform 0.1s, background-color 0.2s;
        }

        input[type=range]::-webkit-slider-thumb:hover {
            transform: scale(1.15);
        }

        .slider-limits {
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: var(--text-secondary);
            margin-top: 6px;
        }

        /* Botón HMI */
        .btn-planificar {
            width: 100%;
            background: linear-gradient(135deg, #0052d4 0%, #4364f7 50%, #6fb1fc 100%);
            border: none;
            border-radius: 8px;
            color: white;
            padding: 14px;
            font-family: var(--font-sans);
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(67, 100, 247, 0.4);
            transition: all 0.3s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }

        .btn-planificar:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(67, 100, 247, 0.55);
            background: linear-gradient(135deg, #0066ff 0%, #4364f7 50%, #8ac1ff 100%);
        }

        .btn-planificar:active {
            transform: translateY(1px);
        }

        /* Panel de Respuesta del Sistema Experto */
        .expert-card {
            margin-top: 20px;
            border-radius: 8px;
            padding: 16px;
            display: none;
            font-size: 14px;
            animation: fadeIn 0.4s ease-out;
        }

        .expert-card.success {
            display: block;
            background: rgba(0, 255, 136, 0.06);
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: #d1fae5;
        }

        .expert-card.error {
            display: block;
            background: rgba(255, 51, 102, 0.06);
            border: 1px solid rgba(255, 51, 102, 0.3);
            color: #ffe4e6;
        }

        .expert-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 12px;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }

        .expert-card.success .expert-header {
            color: var(--accent-green);
        }

        .expert-card.error .expert-header {
            color: var(--accent-red);
        }

        .expert-params {
            margin-top: 12px;
            background: rgba(0,0,0,0.25);
            border-radius: 6px;
            padding: 12px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            font-size: 12px;
            border: 1px solid rgba(255,255,255,0.04);
        }

        .param-label {
            color: var(--text-secondary);
        }

        .param-value {
            font-weight: 600;
            color: var(--text-primary);
            text-align: right;
        }

        .complex-badge {
            grid-column: span 2;
            background: rgba(0, 240, 255, 0.12);
            border: 1px solid rgba(0, 240, 255, 0.25);
            color: var(--accent-blue);
            padding: 4px;
            border-radius: 4px;
            text-align: center;
            font-weight: 700;
            margin-top: 4px;
            text-transform: uppercase;
            font-size: 10px;
        }

        /* Sección Derecha (Canvas y Terminal) */
        .main-content {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Canvas Wrapper */
        .canvas-container {
            position: relative;
            background: #1e1e24;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8);
        }

        canvas {
            display: block;
            width: 100%;
            max-width: 850px;
            height: 480px;
            background-color: #1e1e24;
        }

        /* Terminal Console */
        .terminal-panel {
            background: #09090c;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            font-family: var(--font-mono);
            padding: 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }

        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            padding-bottom: 8px;
            margin-bottom: 12px;
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .terminal-dots {
            display: flex;
            gap: 5px;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .dot-red { background: #ef4444; }
        .dot-yellow { background: #f59e0b; }
        .dot-green { background: #10b981; }

        .terminal-body {
            height: 180px;
            overflow-y: auto;
            color: #38bdf8;
            font-size: 13px;
            line-height: 1.5;
            white-space: pre-wrap;
            padding-right: 8px;
        }

        /* Custom scrollbar para la consola */
        .terminal-body::-webkit-scrollbar {
            width: 6px;
        }

        .terminal-body::-webkit-scrollbar-track {
            background: transparent;
        }

        .terminal-body::-webkit-scrollbar-thumb {
            background: #27273a;
            border-radius: 3px;
        }

        .terminal-body::-webkit-scrollbar-thumb:hover {
            background: #3f3f5a;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Adaptación Móvil */
        @media (max-width: 1024px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Encabezado de la HMI -->
    <header>
        <div class="header-title">
            <h1>HMI CNC - Sistema de Planificación de Corte</h1>
            <p>Controlador Inteligente de Trayectorias y validación de reglas de oxicorte</p>
        </div>
        <div class="machine-status">
            <span class="status-dot"></span>
            <span>SISTEMA ONLINE / CNC CONECTADO</span>
        </div>
    </header>

    <!-- Grid de HMI -->
    <div class="dashboard-grid">
        
        <!-- Panel de Control Izquierdo -->
        <div class="panel">
            <div class="panel-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-blue)"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line></svg>
                Parámetros Operativos
            </div>
            
            <form id="hmi-form" onsubmit="enviarPlanificacion(event)">
                <!-- Selector de Figura -->
                <div class="form-group">
                    <label for="select-figura">Geometría de Corte</label>
                    <select id="select-figura" name="figura" required>
                        <option value="Cuadrado">Cuadrado (Simple)</option>
                        <option value="Triangulo">Triángulo (Simple)</option>
                        <option value="Rombo">Rombo (Simple)</option>
                        <option value="Circulo">Círculo (Curva Compleja)</option>
                        <option value="Estrella">Estrella (Ángulos Complejos)</option>
                    </select>
                </div>

                <!-- Selector de Material -->
                <div class="form-group">
                    <label for="select-material">Material de la Placa</label>
                    <select id="select-material" name="material" required>
                        <option value="acero">Acero al Carbono</option>
                        <option value="aluminio">Aluminio</option>
                        <option value="madera">Madera prensada (Laser/Soplete)</option>
                    </select>
                </div>

                <!-- Deslizador de Presión de Gas -->
                <div class="form-group">
                    <div class="slider-container">
                        <div class="slider-header">
                            <label style="margin-bottom: 0;">Presión de Gas</label>
                            <span class="slider-value" id="val-presion">5.0 bar</span>
                        </div>
                        <input type="range" id="input-presion" name="presion" min="0.0" max="10.0" step="0.1" value="5.0" oninput="actualizarSlider(this.value)">
                        <div class="slider-limits">
                            <span>0.0 bar (Min)</span>
                            <span>10.0 bar (Max)</span>
                        </div>
                    </div>
                </div>

                <!-- Botón Ejecutar -->
                <button type="submit" class="btn-planificar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    Validar y Planificar
                </button>
            </form>

            <!-- Card Dinámica del Sistema Experto -->
            <div id="expert-card" class="expert-card">
                <div class="expert-header" id="expert-title">
                    <!-- Icono dinámico cargado por JS -->
                    <span></span>
                </div>
                <div id="expert-message" style="line-height: 1.4;"></div>
                
                <div id="expert-params-box" class="expert-params">
                    <span class="param-label">Potencia Sugerida:</span>
                    <span class="param-value" id="res-potencia">-</span>
                    <span class="param-label">Velocidad Corte:</span>
                    <span class="param-value" id="res-velocidad">-</span>
                    <span class="param-label">Presión Requerida:</span>
                    <span class="param-value" id="res-presion-min">-</span>
                    <div class="complex-badge" id="complex-badge">Ajuste de inercia activo</div>
                </div>
            </div>
        </div>

        <!-- Columna Derecha: Canvas y Terminal -->
        <div class="main-content">
            <!-- Contenedor del Canvas -->
            <div class="canvas-container">
                <canvas id="cnc-canvas" width="850" height="480"></canvas>
            </div>

            <!-- Panel de Terminal -->
            <div class="terminal-panel">
                <div class="terminal-header">
                    <div class="terminal-dots">
                        <span class="dot dot-red"></span>
                        <span class="dot dot-yellow"></span>
                        <span class="dot dot-green"></span>
                    </div>
                    <span>Registro del Planificador DFS & Comandos G-Code</span>
                    <span style="color: var(--accent-blue); font-weight: bold;">[TERMINAL]</span>
                </div>
                <div class="terminal-body" id="cnc-console">>> HMI CNC cargada. Esperando parámetros operacionales...</div>
            </div>
        </div>

    </div>
</div>

<script>
    // Referencias de elementos
    const sliderVal = document.getElementById('val-presion');
    const consoleBox = document.getElementById('cnc-console');
    const canvas = document.getElementById('cnc-canvas');
    const ctx = canvas.getContext('2d');
    
    let animationId = null;

    // Inicializar la grilla oscura en el canvas al cargar
    resetCanvas();

    function actualizarSlider(val) {
        sliderVal.innerText = parseFloat(val).toFixed(1) + ' bar';
    }

    function resetCanvas() {
        ctx.fillStyle = '#1e1e24';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Dibujar grilla fina
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.lineWidth = 1;
        for (let x = 0; x < canvas.width; x += 30) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += 30) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
        
        // Ejes X/Y iniciales
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(60, canvas.height - 60);
        ctx.lineTo(canvas.width - 20, canvas.height - 60);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(60, canvas.height - 60);
        ctx.lineTo(60, 20);
        ctx.stroke();
        
        // Punto de origen
        ctx.beginPath();
        ctx.arc(60, canvas.height - 60, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#00ff88';
        ctx.fill();
        
        ctx.fillStyle = '#00ff88';
        ctx.font = 'bold 10px Outfit';
        ctx.fillText('Origen (0,0)', 70, canvas.height - 65);
    }

    async function enviarPlanificacion(e) {
        e.preventDefault();
        
        const figura = document.getElementById('select-figura').value;
        const material = document.getElementById('select-material').value;
        const presion = parseFloat(document.getElementById('input-presion').value);
        
        // Limpiar animaciones previas
        if (animationId) {
            clearTimeout(animationId);
            animationId = null;
        }
        
        // Registrar en terminal inicio de petición
        consoleBox.innerHTML = `>> Solicitando validación del sistema experto y planificación DFS para Figura: ${figura}, Material: ${material}, Presión: ${presion.toFixed(1)} bar...\\n`;
        consoleBox.scrollTop = consoleBox.scrollHeight;
        
        try {
            const response = await fetch('/api/planificar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ figura, material, presion_gas: presion })
            });
            
            const data = await response.json();
            
            const expertCard = document.getElementById('expert-card');
            const expertTitle = document.getElementById('expert-title');
            const expertMsg = document.getElementById('expert-message');
            const resPotencia = document.getElementById('res-potencia');
            const resVelocidad = document.getElementById('res-velocidad');
            const resPresionMin = document.getElementById('res-presion-min');
            const complexBadge = document.getElementById('complex-badge');
            
            if (data.aprobado) {
                // Caso exitoso - Luz verde
                expertCard.className = 'expert-card success';
                expertTitle.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> SISTEMA OPERATIVO - LUZ VERDE`;
                expertMsg.innerText = data.motivo;
                
                // Cargar valores recomendados
                resPotencia.innerText = data.potencia;
                resVelocidad.innerText = data.velocidad;
                resPresionMin.innerText = `${data.presion_min.toFixed(1)} bar`;
                
                document.getElementById('expert-params-box').style.display = 'grid';
                
                if (data.geometria_compleja) {
                    complexBadge.style.display = 'block';
                    complexBadge.innerText = "Mitigación de Inercia Activa (G01 Fino)";
                } else {
                    complexBadge.style.display = 'none';
                }
                
                // Mostrar pasos en consola
                consoleBox.innerHTML += `>> [SISTEMA EXPERTO] Aprobado. Iniciando planificación LIFO DFS...\\n`;
                data.listado_pasos.forEach(paso => {
                    consoleBox.innerHTML += `${paso}\\n`;
                });
                consoleBox.scrollTop = consoleBox.scrollHeight;
                
                // Iniciar simulación de trazado en el canvas
                animarCNC(data.coordenadas);
                
            } else {
                // Caso rechazado - Luz roja (Bloqueo de seguridad)
                expertCard.className = 'expert-card error';
                expertTitle.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> ALERTA - BLOQUEO DE SEGURIDAD`;
                expertMsg.innerText = data.motivo;
                
                document.getElementById('expert-params-box').style.display = 'none';
                
                consoleBox.innerHTML += `\\n>> [ERROR] BLOQUEO DE SEGURIDAD: Inferencia abortada. Motivo: ${data.motivo}\\n`;
                consoleBox.scrollTop = consoleBox.scrollHeight;
                
                // Limpiar y resetear el canvas (no hay animación por seguridad)
                resetCanvas();
            }
            
        } catch (err) {
            consoleBox.innerHTML += `\\n>> [ERROR COMUNICACIÓN] Error al conectar con el servidor: ${err.message}\\n`;
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    }

    function animarCNC(coordenadas) {
        const scale = 2.0;
        const marginLeft = 60;
        const marginBottom = 60;
        
        function toCanvas(x, y) {
            return {
                cx: marginLeft + x * scale,
                cy: canvas.height - marginBottom - y * scale
            };
        }
        
        let currentStep = 0;
        let t = 0; 
        const speedFactor = 0.08; // Velocidad de la animación (tasa de incremento)
        let lineHistory = [];
        
        function drawGrid() {
            ctx.fillStyle = '#1e1e24';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Grilla fina
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
            ctx.lineWidth = 1;
            for (let x = 0; x < canvas.width; x += 30) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            for (let y = 0; y < canvas.height; y += 30) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
            
            // Ejes X e Y
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 2;
            
            // Eje X
            ctx.beginPath();
            ctx.moveTo(marginLeft, canvas.height - marginBottom);
            ctx.lineTo(canvas.width - 20, canvas.height - marginBottom);
            ctx.stroke();
            
            // Eje Y
            ctx.beginPath();
            ctx.moveTo(marginLeft, canvas.height - marginBottom);
            ctx.lineTo(marginLeft, 20);
            ctx.stroke();
            
            // Leyenda de ejes
            ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.font = '10px Outfit';
            ctx.fillText('X (mm)', canvas.width - 45, canvas.height - marginBottom + 15);
            ctx.fillText('Y (mm)', marginLeft - 45, 30);
            
            // Graduación de ejes
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.font = '9px Outfit';
            for (let v = 0; v <= 200; v += 50) {
                const {cx, cy} = toCanvas(v, 0);
                ctx.fillText(v, cx - 8, canvas.height - marginBottom + 15);
                ctx.beginPath();
                ctx.moveTo(cx, canvas.height - marginBottom);
                ctx.lineTo(cx, canvas.height - marginBottom - 5);
                ctx.stroke();
                
                const {cx: cx_y, cy: cy_y} = toCanvas(0, v);
                if (v > 0) {
                    ctx.fillText(v, marginLeft - 25, cy_y + 3);
                    ctx.beginPath();
                    ctx.moveTo(marginLeft, cy_y);
                    ctx.lineTo(marginLeft + 5, cy_y);
                    ctx.stroke();
                }
            }
        }
        
        function renderFrame() {
            drawGrid();
            
            // 1. Origen en verde brillante
            const origin = toCanvas(0, 0);
            ctx.beginPath();
            ctx.arc(origin.cx, origin.cy, 6, 0, 2 * Math.PI);
            ctx.fillStyle = '#00ff88';
            ctx.shadowColor = '#00ff88';
            ctx.shadowBlur = 10;
            ctx.fill();
            ctx.shadowBlur = 0;
            
            ctx.fillStyle = '#00ff88';
            ctx.font = 'bold 10px Outfit';
            ctx.fillText('Origen (0,0)', origin.cx + 10, origin.cy + 12);
            
            // 2. Vértices en azul numerados cronológicamente
            coordenadas.forEach((pt, idx) => {
                if (idx === 0) return; // Salta el origen
                const {cx, cy} = toCanvas(pt.x, pt.y);
                
                ctx.beginPath();
                ctx.arc(cx, cy, 5, 0, 2 * Math.PI);
                ctx.fillStyle = '#00f0ff';
                ctx.shadowColor = '#00f0ff';
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
                
                ctx.fillStyle = '#f8fafc';
                ctx.font = 'bold 10px Outfit';
                ctx.fillText(`P${idx}`, cx + 8, cy - 4);
            });
            
            // 3. Historial de líneas dibujadas
            lineHistory.forEach(line => {
                ctx.beginPath();
                ctx.moveTo(line.from.cx, line.from.cy);
                ctx.lineTo(line.to.cx, line.to.cy);
                
                if (line.operacion === 'Corte_Lineal' || line.operacion === 'Apagar_Soplete') {
                    ctx.strokeStyle = '#ff3366'; // Rojo de corte activo
                    ctx.lineWidth = 3.5;
                    ctx.shadowColor = '#ff3366';
                    ctx.shadowBlur = 4;
                } else {
                    ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)'; // Traslado rápido celeste
                    ctx.lineWidth = 1.5;
                    ctx.setLineDash([5, 5]);
                }
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.shadowBlur = 0;
            });
            
            // 4. Dibujar segmento actual en progreso
            if (currentStep < coordenadas.length - 1) {
                const pFrom = coordenadas[currentStep];
                const pTo = coordenadas[currentStep + 1];
                
                const from = toCanvas(pFrom.x, pFrom.y);
                const to = toCanvas(pTo.x, pTo.y);
                
                // Interpolar coordenadas
                const curCx = from.cx + (to.cx - from.cx) * t;
                const curCy = from.cy + (to.cy - from.cy) * t;
                
                ctx.beginPath();
                ctx.moveTo(from.cx, from.cy);
                ctx.lineTo(curCx, curCy);
                
                const op = pTo.operacion;
                if (op === 'Corte_Lineal' || op === 'Apagar_Soplete') {
                    ctx.strokeStyle = '#ff3366';
                    ctx.lineWidth = 3.5;
                    ctx.shadowColor = '#ff3366';
                    ctx.shadowBlur = 6;
                } else {
                    ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
                    ctx.lineWidth = 1.5;
                    ctx.setLineDash([5, 5]);
                }
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.shadowBlur = 0;
                
                // Mostrar el cabezal del soplete con chispas de fuego
                drawTorch(curCx, curCy, op === 'Corte_Lineal' || op === 'Apagar_Soplete');
                
                t += speedFactor;
                if (t >= 1) {
                    lineHistory.push({ from, to, operacion: op });
                    t = 0;
                    currentStep++;
                }
                
                animationId = setTimeout(renderFrame, 30);
            } else {
                // Dibujar cabezal de reposo final
                const pLast = coordenadas[coordenadas.length - 1];
                const last = toCanvas(pLast.x, pLast.y);
                drawTorch(last.cx, last.cy, false);
                
                consoleBox.innerHTML += `>> [CNC] Proceso de corte finalizado. Cabezal retornado a origen o apagado.\\n`;
                consoleBox.scrollTop = consoleBox.scrollHeight;
            }
        }
        
        function drawTorch(cx, cy, isCutting) {
            ctx.beginPath();
            ctx.arc(cx, cy, 9, 0, 2 * Math.PI);
            ctx.fillStyle = '#475569';
            ctx.strokeStyle = '#cbd5e1';
            ctx.lineWidth = 2.5;
            ctx.fill();
            ctx.stroke();
            
            ctx.beginPath();
            ctx.arc(cx, cy, 3, 0, 2 * Math.PI);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
            
            if (isCutting) {
                // Llama de plasma CNC
                ctx.beginPath();
                ctx.arc(cx, cy, 16, 0, 2 * Math.PI);
                let grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 16);
                grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
                grad.addColorStop(0.2, '#ffea00');
                grad.addColorStop(0.6, '#ff3300');
                grad.addColorStop(1, 'rgba(255, 0, 0, 0)');
                ctx.fillStyle = grad;
                ctx.shadowColor = '#ff5100';
                ctx.shadowBlur = 12;
                ctx.fill();
                ctx.shadowBlur = 0;
                
                // Emisión de partículas
                for (let i = 0; i < 5; i++) {
                    const px = cx + (Math.random() - 0.5) * 25;
                    const py = cy + (Math.random() - 0.5) * 25;
                    ctx.beginPath();
                    ctx.arc(px, py, Math.random() * 2.5, 0, 2 * Math.PI);
                    ctx.fillStyle = '#ffb300';
                    ctx.fill();
                }
            }
        }
        
        renderFrame();
    }
</script>
</body>
</html>
"""

# ----------------- FLASK ROUTING -----------------

@app.route('/')
def home():
    """
    Sirve la interfaz HMI completa renderizando el template unificado.
    """
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/planificar', methods=['POST'])
def planificar():
    """
    Endpoint de la API que recibe datos de usuario (figura, material, presion_gas)
    y ejecuta el Sistema Experto y el planificador DFS.
    """
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
        # Cargar base de datos del archivo Excel
        df_figuras, df_parametros = cargar_base_conocimientos()
        
        # 1. Evaluar el Sistema Experto de Reglas
        resultado_experto = evaluar_sistema_experto(figura, material, presion_gas, df_parametros)
        
        # Si el sistema experto rechaza la operación, se aborta y retorna inmediatamente
        if not resultado_experto["aprobado"]:
            return jsonify({
                "aprobado": False,
                "motivo": resultado_experto["motivo"]
            })
            
        # 2. Si es aprobado, ejecutar el planificador de ruta DFS (LIFO)
        resultado_cnc = planificar_dfs_iterativo(figura, df_figuras)
        if resultado_cnc is None:
            return jsonify({
                "aprobado": False,
                "motivo": f"No se encontraron coordenadas para la figura '{figura}' en el dataset."
            })
            
        # 3. Retornar los resultados unificados de planificación e inferencia
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

# ----------------- MAIN ENTRY POINT -----------------

if __name__ == '__main__':
    print("Iniciando el servidor de HMI CNC en: http://127.0.0.1:5000")
    # Iniciar Flask en modo debug para desarrollo local
    app.run(host='127.0.0.1', port=5000, debug=True)
