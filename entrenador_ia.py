import os
from ultralytics import YOLO

def entrenar_modelo():
    """
    Script para reentrenar la red neuronal YOLOv8 con el dataset recolectado
    desde la interfaz web.
    """
    yaml_path = os.path.abspath("dataset_config.yaml")
    
    if not os.path.exists(yaml_path):
        print(f"[!] Error: No se encontró {yaml_path}")
        return
        
    if not os.path.exists("dataset/images"):
        print("[!] No se han guardado imágenes en el dataset aún. Usa la interfaz web para guardar muestras primero.")
        return
        
    print("[*] Iniciando entrenamiento de YOLOv8 para segmentación...")
    
    # Cargar modelo base o el último modelo entrenado si existe
    model_path = "yolov8n-seg.pt"
    if os.path.exists("entrenamientos/modelo_mejora_continua/weights/best.pt"):
        print("[*] Se detectó un modelo previamente entrenado. Continuando aprendizaje...")
        model_path = "entrenamientos/modelo_mejora_continua/weights/best.pt"
        
    modelo = YOLO(model_path)
    
    # Iniciar entrenamiento
    modelo.train(
        data=yaml_path,
        epochs=15,
        imgsz=640,
        batch=4,
        lr0=0.001,
        project="entrenamientos",
        name="modelo_mejora_continua",
        exist_ok=True # Sobrescribir en la misma carpeta para mantener el historial
    )
    
    print("[✓] Entrenamiento finalizado. El modelo ha mejorado.")

if __name__ == "__main__":
    entrenar_modelo()
