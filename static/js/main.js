import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ==========================================
// CONFIGURACIÓN RUTA MODELO GLTF/GLB Y ESCALA
// ==========================================
const MODEL_PATH = '/static/models/brazo_cnc.glb';

// Referencias del DOM
const sliderVal = document.getElementById('val-presion');
const sliderInput = document.getElementById('input-presion');
const consoleBox = document.getElementById('cnc-console');
const canvas2D = document.getElementById('cnc-canvas');
const ctx2D = canvas2D.getContext('2d');
const formHMI = document.getElementById('hmi-form');
const selectFigura = document.getElementById('select-figura');
const btnPlanificar = document.getElementById('btn-planificar');

// Módulo de Vectorización DOM
const inputImagen = document.getElementById('input-imagen');
const fileNameDisplay = document.getElementById('file-name-display');
const btnVectorizar = document.getElementById('btn-vectorizar');
const btnGuardarDataset = document.getElementById('btn-guardar-dataset');
const dropZone = document.getElementById('drop-zone');
const vectorStatusCard = document.getElementById('vector-status-card');
const metricVertices = document.getElementById('metric-vertices');
const metricDims = document.getElementById('metric-dims');
const canvasViewTag = document.getElementById('canvas-view-tag');

// Estado de vectorización para dataset
let puntosNormActuales = [];
let imagenBase64Actual = null;

const telemetryScale = document.getElementById('telemetry-scale');
const telemetryStatus = document.getElementById('telemetry-status');

let animation2DId = null;
let archivoImagenSeleccionado = null;
let figuraVectorizadaActual = null;

// ==========================================
// VARIABLES GLOBALES VISOR THREE.JS Y SIMULACIÓN
// ==========================================
let scene3D, camera3D, renderer3D, controls3D;
let loadedModel = null;
let gridHelper3D = null;
let axesHelper3D = null;

// Elementos de simulación
let metalPlate = null;
let sopleteNozzle = null;
let sopleteLight = null;
let sopleteFlame = null;
let path3DGroup = null;
let robotWrapper = null;

// Inicialización general al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
    initCartesianCanvas2D();
    init3DViewport();
    actualizarListadoFiguras();
    setupEventosVectorizacion();
    
    // Escuchar el deslizador de presión
    sliderInput.addEventListener('input', (e) => {
        sliderVal.innerText = parseFloat(e.target.value).toFixed(1) + ' bar';
    });

    // Evento del formulario HMI (Validar y Planificar)
    formHMI.addEventListener('submit', enviarPlanificacion);
});

// ==========================================
// 1. INICIALIZACIÓN Y MOTOR THREE.JS
// ==========================================
function init3DViewport() {
    const container = document.getElementById('container-3d');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Escena con niebla ambiental para profundidad técnica
    scene3D = new THREE.Scene();
    scene3D.background = new THREE.Color(0x09090d);
    scene3D.fog = new THREE.FogExp2(0x09090d, 0.002);

    // Cámara Perspectiva
    camera3D = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    camera3D.position.set(90, 85, 95);

    // Renderizador WebGL
    renderer3D = new THREE.WebGLRenderer({ antialias: true });
    renderer3D.setSize(width, height);
    renderer3D.setPixelRatio(window.devicePixelRatio || 1);
    renderer3D.shadowMap.enabled = false;
    container.appendChild(renderer3D.domElement);

    // Controles Orbitales de Cámara
    controls3D = new OrbitControls(camera3D, renderer3D.domElement);
    controls3D.enableDamping = true;
    controls3D.dampingFactor = 0.05;
    controls3D.target.set(35, 5, 0);

    // Iluminación Técnica
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
    scene3D.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x00f0ff, 1.2);
    dirLight1.position.set(100, 200, 100);
    scene3D.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xff3366, 0.5);
    dirLight2.position.set(-100, -50, -100);
    scene3D.add(dirLight2);

    // Rejilla de referencia en el plano del suelo
    gridHelper3D = new THREE.GridHelper(160, 16, 0x00f0ff, 0x27273a);
    gridHelper3D.position.y = 0;
    scene3D.add(gridHelper3D);

    // Wrapper para el brazo robótico
    robotWrapper = new THREE.Group();
    robotWrapper.position.set(0, 0, 0);
    scene3D.add(robotWrapper);

    // Cargar objetos auxiliares de simulación
    setupSimulationObjects();

    // Cargar el Modelo GLTF/GLB del Brazo Robótico
    cargarModeloGLTF(MODEL_PATH);

    // Manejo de cambio de tamaño de ventana
    window.addEventListener('resize', onWindowResize3D);

    // Bucle de Renderizado
    function animate3D() {
        requestAnimationFrame(animate3D);
        controls3D.update();
        renderer3D.render(scene3D, camera3D);
    }
    animate3D();
}

