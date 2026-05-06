import pandas as pd


# Aqui pongo el significado de cada columna del dataset de clientes del mall
COLUMN_DESCRIPTIONS = {
    "CustomerID": "Numero de identificacion unico del cliente.",
    "Gender": "Genero del cliente (Male o Female).",
    "Age": "Edad del cliente en anios.",
    "Annual Income (k$)": "Ingreso anual del cliente en miles de dolares.",
    "Spending Score (1-100)": "Puntaje de gasto asignado por el mall (1 = bajo, 100 = alto).",
}


# Esta funcion carga el archivo del dataset
def load_dataset(ruta):
    # Verificar si es CSV o Excel y cargarlo
    if ruta.endswith(".csv"):
        df = pd.read_csv(ruta)
    elif ruta.endswith(".xlsx") or ruta.endswith(".xls"):
        df = pd.read_excel(ruta)
    else:
        raise ValueError("Solo se admiten archivos CSV o Excel.")
    return df



# Esta funcion devuelve solo las columnas que son numericas y sirven para clustering
def get_numeric_columns(df):
    # Tipos de datos que consideramos numericos
    tipos_num = ["int64", "float64", "int32", "float32", "int16", "int8"]

    # Nombres de columnas que son identificadores y no deben usarse para clustering
    columnas_id = ["id", "customerid", "customer_id", "clienteid", "cliente_id", "cluster"]

    cols = []
    for col in df.columns:
        # Revisar si el tipo de dato es numerico
        if str(df[col].dtype) in tipos_num:
            # Limpiar el nombre para comparar
            nombre_limpio = col.replace(" ", "").replace("_", "").lower()
            # Ignorar columnas de ID o la columna cluster
            if nombre_limpio not in columnas_id:
                cols.append(col)

    return cols


# Esta funcion limpia el dataset: rellena valores vacios
def clean_dataset(df):
    # Hacer una copia para no modificar el original
    df_limpio = df.copy()

    # Obtener columnas numericas
    cols_num = get_numeric_columns(df_limpio)

    # Rellenar los valores faltantes con la mediana de cada columna
    for col in cols_num:
        cantidad_vacios = df_limpio[col].isnull().sum()
        if cantidad_vacios > 0:
            valor_mediana = df_limpio[col].median()
            df_limpio[col] = df_limpio[col].fillna(valor_mediana)

    return df_limpio


# Esta funcion arma un resumen del dataset para mostrarlo en la pagina
def build_dataset_summary(df_raw, df_clean):
    cols_num = get_numeric_columns(df_clean)

    # Calcular el rango de cada columna numerica
    rangos = {}
    for col in cols_num:
        rangos[col] = {
            "min": round(float(df_clean[col].min()), 3),
            "max": round(float(df_clean[col].max()), 3),
            "dtype": str(df_clean[col].dtype),
        }

    # Crear el diccionario con toda la informacion
    resumen = {
        "total_rows": len(df_clean),
        "total_columns": df_clean.shape[1],
        "numeric_columns": cols_num,
        "missing_values_raw": int(df_raw.isnull().sum().sum()),
        "missing_values_clean": int(df_clean.isnull().sum().sum()),
        "ranges": rangos,
        "column_descriptions": COLUMN_DESCRIPTIONS,
    }

    return resumen
