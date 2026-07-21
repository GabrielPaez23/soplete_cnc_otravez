import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

excel_path = "dataset_de_cnc.xlsx"
xls = pd.ExcelFile(excel_path)
for name in xls.sheet_names:
    print(f"\n================ SHEET: {name} ================")
    df = pd.read_excel(excel_path, sheet_name=name)
    print(df)
