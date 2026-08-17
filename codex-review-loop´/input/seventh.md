import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# 1. Cargar el dataset
file_path = 'dataset_de_cnc.xlsx'
df_experto = pd.read_excel(file_path, sheet_name='parametros_experto')

# 2. Definir entradas (X) y MÚLTIPLES salidas (y: Velocidad Y Potencia)
X = df_experto[['Material', 'Figura_Compleja']]
y = df_experto[['Velocidad_Sugerida', 'Potencia_Sugerida']]

# 3. Crear transformador con OneHotEncoder
preprocesador = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(sparse_output=False), ['Material', 'Figura_Compleja'])
    ]
)

# 4. Crear Pipeline con el árbol de decisión
modelo_multisalida = Pipeline(steps=[
    ('preprocesador', preprocesador),
    ('arbol', DecisionTreeClassifier(criterion='entropy', random_state=42))
])

# 5. Entrenar el modelo
modelo_multisalida.fit(X, y)

# 6. Probar con una nueva entrada de la máquina CNC
entrada_prueba = pd.DataFrame([['acero', 'no']], columns=['Material', 'Figura_Compleja'])
prediccion = modelo_multisalida.predict(entrada_prueba)

print("=== PARÁMETROS CNC OPTIMIZADOS POR LA IA ===")
print(f"Entrada: Material = Acero | Figura Compleja = No")
print(f"-> Velocidad: {prediccion[0][0]}")
print(f"-> Potencia:  {prediccion[0][1]}")

# 7. Imprimir las reglas claras con nombres de columnas reales
nombres_columnas = modelo_multisalida.named_steps['preprocesador'].get_feature_names_out()
reglas_claras = export_text(modelo_multisalida.named_steps['arbol'], feature_names=list(nombres_columnas))

print("\n=== ÁRBOL DE DECISIÓN MEJORADO (LEGIBLE) ===")
print(reglas_claras)