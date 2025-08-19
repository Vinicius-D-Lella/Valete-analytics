import altair as alt
import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta
from streamlit_product_card import product_card
import pytz
from streamlit_extras.stylable_container import stylable_container 


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

conn = st.connection("sql")
st.title("Resumo do Dia")


sao_paulo_tz = pytz.timezone('America/Sao_Paulo')

end_date = datetime.today().astimezone(tz=sao_paulo_tz)
start_date = datetime.combine(date.today(), time.min).astimezone(tz=sao_paulo_tz)

first_day = date(2025,5,12)
last_day = date.today()


dates = pd.date_range(start=first_day, end=last_day).date
dates = pd.DataFrame(dates, columns=["createdAt"])
dates = dates.sort_values(by="createdAt", ascending=False)
dates = pd.to_datetime(dates["createdAt"], format="%Y-%m-%d").dt.strftime("%d/%m/%y").tolist()
dates = pd.DataFrame(dates, columns=["createdAt"])
with stylable_container(
    key="date_selector",
    css_styles="""
    div[data-testid="stElementContainer"]{
        background-color: transparent;
        display: flex;
        justify-content: center;
    }
    .stSelectbox {
        width: min-content;
        display: flex;
        flex-direction: column;
    }
    .stSelectbox > div > div{
            background-color: transparent;
            border:0;
            color: white;
            font-size: 30px;
            height: min-content;
            font-weight: 500;
        }
    .stSelectbox > label{
    width: min-content;
    height: min-content;
    min-height:0;
    margin: 0;
    }
    """
):
    data_selecionada = st.selectbox("", options=dates)


data_selecionada = data_selecionada.replace("/", "-")
data_selecionada = datetime.strptime(data_selecionada, "%d-%m-%y")
data_selecionada = data_selecionada.date()
start_date = datetime.combine(data_selecionada, time.min)
end_date = datetime.combine(data_selecionada, time.max)

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
                   AND "ContentView"."createdAt" BETWEEN '{start_date + timedelta(hours=3)}' AND '{end_date + timedelta(hours=3)}'
                   ''')
today_content = conn.query(f'''
                            SELECT 
                                "title",
                                "publishedAt"
                            FROM public."Content"
                            WHERE "publishedAt" BETWEEN '{start_date + timedelta(hours=3)}' AND '{end_date + timedelta(hours=3)}'
                            AND "Content"."status" = 'PUBLISHED'
                           ''')

today_content_list = []

for row in today_content.itertuples():
    today_content_list.append({
        "titulo": row.title,
        "publicado": row.publishedAt - timedelta(hours=3)
    })
today_content_list = pd.DataFrame(today_content_list)
if not today_content_list.empty:
    today_content_list = today_content_list.sort_values(by="publicado", ascending=True)
raw_views = raw_dateViews.sort_values(by="createdAt", ascending=True)
new_views = []
for row in raw_views.itertuples():
    hour = row.createdAt - timedelta(hours=3)
    new_views.append({
        "contentId": row.contentId,
        "contentTitle": row.contentTitle,
        "watchUntil": row.watchUntil,
        "totalViews": row.totalViews,
        "createdAt": hour.replace(minute=0, second=0, microsecond=0)
    })

new_views = pd.DataFrame(new_views)
hourViews = new_views.groupby(["contentTitle","createdAt"], as_index=False).agg({"totalViews": "sum"})
hourViews = pd.DataFrame(hourViews)

rankingViews = hourViews.drop("createdAt", axis=1)

rankingViews = rankingViews.groupby(["contentTitle"], as_index=False).agg({"totalViews": "sum"})


dateViews = new_views.groupby(["createdAt","contentTitle","contentId"], as_index=False).agg({"totalViews": "sum","watchUntil": "sum"})
dateViews = pd.DataFrame(dateViews)

views_without_date = new_views.drop("createdAt", axis=1)
contentViews = views_without_date.groupby(["contentId"], as_index=False).agg({"totalViews": "sum","watchUntil": "sum"})
contentViews = pd.DataFrame(contentViews)


horarios = []
top_views_list = []
for row in dateViews.itertuples():
    if row.createdAt not in horarios:
        horarios.append(row.createdAt)

for row in horarios:
    views_hora = hourViews[hourViews["createdAt"] == row]
    views_hora = views_hora.sort_values(by="totalViews", ascending=False)
    mais_visto_da_data = views_hora.iloc[0]
    top_views_list.append(mais_visto_da_data)

top_views_list = pd.DataFrame(top_views_list)

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


tabelaModuleHistory = dateViews.groupby(["createdAt"], as_index=False).agg({"totalViews": "sum","watchUntil": "sum"})
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
        opacity=0.40,              
        line={"color": "steelblue","opacity": 0.70},    
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


datas_conteudos = []

if today_content_list.empty == False:
    for index, row in today_content_list.iterrows():
        if not row["publicado"].tz_localize(tz=sao_paulo_tz) > datetime.now().astimezone(tz=sao_paulo_tz):
            datas_conteudos.append({
                "data": row["publicado"],
                "titulo": row["titulo"]
        })
df_marcadores = pd.DataFrame(datas_conteudos)

linhas = alt.Chart(df_marcadores).mark_rule(size=2, color="white").encode(
    x="data:T",
    tooltip=[
        alt.Tooltip("data:T", title="Horário", format="%d/%m %H:%M"),
        alt.Tooltip("titulo:N", title="Titulo")
    ]

   )


ok_chart = chart + linhas

st.altair_chart(ok_chart, use_container_width=True)

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
            top_views_list,
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
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
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
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
        }
    )
with col3:
    product_card(
    product_name = "Mais visto do dia",
    description = mais_visto["contentTitle"][0],
    price = int(mais_visto_data["totalViews"]),
    on_button_click=ranking_de_views_mais_visto,
    styles={
        "card":{"height": "150px", "display": "flex", "flex-direction": "column", "justify-content": "space-around", "position": "relative", "align-items": "center"},
        "title": {"width": "80%", "font-size": "16px", "font-weight": "bold", "text-align": "center","position": "absolute", "top": "10%","left": "10%"},
        "text": {"font-size": "10px", "font-weight": "bold", "text-align": "center"},
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
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
        "price": {"font-size": "24px", "font-weight": "bold", "text-align": "center","color":"#85BADF"},
        }
)

