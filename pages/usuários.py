import streamlit as st
import json
from pathlib import Path

st.title("👤 Usuários do Sistema")

ARQ = Path("usuarios.json")

if not ARQ.exists():
    ARQ.write_text(
        json.dumps({
            "usuarios": [
                {
                    "usuario": "admin",
                    "senha": "123456",
                    "nivel": "Administrador"
                }
            ]
        }, indent=4),
        encoding="utf-8"
    )

dados = json.loads(
    ARQ.read_text(encoding="utf-8")
)

usuarios = dados["usuarios"]

# ==========================
# NOVO USUÁRIO
# ==========================

st.subheader("➕ Novo Usuário")

with st.form("novo_usuario"):

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    nivel = st.selectbox(
        "Nível",
        [
            "Administrador",
            "Operador"
        ]
    )

    cadastrar = st.form_submit_button(
        "Cadastrar Usuário"
    )

    if cadastrar:

        existe = any(
            u["usuario"] == usuario
            for u in usuarios
        )

        if existe:

            st.error(
                "Usuário já existe."
            )

        else:

            usuarios.append({

                "usuario": usuario,
                "senha": senha,
                "nivel": nivel

            })

            ARQ.write_text(
                json.dumps(
                    dados,
                    indent=4,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            st.success(
                "Usuário criado."
            )

            st.rerun()

st.divider()

# ==========================
# LISTA DE USUÁRIOS
# ==========================

st.subheader("📋 Usuários Cadastrados")

for i, usuario in enumerate(usuarios):

    with st.expander(
        f"{usuario['usuario']} ({usuario['nivel']})"
    ):

        nova_senha = st.text_input(
            "Nova Senha",
            key=f"senha_{i}"
        )

        if st.button(
            "Salvar Senha",
            key=f"salvar_{i}"
        ):

            usuario["senha"] = nova_senha

            ARQ.write_text(
                json.dumps(
                    dados,
                    indent=4,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            st.success(
                "Senha alterada."
            )

            st.rerun()

        if usuario["usuario"] != "admin":

            if st.button(
                "🗑️ Excluir Usuário",
                key=f"excluir_{i}"
            ):

                usuarios.remove(usuario)

                ARQ.write_text(
                    json.dumps(
                        dados,
                        indent=4,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

                st.warning(
                    "Usuário removido."
                )

                st.rerun()
