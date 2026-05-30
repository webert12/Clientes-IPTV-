import streamlit as st
import json
import os
from pathlib import Path

# ==========================
# CONFIGURAÇÃO DA PÁGINA
# ==========================

st.set_page_config(
    page_title="Vision Play TV Company Tecnologic",
    page_icon="📺",
    layout="wide"
)

# ==========================
# ARQUIVOS
# ==========================

USUARIOS_FILE = "usuarios.json"
CONFIG_FILE = "config.json"

# ==========================
# CRIAR ARQUIVOS PADRÃO
# ==========================

if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "usuarios": [
                {
                    "usuario": "admin",
                    "senha": "123456",
                    "nivel": "Administrador"
                }
            ]
        }, f, indent=4, ensure_ascii=False)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "tema": "escuro"
        }, f, indent=4)

# ==========================
# CARREGAR CONFIG
# ==========================

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

tema = config.get("tema", "escuro")

# ==========================
# TEMA
# ==========================

if tema == "escuro":

    st.markdown("""
    <style>
    .stApp {
        background-color: #0F172A;
        color: white;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    div[data-testid="metric-container"]{
        background-color:#1E293B;
        border:1px solid #334155;
        padding:15px;
        border-radius:12px;
    }

    .titulo {
        text-align:center;
        color:white;
        font-size:30px;
        font-weight:bold;
    }
    </style>
    """, unsafe_allow_html=True)

else:

    st.markdown("""
    <style>
    .titulo {
        text-align:center;
        font-size:30px;
        font-weight:bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================
# SESSÃO
# ==========================

if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if "nivel" not in st.session_state:
    st.session_state.nivel = ""

# ==========================
# FUNÇÕES
# ==========================

def carregar_usuarios():
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================
# LOGIN
# ==========================

if not st.session_state.logado:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        if os.path.exists("logo.png"):
            st.image("logo.png", width=250)

        st.markdown(
            "<div class='titulo'>Vision Play TV Company Tecnologic</div>",
            unsafe_allow_html=True
        )

        st.markdown("### 🔐 Login")

        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):

            dados = carregar_usuarios()

            acesso = False

            for user in dados["usuarios"]:

                if (
                    user["usuario"] == usuario
                    and user["senha"] == senha
                ):

                    st.session_state.logado = True
                    st.session_state.usuario = usuario
                    st.session_state.nivel = user.get(
                        "nivel",
                        "Administrador"
                    )

                    acesso = True
                    st.rerun()

            if not acesso:
                st.error("Usuário ou senha inválidos.")

# ==========================
# PAINEL
# ==========================

else:

    with st.sidebar:

        if os.path.exists("logo.png"):
            st.image("logo.png", width=180)

        st.markdown("## Vision Play TV")

        st.write(f"👤 {st.session_state.usuario}")

        st.write(f"🔑 {st.session_state.nivel}")

        st.divider()

        tema_escolhido = st.selectbox(
            "Tema",
            ["escuro", "claro"],
            index=0 if tema == "escuro" else 1
        )

        if tema_escolhido != tema:

            config["tema"] = tema_escolhido

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    config,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            st.rerun()

        st.divider()

        if st.button("🚪 Sair", use_container_width=True):

            st.session_state.logado = False
            st.session_state.usuario = ""
            st.session_state.nivel = ""

            st.rerun()

    st.markdown(
        """
        <div class='titulo'>
        📺 Vision Play TV Company Tecnologic
        </div>
        """,
        unsafe_allow_html=True
    )

    st.success(
        "Sistema carregado com sucesso. Utilize o menu lateral para acessar as funcionalidades."
    )

    st.info(
        f"Bem-vindo {st.session_state.usuario}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Versão",
            "2.0"
        )

    with col2:
        st.metric(
            "Tema",
            tema.capitalize()
        )

    with col3:
        st.metric(
            "Usuário",
            st.session_state.usuario
        )
