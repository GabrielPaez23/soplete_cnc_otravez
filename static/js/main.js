import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ==========================================
// CONFIGURACIÓN RUTA MODELO GLTF/GLB
// ==========================================
const MODEL_PATH = '/static/models/brazo_cnc.glb';

// Referencias del DOM
const sliderVal = document.getElementById('val-presion');
const sliderInput = document.getElementById('input-presion');
const consoleBox = document.getElementById('cnc-console');
const canvas2D = document.getElementById('cnc-canvas');
const ctx2D = canvas2D.getContext('2d');
const formHMI = document.getElementById('hmi-form');

const telemetryScale = document.getElementById('telemetry-scale');
const telemetryStatus = document.getElementById('telemetry-status');

let animation2DId = null;

// ==========================================
// VARIABLES GLOBALES VISOR THREE.JS
// ==========================================
let scene3D, camera3D, renderer3D, controls3D;
let loadedModel = null;
let gridHelper3D = null;
let axesHelper3D = null;

// Inicialización general al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
    init2DCanvas();
    init3DViewport();
    
    // Escuchar el deslizador de presión
    sliderInput.addEventListener('input', (e) => {
        sliderVal.innerText = parseFloat(e.target.value).toFixed(1) + ' bar';
    });

    // Evento del formulario HMI
    formHMI.addEventListener('submit', enviarPlanificacion);
});

// ==========================================
// 1. INICIALIZACIÓN Y MOTOR THREE.JS
// ==========================================
function init3DViewport() {
    const container = document.getElementById('container-3d');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Escena con niebla ambiental para profundidad tipo HMI
    scene3D = new THREE.Scene();
    scene3D.background = new THREE.Color(0x09090d);
    scene3D.fog = new THREE.FogExp2(0x09090d, 0.003);

    // Cámara Perspectiva
    camera3D = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    camera3D.position.set(150, 150, 150);

    // Renderizador WebGL
    renderer3D = new THREE.WebGLRenderer({ antialias: true });
    renderer3D.setSize(width, height);
    renderer3D.setPixelRatio(1);
    renderer3D.shadowMap.enabled = false;
    renderer3D.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer3D.domElement);

    // Controles Orbitales de Cámara
    controls3D = new OrbitControls(camera3D, renderer3D.domElement);
    controls3D.enableDamping = true;
    controls3D.dampingFactor = 0.05;

    // Iluminación Técnica
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene3D.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x00f0ff, 1.2);
    dirLight1.position.set(100, 200, 100);
    dirLight1.castShadow = true;
    scene3D.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xff3366, 0.5);
    dirLight2.position.set(-100, -50, -100);
    scene3D.add(dirLight2);

    // Intentar Cargar el Modelo GLTF/GLB
    cargarModeloGLTF(MODEL_PATH);

    // Manejo de cambio de tamaño de ventana
    window.addEventListener('resize', onWindowResize3D);

    // Bucle de Animación / Renderizado
    function animate3D() {
        requestAnimationFrame(animate3D);
        controls3D.update();
        renderer3D.render(scene3D, camera3D);
    }
    animate3D();
}

// ==========================================
// 2. CARGA DE MODELO Y AUTOAJUSTE DE BOUNDING BOX
// ==========================================
function cargarModeloGLTF(path) {
    const loader = new GLTFLoader();

    loader.load(MODEL_PATH, (gltf) => {
        const model = gltf.scene;
    
        // 1. Calcular el tamaño real del modelo exportado
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
    
        // 2. Centrar el punto pivote del modelo en (0, 0, 0)
        model.position.x += (model.position.x - center.x);
        model.position.y += (model.position.y - center.y);
        model.position.z += (model.position.z - center.z);
    
        // 3. Reescalar automáticamente si es enorme o microscópico
        const maxDim = Math.max(size.x, size.y, size.z);
        if (maxDim > 0) {
            const scale = 40 / maxDim; // Lo ajusta para que encaje bien en la rejilla de 50mm
            model.scale.set(scale, scale, scale);
        }
    
        // 4. Asegurar materiales visibles
        model.traverse((child) => {
            if (child.isMesh) {
                // Si el material original tiene problemas de iluminación, forzar uno visible
                child.material.side = THREE.DoubleSide; 
            }
        });
    
        scene3D.add(model);
    
        // 5. Reubicar cámara y controles para enfocarlo directamente
        camera3D.position.set(60, 60, 60);
        controls3D.target.set(0, 0, 0);
        controls3D.update();
    
        if (telemetryStatus) {
            telemetryStatus.innerText = 'PROCESO FINALIZADO';
            telemetryStatus.style.color = 'var(--accent-green)';
        }
    }, undefined, (error) => {
        console.error("Error al cargar el modelo 3D:", error);
    });
}

