import pandas as pd

excel_path = "dataset_de_cnc.xlsx"
try:
    xls = pd.ExcelFile(excel_path)
    print("Sheets available:", xls.sheet_names)
    for sheet_name in xls.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print("Columns:", df.columns.tolist())
        print(df)
except Exception as e:
    print("Error reading excel:", e)
