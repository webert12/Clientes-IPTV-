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
            query = text("SELECT data_json FROM clientes")
            result = conn.execute(query).fetchall()
            return [json.loads(r[0]) for r in result]
    except Exception:
        return []

def salvar_no_banco(lista_clientes):
    # O bloco 'begin' inicia uma transação automática
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes"))
        for c in lista_clientes:
            sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

# --- INICIALIZAÇÃO ---
if "clientes" not in st.session_state:
    st.session_state.clientes = carregar_clientes()

st.title("👥 Gestão de Clientes")

# =========================
# IMPORTAÇÃO (APENAS USUÁRIO/SENHA)
# =========================
with st.expander("📥 Importar Clientes (Usuário e Senha)"):
    texto = st.text_area("Cole: Usuario Senha (um por linha)", height=200)
    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)

    if st.button("Processar Importação"):
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        hoje = datetime.now()
        for linha in linhas:
            partes = linha.split()
            if len(partes) >= 2:
                user, pwd = partes[0], partes[1]
                ano, mes = (hoje.year, hoje.month + 1) if hoje.day > 10 else (hoje.year, hoje.month)
                if mes > 12: mes, ano = 1, ano + 1
                
                st.session_state.clientes.append({
                    "nome": user, "usuario": user, "senha": pwd,
                    "valor": valor_padrao, "vencimento": datetime(ano, mes, 10).strftime("%d/%m/%Y"),
                    "status": "Pendente", "whatsapp": "", "telas": 1
                })
        salvar_no_banco(st.session_state.clientes)
        st.success("Importação concluída!")
        st.rerun()

# =========================
# LISTAGEM E FILTROS
# =========================
st.subheader("📋 Lista de Clientes")
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    st.dataframe(df[["nome", "usuario", "senha", "vencimento", "status"]], use_container_width=True)
else:
    st.warning("Nenhum cliente cadastrado.")

# =========================
# AÇÃO DE SALVAR GERAL
# =========================
if st.button("💾 Sincronizar Tudo com Banco"):
    salvar_no_banco(st.session_state.clientes)
    st.success("Dados salvos no banco com sucesso!")
