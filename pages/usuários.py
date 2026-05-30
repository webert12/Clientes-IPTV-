import streamlit as st
import json
from pathlib import Path

st.title("👤 Gerenciamento de Usuários")

ARQ_USUARIOS = Path("usuarios.json")

if not ARQ_USUARIOS.exists():
    ARQ_USUARIOS.write_text(
        json.dumps(
            {
                "usuarios": [
                    {
                        "usuario": "admin",
                        "senha": "123456",
                        "nivel": "Administrador"
                    }
                ]
            },
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

dados = json.loads(
    ARQ_USUARIOS.read_text(
        encoding="utf-8"
    )
)

usuarios = dados["usuarios"]

# ====================================
# CADASTRAR USUÁRIO
# ====================================

st.subheader("➕ Novo Usuário")

with st.form("novo_usuario"):

    usuario = st.text_input(
        "Usuário"
    )

    senha = st.text_input(
        "Senha",
        type="password"
    )

    nivel = st.selectbox(
        "Nível",
        [
            "Administrador",
            "Operador"
        ]
    )

    cadastrar = st.form_submit_button(
        "Cadastrar"
    )

    if cadastrar:

        existe = False

        for u in usuarios:

            if (
                u["usuario"].lower()
                ==
                usuario.lower()
            ):
                existe = True

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

            ARQ_USUARIOS.write_text(
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

# ====================================
# LISTAGEM
# ====================================

st.subheader("📋 Usuários")

for i, usuario in enumerate(usuarios):

    with st.expander(
        f"{usuario['usuario']} ({usuario['nivel']})"
    ):

        novo_usuario = st.text_input(
            "Usuário",
            usuario["usuario"],
            key=f"user_{i}"
        )

        nova_senha = st.text_input(
            "Senha",
            value=usuario["senha"],
            key=f"senha_{i}"
        )

        novo_nivel = st.selectbox(
            "Nível",
            [
                "Administrador",
                "Operador"
            ],
            index=0
            if usuario["nivel"]
            ==
            "Administrador"
            else 1,
            key=f"nivel_{i}"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "💾 Salvar",
                key=f"salvar_{i}"
            ):

                usuario["usuario"] = (
                    novo_usuario
                )

                usuario["senha"] = (
                    nova_senha
                )

                usuario["nivel"] = (
                    novo_nivel
                )

                ARQ_USUARIOS.write_text(
                    json.dumps(
                        dados,
                        indent=4,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

                st.success(
                    "Atualizado."
                )

                st.rerun()

        with col2:

            if usuario["usuario"] != "admin":

                if st.button(
                    "🗑️ Excluir",
                    key=f"excluir_{i}"
                ):

                    usuarios.remove(
                        usuario
                    )

                    ARQ_USUARIOS.write_text(
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

            else:

                st.info(
                    "Administrador principal protegido."
                )

st.divider()

# ====================================
# RESUMO
# ====================================

total_admin = len(
    [
        x
        for x in usuarios
        if x["nivel"]
        ==
        "Administrador"
    ]
)

total_operadores = len(
    [
        x
        for x in usuarios
        if x["nivel"]
        ==
        "Operador"
    ]
)

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Administradores",
        total_admin
    )

with col2:

    st.metric(
        "Operadores",
        total_operadores
    )
