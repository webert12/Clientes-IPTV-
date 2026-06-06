import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text, exc

# Configuração da página
st.set_page_config(page_title="Dashboard Vision Play TV", page_icon="📊", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- CRIAÇÃO AUTOMÁTICA DA TABELA ---
def inicializar_banco():
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255),
                    data_json JSONB
                );
            """))
    except Exception as e:
        st.error(f"⚠️ Erro crítico ao criar a estrutura do banco de dados: {e}")

inicializar_banco()

# --- DADOS INICIAIS ---
CLIENTES_INICIAIS = [
    {"nome": "Rejane", "usuario": "Rejaneita", "senha": "1234052466960319", "status": "Pendente", "valor": 25.90},
    {"nome": "Regi", "usuario": "Regijr", "senha": "1234575761818", "status": "Pendente", "valor": 25.90},
    {"nome": "Igor", "usuario": "Teste24h", "senha": "9365318638", "status": "Pendente", "valor": 25.90},
    {"nome": "MariaEduarda", "usuario": "Mariaeduarda", "senha": "12639884293", "status": "Pendente", "valor": 25.90},
    {"nome": "Fatima", "usuario": "Fatima", "senha": "9228953758", "status": "Pendente", "valor": 25.90},
    {"nome": "PauloJunior", "usuario": "34112515116188972742", "senha": "20022026", "status": "Pendente", "valor": 25.90},
    {"nome": "Geraldo", "usuario": "GeraldoM3", "senha": "249591218", "status": "Pendente", "valor": 25.90},
    {"nome": "Kaio", "usuario": "Kaio123", "senha": "6487511788", "status": "Pendente", "valor": 25.90},
    {"nome": "Anderson", "usuario": "Anderson31441015", "senha": "31441015", "status": "Pendente", "valor": 25.90},
    {"nome": "Tania", "usuario": "Tania1234", "senha": "288363116", "status": "Pendente", "valor": 25.90},
    {"nome": "Guilherme", "usuario": "GuilhermeT3", "senha": "877877826", "status": "Pendente", "valor": 25.90},
    {"nome": "Guimba", "usuario": "Guimba2", "senha": "379875886", "status": "Pendente", "valor": 25.90},
    {"nome": "Ednaldo", "usuario": "Ednaldo9", "senha": "434838197", "status": "Pendente", "valor": 25.90},
    {"nome": "Mariana", "usuario": "Mariana5", "senha": "481718365", "status": "Pendente", "valor": 25.90},
    {"nome": "Cairo", "usuario": "Cairo12", "senha": "7858475797", "status": "Pendente", "valor": 25.90},
    {"nome": "Lauren", "usuario": "Lauren2", "senha": "615133128", "status": "Pendente", "valor": 25.90},
    {"nome": "Limarita", "usuario": "Limarita123", "senha": "3214987985", "status": "Pendente", "valor": 25.90},
    {"nome": "Maguila", "usuario": "Maguila15", "senha": "273754722", "status": "Pendente", "valor": 25.90},
    {"nome": "BrazGeraldo", "usuario": "Brazgeraldo4", "senha": "85969684554", "status": "Pendente", "valor": 25.90},
    {"nome": "AndreBernardes", "usuario": "Andrebernardes5", "senha": "489814998", "status": "Pendente", "valor": 25.90},
    {"nome": "Nilcio", "usuario": "25106846837670794071", "senha": "27062025", "status": "Pendente", "valor": 25.90},
    {"nome": "Alonso", "usuario": "Alonso2", "senha": "ck2ccgh235", "status": "Pendente", "valor": 25.90},
    {"nome": "Deivane", "usuario": "Deivanennqnu3", "senha": "th6m", "status": "Pendente", "valor": 25.90},
    {"nome": "NataliaMenezes", "usuario": "81821125638099462524", "senha": "26062025", "status": "Pendente", "valor": 25.90},
    {"nome": "Roseita", "usuario": "Roseita4", "senha": "78945185", "status": "Pendente", "valor": 25.90},
    {"nome": "Paulinho", "usuario": "Paulinho12", "senha": "tp3f9hhqq5", "status": "Pendente", "valor": 25.90},
    {"nome": "Walker", "usuario": "Walker1234", "senha": "yqrj8xv9k3", "status": "Pendente", "valor": 25.90},
    {"nome": "MariaClaudio", "usuario": "MariaClaudio5", "senha": "jxaxs7puu", "status": "Pendente", "valor": 25.90},
    {"nome": "Alonso1", "usuario": "Alonso12345", "senha": "2384y5rwh", "status": "Pendente", "valor": 25.90},
    {"nome": "Deivid", "usuario": "08578350209007893072", "senha": "18062025", "status": "Pendente", "valor": 25.90},
    {"nome": "Elizandra", "usuario": "Elizandra123", "senha": "7576594786", "status": "Pendente", "valor": 25.90},
    {"nome": "Douglas", "usuario": "Douglas123", "senha": "6860511987", "status": "Pendente", "valor": 25.90},
    {"nome": "Zepaulo", "usuario": "Zepaulo1", "senha": "165139999", "status": "Pendente", "valor": 25.90},
    {"nome": "AnnaLaura", "usuario": "AnnaLaura123", "senha": "124906705880", "status": "Pendente", "valor": 25.90},
    {"nome": "Diegoneomp", "usuario": "Diegoneomp9", "senha": "1kf7fnj", "status": "Pendente", "valor": 25.90},
    {"nome": "Diogodiv", "usuario": "Diogodiv4", "senha": "849606387", "status": "Pendente", "valor": 25.90},
    {"nome": "MariaRosa", "usuario": "MariaRosa9", "senha": "158788294", "status": "Pendente", "valor": 25.90},
    {"nome": "Luciano", "usuario": "Luciano123", "senha": "8866992981", "status": "Pendente", "valor": 25.90},
    {"nome": "AlinePrima", "usuario": "84604741183591874711", "senha": "10062025", "status": "Pendente", "valor": 25.90},
    {"nome": "Tamires", "usuario": "Tamires123", "senha": "n3ved26w1e1", "status": "Pendente", "valor": 25.90},
    {"nome": "Cassiano", "usuario": "Cassiano2", "senha": "43pprnj19bg", "status": "Pendente", "valor": 25.90},
    {"nome": "Manoelita", "usuario": "Manoelita1", "senha": "ep4a9mw6rs", "status": "Pendente", "valor": 25.90},
    {"nome": "AirtonCesar", "usuario": "Airtoncesar1", "senha": "937583748", "status": "Pendente", "valor": 25.90},
    {"nome": "Jefinho", "usuario": "Jefinho2", "senha": "2522695854", "status": "Pendente", "valor": 25.90},
    {"nome": "Fredinho", "usuario": "Fredinho6", "senha": "664090314", "status": "Pendente", "valor": 25.90},
    {"nome": "Lidiane", "usuario": "59048676357235395158", "senha": "02052025", "status": "Pendente", "valor": 25.90},
    {"nome": "Cida", "usuario": "89429163675233408932", "senha": "28042025", "status": "Pendente", "valor": 25.90},
    {"nome": "Adilson", "usuario": "Adilson4", "senha": "315751435", "status": "Pendente", "valor": 25.90},
    {"nome": "Natan", "usuario": "cgykd620zdgr", "senha": "rergmfsf", "status": "Pendente", "valor": 25.90},
    {"nome": "Renato", "usuario": "RenatoDel0", "senha": "997708882", "status": "Pendente", "valor": 25.90}
]

# --- PERSISTÊNCIA CORRIGIDA (Utilizando CAST) ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            if not result:
                with engine.begin() as tx:
                    for c in CLIENTES_INICIAIS:
                        tx.execute(text("INSERT INTO clientes (nome, data_json) VALUES (:nome, CAST(:data_json AS JSONB))"), 
                                   {"nome": c['nome'], "data_json": json.dumps(c)})
                return CLIENTES_INICIAIS
            return [json.loads(r[0]) for r in result]
    except Exception as e:
        st.error(f"⚠️ Erro ao acessar o banco de dados: {e}")
        return None

def salvar_no_banco(lista_clientes):
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clientes"))
            for c in lista_clientes:
                sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, CAST(:data_json AS JSONB))")
                conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})
    except exc.SQLAlchemyError as e:
        st.error(f"Erro ao salvar alterações no banco: {e}")

# Inicialização do estado local
if 'clientes' not in st.session_state:
    dados = carregar_clientes()
    st.session_state.clientes = dados if dados is not None else []
if 'marcar_todos' not in st.session_state:
    st.session_state.marcar_todos = False

# --- CÁLCULO DOS METRICS BLINDADO ---
total_clientes = len(st.session_state.clientes)

previsto = sum(float(c.get('valor', 25.90)) for c in st.session_state.clientes)
recebido = sum(float(c.get('valor', 25.90)) for c in st.session_state.clientes 
               if str(c.get('status', '')).strip().lower() in ['confirmado', 'pago'])
pendente = previsto - recebido

# --- INTERFACE DO DASHBOARD ---
st.title("📊 Dashboard Vision Play TV")

st.metric("👥 Clientes", f"{total_clientes}")
st.metric("💰 Previsto", f"R$ {previsto:.2f}")
st.metric("✅ Recebido", f"R$ {recebido:.2f}")
st.metric("⚠️ Pendente", f"R$ {pendente:.2f}")

st.divider()

# --- TABELA DE GERENCIAMENTO ---
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    df.insert(0, "🗑️", st.session_state.marcar_todos)
    
    edited_df = st.data_editor(df, hide_index=True, use_container_width=True)

    col1, col2, col3 = st.columns([1.5, 2, 4])
    with col1:
        if st.button("✅ Marcar/Desmarcar Todos"):
            st.session_state.marcar_todos = not st.session_state.marcar_todos
            st.rerun()

    with col2:
        if st.button("🗑️ Excluir Selecionados"):
            selecionados = edited_df[edited_df["🗑️"] == True]
            if not selecionados.empty:
                st.session_state.clientes = [c for c in st.session_state.clientes if c["nome"] not in selecionados["nome"].values]
                salvar_no_banco(st.session_state.clientes)
                st.session_state.marcar_todos = False
                st.success("Removidos com sucesso.")
                st.rerun()
                
    with col3:
        if st.button("💾 Salvar Modificações da Tabela"):
            dados_atualizados = edited_df.drop(columns=["🗑️"]).to_dict(orient="records")
            st.session_state.clientes = dados_atualizados
            salvar_no_banco(dados_atualizados)
            st.success("Tabela salva com sucesso!")
            st.rerun()

    # --- CONFIRMAÇÃO DE PAGAMENTO RÁPIDA ---
    st.divider()
    st.subheader("💳 Registrar Pagamento rápido")
    nome_sel = st.selectbox("Selecione o cliente para confirmar pagamento", [c['nome'] for c in st.session_state.clientes])
    cli = next((c for c in st.session_state.clientes if c['nome'] == nome_sel), None)

    if cli:
        st.write(f"Status atual de **{cli['nome']}**: {cli.get('status', 'Pendente')}")
        if st.button("✅ Confirmar Pagamento"):
            cli['status'] = "Confirmado"
            salvar_no_banco(st.session_state.clientes)
            st.success(f"Pagamento de {cli['nome']} atualizado!")
            st.rerun() 
else:
    st.info("Nenhum cliente cadastrado ou banco de dados vazio.")
