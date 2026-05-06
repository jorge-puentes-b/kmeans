from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.data_service import (
    COLUMN_DESCRIPTIONS,
    build_dataset_summary,
    clean_dataset,
    get_numeric_columns,
    load_dataset,
)
from services.kmeans_service import run_kmeans_analysis
from services.plot_service import centroid_bar_html, cluster_scatter_html, elbow_plot_html

# Crear el Blueprint de rutas
main_bp = Blueprint("main", __name__)

# Ruta de la carpeta donde estan los datasets
CARPETA_DATOS = Path(__file__).resolve().parents[1] / "data"

# Valores por defecto al iniciar la app
DATASET_DEFAULT = "Mall_Customers.csv"
COLUMNAS_DEFAULT = ["Annual Income (k$)", "Spending Score (1-100)"]
K_DEFAULT = 3


# Funcion para obtener la lista de datasets disponibles en la carpeta data
def obtener_datasets_disponibles():
    archivos = []
    for archivo in sorted(CARPETA_DATOS.glob("*.csv")):
        archivos.append(archivo.name)
    for archivo in sorted(CARPETA_DATOS.glob("*.xlsx")):
        archivos.append(archivo.name)
    for archivo in sorted(CARPETA_DATOS.glob("*.xls")):
        archivos.append(archivo.name)
    return archivos


# Funcion para saber cual dataset esta activo en la sesion del usuario
def obtener_dataset_activo():
    datasets = obtener_datasets_disponibles()

    if len(datasets) == 0:
        raise ValueError("No hay archivos en la carpeta data. Agrega un CSV o Excel.")

    # Buscar el nombre guardado en sesion
    nombre = session.get("dataset_file", DATASET_DEFAULT)

    # Si el nombre no esta disponible usar el primero de la lista
    if nombre not in datasets:
        nombre = datasets[0]
        session["dataset_file"] = nombre

    return CARPETA_DATOS / nombre


# Funcion para obtener las columnas y el K guardados en sesion
def obtener_configuracion():
    # Cargar el dataset activo para saber que columnas hay disponibles
    ruta = obtener_dataset_activo()
    df_raw = load_dataset(str(ruta))
    df = clean_dataset(df_raw)
    cols_disponibles = get_numeric_columns(df)

    # Columnas guardadas en sesion
    columnas = session.get("feature_columns", COLUMNAS_DEFAULT)

    # Filtrar columnas que ya no existan en el dataset actual
    columnas = [c for c in columnas if c in cols_disponibles]

    # Si quedaron menos de 2 columnas, usar las primeras 2 disponibles
    if len(columnas) < 2:
        columnas = cols_disponibles[:2]

    # Obtener el valor de K
    try:
        k = int(session.get("n_clusters", K_DEFAULT))
    except:
        k = K_DEFAULT

    # Asegurarse de que K sea valido
    if k < 2:
        k = 2

    return columnas, k


# --- RUTAS ---

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dataset")
def dataset():
    try:
        ruta = obtener_dataset_activo()
        df_raw = load_dataset(str(ruta))
        df = clean_dataset(df_raw)
        resumen = build_dataset_summary(df_raw, df)
        datasets = obtener_datasets_disponibles()

        return render_template(
            "dataset.html",
            summary=resumen,
            sample=df.head(20).to_dict(orient="records"),
            columns=df.columns.tolist(),
            datasets=datasets,
            active_dataset=ruta.name,
        )
    except Exception as error:
        flash("Error al cargar el dataset: " + str(error), "danger")
        return render_template("dataset.html", summary=None, sample=[], columns=[], datasets=[], active_dataset="")


@main_bp.route("/dataset/select", methods=["POST"])
def select_dataset():
    nombre = request.form.get("dataset_file", "").strip()
    datasets = obtener_datasets_disponibles()

    # Verificar que el archivo existe en la lista
    if nombre not in datasets:
        flash("Ese archivo no esta disponible en la carpeta data.", "danger")
        return redirect(url_for("main.dataset"))

    # Guardar el nuevo dataset en sesion y borrar la configuracion anterior
    session["dataset_file"] = nombre
    session.pop("feature_columns", None)
    flash("Dataset cambiado a: " + nombre, "success")
    return redirect(url_for("main.dataset"))


@main_bp.route("/conceptos")
def conceptos():
    return render_template("conceptos.html")


