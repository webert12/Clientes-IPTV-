import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Gestão IPTV", page_icon="👥", layout="centered")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- FUNÇÃO CORRIGIDA (Upsert em vez de Delete) ---
def salvar_no_banco(lista_clientes):
    with engine.begin() as conn:
        for c in lista_clientes:
            # O PostgreSQL fará o trabalho pesado: se o nome existir, atualiza. Se não, insere.
            sql = text("""
                INSERT INTO clientes (nome, data_json) 
                VALUES (:nome, :data_json::jsonb) 
                ON CONFLICT (nome) DO UPDATE SET data_json = EXCLUDED.data_json
            """)
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            return [json.loads(r[0]) for r in result]
    except Exception:
        return []

# Inicialização
if "clientes" not in st.session_state:
    st.session_state.clientes = carregar_clientes()

st.title("👥 Gestão de Clientes")

# --- IMPORTAÇÃO ---
with st.expander("📥 Importar Clientes"):
    texto = st.text_area("Cole: Usuario Senha (um por linha)", height=200)
    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)

    if st.button("Processar Importação"):
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        hoje = datetime.now()
        novos = []
        for linha in linhas:
            partes = linha.split()
            if len(partes) >= 2:
                user, pwd = partes[0], partes[1]
                # Lógica de vencimento
                ano, mes = (hoje.year, hoje.month + 1) if hoje.day > 10 else (hoje.year, hoje.month)
                if mes > 12: mes, ano = 1, ano + 1
                
                cliente = {
                    "nome": user, "usuario": user, "senha": pwd,
                    "valor": float(valor_padrao), "vencimento": datetime(ano, mes, 10).strftime("%d/%m/%Y"),
                    "status": "Pendente", "whatsapp": "", "telas": 1
                }
                st.session_state.clientes.append(cliente)
                novos.append(cliente)
        
        # Salva apenas os novos ou todos
        salvar_no_banco(st.session_state.clientes)
        st.success(f"{len(novos)} clientes importados e salvos!")
        st.rerun()

# --- LISTAGEM ---
st.subheader("📋 Lista de Clientes")
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    st.dataframe(df[["nome", "usuario", "senha", "vencimento", "status"]], use_container_width=True)
else:
    st.warning("Nenhum cliente cadastrado.")
