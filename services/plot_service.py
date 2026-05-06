import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Funcion para crear la grafica de dispersion con los clusters y los centroides
def cluster_scatter_html(df, col_x, col_y, centroides_df):
    # Armar el hover (lo que se ve al pasar el mouse sobre un punto)
    info_hover = {
        col_x: ":.2f",
        col_y: ":.2f",
        "cluster": True,
        "distancia_centroide": ":.3f",
    }

    # Si el dataset tiene columna CustomerID la muestro tambien
    if "CustomerID" in df.columns:
        info_hover["CustomerID"] = True

    # Crear la grafica de dispersion con Plotly Express
    fig = px.scatter(
        df,
        x=col_x,
        y=col_y,
        color="cluster",
        hover_data=info_hover,
        title="Segmentos de Clientes: " + col_x + " vs " + col_y,
        opacity=0.8,
    )

    # Agregar los centroides como marcadores X en la grafica
    fig.add_trace(
        go.Scatter(
            x=centroides_df[col_x],
            y=centroides_df[col_y],
            mode="markers+text",
            name="Centroides",
            marker=dict(symbol="x", size=15, color="black", line=dict(width=3)),
            text=["C" + str(int(c)) for c in centroides_df["cluster"]],
            textposition="top center",
        )
    )

    fig.update_layout(template="plotly_white")

    # Convertir la figura a HTML para mostrarla en la pagina
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


# Funcion para crear la grafica del metodo del codo
def elbow_plot_html(lista_k, lista_inercias):
    fig = go.Figure()

    # Agregar la linea de inercia vs K
    fig.add_trace(
        go.Scatter(
            x=lista_k,
            y=lista_inercias,
            mode="lines+markers",
            marker=dict(size=10),
            line=dict(width=3),
            name="Inercia",
        )
    )

    fig.update_layout(
        title="Metodo del Codo - Inercia segun el numero de clusters",
        xaxis_title="Numero de Clusters (K)",
        yaxis_title="Inercia",
        template="plotly_white",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


# Funcion para crear la grafica de barras comparando los centroides
def centroid_bar_html(centroides_df, columnas):
    # Armar los datos manualmente en una lista de diccionarios
    datos = []
    for i in range(len(centroides_df)):
        fila = centroides_df.iloc[i]
        for col in columnas:
            datos.append({
                "cluster": "Cluster " + str(int(fila["cluster"])),
                "variable": col,
                "valor": round(float(fila[col]), 2),
            })

    # Convertir la lista a DataFrame para poder graficarla
    df_grafica = pd.DataFrame(datos)

    fig = px.bar(
        df_grafica,
        x="variable",
        y="valor",
        color="cluster",
        barmode="group",
        title="Valores de los Centroides por Variable",
    )

    fig.update_layout(template="plotly_white")

    return fig.to_html(full_html=False, include_plotlyjs="cdn")
