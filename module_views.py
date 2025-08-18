import altair as alt
import streamlit as st
import pandas as pd
from home import tabelaModule
from datetime import date, datetime
from streamlit_product_card import product_card

st.markdown("""
    <style>
        /* Centraliza todo o conteúdo */
        .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

if "Total" not in tabelaModule.title.values:
    tabelaModule.loc[len(tabelaModule)] = [1000000000,"Total",1]
conn = st.connection("sql")
st.title("Análise de Módulo")
select_module, select_date = st.columns(2)
with select_module:
    modulo = st.selectbox("Selecione o módulo", options=tabelaModule.title.values, key="selectModule", index=1)
linha = tabelaModule[tabelaModule["title"] == modulo].iloc[0]

if modulo != "Total":
    conteudos = conn.query(f'SELECT "id" FROM public."Content" WHERE "moduleId" = {linha.id};')
else:
    conteudos = conn.query(f'SELECT "id" FROM public."Content" WHERE "moduleId" = 14;')

initialDate = conn.query(f'''
                   SELECT 
                   CAST("createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS "createdAt"
                   FROM public."ContentView"
                   WHERE "contentId" IN ({','.join(map(str, conteudos.id.values))})''')

today = datetime.now()

if initialDate.createdAt[0] < date(2025,5,12):
    start_limit = date(2025,5,12)
else:
    start_limit = initialDate.createdAt[0]
start_date = start_limit
end_date = today
end_limit = today

with select_date:
    d = st.date_input(
    "Selecione o período",
    (start_date, end_date),
    start_limit,
    end_limit,
    format="DD/MM/YYYY",
    )


if len(d) == 2:
    start_date = d[0]
    end_date = d[1]



raw_dateViews = conn.query(f'''
                   SELECT 
                   "contentId",
                    "watchUntil",
                    CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END AS "totalViews",
                   CAST("createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS "createdAt"
                   FROM public."ContentView"
                   WHERE "contentId" IN ({','.join(map(str, conteudos.id.values))})
                   AND "totalViews" > 0
                   AND "createdAt" BETWEEN '{start_date}' AND '{end_date}'
                   ''')

if modulo == "Total":
    full_raw_dateViews = conn.query(f'''
                   SELECT 
                   "contentId",
                    "watchUntil",
                    CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END AS "totalViews",
                   CAST("createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS "createdAt"
                   FROM public."ContentView"
                   WHERE "totalViews" > 0
                   AND "createdAt" BETWEEN '{start_date}' AND '{end_date}'
                   ''')
    raw_views = full_raw_dateViews.sort_values(by="createdAt", ascending=True)
else:
    raw_views = raw_dateViews.sort_values(by="createdAt", ascending=True)

contentViews = raw_views.groupby(["contentId", "createdAt"]).sum().reset_index()
contentViews = pd.DataFrame(contentViews)

tabelaModuleHistory = contentViews.groupby("createdAt").sum().reset_index()
tabelaModuleHistory = pd.DataFrame(tabelaModuleHistory)

record = tabelaModuleHistory.sort_values(by="totalViews", ascending=False).iloc[0]
engajamento = 0

for index, row in raw_views.iterrows():
    engajamento += row["watchUntil"]
engajamento = engajamento / len(raw_views) if len(raw_views) > 0 else 0
engajamento = int(engajamento * 100)

Tabela = tabelaModuleHistory.rename(columns={"totalViews": "Views","createdAt": "Data"})

chart = (
    alt.Chart(Tabela)
    .mark_area(
        color="steelblue",         
        opacity=0.5,              
        line={"color": "steelblue"},    
        point={"size": 0}     
    )
    .encode(
        x=alt.X("Data:T", title="Data", axis=alt.Axis(format="%d/%m/%y")),
        y=alt.Y("Views:Q", title="Visualizações"),
        tooltip=[alt.Tooltip("Data:T", format="%d/%m/%y"), "Views"]
    )
    .properties(
        width=700,
        height=350
    )
)

st.altair_chart(chart, use_container_width=True)

total_views = Tabela["Views"].sum()
quantidade_dias = Tabela["Data"].nunique()

st.subheader(f"Dados {'' if modulo == 'Total' else 'do Módulo '} durante o período")

col1,col2,col3= st.columns(3)

with col1:
    product_card(
    product_name="Total de Views",
    description=f"Média: {int(total_views / quantidade_dias if quantidade_dias > 0 else 0)}",
    price=total_views,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
        "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
)
    
with col2:
    product_card(
    product_name="Dia com mais views",
    description=record["createdAt"].strftime("%d/%m/%Y"),
    price=record["totalViews"],
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
        "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
)
    
with col3:
    product_card(
    product_name="Engajamento",
    description="",
    price=str(engajamento) + "%",
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
        "text": {"font-size": "16px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
)
    