function setupSimulationObjects() {
    path3DGroup = new THREE.Group();
    scene3D.add(path3DGroup);

    // Placa metálica (chapa) frente al robot
    const plateGeo = new THREE.BoxGeometry(120, 1.5, 120);
    const plateMat = new THREE.MeshStandardMaterial({
        color: 0x3a3b46,
        roughness: 0.4,
        metalness: 0.7
    });
    metalPlate = new THREE.Mesh(plateGeo, plateMat);
    metalPlate.position.set(45, -0.8, 0);
    scene3D.add(metalPlate);

    // Boquilla / Soplete móvil
    sopleteNozzle = new THREE.Group();
    
    const bodyGeo = new THREE.CylinderGeometry(2, 1, 15, 12);
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x5a5a6a, metalness: 0.9, roughness: 0.1 });
    const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    bodyMesh.position.y = 7.5;
    sopleteNozzle.add(bodyMesh);

    // Llama de plasma
    const flameGeo = new THREE.ConeGeometry(1.5, 6, 12);
    flameGeo.rotateX(Math.PI);
    sopleteFlame = new THREE.Mesh(flameGeo, new THREE.MeshBasicMaterial({ color: 0xff3366 }));
    sopleteFlame.position.y = -3;
    sopleteFlame.visible = false;
    sopleteNozzle.add(sopleteFlame);

    // Luz de plasma
    sopleteLight = new THREE.PointLight(0xff3366, 0, 80);
    sopleteLight.position.y = 0;
    sopleteNozzle.add(sopleteLight);

    scene3D.add(sopleteNozzle);
    actualizarPosicionSoplete(45, 0, false);
}

function actualizarPosicionSoplete(x, z, activo) {
    if (sopleteNozzle) {
        sopleteNozzle.position.set(x, 1.0, z);
    }
    if (sopleteFlame) {
        sopleteFlame.visible = activo;
        if (activo) {
            const scaleFactor = 0.8 + Math.random() * 0.4;
            sopleteFlame.scale.set(scaleFactor, scaleFactor, scaleFactor);
        }
    }
    if (sopleteLight) {
        sopleteLight.intensity = activo ? (3.0 + Math.random() * 1.5) : 0;
    }
    
    if (robotWrapper) {
        const angle = Math.atan2(x, z);
        robotWrapper.rotation.y = angle + Math.PI / 2;
    }
}

function cargarModeloGLTF(path) {
    const loader = new GLTFLoader();

    loader.load(path, (gltf) => {
        const model = gltf.scene;
        loadedModel = model;

        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        const maxDim = Math.max(size.x, size.y, size.z);
        let scale = 1.0;
        if (maxDim > 0) {
            scale = 40 / maxDim;
            model.scale.set(scale, scale, scale);
        }
        
        model.position.x = -center.x * scale;
        model.position.y = -box.min.y * scale;
        model.position.z = -center.z * scale;
        
        robotWrapper.add(model);
        robotWrapper.rotation.set(0, 0, 0);

        model.traverse((child) => {
            if (child.isMesh) {
                child.material.side = THREE.DoubleSide;
            }
        });

        if (telemetryStatus) {
            telemetryStatus.innerText = 'ONLINE / LISTO';
            telemetryStatus.style.color = 'var(--accent-green)';
        }
    }, undefined, (error) => {
        console.warn("No se pudo cargar modelo .glb externo. Usando modelo procedural CNC.");
        const fallback = crearModeloGenericoCNC();
        robotWrapper.add(fallback);
        loadedModel = fallback;
    });
}

