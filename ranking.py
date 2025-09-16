import streamlit as st
from datetime import date, datetime
import pandas as pd

today = datetime.now()
start_limit = date(2025,5,12)
start_date = start_limit
end_date = today
end_limit = today + pd.DateOffset(days=1)


st.title("Ranking de Conteúdos e Módulos")

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

conn = st.connection("sql")
tabelaModule = conn.query(f"""SELECT
                            "id",
                            "name" as "title" 
                            FROM public."Module"
                           WHERE "createdAt" BETWEEN '{start_date}' AND '{end_date}'
                          ;""")
conteudos = conn.query(f'''
                       SELECT
                           "Content"."id",
                           "Content"."title",
                           "Module"."name" as "moduleName",
                           "Content"."moduleId",
                            SUM(CASE WHEN "ContentView"."totalViews" > 10 THEN 10 ELSE "ContentView"."totalViews" END) AS "totalViews"
                       FROM public."Content"
                       LEFT JOIN public."ContentView" ON "Content"."id" = "ContentView"."contentId"
                       INNER JOIN public."Module" ON "Content"."moduleId" = "Module"."id"
                       WHERE "totalViews" > 0
                        AND "ContentView"."createdAt" BETWEEN '{start_date}' AND '{end_date}'
                       GROUP BY "Content"."id", "Module"."name"
                       ORDER BY "totalViews" DESC
                       ''')

tabelaModule = conteudos.groupby(["moduleName","moduleId"], as_index=False).agg({"totalViews": "sum"})
tabelaModule = tabelaModule.rename(columns={"totalViews": "totalModuleViews"})

st.subheader("Ranking de Conteúdos durante o período")
st.dataframe(conteudos, column_config={
    "id":None,
    "moduleId": None,
    "title": "Título do Conteúdo",
    "moduleName": "Nome do Módulo",
    "totalViews": "Total de Views",
},
    hide_index=True,
    )

st.subheader("Ranking de Módulos durante o período")
tabelaModule = tabelaModule.sort_values(by="totalModuleViews", ascending=False)
st.dataframe(tabelaModule, column_config={
    "moduleId": None,
    "moduleName": "Nome do Modulo",
    "totalModuleViews": "Total de Views",

},
    hide_index=True,
)
    
