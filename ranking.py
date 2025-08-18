import streamlit as st

conn = st.connection("sql")
tabelaModule = conn.query("""SELECT
                            "id",
                            "name" as "title" 
                            FROM public."Module"
                          ;""")
conteudos = conn.query('''
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
                       GROUP BY "Content"."id", "Module"."name"
                       ORDER BY "totalViews" DESC
                       ''')

tabelaModule = conteudos.groupby(["moduleName","moduleId"], as_index=False).agg({"totalViews": "sum"})
tabelaModule = tabelaModule.rename(columns={"totalViews": "totalModuleViews"})

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
    