function crearModeloGenericoCNC() {
    const grupoCNC = new THREE.Group();
    const matBase = new THREE.MeshStandardMaterial({ color: 0x1e1e28, roughness: 0.5 });
    const matCyan = new THREE.MeshStandardMaterial({ color: 0x00f0ff, roughness: 0.2, metalness: 0.8 });
    const matSoplete = new THREE.MeshStandardMaterial({ color: 0xff3366, emissive: 0x330011 });

    const base = new THREE.Mesh(new THREE.CylinderGeometry(25, 30, 8, 32), matBase);
    base.position.y = 4;
    grupoCNC.add(base);

    const mastil = new THREE.Mesh(new THREE.BoxGeometry(10, 70, 10), matCyan);
    mastil.position.set(0, 39, 0);
    grupoCNC.add(mastil);

    const brazo = new THREE.Mesh(new THREE.BoxGeometry(80, 8, 8), matBase);
    brazo.position.set(25, 70, 0);
    grupoCNC.add(brazo);

    const cabezal = new THREE.Mesh(new THREE.ConeGeometry(5, 15, 16), matSoplete);
    cabezal.rotation.x = Math.PI;
    cabezal.position.set(60, 58, 0);
    grupoCNC.add(cabezal);

    return grupoCNC;
}

function onWindowResize3D() {
    const container = document.getElementById('container-3d');
    if (!container) return;
    camera3D.aspect = container.clientWidth / container.clientHeight;
    camera3D.updateProjectionMatrix();
    renderer3D.setSize(container.clientWidth, container.clientHeight);
}

// ==========================================
// 2. PLANO CARTESIANO 2D INTERACTIVO
// ==========================================
function initCartesianCanvas2D() {
    dibujarPlanoCartesianoBase();
}

function dibujarPlanoCartesianoBase() {
    ctx2D.fillStyle = '#15151c';
    ctx2D.fillRect(0, 0, canvas2D.width, canvas2D.height);

    const margin = 45;
    const cw = canvas2D.width;
    const ch = canvas2D.height;
    const scale = 1.7; // Factor de conversión mm a píxeles

    // 1. Grilla milimétrica fina (cada 10 mm y 20 mm)
    for (let mm = 0; mm <= 200; mm += 10) {
        const px = margin + mm * scale;
        const py = ch - margin - mm * scale;

        const isMajor = (mm % 50 === 0);

        // Líneas verticales (X)
        if (px <= cw - 15) {
            ctx2D.beginPath();
            ctx2D.strokeStyle = isMajor ? 'rgba(0, 240, 255, 0.15)' : 'rgba(255, 255, 255, 0.04)';
            ctx2D.lineWidth = isMajor ? 1.2 : 0.8;
            ctx2D.moveTo(px, 15);
            ctx2D.lineTo(px, ch - margin);
            ctx2D.stroke();

            // Etiqueta del eje X
            if (isMajor) {
                ctx2D.fillStyle = 'rgba(255, 255, 255, 0.5)';
                ctx2D.font = '10px JetBrains Mono';
                ctx2D.textAlign = 'center';
                ctx2D.fillText(`${mm}`, px, ch - margin + 15);
            }
        }

        // Líneas horizontales (Y)
        if (py >= 15) {
            ctx2D.beginPath();
            ctx2D.strokeStyle = isMajor ? 'rgba(0, 240, 255, 0.15)' : 'rgba(255, 255, 255, 0.04)';
            ctx2D.lineWidth = isMajor ? 1.2 : 0.8;
            ctx2D.moveTo(margin, py);
            ctx2D.lineTo(cw - 15, py);
            ctx2D.stroke();

            // Etiqueta del eje Y
            if (isMajor) {
                ctx2D.fillStyle = 'rgba(255, 255, 255, 0.5)';
                ctx2D.font = '10px JetBrains Mono';
                ctx2D.textAlign = 'right';
                ctx2D.fillText(`${mm}`, margin - 8, py + 3);
            }
        }
    }

    // 2. Límites del Área de Trabajo CNC (Chapa de 200 x 200 mm)
    const plateWidth = 200 * scale;
    const plateHeight = 200 * scale;
    ctx2D.strokeStyle = 'rgba(0, 240, 255, 0.3)';
    ctx2D.lineWidth = 1;
    ctx2D.setLineDash([4, 4]);
    ctx2D.strokeRect(margin, ch - margin - plateHeight, plateWidth, plateHeight);
    ctx2D.setLineDash([]);

    // 3. Ejes Principales Cartesiano X e Y
    ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx2D.lineWidth = 2;

    // Eje X
    ctx2D.beginPath();
    ctx2D.moveTo(margin, ch - margin);
    ctx2D.lineTo(cw - 15, ch - margin);
    ctx2D.stroke();

    // Eje Y
    ctx2D.beginPath();
    ctx2D.moveTo(margin, ch - margin);
    ctx2D.lineTo(margin, 15);
    ctx2D.stroke();

    // Títulos de ejes
    ctx2D.fillStyle = 'var(--accent-blue)';
    ctx2D.font = 'bold 11px Outfit';
    ctx2D.textAlign = 'right';
    ctx2D.fillText('EJE X (mm) ➔', cw - 20, ch - margin + 30);

    ctx2D.textAlign = 'left';
    ctx2D.fillText('▲ EJE Y (mm)', margin - 35, 25);

    // 4. Punto Origen (0,0) CNC
    ctx2D.beginPath();
    ctx2D.arc(margin, ch - margin, 6, 0, 2 * Math.PI);
    ctx2D.fillStyle = '#00ff88';
    ctx2D.fill();

    ctx2D.fillStyle = '#00ff88';
    ctx2D.font = 'bold 11px Outfit';
    ctx2D.textAlign = 'left';
    ctx2D.fillText('Origen (0,0) [G00]', margin + 10, ch - margin - 8);
}

