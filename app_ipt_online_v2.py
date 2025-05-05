import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import base64
import json
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema IPT - Avaliação de Treino",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# Inicialização do estado da sessão
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Função para gerenciar usuários
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

# Função para calcular o IPT
def calcular_ipt(sono, stress, dor, energia, refeicao):
    return round((sono * 0.3 + (10 - stress) * 0.25 + (10 - dor) * 0.2 + 
                 energia * 0.15 + refeicao * 0.1), 2)

def interpretar_ipt(ipt):
    if ipt >= 8:
        return "Ótimo para treinar! Pode realizar treino de alta intensidade."
    elif ipt >= 6.5:
        return "Bom para treinar. Realizar treino moderado."
    elif ipt >= 5:
        return "Regular. Considere um treino leve."
    else:
        return "Não recomendado treinar hoje. Considere descanso."

# Função para carregar dados
@st.cache_data
def carregar_dados():
    if os.path.exists('dados_ipt.csv'):
        return pd.read_csv('dados_ipt.csv')
    return pd.DataFrame(
        columns=["Data", "Usuario", "Nome", "Email", "Sono", "Stress", "Dor", 
                "Energia", "Refeicao", "IPT", "Recomendacao"]
    )

# Função para salvar dados
def salvar_dados(df):
    df.to_csv('dados_ipt.csv', index=False)

# Função para filtrar dados por período
def filtrar_por_periodo(df, usuario, dias):
    df['Data'] = pd.to_datetime(df['Data'])
    data_limite = datetime.now() - timedelta(days=dias)
    return df[(df['Usuario'] == usuario) & (df['Data'] >= data_limite)]

