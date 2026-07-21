import zipfile
import xml.etree.ElementTree as ET

excel_path = "dataset_de_cnc.xlsx"
try:
    with zipfile.ZipFile(excel_path, 'r') as zip_ref:
        # Read workbook.xml to get sheet names
        wb_xml = zip_ref.read("xl/workbook.xml")
        root = ET.fromstring(wb_xml)
        
        # Namespace
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        sheets = root.findall('.//ns:sheet', ns)
        print("Sheets in workbook:")
        for sheet in sheets:
            print(sheet.attrib)
            
except Exception as e:
    print("Error reading excel zip:", e)
