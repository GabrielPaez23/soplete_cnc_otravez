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

.container {
    max-width: 1750px;
    margin: 0 auto;
}

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
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #ffffff, #94a3b8);
    background-clip: text;
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

/* Grid de 3 Columnas */
.dashboard-grid {
    display: grid;
    grid-template-columns: 340px 1fr 480px;
    gap: 20px;
    align-items: start;
}

.panel, .viewport-3d-panel {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    backdrop-filter: blur(10px);
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    transition: border-color 0.3s;
}

.panel-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.form-group {
    margin-bottom: 16px;
}

label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 6px;
    letter-spacing: 0.5px;
}

select {
    width: 100%;
    background: rgba(15, 15, 19, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    padding: 10px;
    font-family: var(--font-sans);
    font-size: 13px;
    outline: none;
    cursor: pointer;
    transition: all 0.3s;
}

select:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.15);
}

.slider-container {
    background: rgba(15, 15, 19, 0.6);
    padding: 12px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.slider-header {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
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
}

.slider-limits {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--text-secondary);
    margin-top: 6px;
}

.btn-planificar {
    width: 100%;
    background: linear-gradient(135deg, #0052d4 0%, #4364f7 50%, #6fb1fc 100%);
    border: none;
    border-radius: 8px;
    color: white;
    padding: 12px;
    font-family: var(--font-sans);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(67, 100, 247, 0.4);
    transition: all 0.3s;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
}

.btn-planificar:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(67, 100, 247, 0.55);
}

/* Tarjeta del Sistema Experto */
.expert-card {
    margin-top: 16px;
    border-radius: 8px;
    padding: 14px;
    display: none;
    font-size: 13px;
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
    font-size: 11px;
    margin-bottom: 8px;
}

.expert-params {
    margin-top: 10px;
    background: rgba(0,0,0,0.25);
    border-radius: 6px;
    padding: 10px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    font-size: 11px;
}

.param-label { color: var(--text-secondary); }
.param-value { font-weight: 600; color: var(--text-primary); text-align: right; }

.complex-badge {
    grid-column: span 2;
    background: rgba(0, 240, 255, 0.12);
    border: 1px solid rgba(0, 240, 255, 0.25);
    color: var(--accent-blue);
    padding: 4px;
    border-radius: 4px;
    text-align: center;
    font-weight: 700;
    font-size: 9px;
    text-transform: uppercase;
}

/* Canvas 2D y Main Content */
.main-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.canvas-container {
    position: relative;
    background: #1e1e24;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
}

.view-tag {
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid var(--border-color);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--text-secondary);
    pointer-events: none;
    z-index: 10;
}

canvas {
    display: block;
    width: 100%;
    height: 380px;
}

/* Terminal Console */
.terminal-panel {
    background: #09090c;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    font-family: var(--font-mono);
    padding: 14px;
}

.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 6px;
    margin-bottom: 10px;
    font-size: 10px;
    color: var(--text-secondary);
}

.terminal-dots { display: flex; gap: 4px; }
.dot { width: 7px; height: 7px; border-radius: 50%; }
.dot-red { background: #ef4444; }
.dot-yellow { background: #f59e0b; }
.dot-green { background: #10b981; }

.terminal-body {
    height: 150px;
    overflow-y: auto;
    color: #38bdf8;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
}

/* Estilos de la Columna Visor 3D Three.js */
.viewport-3d-panel {
    display: flex;
    flex-direction: column;
}

.container-3d {
    position: relative;
    width: 100%;
    height: 520px;
    background: #09090d;
    border: 1px solid var(--border-color);
    border-radius: 10px;
    overflow: hidden;
}

.overlay-3d-info {
    position: absolute;
    bottom: 10px;
    left: 10px;
    background: rgba(15, 15, 20, 0.85);
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-secondary);
    display: flex;
    flex-direction: column;
    gap: 4px;
    pointer-events: none;
    z-index: 10;
}

.help-text-3d {
    font-size: 11px;
    color: var(--text-secondary);
    text-align: center;
    margin-top: 8px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Adaptación para pantallas de menor resolución */
@media (max-width: 1400px) {
    .dashboard-grid {
        grid-template-columns: 320px 1fr;
    }
    .viewport-3d-panel {
        grid-column: span 2;
    }
}

@media (max-width: 900px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    .viewport-3d-panel {
        grid-column: span 1;
    }
}