/**
 * Grafica la figura vectorizada en tiempo real sobre el plano cartesiano
 * inmediatamente después de ser procesada por la red neuronal / visión.
 */
function graficarPrevisualizacionCartesiana(coordenadas, figuraNombre) {
    if (animation2DId) clearTimeout(animation2DId);
    dibujarPlanoCartesianoBase();

    const margin = 45;
    const scale = 1.7;
    const ch = canvas2D.height;

    function toCanvas(x, y) {
        return {
            cx: margin + x * scale,
            cy: ch - margin - y * scale
        };
    }

    if (!coordenadas || coordenadas.length === 0) return;

    // 1. Trazar líneas vectoriales de la figura
    ctx2D.lineWidth = 2.5;
    ctx2D.strokeStyle = '#00f0ff';
    ctx2D.shadowColor = 'rgba(0, 240, 255, 0.6)';
    ctx2D.shadowBlur = 8;

    // Trazado de traslado rápido inicial (Origen -> V1)
    const p0 = toCanvas(coordenadas[0].x, coordenadas[0].y);
    const p1 = toCanvas(coordenadas[1].x, coordenadas[1].y);

    ctx2D.beginPath();
    ctx2D.setLineDash([5, 5]);
    ctx2D.strokeStyle = 'rgba(0, 240, 255, 0.4)';
    ctx2D.moveTo(p0.cx, p0.cy);
    ctx2D.lineTo(p1.cx, p1.cy);
    ctx2D.stroke();
    ctx2D.setLineDash([]);

    // Trazado del contorno cerrado de corte
    ctx2D.beginPath();
    ctx2D.strokeStyle = '#00ff88';
    ctx2D.shadowColor = 'rgba(0, 255, 136, 0.6)';
    ctx2D.shadowBlur = 10;
    ctx2D.moveTo(p1.cx, p1.cy);

    for (let i = 2; i < coordenadas.length; i++) {
        const pt = toCanvas(coordenadas[i].x, coordenadas[i].y);
        ctx2D.lineTo(pt.cx, pt.cy);
    }
    ctx2D.stroke();
    ctx2D.shadowBlur = 0;

    // 2. Graficar Vértices y sus etiquetas en el plano
    coordenadas.forEach((pt, index) => {
        if (pt.secuencia === 'Origen') return;

        const cp = toCanvas(pt.x, pt.y);
        const isCierre = pt.secuencia.includes('Cierre');
        
        ctx2D.beginPath();
        ctx2D.arc(cp.cx, cp.cy, isCierre ? 4 : 5, 0, 2 * Math.PI);
        ctx2D.fillStyle = isCierre ? '#ff3366' : '#00f0ff';
        ctx2D.fill();
        ctx2D.strokeStyle = '#ffffff';
        ctx2D.lineWidth = 1.5;
        ctx2D.stroke();

        // Etiqueta del vértice con coordenadas (X, Y)
        if (!isCierre) {
            ctx2D.fillStyle = '#f8fafc';
            ctx2D.font = 'bold 10px JetBrains Mono';
            ctx2D.fillText(`${pt.secuencia} (${pt.x},${pt.y})`, cp.cx + 8, cp.cy - 4);
        }
    });

    // Actualizar etiqueta del canvas
    if (canvasViewTag) {
        canvasViewTag.innerText = `PLANO CARTESIANO: ${figuraNombre.toUpperCase()} [PREVISUALIZACIÓN GEOMÉTRICA - LISTA PARA CORTE]`;
        canvasViewTag.style.color = 'var(--accent-green)';
    }
}

