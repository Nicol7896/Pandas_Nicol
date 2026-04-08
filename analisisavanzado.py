import pandas as pd
import plotly.express as px
import os
import dash
from dash import Input, Output, dcc, html, dash_table
from database import obtener_estudiantes
from flask import Flask, render_template, request, redirect, session


def creartablero(server):

    appnotas = dash.Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/tablero/"
    )

    dataf = obtener_estudiantes()

    appnotas.layout = html.Div([

        html.H1(
            "TABLERO AVANZADO",
            style={
                'textAlign': 'center',
                'backgroundColor': '#ecf0f1',
                'color': '#2c3e50',
                "padding": "20px",
                'borderRadius': '10px',
                'fontFamily': 'poppins'
            }
        ),

        html.Div([

            html.Label("Selecciona una carrera:"),

            dcc.Dropdown(
                id='filtro-carrera',
                options=[
                    {'label': carrera, 'value': carrera}
                    for carrera in dataf['carrera'].unique()
                ],
                value=dataf['carrera'].unique()[0]
            ),

            html.Br(),

            html.Label("Rango de edades:"),

            dcc.RangeSlider(
                id='rango-edades',
                min=int(dataf['edad'].min()),
                max=int(dataf['edad'].max()),
                step=1,
                tooltip={"placement": "bottom", "always_visible": True},
                value=[
                    int(dataf['edad'].min()),
                    int(dataf['edad'].max())
                ],
            ),

            html.Br(),

            html.Label("Rango promedio:"),

            html.Div([
                dcc.RangeSlider(
                    id='rango-promedio',
                    min=float(dataf['promedio'].min()),
                    max=float(dataf['promedio'].max()),
                    step=0.1,
                    tooltip={"placement": "bottom", "always_visible": True},
                    value=[
                        float(dataf['promedio'].min()),
                        float(dataf['promedio'].max())
                    ],
                )
            ], style={'marginBottom': '30px'}),

            html.Br(),

            html.Div(
                id="kpis",
                style={
                    "display": "flex",
                    "justifyContent": "space-around",
                    "marginBottom": "30px"
                }
            ),

            html.Div(
                id="aviso-seleccion",
                style={
                    "textAlign": "center",
                    "color": "#e67e22",
                    "fontFamily": "poppins",
                    "marginBottom": "10px",
                    "fontWeight": "bold"
                }
            ),

            dcc.Loading(
                dash_table.DataTable(
                    id="tabla",
                    row_selectable="multi",
                    filter_action="native",
                    sort_action="native",
                    page_action="native",
                    page_size=10,
                    selected_rows=[],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '10px',
                        'fontFamily': 'poppins',
                        'backgroundColor': '#ecf0f1',
                        'color': '#2c3e50',
                        'border': '1px solid #bdc3c7'
                    },

                    style_data_conditional=[{
                        'if': {'state': 'selected'},
                        'backgroundColor': '#d5e8d4',
                        'border': '1px solid #82b366'
                    }]
                ),
                type="circle"
            ),

            html.Br(),

            dcc.Loading(
                dcc.Graph(id='grafico-detallado'),
                type="default"
            ),

            html.Br(),

            dcc.Tabs([
                dcc.Tab(label="Histograma", children=dcc.Graph(id='histograma')),
                dcc.Tab(label="Dispersión", children=dcc.Graph(id='dispersion')),
                dcc.Tab(label="Pie Edad", children=dcc.Graph(id='pie')),
                dcc.Tab(label="Barras Desempeño", children=dcc.Graph(id='barras'))
            ])

        ])
    ])


    @appnotas.callback(
        Output('tabla', 'data'),
        Output('kpis', 'children'),
        Output("tabla", "columns"),
        Output("grafico-detallado", "figure"),
        Output("histograma", "figure"),
        Output("dispersion", "figure"),
        Output("pie", "figure"),
        Output("barras", "figure"),
        Output("aviso-seleccion", "children"),
        Input("filtro-carrera", "value"),
        Input("rango-edades", "value"),
        Input("rango-promedio", "value"),
        Input("tabla", "selected_rows")
    )

    def actualizar_comp(carrera, rangoedad, rangoprome, selected_rows):

        dataf = obtener_estudiantes()

        filtro = dataf[
            (dataf['carrera'] == carrera) &
            (dataf['edad'] >= rangoedad[0]) &
            (dataf['edad'] <= rangoedad[1]) &
            (dataf['promedio'] >= rangoprome[0]) &
            (dataf['promedio'] <= rangoprome[1])
        ].copy()

        if selected_rows:
            filtro_grafico = filtro.iloc[selected_rows]
            aviso = f" Mostrando gráficos para {len(selected_rows)} estudiante(s) seleccionado(s). Desmarca para ver todos."
        else:
            filtro_grafico = filtro
            aviso = ""

        promedio = round(filtro_grafico['promedio'].mean(), 2) if not filtro_grafico.empty else 0
        total = len(filtro_grafico)
        maximo = round(filtro_grafico['promedio'].max(), 2) if not filtro_grafico.empty else 0

        fig_detalle = px.box(
            filtro_grafico, x="carrera", y="promedio",
            title="Distribución de Promedios"
        )

        fig_hist = px.histogram(
            filtro_grafico, x="promedio", color="carrera",
            nbins=15,
            title="Histograma de Promedios"
        )

        fig_disp = px.scatter(
            filtro_grafico, x="edad", y="promedio",
            color="carrera", size="promedio",
            title="Dispersión Edad vs Promedio"
        )

        filtro_grafico = filtro_grafico.copy()

        filtro_grafico["Rango Edad"] = pd.cut(
            filtro_grafico["edad"],
            bins=[0, 20, 22, 25, 30, 100],
            labels=["≤20", "21-22", "23-25", "26-30", "30+"]
        )

        edad_prom = filtro_grafico.groupby("Rango Edad", observed=True)["promedio"].mean().reset_index()

        fig_pie = px.pie(
            edad_prom, names="Rango Edad", values="promedio",
            title="Promedio por Rango de Edad"
        )

        conteo = filtro_grafico["desempenio"].value_counts().reset_index()
        conteo.columns = ["Desempeño", "Cantidad"]

        fig_barras = px.bar(
            conteo, x="Desempeño", y="Cantidad",
            color="Desempeño",
            title="Distribución de Desempeño"
        )

        kpis = html.Div([
            html.Div([
                html.H6("Promedio"),
                html.H3(f"{promedio}")
            ]),
            html.Div([
                html.H6("Total Estudiantes"),
                html.H3(f"{total}")
            ]),
            html.Div([
                html.H6("Promedio Máximo"),
                html.H3(f"{maximo}")
            ]),
        ], style={"display": "flex", "justifyContent": "space-between"})

        return (
            filtro.to_dict('records'),
            kpis,
            [{"name": col, "id": col} for col in filtro.columns],
            fig_detalle,
            fig_hist,
            fig_disp,
            fig_pie,
            fig_barras,
            aviso
        )

    return appnotas