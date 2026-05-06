import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from services.data_service import load_dataset, clean_dataset, get_numeric_columns


# Guardo el ultimo resultado aqui para no tener que recalcular todo cada vez
# Es como un "cache" simple usando una variable global
ultimo_resultado = {
    "ruta": None,
    "columnas": None,
    "k": None,
    "datos": None,
}


# Esta es la funcion principal que corre el algoritmo K-Means
def run_kmeans_analysis(ruta_datos, columnas, n_clusters, max_k=10):
    global ultimo_resultado

    # Verificar que hay al menos 2 columnas seleccionadas
    if len(columnas) < 2:
        raise ValueError("Necesitas seleccionar al menos 2 columnas para el clustering.")

    # Verificar que el numero de clusters es valido
    if n_clusters < 2:
        raise ValueError("El numero de clusters debe ser minimo 2.")

    # Si ya calcule esto antes con los mismos parametros, devuelvo el resultado guardado
    if (ultimo_resultado["ruta"] == ruta_datos and
            ultimo_resultado["columnas"] == list(columnas) and
            ultimo_resultado["k"] == n_clusters):
        return ultimo_resultado["datos"]

    # --- PASO 1: Cargar y limpiar los datos ---
    df_raw = load_dataset(ruta_datos)
    df = clean_dataset(df_raw)

    # Verificar que las columnas existen en el dataset
    for col in columnas:
        if col not in df.columns:
            raise ValueError("La columna '" + col + "' no existe en el dataset.")

    # --- PASO 2: Preparar los datos para el algoritmo ---
    # Solo me quedo con las columnas seleccionadas
    X = df[list(columnas)].copy()

    # Normalizar con StandardScaler (pone todo en la misma escala)
    escalador = StandardScaler()
    X_escalado = escalador.fit_transform(X)

    # --- PASO 3: Calcular la inercia para el metodo del codo ---
    # Pruebo desde K=1 hasta max_k y guardo la inercia de cada uno
    lista_k = list(range(1, max_k + 1))
    lista_inercias = []

    for k in lista_k:
        modelo_temp = KMeans(n_clusters=k, random_state=42, n_init=10)
        modelo_temp.fit(X_escalado)
        lista_inercias.append(float(modelo_temp.inertia_))

    # --- PASO 4: Entrenar el modelo con el K que eligio el usuario ---
    modelo_final = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    etiquetas = modelo_final.fit_predict(X_escalado)

    # Calcular la distancia de cada punto a su centroide
    distancias = []
    for i in range(len(X_escalado)):
        cluster_del_punto = etiquetas[i]
        centroide = modelo_final.cluster_centers_[cluster_del_punto]
        distancia = np.linalg.norm(X_escalado[i] - centroide)
        distancias.append(round(distancia, 4))

    # Agregar los resultados al dataframe
    df["cluster"] = etiquetas
    df["distancia_centroide"] = distancias

    # --- PASO 5: Calcular los centroides en escala original ---
    centroides_normalizados = modelo_final.cluster_centers_
    centroides_originales = pd.DataFrame(
        escalador.inverse_transform(centroides_normalizados),
        columns=list(columnas)
    )
    centroides_originales["cluster"] = list(range(n_clusters))

    # Reordenar para que cluster quede primero
    columnas_orden = ["cluster"] + list(columnas)
    centroides_originales = centroides_originales[columnas_orden]

    # --- PASO 6: Calcular estadisticas por cluster ---
    # Hago esto manualmente para que sea mas claro
    filas_stats = []
    for cluster_id in range(n_clusters):
        datos_cluster = df[df["cluster"] == cluster_id]
        fila = {"cluster": cluster_id}
        for col in columnas:
            fila[col + "_promedio"] = round(float(datos_cluster[col].mean()), 3)
            fila[col + "_desv_std"] = round(float(datos_cluster[col].std()), 3)
        fila["cantidad_clientes"] = len(datos_cluster)
        filas_stats.append(fila)

    df_stats = pd.DataFrame(filas_stats)

    # Guardar el resultado en la variable global
    resultado = {
        "feature_columns": list(columnas),
        "n_clusters": n_clusters,
        "k_values": lista_k,
        "inertias": lista_inercias,
        "result_df": df,
        "centroids_df": centroides_originales,
        "stats_df": df_stats,
        "preview_rows": df.head(15).round(4).to_dict(orient="records"),
    }

    ultimo_resultado["ruta"] = ruta_datos
    ultimo_resultado["columnas"] = list(columnas)
    ultimo_resultado["k"] = n_clusters
    ultimo_resultado["datos"] = resultado

    return resultado
