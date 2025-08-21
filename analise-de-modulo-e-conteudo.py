import altair as alt
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from streamlit_product_card import product_card
from ranking import tabelaModule
from streamlit_extras.stylable_container import stylable_container 

tabelaModule = tabelaModule.rename(columns={"moduleName": "title", "moduleId": "id"})

conn = st.connection("sql")

st.markdown("""
    <style>
        .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

if "Total" not in tabelaModule.title.values:
    tabelaModule.loc[len(tabelaModule)] = ["Total",1000000000,tabelaModule.totalModuleViews.values[1] - 1]
    tabelaModule = tabelaModule.sort_values(by="totalModuleViews", ascending=False)
conn = st.connection("sql")
st.title("Análise de Módulo")
select_module, select_content = st.columns(2)
active_content = st.checkbox("Selecione o conteúdo do módulo", value=False, key="selectContent")
select_date, blank = st.columns(2)
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
                        "Content"."title" AS "contentTitle",
                        "Module"."name" AS "moduleName",
                        "Module"."id" AS "moduleId",
                        "Content"."createdAt" AS "publishedAt",
                        CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END AS "totalViews",
                    CAST("ContentView"."createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS "createdAt"
                    FROM public."ContentView"
                    INNER JOIN public."Content" ON "Content"."id" = "ContentView"."contentId"
                    INNER JOIN public."Module" ON "Module"."id" = "Content"."moduleId"
                    WHERE "contentId" IN ({','.join(map(str, conteudos.id.values))})
                    AND "totalViews" > 0
                    AND "ContentView"."createdAt" BETWEEN '{start_date} 03:00:00' AND '{end_date + timedelta(days=1)} 03:00:00'
                    ''')

if modulo == "Total":
    full_raw_dateViews = conn.query(f'''
                    SELECT 
                    "contentId",
                        "watchUntil",
                        "Content"."title" AS "contentTitle",
                        "Module"."name" AS "moduleName",
                        "Module"."id" AS "moduleId",
                        "Content"."createdAt" AS "publishedAt",
                        CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END AS "totalViews",
                    CAST("ContentView"."createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS "createdAt"
                    FROM public."ContentView"
                    INNER JOIN public."Content" ON "Content"."id" = "ContentView"."contentId"
                    INNER JOIN public."Module" ON "Module"."id" = "Content"."moduleId"
                    WHERE "totalViews" > 0
                    AND "ContentView"."createdAt" BETWEEN '{start_date} 03:00:00' AND '{end_date + timedelta(days=1)} 03:00:00'
                    ''')
    raw_views = full_raw_dateViews.sort_values(by="createdAt", ascending=True)
else:
    raw_views = raw_dateViews.sort_values(by="createdAt", ascending=True)

conteudos_do_modulo = raw_views.groupby(["contentId","contentTitle","moduleName","moduleId","publishedAt"], as_index=False).agg({"totalViews": "sum"})
contentViews = raw_views.groupby(["contentId","createdAt","contentTitle","moduleName"], as_index=False).agg({"totalViews": "sum","watchUntil": "sum"})
contentViews = pd.DataFrame(contentViews)

contentRaking = contentViews.groupby(["contentTitle","moduleName"], as_index=False).agg({"totalViews": "sum"})
contentRaking = pd.DataFrame(contentRaking)
contentRaking = contentRaking.sort_values(by="totalViews", ascending=False)
mais_visto = contentRaking.iloc[0]

conteudos_do_modulo = conteudos_do_modulo.sort_values(by="publishedAt", ascending=False)

if active_content:
    with select_content:
        conteudo_selected = st.selectbox("Selecione o conteúdo", options=conteudos_do_modulo["contentTitle"].tolist(), key="selectedContent")
        content_views = conn.query(f'''
                                    SELECT
                                        "contentId",
                                        "watchUntil",
                                        "Content"."title" AS "contentTitle",
                                        "Module"."name" AS "moduleName",
                                        "Module"."id" AS "moduleId",
                                        CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END AS "totalViews",
                                        CAST("ContentView"."createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS "createdAt"
                                    FROM public."ContentView"
                                    INNER JOIN public."Content" ON "Content"."id" = "ContentView"."contentId"
                                    INNER JOIN public."Module" ON "Module"."id" = "Content"."moduleId"
                                    WHERE "Content"."title" = '{conteudo_selected}'
                                    AND "ContentView"."createdAt" BETWEEN '{start_date} 03:00:00' AND '{end_date + timedelta(days=1)} 03:00:00'
                                    ''')
        tabelaModuleHistory = content_views.groupby(["createdAt"], as_index=False).agg({"totalViews": "sum"})
else:
    with select_content:
        st.write("")
        tabelaModuleHistory = contentViews.groupby(["createdAt"], as_index=False).agg({"totalViews": "sum"})

tabelaModuleHistory = pd.DataFrame(tabelaModuleHistory)

record = tabelaModuleHistory.sort_values(by="totalViews", ascending=False).iloc[0]
engajamento = 0

for index, row in raw_views.iterrows():
    engajamento += row["watchUntil"]
engajamento = engajamento / len(raw_views) if len(raw_views) > 0 else 0
engajamento = int(engajamento * 100)

if not active_content:
    Tabela = tabelaModuleHistory.rename(columns={"totalViews": "Views","createdAt": "Data"})
else:
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
col4 = st.container()

@st.dialog("Conteúdos Mais Vistos")
def ranking_de_conteudo():
    st.markdown(
        """
        <style>
        /* Aumenta a largura do modal */
        [data-testid="stDialog"] > div > div{
            width: 80%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.dataframe(
            contentRaking,
            column_config={
            "contentTitle": "Título do Conteúdo",
            "totalViews": "Views",
            },
            hide_index=True,
            )

@st.dialog(f"Dias com mais Views")
def ranking_de_dias():
    st.markdown(
        """
        <style>
        /* Aumenta a largura do modal */
        [data-testid="stDialog"] > div > div{
            width: 80%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.dataframe(
            tabelaModuleHistory.sort_values(by="totalViews", ascending=False),
            column_config={
            "createdAt": "Data",
            "totalViews": "Views",
            },
            hide_index=True,
            )


with col1:
    product_card(
    product_name="Total de Views",
    description=f"Média: {int(total_views / quantidade_dias if quantidade_dias > 0 else 0)}",
    price=total_views,
    on_button_click=ranking_de_conteudo,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
        "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
        }
)
    
with col2:
    product_card(
    product_name="Dia com mais views",
    description=record["createdAt"].strftime("%d/%m/%Y"),
    price=record["totalViews"],
    on_button_click=ranking_de_dias,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
        "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
        }
)

with col3:
    if not active_content:
        product_card(
        product_name="Conteúdo Mais Visto",
        description=mais_visto["contentTitle"],
        price=mais_visto["totalViews"],
        on_button_click=ranking_de_conteudo,
        styles={
            "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
            "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
            "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
            "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
            }
    )
    else:
        product_card(
    product_name="Engajamento",
    description="",
    price=str(engajamento) + "%",
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
        "text": {"font-size": "16px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
        }
)

with col4:
    if not active_content:
        product_card(
        product_name="Engajamento",
        description="",
        price=str(engajamento) + "%",
        styles={
            "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
            "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%"},
            "text": {"font-size": "16px", "font-weight": "bold", "text-align": "center"},
            "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
            }
    )
