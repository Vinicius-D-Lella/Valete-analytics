
import streamlit as st
from home import tabelaModule

conn = st.connection("sql")

st.title("Gráfico de Área Múltipla")
titulos = [item.title for item in tabelaModule.itertuples()]
options = st.multiselect(
    "Quais módulos você quer ver?",
    titulos,
    default=[],
)

modulo = st.selectbox("Selecione o módulo", options=tabelaModule.title.values, key="selectModule", index=1)
linha = tabelaModule[tabelaModule["title"] == modulo].iloc[0]

conteudosIds = []

for item in options:
    st.write(item)
    conteudosIds.append(conn.query(f'''
                                SELECT
                                    "Content"."id"
                                    FROM public."Content"
                                    INNER JOIN public."Module" ON "Content"."moduleId" = "Module"."id"
                                    WHERE "Module"."id" = {tabelaModule[tabelaModule["title"] == item].iloc[0].id};
                                '''))
    
st.write(conteudosIds)
