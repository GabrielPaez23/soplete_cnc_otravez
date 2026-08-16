<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMI CNC - Panel de Control e Inspección 3D</title>
    <!-- Importación de Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <!-- CSS Estilos -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">

    <!-- Import Map para dependencias ES Modules de Three.js -->
    <script type="importmap">
      {
        "imports": {
          "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
          "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
        }
      }
    </script>
</head>
<body>

<div class="container">
    <!-- Encabezado de la HMI -->
    <header>
        <div class="header-title">
            <h1>HMI CNC - Sistema de Planificación e Inspección 3D</h1>
            <p>Controlador Inteligente de Trayectorias y Análisis tridimensional de piezas</p>
        </div>
        <div class="machine-status">
            <span class="status-dot"></span>
            <span>SISTEMA ONLINE / CNC & VISOR 3D CONECTADOS</span>
        </div>
    </header>

    <!-- Grid Principal de la HMI -->
    <div class="dashboard-grid">
        
        <!-- Columna Izquierda: Panel de Controles -->
        <div class="panel">
            <div class="panel-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line></svg>
                Parámetros Operativos
            </div>
            
            <form id="hmi-form">
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

                <!-- Deslizador de Presión -->
                <div class="form-group">
                    <div class="slider-container">
                        <div class="slider-header">
                            <label style="margin-bottom: 0;">Presión de Gas</label>
                            <span class="slider-value" id="val-presion">5.0 bar</span>
                        </div>
                        <input type="range" id="input-presion" name="presion" min="0.0" max="10.0" step="0.1" value="5.0">
                        <div class="slider-limits">
                            <span>0.0 bar (Min)</span>
                            <span>10.0 bar (Max)</span>
                        </div>
                    </div>
                </div>

                <!-- Botón de Planificación -->
                <button type="submit" class="btn-planificar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    Validar y Planificar
                </button>
            </form>

            <!-- Card del Sistema Experto -->
            <div id="expert-card" class="expert-card">
                <div class="expert-header" id="expert-title">
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

        <!-- Columna Central: Canvas 2D + Terminal -->
        <div class="main-content">
            <div class="canvas-container">
                <div class="view-tag">PLANO 2D (TRAYECTORIA G-CODE)</div>
                <canvas id="cnc-canvas" width="850" height="380"></canvas>
            </div>

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

        <!-- Columna Derecha: Visor 3D Three.js -->
        <div class="viewport-3d-panel">
            <div class="panel-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
                Visor Tridimensional
            </div>
            
            <div class="container-3d" id="container-3d">
                <div class="view-tag">VISOR 3D (INTERACTIVO)</div>
                <!-- Contenedor overlay para datos telemetria 3D -->
                <div class="overlay-3d-info">
                    <div>ESCALA EJE (MAX): <span id="telemetry-scale">0 mm</span></div>
                    <div>ESTADO 3D: <span id="telemetry-status" style="color: var(--accent-green);">ESPERA</span></div>
                </div>
            </div>
            <p class="help-text-3d">Clic izquierdo: Rotar | Clic derecho: Trasladar | Rueda: Zoom</p>
        </div>

    </div>
</div>

<!-- Carga del script principal tipo ES Module -->
<script type="module" src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>