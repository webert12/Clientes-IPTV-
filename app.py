import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração
st.set_page_config(page_title="Gestão IPTV Pro", page_icon="👥", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- DADOS INICIAIS ---
CLIENTES_INICIAIS = [
    {"nome": "Rejane", "usuario": "Rejaneita", "senha": "1234052466960319", "status": "Pendente", "valor": 25.0},
    {"nome": "Regi", "usuario": "Regijr", "senha": "1234575761818", "status": "Pendente", "valor": 25.0},
    {"nome": "Igor", "usuario": "Teste24h", "senha": "9365318638", "status": "Pendente", "valor": 25.0},
    # ... (restante da lista mantida conforme padrão)
]

# --- PERSISTÊNCIA ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            if not result:
                # Inicializa com valor padrão caso não existam dados
                for c in CLIENTES_INICIAIS: c['valor'] = 25.0
                salvar_no_banco(CLIENTES_INICIAIS)
                return CLIENTES_INICIAIS
            return [json.loads(r[0]) for r in result]
    except: return CLIENTES_INICIAIS

def salvar_no_banco(lista_clientes):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes"))
        for c in lista_clientes:
            sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

# --- INICIALIZAÇÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()
if 'marcar_todos' not in st.session_state:
    st.session_state.marcar_todos = False

st.title("👥 Gestão de Clientes IPTV")

# --- DASHBOARD FINANCEIRO ---
st.subheader("📊 Resumo Financeiro")
confirmados = [c for c in st.session_state.clientes if c.get('status') == 'Confirmado']
valor_total = sum(c.get('valor', 25.0) for c in confirmados)

c1, c2 = st.columns(2)
c1.metric("Pagamentos Recebidos", len(confirmados))
c2.metric("Valor Total Arrecadado", f"R$ {valor_total:.2f}")

st.divider()

# --- LISTAGEM E EXCLUSÃO ---
df = pd.DataFrame(st.session_state.clientes)
df.insert(0, "🗑️", st.session_state.marcar_todos)
edited_df = st.data_editor(df, hide_index=True, use_container_width=True)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("✅ Marcar Todos"):
        st.session_state.marcar_todos = not st.session_state.marcar_todos
        st.rerun()

with col2:
    if st.button("🗑️ Excluir Selecionados"):
        selecionados = edited_df[edited_df["🗑️"] == True]
        if not selecionados.empty:
            st.session_state.clientes = [c for c in st.session_state.clientes if c["nome"] not in selecionados["nome"].values]
            salvar_no_banco(st.session_state.clientes)
            st.session_state.marcar_todos = False
            st.rerun()

# --- REGISTRO DE PAGAMENTO ---
st.divider()
st.subheader("💳 Registrar Pagamento")
nome_sel = st.selectbox("Selecione o cliente para confirmar pagamento", [c['nome'] for c in st.session_state.clientes])
cli = next((c for c in st.session_state.clientes if c['nome'] == nome_sel), None)

if cli:
    st.write(f"Status atual de **{cli['nome']}**: {cli.get('status', 'Pendente')}")
    if st.button("✅ Confirmar Pagamento"):
        cli['status'] = "Confirmado"
        salvar_no_banco(st.session_state.clientes)
        st.success(f"Pagamento de {cli['nome']} confirmado com sucesso!")
        st.rerun()