// ==========================================
// 3. MÓDULO DE INTEGRACIÓN DE VECTORIZACIÓN IA
// ==========================================
function setupEventosVectorizacion() {
    // Selección de archivo
    inputImagen.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            archivoImagenSeleccionado = e.target.files[0];
            fileNameDisplay.innerText = `Archivo: ${archivoImagenSeleccionado.name}`;
            fileNameDisplay.style.color = 'var(--accent-green)';
        }
    });

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-blue)';
        dropZone.style.backgroundColor = 'rgba(0, 240, 255, 0.08)';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(0, 240, 255, 0.3)';
        dropZone.style.backgroundColor = 'rgba(15, 15, 22, 0.7)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(0, 240, 255, 0.3)';
        dropZone.style.backgroundColor = 'rgba(15, 15, 22, 0.7)';
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            archivoImagenSeleccionado = e.dataTransfer.files[0];
            inputImagen.files = e.dataTransfer.files;
            fileNameDisplay.innerText = `Archivo: ${archivoImagenSeleccionado.name}`;
            fileNameDisplay.style.color = 'var(--accent-green)';
        }
    });

    // Botones de Muestras Rápidas
    document.querySelectorAll('.btn-sample').forEach(btn => {
        btn.addEventListener('click', () => {
            const presetName = btn.getAttribute('data-preset');
            cargarMuestraRapida(presetName);
        });
    });

    // Botón Principal: "Vectorizar"
    btnVectorizar.addEventListener('click', ejecutarVectorizacion);

    // Botón: "Guardar Muestra en Dataset"
    if (btnGuardarDataset) {
        btnGuardarDataset.addEventListener('click', guardarEnDataset);
    }
}

/**
 * Genera imágenes de prueba sintéticas para probar la vectorización con un clic
 */
function cargarMuestraRapida(tipo) {
    const offCanvas = document.createElement('canvas');
    offCanvas.width = 300;
    offCanvas.height = 300;
    const offCtx = offCanvas.getContext('2d');

    // Fondo negro
    offCtx.fillStyle = '#000000';
    offCtx.fillRect(0, 0, 300, 300);

    offCtx.fillStyle = '#ffffff';
    offCtx.strokeStyle = '#ffffff';

    if (tipo === 'engranaje') {
        const cx = 150, cy = 150, outerR = 100, innerR = 70, teeth = 8;
        offCtx.beginPath();
        for (let i = 0; i < teeth * 2; i++) {
            const r = (i % 2 === 0) ? outerR : innerR;
            const a = (i / (teeth * 2)) * Math.PI * 2;
            const x = cx + Math.cos(a) * r;
            const y = cy + Math.sin(a) * r;
            if (i === 0) offCtx.moveTo(x, y);
            else offCtx.lineTo(x, y);
        }
        offCtx.closePath();
        offCtx.fill();
    } else if (tipo === 'estrella_ninja') {
        const cx = 150, cy = 150, outerR = 110, innerR = 35, points = 4;
        offCtx.beginPath();
        for (let i = 0; i < points * 2; i++) {
            const r = (i % 2 === 0) ? outerR : innerR;
            const a = (i / (points * 2)) * Math.PI * 2;
            const x = cx + Math.cos(a) * r;
            const y = cy + Math.sin(a) * r;
            if (i === 0) offCtx.moveTo(x, y);
            else offCtx.lineTo(x, y);
        }
        offCtx.closePath();
        offCtx.fill();
    } else {
        // Soporte mecánico / bracket
        offCtx.beginPath();
        offCtx.moveTo(60, 60);
        offCtx.lineTo(240, 60);
        offCtx.lineTo(240, 140);
        offCtx.lineTo(180, 140);
        offCtx.lineTo(180, 240);
        offCtx.lineTo(60, 240);
        offCtx.closePath();
        offCtx.fill();
    }

    offCanvas.toBlob((blob) => {
        const file = new File([blob], `${tipo}.png`, { type: 'image/png' });
        archivoImagenSeleccionado = file;
        fileNameDisplay.innerText = `Muestra cargada: ${tipo}.png`;
        fileNameDisplay.style.color = 'var(--accent-blue)';
    });
}

