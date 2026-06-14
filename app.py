"""
Painel de Recursos Humanos - Desempenho de Colaboradores
Faculdade Nova Roma | Análise e Visualização de Dados

Modelo dimensional: fato_desempenho_funcionario + dim_funcionario,
dim_tempo, dim_cargo_area, dim_localidade, dim_genero
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------
# 1. ETL
# ------------------------------------------------------------------
RAW_PATH = "BaseFuncionarios.xlsx"

df = pd.read_excel(RAW_PATH, header=2)

df = df.rename(columns={
    "ID RH": "id_funcionario",
    "Nome Completo": "nome_completo",
    "Genero": "genero",
    "Data de Nascimento": "data_nascimento",
    "Endereço Sede": "endereco_sede",
    "Data de Contratacao": "data_contratacao",
    "Salario": "salario_base",
    "VR": "valor_vr",
    "VT": "valor_vt",
    "Cargo - Area": "cargo_area",
    "Avaliação do Funcionário": "nota_avaliacao",
    "RG": "rg",
})

df[["nome_cargo", "nome_area"]] = df["cargo_area"].str.split(" - ", expand=True)
df["cidade"] = df["endereco_sede"].str.extract(r", ([^,]+) - [A-Z]{2},")
df["estado"] = df["endereco_sede"].str.extract(r"- ([A-Z]{2}), \d{5}")
df["ano_contratacao"] = df["data_contratacao"].dt.year
df["mes_ano_contratacao"] = df["data_contratacao"].dt.to_period("M").dt.to_timestamp()
df["genero_desc"] = df["genero"].map({"M": "Masculino", "F": "Feminino"})
df["remuneracao_total"] = df["salario_base"] + df["valor_vr"] + df["valor_vt"]

# ------------------------------------------------------------------
# 2. App / Tema
# ------------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.icons.BOOTSTRAP])
app.title = "RH | Desempenho de Colaboradores"

CARGOS = sorted(df["nome_cargo"].unique())
AREAS = sorted(df["nome_area"].unique())
GENEROS = sorted(df["genero_desc"].unique())
ESTADOS = sorted(df["estado"].unique())
ANOS = sorted(df["ano_contratacao"].unique())

# Paleta - sóbria / corporativa (estilo Power BI)
INK = "#252423"
SLATE = "#3B3A39"
CANVAS = "#F3F2F1"
PANEL = "#FFFFFF"
BORDER = "#E1DFDD"
ACCENT = "#118DFF"
ACCENT_2 = "#5F6B6D"
MUTED = "#605E5C"

CAT_SEQ = ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7", "#744EC2"]
SEQ_SCALE = ["#E6F2FF", "#A9D4FF", "#5FB0FF", "#118DFF", "#0A5BA8", "#073B6E"]

FONT_FAMILY = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family=FONT_FAMILY, size=12, color=INK),
    colorway=CAT_SEQ,
    margin=dict(l=8, r=8, t=8, b=8),
    hoverlabel=dict(font_family=FONT_FAMILY, font_size=12),
    legend=dict(font=dict(size=11)),
)

PANEL_STYLE = {
    "backgroundColor": PANEL,
    "border": f"1px solid {BORDER}",
    "borderRadius": "2px",
    "padding": "12px 14px",
    "height": "100%",
}

LABEL_STYLE = {"fontSize": "11px", "fontWeight": "600", "color": MUTED,
                "textTransform": "uppercase", "letterSpacing": "0.04em", "marginBottom": "4px"}

PANEL_TITLE_STYLE = {"fontSize": "12px", "fontWeight": "600", "color": SLATE,
                      "textTransform": "uppercase", "letterSpacing": "0.04em",
                      "marginBottom": "8px", "borderBottom": f"2px solid {ACCENT}",
                      "paddingBottom": "6px", "display": "inline-block"}

DROPDOWN_STYLE = {"fontSize": "12px"}


# ------------------------------------------------------------------
# 3. Layout
# ------------------------------------------------------------------
def panel(title, controls, graph_id, height):
    header_children = [html.Div(title, style=PANEL_TITLE_STYLE)]
    if controls is not None:
        header_children.append(html.Div(controls, style={"float": "right", "marginTop": "2px"}))
    return html.Div([
        html.Div(header_children, style={"overflow": "hidden", "marginBottom": "4px",
                                          "display": "flex", "justifyContent": "space-between",
                                          "alignItems": "flex-start"}),
        dcc.Graph(id=graph_id, config={"displayModeBar": False}, style={"height": f"{height}px"}),
    ], style=PANEL_STYLE)


def kpi(id_value, label):
    return html.Div([
        html.Div(label, style=LABEL_STYLE),
        html.Div(id="kpi-" + id_value, style={"fontSize": "24px", "fontWeight": "600", "color": INK,
                                                "lineHeight": "1.1"}),
    ], style={**PANEL_STYLE, "borderTop": f"3px solid {ACCENT}", "padding": "10px 14px"})


header_bar = html.Div([
    html.Div([
        html.Span("RH", style={"fontSize": "13px", "fontWeight": "700", "color": "#FFFFFF",
                                "backgroundColor": ACCENT, "padding": "3px 8px", "borderRadius": "2px",
                                "marginRight": "10px"}),
        html.Span("Desempenho de Colaboradores", style={"fontSize": "16px", "fontWeight": "600", "color": "#FFFFFF"}),
    ]),
    html.Div("fato_desempenho_funcionario", style={"fontSize": "11px", "color": "#C8C6C4",
                                                     "fontFamily": "monospace"}),
], style={"backgroundColor": INK, "padding": "10px 20px", "display": "flex",
          "justifyContent": "space-between", "alignItems": "center"})

filters_bar = html.Div([
    html.Div([
        html.Div("Área", style=LABEL_STYLE),
        dcc.Dropdown(id="f-area", options=AREAS, multi=True, placeholder="Todas",
                      style=DROPDOWN_STYLE, className="rh-dd"),
    ], style={"flex": "1", "minWidth": "150px"}),
    html.Div([
        html.Div("Cargo", style=LABEL_STYLE),
        dcc.Dropdown(id="f-cargo", options=CARGOS, multi=True, placeholder="Todos",
                      style=DROPDOWN_STYLE, className="rh-dd"),
    ], style={"flex": "1", "minWidth": "150px"}),
    html.Div([
        html.Div("Gênero", style=LABEL_STYLE),
        dcc.Dropdown(id="f-genero", options=GENEROS, multi=True, placeholder="Todos",
                      style=DROPDOWN_STYLE, className="rh-dd"),
    ], style={"flex": "1", "minWidth": "130px"}),
    html.Div([
        html.Div("UF Sede", style=LABEL_STYLE),
        dcc.Dropdown(id="f-estado", options=ESTADOS, multi=True, placeholder="Todas",
                      style=DROPDOWN_STYLE, className="rh-dd"),
    ], style={"flex": "1", "minWidth": "130px"}),
    html.Div([
        html.Div("Ano de contratação", style=LABEL_STYLE),
        dcc.RangeSlider(
            id="f-ano", min=min(ANOS), max=max(ANOS), step=1,
            value=[min(ANOS), max(ANOS)],
            marks={int(a): str(a) for a in ANOS[::2]},
            tooltip={"placement": "bottom", "always_visible": False},
        ),
    ], style={"flex": "2", "minWidth": "260px", "paddingTop": "2px"}),
], style={**PANEL_STYLE, "display": "flex", "gap": "20px", "alignItems": "flex-start",
          "marginBottom": "10px", "padding": "10px 16px"})

kpi_row = html.Div([
    kpi("total", "Colaboradores"),
    kpi("salario", "Salário médio"),
    kpi("avaliacao", "Avaliação média"),
    kpi("vr", "VR médio"),
    kpi("vt", "VT médio"),
    kpi("massa", "Folha salarial"),
], style={"display": "grid", "gridTemplateColumns": "repeat(6, 1fr)", "gap": "10px", "marginBottom": "10px"})


radio_dim = dcc.RadioItems(
    id="radio-dim",
    options=[{"label": "Área", "value": "nome_area"}, {"label": "Cargo", "value": "nome_cargo"}],
    value="nome_area", inline=True, className="rh-radio",
    labelStyle={"marginRight": "10px", "fontSize": "11px", "fontWeight": "600", "color": MUTED},
)

radio_geo = dcc.RadioItems(
    id="radio-geo",
    options=[{"label": "Colaboradores", "value": "qtd"}, {"label": "Massa salarial", "value": "salario"}],
    value="qtd", inline=True, className="rh-radio",
    labelStyle={"marginRight": "10px", "fontSize": "11px", "fontWeight": "600", "color": MUTED},
)

app.layout = html.Div([
    header_bar,
    html.Div([
        filters_bar,
        kpi_row,

        html.Div([
            panel("Contratações por período", None, "g-linha-contratacoes", 230),
        ], style={"marginBottom": "10px"}),

        html.Div([
            html.Div(panel("Avaliação média", radio_dim, "g-barras-desempenho", 320),
                     style={"flex": "1"}),
            html.Div(panel("Composição por gênero", None, "g-colunas-genero", 320),
                     style={"flex": "1"}),
        ], style={"display": "flex", "gap": "10px", "marginBottom": "10px"}),

        html.Div([
            panel("Distribuição por UF de sede", radio_geo, "g-geo", 270),
        ], style={"marginBottom": "10px"}),

        html.Div([
            panel("Salário base x avaliação de desempenho", None, "g-scatter", 400),
        ], style={"marginBottom": "10px"}),

        html.Div([
            html.Div("Detalhe — top 15 por avaliação", style=PANEL_TITLE_STYLE),
            html.Div(id="g-tabela"),
        ], style={**PANEL_STYLE, "marginBottom": "16px"}),

        html.Div("Análise e Visualização de Dados — Faculdade Nova Roma — Prof. Davi Maia",
                 style={"fontSize": "11px", "color": MUTED, "textAlign": "center", "padding": "8px 0 16px"}),
    ], style={"padding": "12px 20px"}),
], style={"backgroundColor": CANVAS, "minHeight": "100vh", "fontFamily": FONT_FAMILY})


# ------------------------------------------------------------------
# 4. Filtro central
# ------------------------------------------------------------------
def filter_df(area, cargo, genero, estado, ano_range):
    dff = df.copy()
    if area:
        dff = dff[dff["nome_area"].isin(area)]
    if cargo:
        dff = dff[dff["nome_cargo"].isin(cargo)]
    if genero:
        dff = dff[dff["genero_desc"].isin(genero)]
    if estado:
        dff = dff[dff["estado"].isin(estado)]
    dff = dff[(dff["ano_contratacao"] >= ano_range[0]) & (dff["ano_contratacao"] <= ano_range[1])]
    return dff


def apply_layout(fig, **kwargs):
    layout = {**PLOTLY_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig


# ------------------------------------------------------------------
# 5. Callback
# ------------------------------------------------------------------
@app.callback(
    Output("kpi-total", "children"),
    Output("kpi-salario", "children"),
    Output("kpi-avaliacao", "children"),
    Output("kpi-vr", "children"),
    Output("kpi-vt", "children"),
    Output("kpi-massa", "children"),
    Output("g-linha-contratacoes", "figure"),
    Output("g-barras-desempenho", "figure"),
    Output("g-colunas-genero", "figure"),
    Output("g-geo", "figure"),
    Output("g-scatter", "figure"),
    Output("g-tabela", "children"),
    Input("f-area", "value"),
    Input("f-cargo", "value"),
    Input("f-genero", "value"),
    Input("f-estado", "value"),
    Input("f-ano", "value"),
    Input("radio-dim", "value"),
    Input("radio-geo", "value"),
)
def update_dashboard(area, cargo, genero, estado, ano_range, dim_choice, geo_choice):
    dff = filter_df(area, cargo, genero, estado, ano_range)

    if dff.empty:
        kpis = ["—", "—", "—", "—", "—", "—"]
        empty_fig = apply_layout(go.Figure().add_annotation(
            text="Sem dados para os filtros selecionados", showarrow=False,
            font=dict(size=13, color=MUTED)))
        return (*kpis, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("Sem dados.", style={"fontSize": "12px", "color": MUTED, "padding": "8px"}))

    kpi_total = f"{len(dff):,}".replace(",", ".")
    kpi_salario = f"R$ {dff['salario_base'].mean():,.0f}".replace(",", ".")
    kpi_avaliacao = f"{dff['nota_avaliacao'].mean():.2f}"
    kpi_vr = f"R$ {dff['valor_vr'].mean():,.0f}".replace(",", ".")
    kpi_vt = f"R$ {dff['valor_vt'].mean():,.0f}".replace(",", ".")
    kpi_massa = f"R$ {dff['salario_base'].sum():,.0f}".replace(",", ".")

    # 1. Contratações por período
    contratacoes = (
        dff.groupby("mes_ano_contratacao").size().reset_index(name="contratacoes")
        .sort_values("mes_ano_contratacao")
    )
    fig_linha = px.area(contratacoes, x="mes_ano_contratacao", y="contratacoes",
                         color_discrete_sequence=[ACCENT])
    fig_linha.update_traces(line_shape="spline", fillcolor="rgba(17,141,255,0.12)", line_width=2)
    apply_layout(fig_linha, xaxis_title=None, yaxis_title="Contratações",
                  xaxis=dict(showgrid=False), yaxis=dict(gridcolor=BORDER))

    # 2. Avaliação média por dimensão
    desempenho = (
        dff.groupby(dim_choice)["nota_avaliacao"].mean().reset_index()
        .sort_values("nota_avaliacao", ascending=True)
    )
    label = "Área" if dim_choice == "nome_area" else "Cargo"
    fig_barras = px.bar(
        desempenho, x="nota_avaliacao", y=dim_choice, orientation="h",
        text=desempenho["nota_avaliacao"].round(2),
        color="nota_avaliacao", color_continuous_scale=SEQ_SCALE,
        labels={dim_choice: label, "nota_avaliacao": "Avaliação média"},
    )
    media_geral = dff["nota_avaliacao"].mean()
    fig_barras.add_vline(x=media_geral, line_dash="dash", line_color=ACCENT_2,
                          annotation_text=f"Média {media_geral:.2f}", annotation_position="top",
                          annotation_font_size=10, annotation_font_color=ACCENT_2)
    fig_barras.update_traces(textposition="outside", textfont_size=11)
    apply_layout(fig_barras, coloraxis_showscale=False, xaxis_range=[0, 10.6],
                  xaxis_title=None, yaxis_title=None, margin=dict(l=8, r=8, t=24, b=8),
                  xaxis=dict(gridcolor=BORDER), yaxis=dict(showgrid=False))

    # 3. Composição de gênero por área
    genero_area = dff.groupby(["nome_area", "genero_desc"]).size().reset_index(name="quantidade")
    fig_colunas = px.bar(
        genero_area, x="nome_area", y="quantidade", color="genero_desc",
        barmode="stack",
        color_discrete_map={"Feminino": "#E044A7", "Masculino": "#118DFF"},
        labels={"quantidade": "Colaboradores", "genero_desc": "Gênero"},
    )
    apply_layout(fig_colunas, xaxis_title=None, legend_title_text=None,
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
                  xaxis=dict(showgrid=False), yaxis=dict(gridcolor=BORDER))

    # 4. Distribuição geográfica
    if geo_choice == "qtd":
        geo_data = dff.groupby("estado").size().reset_index(name="valor")
        title_y = "Colaboradores"
    else:
        geo_data = dff.groupby("estado")["salario_base"].sum().reset_index(name="valor")
        title_y = "Massa salarial (R$)"
    geo_data = geo_data.sort_values("valor", ascending=False)
    fig_geo = px.bar(
        geo_data, x="estado", y="valor", color="valor", color_continuous_scale=SEQ_SCALE,
        text=geo_data["valor"].apply(lambda v: f"{v:,.0f}".replace(",", ".")),
        labels={"valor": title_y},
    )
    fig_geo.update_traces(textposition="outside", textfont_size=11)
    apply_layout(fig_geo, coloraxis_showscale=False, xaxis_title=None, yaxis_title=None,
                  xaxis=dict(showgrid=False), yaxis=dict(gridcolor=BORDER))

    # 5. Salário x avaliação
    fig_scatter = px.scatter(
        dff, x="salario_base", y="nota_avaliacao",
        color="nome_area", size="remuneracao_total",
        hover_name="nome_completo",
        hover_data={"nome_cargo": True, "estado": True, "salario_base": ":,.0f", "nota_avaliacao": True,
                     "nome_area": False, "remuneracao_total": False},
        labels={"salario_base": "Salário base (R$)", "nota_avaliacao": "Avaliação", "nome_area": "Área"},
        opacity=0.75,
    )
    med_sal = dff["salario_base"].median()
    med_aval = dff["nota_avaliacao"].median()
    fig_scatter.add_vline(x=med_sal, line_dash="dot", line_color=ACCENT_2, line_width=1)
    fig_scatter.add_hline(y=med_aval, line_dash="dot", line_color=ACCENT_2, line_width=1)
    apply_layout(fig_scatter, legend_title_text=None,
                  xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER))

    # Tabela
    tabela_df = dff[["id_funcionario", "nome_completo", "nome_cargo", "nome_area", "genero_desc",
                      "estado", "data_contratacao", "salario_base", "valor_vr", "valor_vt", "nota_avaliacao"]].copy()
    tabela_df["data_contratacao"] = tabela_df["data_contratacao"].dt.strftime("%d/%m/%Y")
    tabela_df = tabela_df.rename(columns={
        "id_funcionario": "ID", "nome_completo": "Colaborador", "nome_cargo": "Cargo",
        "nome_area": "Área", "genero_desc": "Gênero", "estado": "UF",
        "data_contratacao": "Contratação", "salario_base": "Salário",
        "valor_vr": "VR", "valor_vt": "VT", "nota_avaliacao": "Avaliação",
    }).sort_values("Avaliação", ascending=False)

    table = dbc.Table.from_dataframe(
        tabela_df.head(15), striped=False, bordered=False, hover=True, size="sm", responsive=True,
        className="rh-table",
    )

    return (kpi_total, kpi_salario, kpi_avaliacao, kpi_vr, kpi_vt, kpi_massa,
            fig_linha, fig_barras, fig_colunas, fig_geo, fig_scatter, table)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
