import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text, exc

# Configuração da Aplicação
st.set_page_config(page_title="Gestão IPTV Profissional", page_icon="👥", layout="centered")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- CAMADA DE PERSISTÊNCIA (DATA ACCESS LAYER) ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            query = text("SELECT data_json FROM clientes")
            result = conn.execute(query).fetchall()
            return [json.loads(r[0]) for r in result]
    except Exception:
        return []

def salvar_no_banco(lista_clientes):
    """
    Realiza o 'upsert' (inserção ou atualização) no banco de dados.
    O uso de cast '::jsonb' é obrigatório para conformidade com o PostgreSQL.
    """
    try:
        with engine.begin() as conn:
            for c in lista_clientes:
                sql = text("""
                    INSERT INTO clientes (nome, data_json) 
                    VALUES (:nome, :data_json::jsonb)
                    ON CONFLICT (nome) DO UPDATE SET data_json = EXCLUDED.data_json
                """)
                conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})
    except exc.SQLAlchemyError as e:
        st.error(f"Falha na sincronização com o banco: {str(e)}")
        raise e

# --- INICIALIZAÇÃO DE ESTADO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

st.title("👥 Gestão de Clientes IPTV")

# --- MÓDULO DE IMPORTAÇÃO ---
with st.expander("📥 Importação em Massa"):
    texto_input = st.text_area("Formato: Usuario Senha (um por linha)", height=150)
    if st.button("Executar Importação"):
        linhas = [l.strip() for l in texto_input.splitlines() if l.strip()]
        for linha in linhas:
            partes = linha.split()
            if len(partes) >= 2:
                user, pwd = partes[0], partes[1]
                novo = {
                    "nome": user, "usuario": user, "senha": pwd,
                    "valor": 25.0, "status": "Pendente",
                    "vencimento": datetime.now().strftime("%d/%m/%Y")
                }
                st.session_state.clientes.append(novo)
        
        salvar_no_banco(st.session_state.clientes)
        st.rerun()

# --- MÓDULO DE LISTAGEM ---
st.subheader("📋 Clientes Cadastrados")
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    st.dataframe(df[["nome", "usuario", "senha", "status"]], use_container_width=True)

    # --- EDIÇÃO ---
    st.divider()
    cliente_selecionado = st.selectbox("Editar Cliente", [c['nome'] for c in st.session_state.clientes])
    cli = next((c for c in st.session_state.clientes if c['nome'] == cliente_selecionado), None)
    
    if cli:
        cli['usuario'] = st.text_input("Usuário", cli['usuario'])
        cli['senha'] = st.text_input("Senha", cli['senha'])
        if st.button("Salvar Edição"):
            salvar_no_banco(st.session_state.clientes)
            st.success("Atualizado com sucesso.")
            st.rerun()
else:
    st.info("Nenhum cliente na base.")
