import streamlit as st


if not st.user.is_logged_in:
    st.title("Login")
    st.write("Por favor, faça login para continuar, caso não tenha acesso fale com o administrador.")
    if st.button("Log in com Google"):
        st.login()

pages = {
    "Menu": [
        st.Page("home.py", title="Resumo do Dia"),
        st.Page("analise-de-modulo-e-conteudo.py", title="Análise de Módulo e Conteúdo"),
        st.Page("bar_chart_solo.py", title="Análise de Público"),
        st.Page("ranking.py", title="Ranking"),
        #st.Page("bar_chart.py", title="Comparação entre views de graça ou pagas"),
    ]
}
if st.user.is_logged_in:
    if st.user.email in st.secrets["whitelist"]:
        pg = st.navigation(pages)
        st.sidebar.write(f"Em caso de Bug entre em contato com o suporte.")
        st.sidebar.button("Log out", on_click=st.logout)
        st.set_page_config(layout="wide")
        pg.run()
    else:
        st.write("Você não tem permissão para acessar esta página.")
        if st.button("Log out"):
            st.logout()

