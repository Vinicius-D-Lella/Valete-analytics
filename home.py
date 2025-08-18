import altair as alt
import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
from streamlit_product_card import product_card
import pytz


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

conn = st.connection("sql")
st.title("Resumo do Dia")
st.subheader(date.today().strftime("%d/%m"))
views = conn.query('''
                   SELECT 
                   "contentId",
                   "Content"."title" AS "contentTitle",
                   "Content"."moduleId" AS "moduleId",
                   "Module"."name" AS "moduleName",
                   SUM(CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END) AS "totalViews"
                   FROM public."ContentView"
                   INNER JOIN public."Content" ON "Content"."id" = "ContentView"."contentId"
                   INNER JOIN public."Module" ON "Module"."id" = "Content"."moduleId"
                   WHERE "totalViews" != 0
                   GROUP BY "contentId","moduleId","contentTitle","moduleName"
                   ;''')

tabelaModule = []

views = pd.DataFrame(views)
views = views.sort_values(by="totalViews", ascending=False)


for row in views.itertuples():
    if row.moduleId not in [item["id"] for item in tabelaModule]:
        tabelaModule.append({
            "id": row.moduleId,
            "title": row.moduleName,
            "totalModuleViews": row.totalViews
        })
    else:
        for item in tabelaModule:
            if item["id"] == row.moduleId:
                item["totalModuleViews"] += row.totalViews

tabelaModule = pd.DataFrame(tabelaModule)
tabelaModule = tabelaModule.sort_values(by="totalModuleViews", ascending=False)
sao_paulo_tz = pytz.timezone('America/Sao_Paulo')

end_date = datetime.today().astimezone(tz=sao_paulo_tz)
start_date = datetime.combine(date.today(), time.min).astimezone(tz=sao_paulo_tz)

raw_dateViews = conn.query(f'''
                   SELECT 
                   "contentId",
                    "Content"."title" AS "contentTitle",
                    "watchUntil",
                    "totalViews",
                    "ContentView"."createdAt"
                   FROM public."ContentView"
                   INNER JOIN public."Content" ON "Content"."id" = "ContentView"."contentId"
                   WHERE "totalViews" > 0
                   AND "ContentView"."createdAt" BETWEEN '{start_date}' AND '{end_date}'
                   ''')

raw_views = raw_dateViews.sort_values(by="createdAt", ascending=True)
views = []
for row in raw_views.itertuples():
    views.append({
        "contentId": row.contentId,
        "contentTitle": row.contentTitle,
        "watchUntil": row.watchUntil,
        "totalViews": row.totalViews,
        "createdAt": row.createdAt.replace(minute=0, second=0, microsecond=0)
    })

views = pd.DataFrame(views)
hourViews = views.groupby(["contentTitle","createdAt"], as_index=False).agg({"totalViews": "sum"})
hourViews = pd.DataFrame(hourViews)


rankingViews = hourViews.drop("createdAt", axis=1)

rankingViews = rankingViews.groupby(["contentTitle"], as_index=False).agg({"totalViews": "sum"})


dateViews = views.groupby(["createdAt"]).sum().reset_index()
dateViews = pd.DataFrame(dateViews)

views_without_date = views.drop("createdAt", axis=1)
contentViews = views_without_date.groupby(["contentId"]).sum().reset_index()
contentViews = pd.DataFrame(contentViews)

mais_visto_data = contentViews.sort_values(by="totalViews", ascending=False).iloc[0]

mais_visto = conn.query(f'''
                   SELECT 
                   "contentId",
                   "Content"."title" AS "contentTitle",
                   "Content"."moduleId" AS "moduleId",
                   "Module"."name" AS "moduleName",
                   SUM(CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END) AS "totalViews"
                   FROM public."ContentView"
                   INNER JOIN public."Content" ON "Content"."id" = "ContentView"."contentId"
                   INNER JOIN public."Module" ON "Module"."id" = "Content"."moduleId"
                   WHERE "totalViews" != 0
                   AND "contentId" = {mais_visto_data["contentId"]}
                   GROUP BY "contentId","moduleId","contentTitle","moduleName"
                   ;''')


tabelaModuleHistory = dateViews.groupby("createdAt").sum().reset_index()
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
        x=alt.X("Data:T", title="Data", axis=alt.Axis(format="%H:%M")),
        y=alt.Y("Views:Q", title="Visualizações"),
        tooltip=[alt.Tooltip("Data:T", format="%H:%M"), "Views"]
    )
    .properties(
        width=700,
        height=350
    )
)


st.altair_chart(chart, use_container_width=True)

total_views = Tabela["Views"].sum()
quantidade_horas = Tabela["Data"].nunique()

st.subheader("Dados do Módulo de hoje")

col1,col2,col3= st.columns(3)
col4 = st.container()
@st.dialog(f"Mais vistos do dia")
def ranking_de_views_dia():
    st.dataframe(
            rankingViews.sort_values(by="totalViews", ascending=False),
            column_config={
            "contentTitle": "Título do Conteúdo",
            "createdAt": None,
            "totalViews": "Views",
            },
            hide_index=True,
            )

@st.dialog(f"Views as {record["createdAt"].strftime("%H")} horas")
def ranking_de_views_pico():
    st.dataframe(
            hourViews[hourViews["createdAt"] == record["createdAt"]].sort_values(by="totalViews", ascending=False),
            column_config={
            "contentTitle": "Título do Conteúdo",
            "createdAt": None,
            "totalViews": f"Views as {record['createdAt'].strftime('%H')} horas",
            },
            hide_index=True,
            )
    
@st.dialog(f"Horarios mais vistos")
def ranking_de_views_mais_visto():
    st.dataframe(
            hourViews[hourViews["contentTitle"] == mais_visto["contentTitle"][0]].sort_values(by="totalViews", ascending=False),
            column_config={
            "contentTitle": "Título do Conteúdo",
            "createdAt": "Horário",
            "totalViews": "Views",
            },
            hide_index=True,
            )
    


with col1:
    product_card(
    product_name="Total de Views",
    description=f"Média por hora: {int(total_views / quantidade_horas) if quantidade_horas > 0 else 0}",
    price=total_views,
    on_button_click=ranking_de_views_dia,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%","left": "10%"},
        "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
)
    
with col2:
    product_card(
    product_name="Pico de Views",
    description=record["createdAt"].strftime("%H") + "h",
    price=record["totalViews"],
    on_button_click=ranking_de_views_pico,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%","left": "10%"},
        "text": {"font-size": "12px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
    )
with col3:
    product_card(
    product_name = "Mais visto",
    description = mais_visto["contentTitle"][0],
    price = int(mais_visto_data["totalViews"]),
    on_button_click=ranking_de_views_mais_visto,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%","left": "10%"},
        "text": {"font-size": "10px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
)
    
with col4:
    product_card(
    product_name="Engajamento diário",
    description="",
    price=str(engajamento) + "%",
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%","left": "10%"},
        "text": {"font-size": "16px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center"},
        }
)
