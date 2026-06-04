import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão IPTV", page_icon="👥", layout="centered")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            return [json.loads(r[0]) for r in result]
    except:
        return []

def salvar_no_banco(lista_clientes):
    with engine.begin() as conn:
        for c in lista_clientes:
            # Upsert: Insere ou atualiza o cliente pelo nome
            sql = text("""
                INSERT INTO clientes (nome, data_json) 
                VALUES (:nome, :data_json::jsonb)
                ON CONFLICT (nome) DO UPDATE SET data_json = EXCLUDED.data_json
            """)
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

# --- INICIALIZAÇÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

st.title("👥 Gestão de Clientes")

# --- IMPORTAÇÃO ---
with st.expander("📥 Importar Clientes em Massa"):
    texto = st.text_area("Cole usuários / senhas / nomes", height=200)
    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)
    if st.button("Processar Importação"):
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        hoje = datetime.now()
        for linha in linhas:
            partes = linha.split()
            nome = partes[2] if len(partes) >= 3 else partes[0]
            st.session_state.clientes.append({
                "nome": nome, "whatsapp": "", "usuario": partes[0], "senha": partes[1],
                "valor": valor_padrao, "telas": 1, "status": "Pendente",
                "vencimento": datetime(hoje.year, hoje.month + 1, 10).strftime("%d/%m/%Y")
            })
        salvar_no_banco(st.session_state.clientes)
        st.rerun()

# --- FILTROS ---
pesquisa = st.text_input("🔍 Pesquisar cliente")
clientes_filtrados = [c for c in st.session_state.clientes if pesquisa.lower() in c['nome'].lower()]

# --- TABELA ---
df = pd.DataFrame(clientes_filtrados)
if not df.empty:
    st.dataframe(df[["nome", "usuario", "senha", "vencimento", "status"]], use_container_width=True)

# --- AÇÕES ---
st.divider()
st.subheader("✏️ Editar ou Receber Pagamento")
nomes = [c["nome"] for c in st.session_state.clientes]
sel = st.selectbox("Selecione o Cliente", nomes)
cli = next(c for c in st.session_state.clientes if c["nome"] == sel)

cli["usuario"] = st.text_input("Usuário", cli["usuario"])
cli["senha"] = st.text_input("Senha", cli["senha"])
if st.button("Salvar Alterações"):
    salvar_no_banco(st.session_state.clientes)
    st.success("Salvo!")
    st.rerun()

if st.button("💵 Receber Pagamento"):
    cli["status"] = "Recebido"
    salvar_no_banco(st.session_state.clientes)
    st.rerun()
