import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from calendar import monthrange
from urllib.parse import quote

st.title("👥 Gestão de Clientes")

ARQ = Path("clientes.json")

if not ARQ.exists():
    ARQ.write_text("[]", encoding="utf-8")

clientes = json.loads(
    ARQ.read_text(encoding="utf-8")
)

# =====================================
# PESQUISA
# =====================================

st.subheader("🔍 Pesquisa")

pesquisa = st.text_input(
    "Pesquisar por nome, whatsapp ou usuário IPTV"
)

# =====================================
# CADASTRO
# =====================================

with st.expander("➕ Cadastrar Cliente", expanded=False):

    with st.form("novo_cliente"):

        nome = st.text_input("Nome")

        whatsapp = st.text_input("WhatsApp")

        usuario = st.text_input("Usuário IPTV")

        senha = st.text_input("Senha IPTV")

        valor = st.number_input(
            "Valor Mensal",
            min_value=0.0,
            step=1.0
        )

        data = st.date_input(
            "Data de Criação"
        )

        observacao = st.text_area(
            "Observações"
        )

        cadastrar = st.form_submit_button(
            "Cadastrar Cliente"
        )

        if cadastrar:

            mes = data.month + 1
            ano = data.year

            if mes > 12:
                mes = 1
                ano += 1

            dia = min(
                data.day,
                monthrange(ano, mes)[1]
            )

            vencimento = datetime(
                ano,
                mes,
                dia
            ).strftime("%d/%m/%Y")

            clientes.append({

                "nome": nome,
                "whatsapp": whatsapp,
                "usuario": usuario,
                "senha": senha,
                "valor": valor,
                "observacao": observacao,
                "vencimento": vencimento,
                "status": "Pendente"

            })

            ARQ.write_text(
                json.dumps(
                    clientes,
                    indent=4,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            st.success(
                "Cliente cadastrado com sucesso."
            )

            st.rerun()

# =====================================
# LISTAGEM
# =====================================

st.divider()

st.subheader("📋 Clientes")

hoje = datetime.now().date()

clientes_filtrados = []

for cliente in clientes:

    texto = (
        cliente["nome"]
        + cliente["whatsapp"]
        + cliente["usuario"]
    ).lower()

    if pesquisa.lower() in texto:
        clientes_filtrados.append(cliente)

if not clientes_filtrados:

    st.warning(
        "Nenhum cliente encontrado."
    )

for i, cliente in enumerate(clientes_filtrados):

    try:

        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (
            vencimento - hoje
        ).days

        if dias < 0:

            status_cor = "🔴 Vencido"

        elif dias <= 2:

            status_cor = "🟡 Vencendo"

        else:

            status_cor = "🟢 Em Dia"

    except:

        status_cor = "⚪"

    with st.container():

        col1, col2 = st.columns(
            [5, 2]
        )

        with col1:

            st.markdown(
                f"""
### {cliente['nome']}

📞 {cliente['whatsapp']}

👤 {cliente['usuario']}

💰 R$ {cliente['valor']:.2f}

📅 {cliente['vencimento']}

{status_cor}
"""
            )

        with col2:

            mensagem = quote(
                f"Olá {cliente['nome']}.\n\n"
                f"Seu acesso Vision Play TV "
                f"vence em breve.\n\n"
                f"Entre em contato para renovar."
            )

            st.link_button(
                "📲 WhatsApp",
                f"https://wa.me/55{cliente['whatsapp']}?text={mensagem}"
            )

        with st.expander(
            f"⚙️ Gerenciar {cliente['nome']}"
        ):

            novo_nome = st.text_input(
                "Nome",
                cliente["nome"],
                key=f"nome_{i}"
            )

            novo_whatsapp = st.text_input(
                "WhatsApp",
                cliente["whatsapp"],
                key=f"zap_{i}"
            )

            novo_usuario = st.text_input(
                "Usuário IPTV",
                cliente["usuario"],
                key=f"user_{i}"
            )

            nova_senha = st.text_input(
                "Senha IPTV",
                cliente["senha"],
                key=f"senha_{i}"
            )

            novo_valor = st.number_input(
                "Valor",
                value=float(
                    cliente["valor"]
                ),
                key=f"valor_{i}"
            )

            nova_obs = st.text_area(
                "Observação",
                cliente.get(
                    "observacao",
                    ""
                ),
                key=f"obs_{i}"
            )

            col_editar, col_excluir = st.columns(
                2
            )

            with col_editar:

                if st.button(
                    "💾 Salvar",
                    key=f"salvar_{i}"
                ):

                    cliente["nome"] = novo_nome
                    cliente["whatsapp"] = novo_whatsapp
                    cliente["usuario"] = novo_usuario
                    cliente["senha"] = nova_senha
                    cliente["valor"] = novo_valor
                    cliente["observacao"] = nova_obs

                    ARQ.write_text(
                        json.dumps(
                            clientes,
                            indent=4,
                            ensure_ascii=False
                        ),
                        encoding="utf-8"
                    )

                    st.success(
                        "Cliente atualizado."
                    )

                    st.rerun()

            with col_excluir:

                if st.button(
                    "🗑️ Excluir",
                    key=f"excluir_{i}"
                ):

                    clientes.remove(cliente)

                    ARQ.write_text(
                        json.dumps(
                            clientes,
                            indent=4,
                            ensure_ascii=False
                        ),
                        encoding="utf-8"
                    )

                    st.warning(
                        "Cliente removido."
                    )

                    st.rerun()

        st.divider()

# =====================================
# RESUMO
# =====================================

st.subheader("📊 Resumo")

df = pd.DataFrame(clientes)

if not df.empty:

    st.dataframe(
        df,
        use_container_width=True
    )
