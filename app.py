import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Controle de Clientes", layout="wide")

USUARIOS = Path("usuarios.json")

if "logado" not in st.session_state:
    st.session_state.logado = False

def carregar_usuarios():
    if not USUARIOS.exists():
        USUARIOS.write_text('{"usuarios":[{"usuario":"admin","senha":"123456"}]}', encoding="utf-8")
    return json.loads(USUARIOS.read_text(encoding="utf-8"))

if not st.session_state.logado:
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        dados = carregar_usuarios()
        for u in dados["usuarios"]:
            if u["usuario"] == usuario and u["senha"] == senha:
                st.session_state.logado = True
                st.rerun()
        st.error("Usuário ou senha inválidos")
else:
    st.title("✅ Sistema Controle de Clientes")
    st.success("Use o menu lateral para acessar Dashboard, Clientes e Financeiro.")
