import streamlit as st

if not st.user.is_logged_in:
    if st.button("Log in"):
        st.login()
else:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Log out"):
            st.logout()
    with col2:
        st.write("")

pages = {
    "Pages": [
        st.Page("home.py", title="Resumo do Dia"),
        st.Page("module_views.py", title="Análise de Módulo"),
        st.Page("bar_chart_solo.py", title="Análise de Público"),
        st.Page("ranking.py", title="Ranking"),
        #st.Page("bar_chart.py", title="Comparação entre views de graça ou pagas"),
    ]
}

if st.user.is_logged_in:
    if st.user.email in st.secrets["whitelist"]:
        pg = st.navigation(pages)
        pg.run()
    else:
        st.write("Você não tem permissão para acessar esta página.")

