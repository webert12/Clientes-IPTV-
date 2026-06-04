import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# --- CONEXÃO SQL (Substitui o Path ARQ) ---
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- FUNÇÕES DE DADOS (Substituem leitura/escrita JSON) ---
def carregar_clientes():
    with engine.connect() as conn:
        query = text("SELECT data_json FROM clientes")
        result = conn.execute(query).fetchall()
        return [json.loads(r[0]) for r in result]

def salvar_no_banco(clientes):
    with engine.begin() as conn:
        # Limpa e reinsere para manter sincronia total com a lista da sessão
        conn.execute(text("DELETE FROM clientes"))
        for c in clientes:
            sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

st.title("👥 Gestão de Clientes")

# Carrega do Banco
clientes = carregar_clientes()

if "show_delete" not in st.session_state:
    st.session_state["show_delete"] = False

# =========================
# IMPORTAÇÃO EM MASSA
# =========================
with st.expander("📥 Importar Clientes em Massa (Inteligente)"):
    texto = st.text_area("Cole usuários / senhas / nomes", height=300)
    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)

    if st.button("Processar Importação"):
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        hoje = datetime.now()
        for linha in linhas:
            partes = linha.split()
            nome, usuario, senha = (partes[2], partes[0], partes[1]) if len(partes) >= 3 else (partes[0], partes[0], partes[1])
            
            ano, mes = (hoje.year, hoje.month + 1) if hoje.day > 10 else (hoje.year, hoje.month)
            if mes > 12: mes, ano = 1, ano + 1
            
            clientes.append({
                "nome": nome, "whatsapp": "", "usuario": usuario, "senha": senha,
                "valor": valor_padrao, "telas": 1, "observacao": "",
                "vencimento": datetime(ano, mes, 10).strftime("%d/%m/%Y"), "status": "Pendente"
            })
        salvar_no_banco(clientes)
        st.rerun()

# =========================
# TABELA E FILTROS (Mantenha sua lógica de exibição aqui...)
# =========================
# ... (O restante da sua lógica permanece idêntica) ...

# EX: No botão de salvar ou editar, apenas troque ARQ.write_text por:
# salvar_no_banco(clientes)