/**
 * Envía la imagen al backend para ser procesada por la red neuronal / visión,
 * recibe las coordenadas vectoriales, las inserta en el dataset CNC y grafica en el plano.
 */
async function ejecutarVectorizacion() {
    if (!archivoImagenSeleccionado) {
        alert("Por favor selecciona o arrastra una imagen antes de presionar 'Vectorizar'.");
        return;
    }

    btnVectorizar.disabled = true;
    btnVectorizar.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="status-dot">
            <circle cx="12" cy="12" r="10"></circle>
        </svg>
        Procesando Red Neuronal...
    `;

    consoleBox.innerHTML += `\n>> [RED NEURONAL] Iniciando extracción y vectorización de imagen: ${archivoImagenSeleccionado.name}...\n`;

    const formData = new FormData();
    formData.append('imagen', archivoImagenSeleccionado);

    try {
        const response = await fetch('/api/vectorizar', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            figuraVectorizadaActual = data.figura;

            // Guardar datos para uso posterior en dataset
            puntosNormActuales = data.puntos_norm || [];
            // Convertir imagen a base64 para enviarla al endpoint de dataset
            if (archivoImagenSeleccionado) {
                const reader = new FileReader();
                reader.onloadend = () => { imagenBase64Actual = reader.result; };
                reader.readAsDataURL(archivoImagenSeleccionado);
            }

            // 1. Actualizar métricas y tarjeta de estado: "Figura lista para corte"
            vectorStatusCard.classList.add('visible');
            metricVertices.innerText = data.num_vertices;
            metricDims.innerText = `${data.dimensiones.ancho_mm} x ${data.dimensiones.alto_mm} mm`;

            // 2. Graficar en tiempo real sobre el plano cartesiano 2D
            graficarPrevisualizacionCartesiana(data.coordenadas, data.figura);

            // 3. Actualizar el selector de figuras y seleccionar la nueva figura
            await actualizarListadoFiguras(data.figura);

            // 4. Activar/Destacar el botón "Validar y Planificar" para confirmar el corte
            btnPlanificar.classList.add('highlight');

            consoleBox.innerHTML += `>> [ÉXITO] ${data.mensaje}\n`;
            consoleBox.innerHTML += `>> Geometría: ${data.figura} | ${data.num_vertices} vértices poligonales detectados.\n`;
            consoleBox.innerHTML += `>> ALERTA: [FIGURA LISTA PARA CORTE]. Presione 'Validar y Planificar' para ejecutar la trayectoria.\n`;

        } else {
            alert(`Error en vectorización: ${data.motivo}`);
            consoleBox.innerHTML += `>> [ERROR VECTORIZACIÓN] ${data.motivo}\n`;
        }
    } catch (err) {
        consoleBox.innerHTML += `>> [ERROR CONEXIÓN] ${err.message}\n`;
    } finally {
        btnVectorizar.disabled = false;
        btnVectorizar.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
            Vectorizar Imagen
        `;
    }
}

/**
 * Guarda la imagen actual y sus coordenadas normalizadas en el dataset YOLO
 * para reentrenar la red neuronal y mejorar el modelo de forma continua.
 */