/**
 * Calcula la Bounding Box del modelo y autoajusta la escala de los GridHelper, AxesHelper y Cámara
 */
function autoAjustarBoundingBox(objeto3D, tamanoBaseOptativo = null) {
    // 1. Calcular la Caja Envolvente (Bounding Box) 3D
    const boundingBox = new THREE.Box3().setFromObject(objeto3D);
    
    const size = new THREE.Vector3();
    boundingBox.getSize(size);

    const center = new THREE.Vector3();
    boundingBox.getCenter(center);

    // 2. Centrar el modelo en el origen del espacio
    objeto3D.position.x += (objeto3D.position.x - center.x);
    objeto3D.position.y -= boundingBox.min.y; // Apoyar sobre el plano Y = 0
    objeto3D.position.z += (objeto3D.position.z - center.z);

    // 3. Determinar la dimensión máxima para escalar el Grid y los Ejes
    const maxDimension = tamanoBaseOptativo || Math.max(size.x, size.y, size.z, 50);

    // Actualizar ayuda visual de rejilla (GridHelper)
    if (gridHelper3D) scene3D.remove(gridHelper3D);
    gridHelper3D = new THREE.GridHelper(maxDimension * 2, 20, 0x00f0ff, 0x27273a);
    gridHelper3D.position.y = 0;
    scene3D.add(gridHelper3D);

    // Actualizar ayuda visual de ejes XYZ (AxesHelper)
    if (axesHelper3D) scene3D.remove(axesHelper3D);
    axesHelper3D = new THREE.AxesHelper(maxDimension * 0.8);
    // Configurar grosor/color
    axesHelper3D.position.set(-maxDimension, 0, -maxDimension);
    scene3D.add(axesHelper3D);

    // 4. Reposicionar la cámara para encuadrar dinámicamente la pieza
    const fov = camera3D.fov * (Math.PI / 180);
    let cameraDistance = Math.abs(maxDimension / Math.sin(fov / 2));
    
    camera3D.position.set(center.x + cameraDistance * 0.8, center.y + cameraDistance * 0.8, center.z + cameraDistance * 0.8);
    camera3D.lookAt(center.x, center.y / 2, center.z);
    
    controls3D.target.set(center.x, center.y / 2, center.z);
    controls3D.update();

    // Actualizar panel de telemetría de la interfaz
    if (telemetryScale) telemetryScale.innerText = `${maxDimension.toFixed(0)} mm`;
}

/**
 * Genera un modelo 3D articulado genérico de respaldo mediante primitivas de Three.js
 */
