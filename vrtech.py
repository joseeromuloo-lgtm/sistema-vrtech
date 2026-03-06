import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="VR TECH | Gestão", layout="wide", initial_sidebar_state="expanded")

# --- DESIGN MINIMALISTA PREMIUM ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #F3F4F6; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1F2937; }
    .stButton>button { background-color: transparent; color: #9CA3AF; border: none; text-align: left; padding: 12px 20px; width: 100%; border-radius: 6px; transition: 0.2s; }
    .stButton>button:hover { background-color: #1F2937; color: #3B82F6; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input { background-color: #111827 !important; color: #F3F4F6 !important; border: 1px solid #374151 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO FIREBASE ---
if not firebase_admin._apps:
    try:
        cred_dict = st.secrets["gcp_service_account"]
        cred = credentials.Certificate(dict(cred_dict))
    except:
        try:
            cred = credentials.Certificate("chavedeacesso.json")
        except:
            st.error("Erro: Arquivo 'chavedeacesso.json' não encontrado.")
            st.stop()
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://vr-tech-a49e5-default-rtdb.firebaseio.com/'} )

# --- FUNÇÕES DE BANCO DE DADOS ---
def get_os():
    data = db.reference('os').get()
    return list(data.values()) if data else []

def salvar_os(nova_os):
    db.reference('os').push(nova_os)

def atualizar_status_os(os_id, novo_status):
    ref = db.reference('os')
    os_data = ref.get()
    if os_data:
        for key, val in os_data.items():
            if val.get('id') == os_id:
                ref.child(key).update({'status': novo_status})
                break

def verificar_login(usuario, senha):
    usuarios = db.reference('usuarios').get()
    return usuarios.get(usuario) == senha if usuarios else False

def cadastrar_usuario(usuario, senha):
    ref = db.reference('usuarios')
    if ref.child(usuario).get(): return False
    ref.child(usuario).set(senha)
    return True

# --- CONTROLE DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'menu' not in st.session_state: st.session_state.menu = "Dashboard"

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>VR TECH</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        t1, t2 = st.tabs(["Entrar", "Criar Conta"])
        with t1:
            u = st.text_input("Usuário", key="l_u")
            p = st.text_input("Senha", type="password", key="l_p")
            if st.button("Acessar", use_container_width=True):
                if verificar_login(u, p):
                    st.session_state.logado = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Erro de login.")
        with t2:
            nu = st.text_input("Novo Usuário", key="c_u")
            np = st.text_input("Nova Senha", type="password", key="c_p")
            if st.button("Cadastrar", use_container_width=True):
                if cadastrar_usuario(nu, np): st.success("Usuário criado!")
                else: st.error("Erro ao criar usuário.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"👤 **{st.session_state.user}**")
if st.sidebar.button("📊 Dashboard"): st.session_state.menu = "Dashboard"
if st.sidebar.button("📝 Nova OS"): st.session_state.menu = "Nova OS"
if st.sidebar.button("🛠️ Serviços"): st.session_state.menu = "Serviços"
if st.sidebar.button("💰 Financeiro"): st.session_state.menu = "Financeiro"
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()

# --- DADOS ---
os_list = get_os()
df = pd.DataFrame(os_list) if os_list else pd.DataFrame(columns=['id', 'cliente', 'servico', 'valor', 'data', 'status'])

# --- PÁGINAS ---
if st.session_state.menu == "Dashboard":
    st.title("Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de OS", len(df))
    c2.metric("Pendentes", len(df[df['status'] == 'Pendente']))
    c3.metric("Concluídas", len(df[df['status'] == 'Concluído']))

elif st.session_state.menu == "Nova OS":
    st.title("Nova Ordem de Serviço")
    with st.form("os_form", clear_on_submit=True):
        cli = st.text_input("Nome do Cliente")
        ser = st.text_input("Descrição do Serviço")
        val = st.number_input("Valor do Serviço (R$)", min_value=0.0, step=10.0)
        dat = st.date_input("Data do Serviço", datetime.now())
        
        enviar = st.form_submit_button("Registrar Serviço")
        if enviar:
            if cli and ser:
                nova_os = {
                    "id": int(datetime.now().timestamp()),
                    "cliente": cli, "servico": ser, "valor": val,
                    "data": dat.strftime("%d/%m/%Y"), "status": "Pendente"
                }
                salvar_os(nova_os)
                st.success(f"OS para {cli} registrada com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, preencha o nome do cliente e o serviço.")

elif st.session_state.menu == "Serviços":
    st.title("Gerenciamento de Serviços")
    busca = st.text_input("🔍 Buscar por cliente...")
    df_f = df[df['cliente'].str.contains(busca, case=False)] if not df.empty else df
    
    if df_f.empty:
        st.info("Nenhum serviço encontrado.")
    else:
        for _, r in df_f.iterrows():
            cor_status = "🟡" if r['status'] == "Pendente" else "🟢"
            with st.expander(f"{cor_status} {r['cliente']} - {r['servico']}"):
                st.write(f"**Valor:** R$ {r['valor']:.2f}")
                st.write(f"**Data:** {r['data']}")
                st.write(f"**Status:** {r['status']}")
                if r['status'] == "Pendente":
                    if st.button("Marcar como Concluído", key=f"btn_{r['id']}"):
                        atualizar_status_os(r['id'], "Concluído")
                        st.success("Status atualizado!")
                        st.rerun()

elif st.session_state.menu == "Financeiro":
    st.title("Relatório Financeiro")
    df_c = df[df['status'] == 'Concluído'].copy()
    
    if df_c.empty:
        st.info("Ainda não há serviços concluídos para gerar relatórios.")
    else:
        # Converter data para formato de data do pandas
        df_c['data_dt'] = pd.to_datetime(df_c['data'], format='%d/%m/%Y')
        # Criar coluna Mês/Ano para agrupamento
        df_c['Mês/Ano'] = df_c['data_dt'].dt.strftime('%m/%Y')
        
        # Saldo Total
        st.metric("Saldo Total Acumulado", f"R$ {df_c['valor'].sum():.2f}")
        
        st.write("### Ganhos por Mês")
        # Agrupar e formatar os valores para 2 casas decimais
        mensal = df_c.groupby('Mês/Ano')['valor'].sum().reset_index()
        # Formatação para evitar os "zeros" extras
        mensal['Total Ganho (R$)'] = mensal['valor'].apply(lambda x: f"R$ {x:,.2f}")
        
        # Exibir apenas as colunas formatadas
        st.table(mensal[['Mês/Ano', 'Total Ganho (R$)']])
        
        st.write("### Detalhamento de Serviços Concluídos")
        # Formatar a coluna valor no dataframe de exibição também
        df_display = df_c[['data', 'cliente', 'servico', 'valor']].copy()
        df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_display, use_container_width=True)