@main_bp.route("/ejecucion", methods=["GET", "POST"])
def ejecucion():
    # Cargar el dataset activo
    ruta = obtener_dataset_activo()
    df_raw = load_dataset(str(ruta))
    df = clean_dataset(df_raw)
    cols_numericas = get_numeric_columns(df)
    columnas_actuales, k_actual = obtener_configuracion()

    if request.method == "POST":
        # Leer los datos del formulario
        columnas_seleccionadas = request.form.getlist("feature_columns")
        k_texto = request.form.get("n_clusters", "3")

        # Validar el numero de clusters
        try:
            k = int(k_texto)
        except:
            flash("El numero de clusters debe ser un numero entero.", "danger")
            return redirect(url_for("main.ejecucion"))

        if k < 2 or k > 10:
            flash("El numero de clusters debe estar entre 2 y 10.", "danger")
            return redirect(url_for("main.ejecucion"))

        # Validar que se seleccionaron columnas suficientes
        if len(columnas_seleccionadas) < 2:
            flash("Debes seleccionar al menos 2 variables para el clustering.", "danger")
            return redirect(url_for("main.ejecucion"))

        # Guardar la configuracion en sesion
        session["feature_columns"] = columnas_seleccionadas
        session["n_clusters"] = k

        flash("Configuracion guardada correctamente. Ahora revisa los clusters.", "success")
        return redirect(url_for("main.clusters"))

    return render_template(
        "ejecucion.html",
        numeric_columns=cols_numericas,
        selected_columns=columnas_actuales,
        k_value=k_actual,
        descriptions=COLUMN_DESCRIPTIONS,
        active_dataset=ruta.name,
    )


@main_bp.route("/clusters")
def clusters():
    try:
        ruta = obtener_dataset_activo()
        columnas, k = obtener_configuracion()

        # Correr el algoritmo K-Means
        resultado = run_kmeans_analysis(str(ruta), columnas, k)

        # Crear la grafica de dispersion
        grafica = cluster_scatter_html(
            resultado["result_df"],
            columnas[0],
            columnas[1],
            resultado["centroids_df"],
        )

        return render_template(
            "clusters.html",
            scatter_html=grafica,
            selected_columns=columnas,
            k_value=k,
        )
    except Exception as error:
        flash("Error al generar los clusters: " + str(error), "danger")
        return redirect(url_for("main.ejecucion"))


@main_bp.route("/centroides")
def centroides():
    try:
        ruta = obtener_dataset_activo()
        columnas, k = obtener_configuracion()
        resultado = run_kmeans_analysis(str(ruta), columnas, k)

        # Crear la grafica de barras de centroides
        grafica_barras = centroid_bar_html(resultado["centroids_df"], columnas)

        return render_template(
            "centroides.html",
            centroides=resultado["centroids_df"].round(3).to_dict(orient="records"),
            columns=resultado["centroids_df"].columns.tolist(),
            centroid_chart=grafica_barras,
        )
    except Exception as error:
        flash("Error al mostrar centroides: " + str(error), "danger")
        return redirect(url_for("main.ejecucion"))


@main_bp.route("/elbow")
def elbow():
    try:
        ruta = obtener_dataset_activo()
        columnas, k = obtener_configuracion()
        resultado = run_kmeans_analysis(str(ruta), columnas, k)

        # Crear la grafica del metodo del codo
        grafica_codo = elbow_plot_html(resultado["k_values"], resultado["inertias"])

        return render_template(
            "elbow.html",
            elbow_html=grafica_codo,
            k_values=resultado["k_values"],
            inertias=[round(v, 3) for v in resultado["inertias"]],
        )
    except Exception as error:
        flash("Error al mostrar el metodo del codo: " + str(error), "danger")
        return redirect(url_for("main.ejecucion"))


@main_bp.route("/resultados")
def resultados():
    try:
        ruta = obtener_dataset_activo()
        columnas, k = obtener_configuracion()
        resultado = run_kmeans_analysis(str(ruta), columnas, k)

        df_resultado = resultado["result_df"]

        return render_template(
            "resultados.html",
            result_columns=df_resultado.columns.tolist(),
            result_rows=df_resultado.round(3).to_dict(orient="records"),
            stats_columns=resultado["stats_df"].columns.tolist(),
            stats_rows=resultado["stats_df"].round(3).to_dict(orient="records"),
            k_value=k,
            selected_columns=columnas,
        )
    except Exception as error:
        flash("Error al mostrar los resultados: " + str(error), "danger")
        return redirect(url_for("main.ejecucion"))
