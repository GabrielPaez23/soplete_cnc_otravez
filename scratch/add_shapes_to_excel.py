import pandas as pd

excel_path = "dataset_de_cnc.xlsx"

# Read existing sheets
try:
    df_figuras = pd.read_excel(excel_path, sheet_name="figuras")
    df_parametros = pd.read_excel(excel_path, sheet_name="parametros_experto")
except Exception as e:
    print("Error reading sheet:", e)
    df_figuras = pd.DataFrame()
    df_parametros = pd.DataFrame()

# Check if Circulo and Estrella are already in df_figuras
if "Circulo" not in df_figuras["Figura"].values:
    print("Adding Circulo coordinates...")
    circulo_rows = [
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "Origen", "Coordenada_X": 0, "Coordenada_Y": 0, "Operacion_CNC": "Traslado_Apagado", "Pasos_Acumulados": 0},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V1", "Coordenada_X": 190, "Coordenada_Y": 150, "Operacion_CNC": "Encender_Soplete", "Pasos_Acumulados": 1},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V2", "Coordenada_X": 178, "Coordenada_Y": 178, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 2},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V3", "Coordenada_X": 150, "Coordenada_Y": 190, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 3},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V4", "Coordenada_X": 122, "Coordenada_Y": 178, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 4},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V5", "Coordenada_X": 110, "Coordenada_Y": 150, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 5},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V6", "Coordenada_X": 122, "Coordenada_Y": 122, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 6},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V7", "Coordenada_X": 150, "Coordenada_Y": 110, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 7},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V8", "Coordenada_X": 178, "Coordenada_Y": 122, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 8},
        {"ID_Pieza": 4, "Figura": "Circulo", "Vertice_Secuencia": "V1 (Cierre)", "Coordenada_X": 190, "Coordenada_Y": 150, "Operacion_CNC": "Apagar_Soplete", "Pasos_Acumulados": 9},
    ]
    df_figuras = pd.concat([df_figuras, pd.DataFrame(circulo_rows)], ignore_index=True)

if "Estrella" not in df_figuras["Figura"].values:
    print("Adding Estrella coordinates...")
    estrella_rows = [
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "Origen", "Coordenada_X": 0, "Coordenada_Y": 0, "Operacion_CNC": "Traslado_Apagado", "Pasos_Acumulados": 0},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V1", "Coordenada_X": 165, "Coordenada_Y": 120, "Operacion_CNC": "Encender_Soplete", "Pasos_Acumulados": 1},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V2", "Coordenada_X": 135, "Coordenada_Y": 131, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 2},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V3", "Coordenada_X": 134, "Coordenada_Y": 163, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 3},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V4", "Coordenada_X": 111, "Coordenada_Y": 137, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 4},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V5", "Coordenada_X": 84, "Coordenada_Y": 146, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 5},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V6", "Coordenada_X": 101, "Coordenada_Y": 120, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 6},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V7", "Coordenada_X": 84, "Coordenada_Y": 94, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 7},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V8", "Coordenada_X": 111, "Coordenada_Y": 103, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 8},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V9", "Coordenada_X": 134, "Coordenada_Y": 77, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 9},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V10", "Coordenada_X": 135, "Coordenada_Y": 109, "Operacion_CNC": "Corte_Lineal", "Pasos_Acumulados": 10},
        {"ID_Pieza": 5, "Figura": "Estrella", "Vertice_Secuencia": "V1 (Cierre)", "Coordenada_X": 165, "Coordenada_Y": 120, "Operacion_CNC": "Apagar_Soplete", "Pasos_Acumulados": 11},
    ]
    df_figuras = pd.concat([df_figuras, pd.DataFrame(estrella_rows)], ignore_index=True)

# Write back to Excel with openpyxl engine
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df_figuras.to_excel(writer, sheet_name="figuras", index=False)
    df_parametros.to_excel(writer, sheet_name="parametros_experto", index=False)

print("Excel file successfully updated with Circle and Star coordinates!")
