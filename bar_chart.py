import streamlit as st
import pandas as pd
from home import tabelaModule

st.title("Gráfico de Barras")
titulos = [item.title for item in tabelaModule.itertuples()]
options = st.multiselect(
    "Quais módulos você quer ver?",
    titulos,
    default=[],
)

st.checkbox("Tipo de Conteudo", key="tipoConteudo", value=True)
st.checkbox("Tipo de Espectador", key="tipoEspectador")

escolhidos = []

for item in tabelaModule.itertuples():
    if item.title in options:
        escolhidos.append(item)




dadosConteudo = []

dadosViewer = []


for row in escolhidos:
    if row.freeContentView != 0:
        dadosConteudo.append({
            "Módulo":row.title,
            "Views":row.freeContentView,
            "Assinatura":"Gratuita"
        })
    if row.paidContentView != 0:
        dadosConteudo.append({
            "Módulo":row.title,
            "Views":row.paidContentView,
            "Assinatura":"Paga"
        })

for row in escolhidos:
    if row.subFreeContentView != 0:
        dadosViewer.append({
            "Módulo":row.title,
            "Views":row.subFreeContentView,
            "Tipo de Vizualização":"Sub Free View"
        })
    if row.unsubFreeContentView != 0:
        dadosViewer.append({
            "Módulo":row.title,
            "Views":row.unsubFreeContentView,
            "Tipo de Vizualização":"Unsub Free View"
        })
    if row.subPaidContentView != 0:
        dadosViewer.append({
            "Módulo":row.title,
            "Views":row.subPaidContentView,
            "Tipo de Vizualização":"Sub Paid View"
        })



dc = pd.DataFrame(dadosConteudo)
dv = pd.DataFrame(dadosViewer)

if escolhidos != []:
    if st.session_state.tipoConteudo:
        st.subheader("Gráfico de Barras - Conteúdo")
        st.bar_chart(dc, x="Módulo", y="Views", color="Assinatura", stack=False)
    if st.session_state.tipoEspectador:
        st.subheader("Gráfico de Barras - Espectador")
        st.bar_chart(dv, x="Módulo", y="Views", color="Tipo de Vizualização", stack=False, use_container_width=True)