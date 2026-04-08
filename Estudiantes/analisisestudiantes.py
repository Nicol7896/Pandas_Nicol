import pandas as pd
import plotly.express as px
import os
import dash
from dash import html, Input, Output, dcc

ruta = os.path.join(os.path.dirname(__file__), "coso.xlsx")

dataf = pd.read_excel(ruta)
print(dataf)

appnotas = dash.Dash(__name__)

appnotas.layout = html.Div([
    html.H1(
        "Tablero de notas de estudiantes",
        style={
            "textAlign": "center",
            "color": "#F54927",
            "padding": "20px",
            "fontFamily": "Arial",
            "backgroundColor": "#A9D1EC"
        }
    ),

    html.Label("SELECCIONAR CARRERA", style={"margin": "10px"}),

    dcc.Dropdown(
        id="filtro_materia",
        options=[{"label": c, "value": c} for c in sorted(dataf["Carrera"].unique())],
        value=dataf["Carrera"].unique()[0],
        style={"width": "100%", "margin": "auto"}
    ),

    html.Br(),

    dcc.Tabs([
        dcc.Tab(
            label='Grafico de promedio',
            children=[dcc.Graph(id='histograma')]
        )
    ], style={"color":"#2c3e50","fontWeight":"bold"})
])


@appnotas.callback(
    Output("histograma", "figure"),
    Input("filtro_materia", "value")
)
def actualizarG(filtro_materia):

    filtro = dataf[dataf["Carrera"] == filtro_materia]

    histo = px.histogram(
        filtro,
        x="Promedio",
        nbins=10,
        title=f"Distribucion de promedios - {filtro_materia}",
        color_discrete_sequence=["#3498db"]
    )

    histo.update_layout(
        template="plotly_white",
        yaxis_title="Cantidad"
    )

    return histo


if __name__ == "__main__":
    appnotas.run(debug=True)