import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text, exc

# Configuração
st.set_page_config(page_title="Gestão IPTV Profissional", page_icon="👥", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- PERSISTÊNCIA ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            return [json.loads(r[0]) for r in result]
    except: return []

def salvar_no_banco(lista_clientes):
    with engine.begin() as conn:
        # Limpa tudo e reinseri para garantir consistência após exclusões
        conn.execute(text("DELETE FROM clientes"))
        for c in lista_clientes:
            sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

# --- INICIALIZAÇÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

st.title("👥 Gestão de Clientes IPTV")

# --- IMPORTAÇÃO ---
with st.expander("📥 Importação em Massa"):
    texto = st.text_area("Formato: Nome Usuario Senha", height=150)
    if st.button("Executar Importação"):
        for linha in texto.splitlines():
            p = linha.split()
            if len(p) >= 3:
                st.session_state.clientes.append({"nome": p[0], "usuario": p[1], "senha": p[2], "status": "Pendente"})
        salvar_no_banco(st.session_state.clientes)
        st.rerun()

# --- EXCLUSÃO EM MASSA ---
st.subheader("📋 Clientes Cadastrados")
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    
    # Adiciona coluna de seleção na tabela
    df.insert(0, "Selecionar", False)
    
    # O data_editor permite marcar um por um ou o cabeçalho "Selecionar" (marcar todos)
    edited_df = st.data_editor(df, hide_index=True, use_container_width=True)
    
    if st.button("🗑️ Excluir Selecionados"):
        # Filtra os que NÃO foram selecionados
        selecionados = edited_df[edited_df["Selecionar"] == True]
        if not selecionados.empty:
            st.session_state.clientes = [c for c in st.session_state.clientes if c["nome"] not in selecionados["nome"].values]
            salvar_no_banco(st.session_state.clientes)
            st.success("Clientes excluídos com sucesso!")
            st.rerun()
        else:
            st.warning("Nenhum cliente selecionado.")

    # --- EDIÇÃO ---
    st.divider()
    st.subheader("✏️ Editar Cliente")
    nome_sel = st.selectbox("Selecione para editar", [c['nome'] for c in st.session_state.clientes])
    cli = next((c for c in st.session_state.clientes if c['nome'] == nome_sel), None)
    
    if cli:
        cli['usuario'] = st.text_input("Usuário", cli['usuario'])
        cli['senha'] = st.text_input("Senha", cli['senha'])
        if st.button("Salvar Alterações"):
            salvar_no_banco(st.session_state.clientes)
            st.rerun()
else:
    st.info("Nenhum cliente na base.")
