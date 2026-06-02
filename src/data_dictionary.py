import pandas as pd
from typing import Dict, Any, List

def parse_variables(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses the variables definition from the 'Diccionario' sheet.
    """
    df = pd.read_excel(file_path, sheet_name='Diccionario', skiprows=5)
    
    # Clean column names (strip spaces)
    df.columns = [str(c).strip() for c in df.columns]
    
    variables = []
    for _, row in df.iterrows():
        # Stop if the row is empty or doesn't have a variable code
        code = row.get('Código de la variable')
        if pd.isnull(code) or str(code).strip() == '':
            continue
            
        variables.append({
            "code": str(code).strip(),
            "name": str(row.get('Nombre de la variable', '')).strip(),
            "definition": str(row.get('Definición de la variable', '')).strip(),
            "type": str(row.get('Tipo de variable', '')).strip(),
            "format": str(row.get('Formato del dato', '')).strip(),
            "length": row.get('Longitud') if pd.notnull(row.get('Longitud')) else None,
            "min_val": row.get('Valor mínimo') if pd.notnull(row.get('Valor mínimo')) else None,
            "max_val": row.get('Valor máximo') if pd.notnull(row.get('Valor máximo')) else None,
            "validation": str(row.get('Validación', '')).strip(),
            "risk": str(row.get('Riesgo', '')).strip()
        })
        
    return variables

def parse_colors(file_path: str) -> Dict[str, str]:
    """
    Parses the color catalog sheet.
    """
    df = pd.read_excel(file_path, sheet_name='Catálogo_Colores')
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    colors_map = {}
    for _, row in df.iterrows():
        code = row.get('CÓDIGO')
        desc = row.get('DESCRIPCION')
        if pd.notnull(code) and pd.notnull(desc):
            colors_map[str(code).strip()] = str(desc).strip()
            
    return colors_map

def parse_cantons(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses the cantons and provinces catalog sheet.
    """
    df = pd.read_excel(file_path, sheet_name='Catálogo_Cantones', skiprows=1)
    
    # Rename duplicate columns to make them clear
    df.columns = ['canton_code', 'canton_desc', 'province_code', 'province_desc']
    
    cantons_map = {}
    for _, row in df.iterrows():
        c_code = row.get('canton_code')
        c_desc = row.get('canton_desc')
        p_code = row.get('province_code')
        p_desc = row.get('province_desc')
        
        if pd.notnull(c_code) and pd.notnull(c_desc):
            # Convert float canton codes to int, then string
            try:
                c_code_str = str(int(float(c_code))).strip()
            except ValueError:
                c_code_str = str(c_code).strip()
                
            try:
                p_code_str = str(int(float(p_code))).strip() if pd.notnull(p_code) else None
            except ValueError:
                p_code_str = str(p_code).strip() if pd.notnull(p_code) else None
                
            cantons_map[c_code_str] = {
                "canton_name": str(c_desc).strip(),
                "province_code": p_code_str,
                "province_name": str(p_desc).strip() if pd.notnull(p_desc) else None
            }
            
    return cantons_map

def parse_data_dictionary(file_path: str) -> Dict[str, Any]:
    """
    Parses the entire data dictionary excel file.
    """
    return {
        "variables": parse_variables(file_path),
        "colors": parse_colors(file_path),
        "cantons": parse_cantons(file_path)
    }
