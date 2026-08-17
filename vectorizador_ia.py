import io
import os
import cv2
import numpy as np
import pandas as pd
from PIL import Image

try:
    from ultralytics import YOLO
    YOLO_DISPONIBLE = True
except ImportError:
    YOLO_DISPONIBLE = False

class VectorizadorCNC:
    """
    Módulo de Visión por Computadora e Inteligencia Artificial para
    la vectorización automática de imágenes y conversión a coordenadas CNC.
    """
    def __init__(self, target_size=(200, 200), margin=20):
        self.target_width = target_size[0]
        self.target_height = target_size[1]
        self.margin = margin
        self.modelo_yolo = None
        
        # Intentar cargar YOLO si está disponible
        if YOLO_DISPONIBLE:
            ruta_mejorada = "entrenamientos/modelo_mejora_continua/weights/best.pt"
            ruta_base = "yolov8n-seg.pt"
            try:
                if os.path.exists(ruta_mejorada):
                    self.modelo_yolo = YOLO(ruta_mejorada)
                    print(f"[*] Modelo YOLO mejorado cargado desde {ruta_mejorada}")
                elif os.path.exists(ruta_base):
                    self.modelo_yolo = YOLO(ruta_base)
                    print(f"[*] Modelo YOLO base cargado desde {ruta_base}")
            except Exception as e:
                print(f"[!] Error al cargar YOLO: {e}")

    def procesar_imagen_bytes(self, image_bytes, nombre_figura="Figura_Vectorizada", epsilon_factor=0.015):
        """
        Procesa una imagen en bytes (PNG, JPG, BMP, etc.), extrae el contorno
        vectorial principal y formatea las coordenadas para el dataset CNC.
        """
        # Convertir bytes a imagen PIL y luego a formato OpenCV (numpy array)
        pil_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_np = np.array(pil_img)
        
        # Intentar obtener la máscara usando YOLO
        mask_obtenida = False
        thresh = None
        
        if self.modelo_yolo is not None:
            try:
                resultados = self.modelo_yolo.predict(img_np, verbose=False)
                if resultados and len(resultados) > 0 and resultados[0].masks is not None:
                    # Extraer la máscara con mayor confianza
                    mask_data = resultados[0].masks.data[0].cpu().numpy()
                    
                    # Redimensionar la máscara a las dimensiones originales de la imagen
                    h_orig, w_orig = img_np.shape[:2]
                    mask_resized = cv2.resize(mask_data, (w_orig, h_orig), interpolation=cv2.INTER_NEAREST)
                    
                    # Convertir a imagen binaria (0 y 255)
                    thresh = (mask_resized * 255).astype(np.uint8)
                    mask_obtenida = True
                    print("[*] Segmentación inteligente aplicada con éxito.")
            except Exception as e:
                print(f"[!] Falló la predicción YOLO, usando respaldo matemático: {e}")

        # Respaldo: Método Matemático Tradicional (OpenCV) si YOLO falla o no está
        if not mask_obtenida:
            # Convertir a escala de grises
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            
            # Suavizado para reducir ruido
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Binarización adaptativa / Otsu
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Si la imagen tiene fondo oscuro y figura clara, verificar conteo de píxeles
            if np.sum(thresh == 255) > np.sum(thresh == 0):
                # Invertir si el fondo terminó siendo blanco
                thresh = cv2.bitwise_not(thresh)
                
            # Operación morfológica para cerrar pequeñas discontinuidades
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # Si no detectó contorno invertido, probar detección de bordes Canny
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
        if not contours:
            raise ValueError("No se pudo detectar ninguna figura o contorno claro en la imagen.")
            
        # Seleccionar el contorno con mayor área
        contour_principal = max(contours, key=cv2.contourArea)
        
        # Aproximación poligonal (Algoritmo Douglas-Peucker)
        perimetro = cv2.arcLength(contour_principal, True)
        epsilon = max(1.5, epsilon_factor * perimetro)
        approx = cv2.approxPolyDP(contour_principal, epsilon, True)
        
        # Asegurar al menos 3 vértices
        if len(approx) < 3:
            approx = cv2.approxPolyDP(contour_principal, 0.005 * perimetro, True)
            
        # Extraer puntos brutos (x, y) de la imagen
        puntos_brutos = approx.reshape(-1, 2)
        
        # Calcular puntos normalizados para formato YOLO Segmentación (0.0 a 1.0)
        h_img, w_img = img_np.shape[:2]
        puntos_norm = []
        for pt in puntos_brutos:
            x_norm = pt[0] / w_img
            y_norm = pt[1] / h_img
            puntos_norm.extend([round(x_norm, 6), round(y_norm, 6)])
        
        # Normalizar y escalar las coordenadas al plano de trabajo CNC (e.g. 20 a 180 mm)
        coordenadas_cnc = self._escalar_coordenadas_a_cnc(puntos_brutos)
        
        # Evaluar complejidad geométrica
        es_compleja = len(coordenadas_cnc) > 6 or self._es_geometria_compleja(coordenadas_cnc)
        
        # Construir listado de puntos estructurados para la máquina CNC
        filas_dataset, listado_frontend = self._construir_filas_cnc(nombre_figura, coordenadas_cnc)
        
        # Dimensiones de la pieza
        xs = [p['x'] for p in listado_frontend if p['operacion'] != 'Traslado_Apagado']
        ys = [p['y'] for p in listado_frontend if p['operacion'] != 'Traslado_Apagado']
        
        dimensiones = {
            "min_x": int(min(xs)) if xs else 0,
            "max_x": int(max(xs)) if xs else 0,
            "min_y": int(min(ys)) if ys else 0,
            "max_y": int(max(ys)) if ys else 0,
            "ancho_mm": int(max(xs) - min(xs)) if xs else 0,
            "alto_mm": int(max(ys) - min(ys)) if ys else 0
        }
        
        return {
            "figura": nombre_figura,
            "coordenadas": listado_frontend,
            "filas_excel": filas_dataset,
            "es_compleja": es_compleja,
            "num_vertices": len(coordenadas_cnc),
            "dimensiones": dimensiones,
            "puntos_norm": puntos_norm
        }

    def _escalar_coordenadas_a_cnc(self, puntos):
        """
        Escala y centra las coordenadas del contorno dentro de la chapa de trabajo del CNC
        (Margen útil: [margin, target_width - margin] x [margin, target_height - margin]).
        Invierte el eje Y para adecuar la orientación de imagen al plano cartesiano estándar.
        """
        min_x = np.min(puntos[:, 0])
        max_x = np.max(puntos[:, 0])
        min_y = np.min(puntos[:, 1])
        max_y = np.max(puntos[:, 1])
        
        w_orig = max(1, max_x - min_x)
        h_orig = max(1, max_y - min_y)
        
        # Área útil disponible en la chapa
        util_w = self.target_width - (2 * self.margin)
        util_h = self.target_height - (2 * self.margin)
        
        # Factor de escala preservando la relación de aspecto
        escala = min(util_w / w_orig, util_h / h_orig)
        
        w_final = w_orig * escala
        h_final = h_orig * escala
        
        # Centrar en la chapa
        offset_x = self.margin + (util_w - w_final) / 2
        offset_y = self.margin + (util_h - h_final) / 2
        
        puntos_cnc = []
        for pt in puntos:
            px = pt[0]
            py = pt[1]
            
            # Escalar y desplazar
            cnc_x = int(round(offset_x + (px - min_x) * escala))
            # Invertir eje Y (en imagen Y va hacia abajo, en CNC cartesiano Y va hacia arriba)
            cnc_y = int(round(offset_y + (max_y - py) * escala))
            
            puntos_cnc.append((cnc_x, cnc_y))
            
        return puntos_cnc

    def _es_geometria_compleja(self, puntos):
        """
        Calcula si la figura posee cambios de curvatura o ángulos significativos.
        """
        if len(puntos) > 8:
            return True
        return False

    def _construir_filas_cnc(self, nombre_figura, puntos_cnc):
        """
        Genera la estructura de comandos y pasos CNC (G00, M03, G01, M05).
        """
        filas_excel = []
        listado_frontend = []
        
        # Paso 0: Origen (0,0) - Traslado Apagado (G00)
        filas_excel.append({
            "Figura": nombre_figura,
            "Vertice_Secuencia": "Origen",
            "Coordenada_X": 0,
            "Coordenada_Y": 0,
            "Coordenada_Z": 0,
            "Operacion_CNC": "Traslado_Apagado",
            "Pasos_Acumulados": 0
        })
        listado_frontend.append({
            "secuencia": "Origen",
            "x": 0,
            "y": 0,
            "operacion": "Traslado_Apagado",
            "paso": 0
        })
        
        if not puntos_cnc:
            return filas_excel, listado_frontend
            
        # Paso 1: V1 - Encender Soplete (M03)
        v1_x, v1_y = puntos_cnc[0]
        filas_excel.append({
            "Figura": nombre_figura,
            "Vertice_Secuencia": "V1",
            "Coordenada_X": v1_x,
            "Coordenada_Y": v1_y,
            "Coordenada_Z": 0,
            "Operacion_CNC": "Encender_Soplete",
            "Pasos_Acumulados": 1
        })
        listado_frontend.append({
            "secuencia": "V1",
            "x": v1_x,
            "y": v1_y,
            "operacion": "Encender_Soplete",
            "paso": 1
        })
        
        paso_actual = 2
        # Pasos 2 a N: Corte Lineal hacia los siguientes vértices
        for i in range(1, len(puntos_cnc)):
            vx, vy = puntos_cnc[i]
            v_name = f"V{i+1}"
            filas_excel.append({
                "Figura": nombre_figura,
                "Vertice_Secuencia": v_name,
                "Coordenada_X": vx,
                "Coordenada_Y": vy,
                "Coordenada_Z": 0,
                "Operacion_CNC": "Corte_Lineal",
                "Pasos_Acumulados": paso_actual
            })
            listado_frontend.append({
                "secuencia": v_name,
                "x": vx,
                "y": vy,
                "operacion": "Corte_Lineal",
                "paso": paso_actual
            })
            paso_actual += 1
            
        # Paso final: Cierre de contorno volviendo a V1 y apagar soplete (M05)
        filas_excel.append({
            "Figura": nombre_figura,
            "Vertice_Secuencia": "V1 (Cierre)",
            "Coordenada_X": v1_x,
            "Coordenada_Y": v1_y,
            "Coordenada_Z": 0,
            "Operacion_CNC": "Apagar_Soplete",
            "Pasos_Acumulados": paso_actual
        })
        listado_frontend.append({
            "secuencia": "V1 (Cierre)",
            "x": v1_x,
            "y": v1_y,
            "operacion": "Apagar_Soplete",
            "paso": paso_actual
        })
        
        return filas_excel, listado_frontend