function crearModeloGenericoCNC() {
    const grupoCNC = new THREE.Group();

    const matBase = new THREE.MeshStandardMaterial({ color: 0x1e1e28, roughness: 0.5 });
    const matCyan = new THREE.MeshStandardMaterial({ color: 0x00f0ff, roughness: 0.2, metalness: 0.8 });
    const matSoplete = new THREE.MeshStandardMaterial({ color: 0xff3366, emissive: 0x330011 });

    // Base del robot
    const base = new THREE.Mesh(new THREE.CylinderGeometry(30, 35, 10, 32), matBase);
    base.position.y = 5;
    grupoCNC.add(base);

    // Mástil Vertical
    const mastil = new THREE.Mesh(new THREE.BoxGeometry(12, 80, 12), matCyan);
    mastil.position.set(0, 45, 0);
    grupoCNC.add(mastil);

    // Brazo Transversal (Eje X)
    const brazo = new THREE.Mesh(new THREE.BoxGeometry(100, 10, 10), matBase);
    brazo.position.set(30, 80, 0);
    grupoCNC.add(brazo);

    // Cabezal / Soplete
    const cabezal = new THREE.Mesh(new THREE.ConeGeometry(6, 20, 16), matSoplete);
    cabezal.rotation.x = Math.PI;
    cabezal.position.set(70, 65, 0);
    cabezal.name = "cabezal_soplete";
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
// 3. LÓGICA DE COMUNICACIÓN API HMI Y DIBUJO 2D
// ==========================================
function init2DCanvas() {
    ctx2D.fillStyle = '#1e1e24';
    ctx2D.fillRect(0, 0, canvas2D.width, canvas2D.height);
    drawGrid2D();
}

function drawGrid2D() {
    ctx2D.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx2D.lineWidth = 1;
    for (let x = 0; x < canvas2D.width; x += 30) {
        ctx2D.beginPath(); ctx2D.moveTo(x, 0); ctx2D.lineTo(x, canvas2D.height); ctx2D.stroke();
    }
    for (let y = 0; y < canvas2D.height; y += 30) {
        ctx2D.beginPath(); ctx2D.moveTo(0, y); ctx2D.lineTo(canvas2D.width, y); ctx2D.stroke();
    }
    
    // Origen (0,0)
    ctx2D.beginPath();
    ctx2D.arc(40, canvas2D.height - 40, 5, 0, 2 * Math.PI);
    ctx2D.fillStyle = '#00ff88';
    ctx2D.fill();
}

async function enviarPlanificacion(e) {
    e.preventDefault();

    const figura = document.getElementById('select-figura').value;
    const material = document.getElementById('select-material').value;
    const presion = parseFloat(sliderInput.value);

    if (animation2DId) clearTimeout(animation2DId);

    consoleBox.innerHTML = `>> Solicitando inferencia del sistema experto para ${figura}, Material: ${material}, Presión: ${presion} bar...\n`;

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

            // Iniciar animación en Canvas 2D
            animar2D(data.coordenadas);

        } else {
            expertCard.className = 'expert-card error';
            expertTitle.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> ALERTA - BLOQUEO DE SEGURIDAD`;
            expertMsg.innerText = data.motivo;
            document.getElementById('expert-params-box').style.display = 'none';

            consoleBox.innerHTML += `\n>> [ERROR] BLOQUEO: ${data.motivo}\n`;

            setEstadoVisual3D(false);
            init2DCanvas();
        }

    } catch (err) {
        consoleBox.innerHTML += `\n>> [ERROR COMUNICACIÓN] ${err.message}\n`;
        setEstadoVisual3D(false);
    }
}

/**
 * Cambia el estado y color emisivo del modelo 3D según el proceso
 */
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

function animar2D(coordenadas) {
    init2DCanvas();

    const scale = 1.8;
    const margin = 40;

    function toCanvas(x, y) {
        return {
            cx: margin + x * scale,
            cy: canvas2D.height - margin - y * scale
        };
    }

    let step = 0;
    let t = 0;
    let lineHistory = [];

    function renderFrame() {
        init2DCanvas();

        // Dibujar líneas procesadas
        lineHistory.forEach(line => {
            ctx2D.beginPath();
            ctx2D.moveTo(line.from.cx, line.from.cy);
            ctx2D.lineTo(line.to.cx, line.to.cy);
            ctx2D.strokeStyle = (line.op === 'Corte_Lineal' || line.op === 'Apagar_Soplete') ? '#ff3366' : 'rgba(0, 240, 255, 0.4)';
            ctx2D.lineWidth = (line.op === 'Corte_Lineal' || line.op === 'Apagar_Soplete') ? 3 : 1.5;
            ctx2D.stroke();
        });

        // Interpolar paso actual
        if (step < coordenadas.length - 1) {
            const pFrom = coordenadas[step];
            const pTo = coordenadas[step + 1];

            const from = toCanvas(pFrom.x, pFrom.y);
            const to = toCanvas(pTo.x, pTo.y);

            const curCx = from.cx + (to.cx - from.cx) * t;
            const curCy = from.cy + (to.cy - from.cy) * t;

            ctx2D.beginPath();
            ctx2D.moveTo(from.cx, from.cy);
            ctx2D.lineTo(curCx, curCy);
            ctx2D.strokeStyle = '#00f0ff';
            ctx2D.lineWidth = 2;
            ctx2D.stroke();

            t += 0.08;
            if (t >= 1) {
                lineHistory.push({ from, to, op: pTo.operacion });
                t = 0;
                step++;
            }

            animation2DId = setTimeout(renderFrame, 30);
        } else {
            if (telemetryStatus) {
                telemetryStatus.innerText = 'PROCESO FINALIZADO';
                telemetryStatus.style.color = 'var(--accent-blue)';
            }
        }
    }

    renderFrame();
}