# Interface de Login/Registro
def login_interface():
    st.title("🏋️‍♂️ Sistema de Avaliação de Prontidão para Treino")

    tab1, tab2 = st.tabs(["Login", "Registro"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                users = load_users()
                if username in users and users[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")

    with tab2:
        with st.form("registro_form"):
            new_username = st.text_input("Novo Usuário")
            new_password = st.text_input("Nova Senha", type="password")
            nome = st.text_input("Nome Completo")
            email = st.text_input("Email")
            submitted = st.form_submit_button("Registrar")

            if submitted:
                users = load_users()
                if new_username in users:
                    st.error("Usuário já existe!")
                else:
                    users[new_username] = {
                        "password": new_password,
                        "nome": nome,
                        "email": email
                    }
                    save_users(users)
                    st.success("Registro realizado com sucesso!")

# Interface Principal
def main_interface():
    users = load_users()
    user_data = users[st.session_state.current_user]

    st.sidebar.title(f"Bem-vindo, {user_data['nome']}")
    menu = st.sidebar.selectbox(
        "Menu",
        ["Nova Avaliação", "Meu Histórico", "Área do Personal"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

    if menu == "Nova Avaliação":
        nova_avaliacao(user_data)
    elif menu == "Meu Histórico":
        ver_historico(st.session_state.current_user)
    elif menu == "Área do Personal":
        area_personal()

def nova_avaliacao(user_data):
    st.subheader("Nova Avaliação")

    with st.form("formulario_ipt"):
        col1, col2 = st.columns(2)

        with col1:
            sono = st.slider("Quantas horas você dormiu?", 0, 10, 7)
            stress = st.slider("Nível de stress (1 = baixo, 10 = alto)", 1, 10, 5)
            dor = st.slider("Dor muscular (1 = sem dor, 10 = muita dor)", 1, 10, 3)

        with col2:
            energia = st.slider("Nível de energia (1 = baixo, 10 = alto)", 1, 10, 7)
            refeicao = st.slider("Qualidade da última refeição (1 = ruim, 10 = ótima)", 1, 10, 7)

        submitted = st.form_submit_button("Calcular IPT")

        if submitted:
            ipt = calcular_ipt(sono, stress, dor, energia, refeicao)
            recomendacao = interpretar_ipt(ipt)

            df = carregar_dados()
            novo_registro = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Usuario": st.session_state.current_user,
                "Nome": user_data['nome'],
                "Email": user_data['email'],
                "Sono": sono,
                "Stress": stress,
                "Dor": dor,
                "Energia": energia,
                "Refeicao": refeicao,
                "IPT": ipt,
                "Recomendacao": recomendacao
            }])

            df = pd.concat([df, novo_registro], ignore_index=True)
            salvar_dados(df)

            if ipt >= 8:
                st.success(f"Seu IPT: {ipt:.1f}/10\n{recomendacao}")
            elif ipt >= 6.5:
                st.info(f"Seu IPT: {ipt:.1f}/10\n{recomendacao}")
            elif ipt >= 5:
                st.warning(f"Seu IPT: {ipt:.1f}/10\n{recomendacao}")
            else:
                st.error(f"Seu IPT: {ipt:.1f}/10\n{recomendacao}")

def ver_historico(usuario):
    st.subheader("Meu Histórico de Avaliações")

    periodo = st.selectbox(
        "Selecione o período:",
        ["Últimos 7 dias", "Últimos 14 dias", "Últimos 30 dias", "Todo histórico"]
    )

    df = carregar_dados()

    if periodo == "Últimos 7 dias":
        df_filtrado = filtrar_por_periodo(df, usuario, 7)
    elif periodo == "Últimos 14 dias":
        df_filtrado = filtrar_por_periodo(df, usuario, 14)
    elif periodo == "Últimos 30 dias":
        df_filtrado = filtrar_por_periodo(df, usuario, 30)
    else:
        df_filtrado = df[df['Usuario'] == usuario]

    if not df_filtrado.empty:
        # Gráfico de evolução do IPT
        fig1 = px.line(df_filtrado, x='Data', y='IPT', 
                      title='Evolução do seu IPT',
                      labels={'IPT': 'Índice de Prontidão para Treino'})
        st.plotly_chart(fig1)

        # Gráfico de radar com médias
        medias = df_filtrado[['Sono', 'Stress', 'Dor', 'Energia', 'Refeicao']].mean()
        fig2 = go.Figure(data=go.Scatterpolar(
            r=medias.values,
            theta=medias.index,
            fill='toself'
        ))
        fig2.update_layout(title='Médias dos Indicadores')
        st.plotly_chart(fig2)

        # Tabela com últimas avaliações
        st.subheader("Últimas Avaliações")
        st.dataframe(
            df_filtrado[['Data', 'IPT', 'Recomendacao']]
            .sort_values('Data', ascending=False)
        )

        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média de IPT", f"{df_filtrado['IPT'].mean():.2f}")
        with col2:
            st.metric("Melhor IPT", f"{df_filtrado['IPT'].max():.2f}")
        with col3:
            st.metric("Pior IPT", f"{df_filtrado['IPT'].min():.2f}")
    else:
        st.info("Nenhum registro encontrado para o período selecionado.")

def area_personal():
    st.subheader("Área do Personal")

    senha = st.text_input("Senha:", type="password")
    if senha == "123":
        df = carregar_dados()

        if not df.empty:
            st.success("Acesso autorizado!")

            # Filtro de período
            periodo = st.selectbox(
                "Selecione o período:",
                ["Últimos 7 dias", "Últimos 14 dias", "Últimos 30 dias", "Todo histórico"]
            )

            if periodo == "Últimos 7 dias":
                df = df[df['Data'] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]
            elif periodo == "Últimos 14 dias":
                df = df[df['Data'] >= (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")]
            elif periodo == "Últimos 30 dias":
                df = df[df['Data'] >= (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")]

            # Estatísticas gerais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Avaliações", len(df))
            with col2:
                st.metric("Média Geral de IPT", f"{df['IPT'].mean():.2f}")
            with col3:
                st.metric("Alunos Ativos", len(df['Usuario'].unique()))

            # Gráfico de média por aluno
            media_alunos = df.groupby('Nome')['IPT'].mean().reset_index()
            fig = px.bar(media_alunos, x='Nome', y='IPT',
                        title='Média de IPT por Aluno')
            st.plotly_chart(fig)

            # Download dos dados
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="dados_ipt.csv">Download dos dados (CSV)</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Últimas avaliações
            st.subheader("Últimas Avaliações")
            st.dataframe(df.sort_values('Data', ascending=False))
        else:
            st.info("Ainda não há dados registrados.")
    elif senha:
        st.error("Senha incorreta!")

# Execução principal
if not st.session_state.logged_in:
    login_interface()
else:
    main_interface()
