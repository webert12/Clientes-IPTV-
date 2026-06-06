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

def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes ORDER BY id ASC")).fetchall()
            if not result:
                with engine.begin() as tx:
                    for c in CLIENTES_INICIAIS:
                        tx.execute(text("INSERT INTO clientes (nome, data_json) VALUES (:nome, CAST(:data_json AS JSONB))"), 
                                   {"nome": c['nome'], "data_json": json.dumps(c)})
                result = conn.execute(text("SELECT data_json FROM clientes ORDER BY id ASC")).fetchall()
            return [json.loads(r[0]) for r in result]
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados do banco: {e}")
        return []

def salvar_no_banco(lista_clientes):
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clientes"))
            for c in lista_clientes:
                sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, CAST(:data_json AS JSONB))")
                conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})
    except exc.SQLAlchemyError as e:
        st.error(f"Erro ao salvar alterações no banco: {e}")

# --- CONTROLE DE SESSÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

# --- CALLBACK PARA SALVAMENTO AUTOMÁTICO DA TABELA ---
def ao_alterar_tabela():
    alteracoes = st.session_state.editor_principal.get("edited_rows", {})
    if alteracoes:
        for idx, mudancas in alteracoes.items():
            st.session_state.clientes[idx].update(mudancas)
        salvar_no_banco(st.session_state.clientes)
        # Recarrega para garantir que os cálculos do topo peguem o dado atualizado imediatamente
        st.rerun()

# --- CÁLCULO DOS CARD FINANCEIROS (Sempre dinâmicos e precisos) ---
total_clientes = len(st.session_state.clientes)
previsto = sum(float(c.get('valor', 25.90)) for c in st.session_state.clientes)
recebido = sum(float(c.get('valor', 25.90)) for c in st.session_state.clientes 
               if str(c.get('status', '')).strip().lower() == 'confirmado')
pendente = previsto - recebido

# --- LOUYOUT DA TELA (Idêntico ao seu print) ---
st.title(" Dashboard Vision Play TV")

st.metric("👥 Clientes", f"{total_clientes}")
st.metric("💰 Previsto", f"R$ {previsto:.2f}")
st.metric("✅ Recebido", f"R$ {recebido:.2f}")
st.metric("⚠️ Pendente", f"R$ {pendente:.2f}")

st.divider()

# --- TABELA DE GERENCIAMENTO INTELIGENTE ---
st.subheader("👥 Lista de Clientes")
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    
    # Organiza a exibição das colunas desejadas
    df = df[["nome", "usuario", "senha", "status", "valor"]]
    
    # Renderiza o editor com validação automática por Selectbox
    st.data_editor(
        df,
        key="editor_principal",
        on_change=ao_alterar_tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "nome": st.column_config.TextColumn("Nome", disabled=True),
            "usuario": st.column_config.TextColumn("Usuário", disabled=True),
            "senha": st.column_config.TextColumn("Senha", disabled=True),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Pendente", "Confirmado"],
                required=True
            ),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", disabled=True)
        }
    )

    # --- REGISTRADOR RÁPIDO PARALELO ---
    st.divider()
    st.subheader("💳 Registrar Pagamento Rápido")
    nome_sel = st.selectbox("Selecione o cliente abaixo:", [c['nome'] for c in st.session_state.clientes])
    
    if st.button("⚡ Confirmar Pagamento do Selecionado", use_container_width=True):
        for c in st.session_state.clientes:
            if c['nome'] == nome_sel:
                c['status'] = "Confirmado"
                break
        salvar_no_banco(st.session_state.clientes)
        st.success(f"Sucesso! O pagamento de {nome_sel} foi processado.")
        st.rerun()
else:
    st.info("Nenhum cliente cadastrado no momento.")
