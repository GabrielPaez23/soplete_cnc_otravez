# Contenido del Dataset CNC

## Hoja: `figuras`

|   ID_Pieza | Figura    | Vertice_Secuencia   |   Coordenada_X |   Coordenada_Y |   Coordenada_Z | Operacion_CNC    |   Pasos_Acumulados |
|-----------:|:----------|:--------------------|---------------:|---------------:|---------------:|:-----------------|-------------------:|
|          1 | Cuadrado  | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          1 | Cuadrado  | V1                  |             10 |             10 |              0 | Encender_Soplete |                  1 |
|          1 | Cuadrado  | V2                  |             50 |             10 |              0 | Corte_Lineal     |                  2 |
|          1 | Cuadrado  | V3                  |             50 |             50 |              0 | Corte_Lineal     |                  3 |
|          1 | Cuadrado  | V4                  |             10 |             50 |              0 | Corte_Lineal     |                  4 |
|          1 | Cuadrado  | V1 (Cierre)         |             10 |             10 |              0 | Apagar_Soplete   |                  5 |
|          2 | Triangulo | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          2 | Triangulo | V1                  |             60 |             15 |              0 | Encender_Soplete |                  1 |
|          2 | Triangulo | V2                  |             90 |             15 |              0 | Corte_Lineal     |                  2 |
|          2 | Triangulo | V3                  |             75 |             45 |              0 | Corte_Lineal     |                  3 |
|          2 | Triangulo | V1 (Cierre)         |             60 |             15 |              0 | Apagar_Soplete   |                  4 |
|          3 | Rombo     | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          3 | Rombo     | V1                  |            110 |             30 |              0 | Encender_Soplete |                  1 |
|          3 | Rombo     | V2                  |            130 |             50 |              0 | Corte_Lineal     |                  2 |
|          3 | Rombo     | V3                  |            110 |             70 |              0 | Corte_Lineal     |                  3 |
|          3 | Rombo     | V4                  |             90 |             50 |              0 | Corte_Lineal     |                  4 |
|          3 | Rombo     | V1 (Cierre)         |            110 |             30 |              0 | Apagar_Soplete   |                  5 |
|          4 | Circulo   | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          4 | Circulo   | V1                  |            190 |            150 |              0 | Encender_Soplete |                  1 |
|          4 | Circulo   | V2                  |            178 |            178 |              0 | Corte_Lineal     |                  2 |
|          4 | Circulo   | V3                  |            150 |            190 |              0 | Corte_Lineal     |                  3 |
|          4 | Circulo   | V4                  |            122 |            178 |              0 | Corte_Lineal     |                  4 |
|          4 | Circulo   | V5                  |            110 |            150 |              0 | Corte_Lineal     |                  5 |
|          4 | Circulo   | V6                  |            122 |            122 |              0 | Corte_Lineal     |                  6 |
|          4 | Circulo   | V7                  |            150 |            110 |              0 | Corte_Lineal     |                  7 |
|          4 | Circulo   | V8                  |            178 |            122 |              0 | Corte_Lineal     |                  8 |
|          4 | Circulo   | V1 (Cierre)         |            190 |            150 |              0 | Apagar_Soplete   |                  9 |
|          5 | Estrella  | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          5 | Estrella  | V1                  |            165 |            120 |              0 | Encender_Soplete |                  1 |
|          5 | Estrella  | V2                  |            135 |            131 |              0 | Corte_Lineal     |                  2 |
|          5 | Estrella  | V3                  |            134 |            163 |              0 | Corte_Lineal     |                  3 |
|          5 | Estrella  | V4                  |            111 |            137 |              0 | Corte_Lineal     |                  4 |
|          5 | Estrella  | V5                  |             84 |            146 |              0 | Corte_Lineal     |                  5 |
|          5 | Estrella  | V6                  |            101 |            120 |              0 | Corte_Lineal     |                  6 |
|          5 | Estrella  | V7                  |             84 |             94 |              0 | Corte_Lineal     |                  7 |
|          5 | Estrella  | V8                  |            111 |            103 |              0 | Corte_Lineal     |                  8 |
|          5 | Estrella  | V9                  |            134 |             77 |              0 | Corte_Lineal     |                  9 |
|          5 | Estrella  | V10                 |            135 |            109 |              0 | Corte_Lineal     |                 10 |
|          5 | Estrella  | V1 (Cierre)         |            165 |            120 |              0 | Apagar_Soplete   |                 11 |
|          6 | Cubo      | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          6 | Cubo      | V1_Base             |             20 |             20 |              0 | Encender_Soplete |                  1 |
|          6 | Cubo      | V2_Base             |             60 |             20 |              0 | Corte_Lineal     |                  2 |
|          6 | Cubo      | V3_Base             |             60 |             60 |              0 | Corte_Lineal     |                  3 |
|          6 | Cubo      | V4_Base             |             20 |             60 |              0 | Corte_Lineal     |                  4 |
|          6 | Cubo      | V1_Base_Cierre      |             20 |             20 |              0 | Corte_Lineal     |                  5 |
|          6 | Cubo      | V1_Top              |             20 |             20 |             40 | Corte_Lineal     |                  6 |
|          6 | Cubo      | V2_Top              |             60 |             20 |             40 | Corte_Lineal     |                  7 |
|          6 | Cubo      | V3_Top              |             60 |             60 |             40 | Corte_Lineal     |                  8 |
|          6 | Cubo      | V4_Top              |             20 |             60 |             40 | Corte_Lineal     |                  9 |
|          6 | Cubo      | V1_Top_Cierre       |             20 |             20 |             40 | Corte_Lineal     |                 10 |
|          6 | Cubo      | Fin                 |             20 |             20 |             40 | Apagar_Soplete   |                 11 |
|          7 | Piramide  | Origen              |              0 |              0 |              0 | Traslado_Apagado |                  0 |
|          7 | Piramide  | V1_Base             |             30 |             30 |              0 | Encender_Soplete |                  1 |
|          7 | Piramide  | V2_Base             |             80 |             30 |              0 | Corte_Lineal     |                  2 |
|          7 | Piramide  | V3_Base             |             80 |             80 |              0 | Corte_Lineal     |                  3 |
|          7 | Piramide  | V4_Base             |             30 |             80 |              0 | Corte_Lineal     |                  4 |
|          7 | Piramide  | V1_Base_Cierre      |             30 |             30 |              0 | Corte_Lineal     |                  5 |
|          7 | Piramide  | Cuspide             |             55 |             55 |             45 | Corte_Lineal     |                  6 |
|          7 | Piramide  | V2_Base             |             80 |             30 |              0 | Corte_Lineal     |                  7 |
|          7 | Piramide  | Cuspide_2           |             55 |             55 |             45 | Corte_Lineal     |                  8 |
|          7 | Piramide  | V3_Base             |             80 |             80 |              0 | Corte_Lineal     |                  9 |
|          7 | Piramide  | Fin                 |             80 |             80 |              0 | Apagar_Soplete   |                 10 |

---

## Hoja: `parametros_experto`

| Material   | Figura_Compleja   |   Presion_Min_Gas | Potencia_Sugerida         | Velocidad_Sugerida                |
|:-----------|:------------------|------------------:|:--------------------------|:----------------------------------|
| acero      | no                |                 4 | 75% (Corte óptimo)        | Rápida (G01 - 1800 mm/min)        |
| aluminio   | no                |                 4 | 100% (Alta reflectividad) | Moderada (G01 - 1200 mm/min)      |
| madera     | no                |                 4 | 40% (Baja potencia)       | Rápida (G01 - 2000 mm/min)        |
| circulo    | si                |                 4 | 80% (Estándar)            | Precisión Fina (G01 - 800 mm/min) |
| estrella   | si                |                 4 | 80% (Estándar)            | Precisión Fina (G01 - 800 mm/min) |
| cubo       | si                |                 4 | 85% (3D Multieje)         | Precisión 3D (G01 - 600 mm/min)   |
| piramide   | si                |                 4 | 85% (3D Multieje)         | Precisión 3D (G01 - 600 mm/min)   |

---

