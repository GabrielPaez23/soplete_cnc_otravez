import pandas as pd

excel_path = "dataset_de_cnc.xlsx"
df_figuras = pd.read_excel(excel_path, sheet_name="figuras")
df_experto = pd.read_excel(excel_path, sheet_name="parametros_experto")

def run_expert_system(figura, material, presion_gas):
    # Find material row
    mat_row = df_experto[df_experto['Material'].str.lower() == material.lower()]
    if mat_row.empty:
        return {"success": False, "alerta": f"Material '{material}' no encontrado en la base de conocimientos."}
    
    row_data = mat_row.iloc[0]
    presion_min = float(row_data['Presion_Min_Gas'])
    potencia = row_data['Potencia_Sugerida']
    velocidad = row_data['Velocidad_Sugerida']
    
    if presion_gas < presion_min:
        return {
            "success": False,
            "alerta": f"SISTEMA EXPERTO - BLOQUEO DE SEGURIDAD: La presión de gas ({presion_gas} bar) es menor al mínimo requerido para {material} ({presion_min} bar)."
        }
    
    # Check if shape is complex
    is_complex = False
    shape_row = df_experto[df_experto['Material'].str.lower() == figura.lower()]
    if not shape_row.empty:
        shape_data = shape_row.iloc[0]
        if str(shape_data['Figura_Compleja']).lower() == 'si':
            is_complex = True
            velocidad = shape_data['Velocidad_Sugerida']
            
    return {
        "success": True,
        "is_complex": is_complex,
        "potencia": potencia,
        "velocidad": velocidad
    }

def run_dfs_planning(figura):
    fig_rows = df_figuras[df_figuras['Figura'].str.lower() == figura.lower()].sort_values(by='Pasos_Acumulados')
    if fig_rows.empty:
        return None
    
    # DFS Stack-based LIFO path planning
    # Let's decompose tasks: PLAN_CNC -> APROXIMACION, CORTE, RETORNO
    stack = [{"type": "PLAN_CNC", "figura": figura}]
    
    pasos = []
    coords = []
    current_pos = (0, 0)
    
    # To run a LIFO stack for hierarchical planning, we pull from stack
    while stack:
        task = stack.pop()
        t_type = task["type"]
        
        if t_type == "PLAN_CNC":
            # Push in reverse order: RETORNO first, then CORTE, then APROXIMACION
            stack.append({"type": "FASE_RETORNO", "figura": task["figura"]})
            stack.append({"type": "FASE_CORTE", "figura": task["figura"]})
            stack.append({"type": "FASE_APROXIMACION", "figura": task["figura"]})
            
        elif t_type == "FASE_APROXIMACION":
            # Aproximacion goes from (0,0) to V1 and turns on torch
            # Find the row that turns soplete on (usually step 1) and any preceding steps
            aprox_rows = fig_rows[fig_rows['Operacion_CNC'].isin(['Traslado_Apagado', 'Encender_Soplete']) & (fig_rows['Pasos_Acumulados'] <= 1)]
            # We want to process them: first move to V1 (row with Encender_Soplete coords), then Encender_Soplete.
            # Row 1 is V1 (10,10), Encender_Soplete.
            # So we push the actions in reverse LIFO:
            # 1. Turn torch ON
            # 2. Move to V1
            row_v1 = fig_rows[fig_rows['Vertice_Secuencia'] == 'V1'].iloc[0]
            stack.append({"type": "ACCION_SOPLETE", "op": "ON", "x": int(row_v1['Coordenada_X']), "y": int(row_v1['Coordenada_Y']), "label": "V1"})
            stack.append({"type": "ACCION_MOVER", "op": "Traslado_Apagado", "x": int(row_v1['Coordenada_X']), "y": int(row_v1['Coordenada_Y']), "label": "V1"})
            
        elif t_type == "FASE_CORTE":
            # Corte contains all Corte_Lineal steps
            corte_rows = fig_rows[fig_rows['Operacion_CNC'] == 'Corte_Lineal']
            # Push in reverse order so they are popped in chronological order
            for _, row in corte_rows.iloc[::-1].iterrows():
                stack.append({
                    "type": "ACCION_MOVER",
                    "op": "Corte_Lineal",
                    "x": int(row['Coordenada_X']),
                    "y": int(row['Coordenada_Y']),
                    "label": str(row['Vertice_Secuencia'])
                })
                
        elif t_type == "FASE_RETORNO":
            # Retorno contains Apagar_Soplete and return to origin
            cierre_rows = fig_rows[fig_rows['Operacion_CNC'] == 'Apagar_Soplete']
            if not cierre_rows.empty:
                row_cierre = cierre_rows.iloc[0]
                # Push in reverse LIFO:
                # 1. Return to Origin
                # 2. Turn torch OFF
                # 3. Final cut to closing vertex
                stack.append({"type": "ACCION_MOVER", "op": "Traslado_Apagado", "x": 0, "y": 0, "label": "Origen"})
                stack.append({"type": "ACCION_SOPLETE", "op": "OFF", "x": int(row_cierre['Coordenada_X']), "y": int(row_cierre['Coordenada_Y']), "label": str(row_cierre['Vertice_Secuencia'])})
                stack.append({"type": "ACCION_MOVER", "op": "Corte_Lineal", "x": int(row_cierre['Coordenada_X']), "y": int(row_cierre['Coordenada_Y']), "label": str(row_cierre['Vertice_Secuencia'])})
        
        elif t_type == "ACCION_MOVER":
            start_x, start_y = current_pos
            end_x, end_y = task["x"], task["y"]
            code = "G00" if task["op"] == "Traslado_Apagado" else "G01"
            op_desc = "Traslado Rápido" if task["op"] == "Traslado_Apagado" else "Corte Lineal"
            
            # Record step
            step_num = len(pasos) + 1
            step_str = f"Paso {step_num}: ({start_x},{start_y}) -> ({end_x},{end_y}) | [{code} - {op_desc}]"
            pasos.append(step_str)
            
            # Record coordinate for drawing
            # We want to keep track of the trajectory points for the frontend canvas
            # We can also add labels for vertices
            coords.append({
                "x": end_x,
                "y": end_y,
                "op": task["op"],
                "label": task["label"]
            })
            
            current_pos = (end_x, end_y)
            
        elif t_type == "ACCION_SOPLETE":
            code = "M03" if task["op"] == "ON" else "M05"
            op_desc = "Encender Soplete" if task["op"] == "ON" else "Apagar Soplete"
            step_num = len(pasos) + 1
            step_str = f"Paso {step_num}: ({task['x']},{task['y']}) | [{code} - {op_desc}]"
            pasos.append(step_str)
            
    # Include initial origin point in coords at start
    coords_with_origin = [{"x": 0, "y": 0, "op": "Inicio", "label": "Origen"}] + coords
    
    return {
        "pasos": pasos,
        "coordenadas": coords_with_origin
    }

# Test the functions
print("TEST 1: Experto - Acero, Cuadrado, Presion 5")
print(run_expert_system("Cuadrado", "acero", 5))
print("DFS planning for Cuadrado:")
plan = run_dfs_planning("Cuadrado")
for p in plan['pasos']:
    print(p)

print("\nTEST 2: Experto - Acero, Circulo, Presion 5")
print(run_expert_system("Circulo", "acero", 5))

print("\nTEST 3: Experto - Madera, Estrella, Presion 3")
print(run_expert_system("Estrella", "madera", 3))