async function guardarEnDataset() {
    if (!imagenBase64Actual || puntosNormActuales.length === 0) {
        alert("Primero vectoriza una imagen antes de guardar en el dataset.");
        return;
    }

    btnGuardarDataset.disabled = true;
    btnGuardarDataset.textContent = 'Guardando...';

    try {
        const response = await fetch('/api/dataset/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                imagen_base64: imagenBase64Actual,
                puntos_norm: puntosNormActuales
            })
        });

        const data = await response.json();
        if (data.success) {
            consoleBox.innerHTML += `>> [DATASET] Muestra guardada: ${data.id_muestra}. La IA aprenderá de esta imagen en el próximo entrenamiento.\n`;
            alert(`✓ ${data.mensaje}\nEjecuta 'python entrenador_ia.py' para que la IA aprenda de esta y otras muestras guardadas.`);
        } else {
            consoleBox.innerHTML += `>> [ERROR DATASET] ${data.motivo}\n`;
            alert(`Error al guardar: ${data.motivo}`);
        }
    } catch (err) {
        consoleBox.innerHTML += `>> [ERROR CONEXIÓN DATASET] ${err.message}\n`;
    } finally {
        btnGuardarDataset.disabled = false;
        btnGuardarDataset.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            Guardar Muestra en Dataset
        `;
    }
}

async function actualizarListadoFiguras(seleccionarFigura = null) {
    try {
        const response = await fetch('/api/figuras');
        const data = await response.json();
        if (data.success && data.figuras) {
            selectFigura.innerHTML = '';
            data.figuras.forEach(fig => {
                const opt = document.createElement('option');
                opt.value = fig;
                opt.innerText = fig;
                selectFigura.appendChild(opt);
            });

            if (seleccionarFigura) {
                selectFigura.value = seleccionarFigura;
            }
        }
    } catch (e) {
        console.error("Error al actualizar listado de figuras:", e);
    }
}

// ==========================================
// 4. LÓGICA DE VALIDACIÓN Y PLANIFICACIÓN (CORTE)
// ==========================================
async function enviarPlanificacion(e) {
    e.preventDefault();

    const figura = selectFigura.value;
    const material = document.getElementById('select-material').value;
    const presion = parseFloat(sliderInput.value);

    btnPlanificar.classList.remove('highlight');
    if (animation2DId) clearTimeout(animation2DId);

    consoleBox.innerHTML += `\n>> Solicitando inferencia del sistema experto para ${figura}, Material: ${material}, Presión: ${presion} bar...\n`;

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
            expertCard.className = 'expert-card success';
            expertTitle.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> SISTEMA OPERATIVO`;
            expertMsg.innerText = data.motivo;

            resPotencia.innerText = data.potencia;
            resVelocidad.innerText = data.velocidad;
            resPresionMin.innerText = `${data.presion_min.toFixed(1)} bar`;

            document.getElementById('expert-params-box').style.display = 'grid';
            complexBadge.style.display = data.geometria_compleja ? 'block' : 'none';

            consoleBox.innerHTML += `>> [SISTEMA EXPERTO] Aprobado. Ejecutando planificador DFS...\n`;
            data.listado_pasos.forEach(p => consoleBox.innerHTML += `${p}\n`);

            // Actualizar estado visual en el visor 3D
            setEstadoVisual3D(true);

            // Iniciar animación de corte en el Canvas Cartesiano 2D y 3D
            animarEjecucionCorte2D(data.coordenadas);

        } else {
            expertCard.className = 'expert-card error';
            expertTitle.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> ALERTA - BLOQUEO DE SEGURIDAD`;
            expertMsg.innerText = data.motivo;
            document.getElementById('expert-params-box').style.display = 'none';

            consoleBox.innerHTML += `\n>> [ERROR] BLOQUEO: ${data.motivo}\n`;

            setEstadoVisual3D(false);
        }

    } catch (err) {
        consoleBox.innerHTML += `\n>> [ERROR COMUNICACIÓN] ${err.message}\n`;
        setEstadoVisual3D(false);
    }
}

function setEstadoVisual3D(enEjecucion) {
    if (!loadedModel) return;

    if (telemetryStatus) {
        telemetryStatus.innerText = enEjecucion ? 'EJECUTANDO CORTE' : 'BLOQUEADO / SEGURIDAD';
        telemetryStatus.style.color = enEjecucion ? 'var(--accent-green)' : 'var(--accent-red)';
    }

    loadedModel.traverse((child) => {
        if (child.isMesh && child.material) {
            if (enEjecucion) {
                child.material.emissive = new THREE.Color(0x003344);
            } else {
                child.material.emissive = new THREE.Color(0x440011);
            }
        }
    });
}

function animarEjecucionCorte2D(coordenadas) {
    dibujarPlanoCartesianoBase();

    if (canvasViewTag) {
        canvasViewTag.innerText = `PLANO CARTESIANO 2D (TRAYECTORIA DE CORTE ACTIVA)`;
        canvasViewTag.style.color = 'var(--accent-blue)';
    }

    const margin = 45;
    const scale = 1.7;
    const ch = canvas2D.height;

    function toCanvas(x, y) {
        return {
            cx: margin + x * scale,
            cy: ch - margin - y * scale
        };
    }

    let step = 0;
    let t = 0;
    let lineHistory = [];

    // Mapeo a la placa 3D Three.js
    const scale_factor = 0.45;
    let lastX3d = (coordenadas[0].x - 95) * scale_factor + 45;
    let lastZ3d = (coordenadas[0].y - 95) * scale_factor;

    // Limpiar rastro de corte 3D previo
    if (path3DGroup) {
        while (path3DGroup.children.length > 0) {
            const obj = path3DGroup.children[0];
            path3DGroup.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        }
    }

    function renderFrame() {
        dibujarPlanoCartesianoBase();

        // 1. Dibujar líneas ya completadas
        lineHistory.forEach(line => {
            ctx2D.beginPath();
            ctx2D.moveTo(line.from.cx, line.from.cy);
            ctx2D.lineTo(line.to.cx, line.to.cy);
            ctx2D.strokeStyle = (line.op === 'Corte_Lineal' || line.op === 'Apagar_Soplete') ? '#ff3366' : 'rgba(0, 240, 255, 0.4)';
            ctx2D.lineWidth = (line.op === 'Corte_Lineal' || line.op === 'Apagar_Soplete') ? 3 : 1.5;
            ctx2D.stroke();
        });

        // 2. Interpolar tramo actual
        if (step < coordenadas.length - 1) {
            const pFrom = coordenadas[step];
            const pTo = coordenadas[step + 1];

            const from = toCanvas(pFrom.x, pFrom.y);
            const to = toCanvas(pTo.x, pTo.y);

            const curCx = from.cx + (to.cx - from.cx) * t;
            const curCy = from.cy + (to.cy - from.cy) * t;

            const corteActivo = (pTo.operacion === 'Corte_Lineal' || pTo.operacion === 'Apagar_Soplete');

            ctx2D.beginPath();
            ctx2D.moveTo(from.cx, from.cy);
            ctx2D.lineTo(curCx, curCy);
            ctx2D.strokeStyle = corteActivo ? '#ff3366' : '#00f0ff';
            ctx2D.lineWidth = corteActivo ? 3 : 2;
            ctx2D.stroke();

            // Dibujar cabezal de soplete en 2D (punto brillante)
            ctx2D.beginPath();
            ctx2D.arc(curCx, curCy, 4, 0, 2 * Math.PI);
            ctx2D.fillStyle = corteActivo ? '#ff3366' : '#00f0ff';
            ctx2D.fill();

            // Mapeo 3D
            const x3d_from = (pFrom.x - 95) * scale_factor + 45;
            const z3d_from = (pFrom.y - 95) * scale_factor;
            const x3d_to = (pTo.x - 95) * scale_factor + 45;
            const z3d_to = (pTo.y - 95) * scale_factor;

            const curX3d = x3d_from + (x3d_to - x3d_from) * t;
            const curZ3d = z3d_from + (z3d_to - z3d_from) * t;

            actualizarPosicionSoplete(curX3d, curZ3d, corteActivo);

            // Trazo 3D
            const materialColor = corteActivo ? 0xff3366 : 0x00f0ff;
            const lineMat = new THREE.LineBasicMaterial({ color: materialColor });
            const lineGeo = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(lastX3d, 0.2, lastZ3d),
                new THREE.Vector3(curX3d, 0.2, curZ3d)
            ]);
            const segment = new THREE.Line(lineGeo, lineMat);
            path3DGroup.add(segment);

            lastX3d = curX3d;
            lastZ3d = curZ3d;

            t += 0.05;
            if (t >= 1) {
                lineHistory.push({ from, to, op: pTo.operacion });
                t = 0;
                step++;
                lastX3d = (pTo.x - 95) * scale_factor + 45;
                lastZ3d = (pTo.y - 95) * scale_factor;
            }

            animation2DId = setTimeout(renderFrame, 30);
        } else {
            // Finalizado
            const finalX3d = (coordenadas[coordenadas.length - 1].x - 95) * scale_factor + 45;
            const finalZ3d = (coordenadas[coordenadas.length - 1].y - 95) * scale_factor;
            actualizarPosicionSoplete(finalX3d, finalZ3d, false);
            if (telemetryStatus) {
                telemetryStatus.innerText = 'CORTE FINALIZADO';
                telemetryStatus.style.color = 'var(--accent-blue)';
            }
            if (canvasViewTag) {
                canvasViewTag.innerText = `PLANO CARTESIANO 2D [CORTE CNC COMPLETADO CON ÉXITO]`;
                canvasViewTag.style.color = 'var(--accent-green)';
            }
        }
    }

    renderFrame();
}