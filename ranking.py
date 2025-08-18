import streamlit as st
import pandas as pd 
from home import tabelaModule 

conn = st.connection("sql")



conteudos = conn.query('''
                       SELECT
                           "Content"."id",
                           "Content"."title",
                           "Module"."name",
                            SUM(CASE WHEN "ContentView"."totalViews" > 10 THEN 10 ELSE "ContentView"."totalViews" END) AS "totalViews"
                       FROM public."Content"
                       LEFT JOIN public."ContentView" ON "Content"."id" = "ContentView"."contentId"
                       INNER JOIN public."Module" ON "Content"."moduleId" = "Module"."id"
                       WHERE "totalViews" > 0
                       GROUP BY "Content"."id", "Module"."name"
                       ORDER BY "totalViews" DESC
                       ''')

st.title("Ranking de Conteúdos")
st.dataframe(conteudos, column_config={
    "id": None,
    "title": "Título do Conteúdo",
    "name": "Nome do Módulo",
    "totalViews": "Total de Views",
},
    hide_index=True,
    )

st.title("Ranking de Módulos")
tabelaModule = tabelaModule.sort_values(by="totalModuleViews", ascending=False)
st.dataframe(tabelaModule, column_config={
    "id": None,
    "title": "Nome do Modulo",
    "totalModuleViews": "Total de Views",

},
    hide_index=True,
)
    
