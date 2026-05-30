import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from calendar import monthrange

st.title("👥 Gestão de Clientes")

ARQ = Path("clientes.json")

if not ARQ.exists():
    ARQ.write_text("[]", encoding="utf-8")

clientes = json.loads(
    ARQ.read_text(encoding="utf-8")
)

# ====================================
# IMPORTAÇÃO EM MASSA
# ====================================

with st.expander("📥 Importar Clientes em Massa"):

    texto = st.text_area("Cole usuários e senhas aqui", height=250)

    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)

    if st.button("Importar Clientes"):

        linhas = [l.strip() for l in texto.splitlines() if l.strip()]

        novos = 0
        i = 0

        while i < len(linhas) - 1:

            usuario = linhas[i]
            senha = linhas[i + 1]

            hoje = datetime.now()

            mes = hoje.month + 1
            ano = hoje.year

            if mes > 12:
                mes = 1
                ano += 1

            dia = min(hoje.day, monthrange(ano, mes)[1])

            vencimento = datetime(ano, mes, dia).strftime("%d/%m/%Y")

            clientes.append({
                "nome": usuario,
                "whatsapp": "",
                "usuario": usuario,
                "senha": senha,
                "valor": valor_padrao,
                "observacao": "",
                "vencimento": vencimento,
                "status": "Pendente"
            })

            novos += 1
            i += 2

        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success(f"{novos} clientes importados.")
        st.rerun()

# ====================================
# PESQUISA
# ====================================

st.subheader("🔍 Pesquisa")

pesquisa = st.text_input("Pesquisar cliente")

status_filtro = st.selectbox(
    "Filtrar por Status",
    ["Todos", "Em Dia", "Vencendo", "Vencido", "Recebido", "Pendente"]
)

# ====================================
# FILTRAR
# ====================================

hoje = datetime.now().date()

dados = []

for i, cliente in enumerate(clientes):

    try:
        venc = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (venc - hoje).days

        if dias < 0:
            situacao = "Vencido"
        elif dias <= 2:
            situacao = "Vencendo"
        else:
            situacao = "Em Dia"

    except:
        situacao = "Desconhecido"

    texto = (cliente["nome"] + cliente["usuario"] + cliente["whatsapp"]).lower()

    if pesquisa.lower() not in texto:
        continue

    if status_filtro != "Todos":

        if status_filtro in ["Em Dia", "Vencendo", "Vencido"]:
            if situacao != status_filtro:
                continue
        else:
            if cliente["status"] != status_filtro:
                continue

    dados.append({
        "ID": i,
        "Nome": cliente["nome"],
        "WhatsApp": cliente["whatsapp"],
        "Usuário IPTV": cliente["usuario"],
        "Valor": f"R$ {cliente['valor']:.2f}",
        "Vencimento": cliente["vencimento"],
        "Status": situacao,
        "Pagamento": cliente["status"]
    })

# ====================================
# TABELA PROFISSIONAL (COM CORES)
# ====================================

st.subheader("📋 Lista de Clientes")

def color_pagamento(val):
    if val == "Recebido":
        return "background-color: #2ecc71; color: white;"
    elif val == "Pendente":
        return "background-color: #f1c40f; color: black;"
    return ""

if dados:

    df = pd.DataFrame(dados)

    styled_df = df.style.applymap(
        color_pagamento,
        subset=["Pagamento"]
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Nenhum cliente encontrado.")

# ====================================
# EDIÇÃO
# ====================================

st.divider()

with st.expander("✏️ Editar Cliente", expanded=False):

    if clientes:

        nomes = [c["nome"] for c in clientes]

        selecionado = st.selectbox("Selecione o Cliente", nomes)

        cliente = next(c for c in clientes if c["nome"] == selecionado)

        novo_nome = st.text_input("Nome", cliente["nome"])
        novo_whatsapp = st.text_input("WhatsApp", cliente["whatsapp"])
        novo_usuario = st.text_input("Usuário IPTV", cliente["usuario"])
        nova_senha = st.text_input("Senha IPTV", cliente["senha"])

        novo_valor = st.number_input("Valor", value=float(cliente["valor"]))

        if st.button("Salvar Alterações"):

            cliente["nome"] = novo_nome
            cliente["whatsapp"] = novo_whatsapp
            cliente["usuario"] = novo_usuario
            cliente["senha"] = nova_senha
            cliente["valor"] = novo_valor

            ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

            st.success("Cliente atualizado.")
            st.rerun()

# ====================================
# AÇÕES DO CLIENTE
# ====================================

st.divider()

st.subheader("⚙️ Ações do Cliente")

if clientes:

    nomes_clientes = [c["nome"] for c in clientes]

    cliente_acao_nome = st.selectbox("Selecionar Cliente", nomes_clientes, key="acoes_cliente")

    cliente_acao = next(c for c in clientes if c["nome"] == cliente_acao_nome)

    col1, col2, col3 = st.columns(3)

    with col1:

        whatsapp = str(cliente_acao.get("whatsapp", "")).replace("+", "").replace(" ", "")

        mensagem = (
            f"Olá {cliente_acao['nome']}.\n\n"
            f"Seu acesso Vision Play TV vence em breve.\n\n"
            f"Entre em contato para renovar."
        )

        if whatsapp:
            st.link_button("📲 WhatsApp", f"https://wa.me/55{whatsapp}?text={mensagem}")

    with col2:

        if st.button("💵 Receber Pagamento"):

            try:
                vencimento = datetime.strptime(cliente_acao["vencimento"], "%d/%m/%Y")

                mes = vencimento.month + 1
                ano = vencimento.year

                if mes > 12:
                    mes = 1
                    ano += 1

                dia = min(vencimento.day, monthrange(ano, mes)[1])

                novo_vencimento = datetime(ano, mes, dia)

                cliente_acao["vencimento"] = novo_vencimento.strftime("%d/%m/%Y")
                cliente_acao["status"] = "Recebido"

                ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

                st.success("Pagamento confirmado.")
                st.rerun()

            except Exception as erro:
                st.error(f"Erro: {erro}")

    with col3:

        confirmar = st.checkbox("Confirmar exclusão")

        if confirmar:

            if st.button("🗑️ Excluir Cliente"):

                clientes.remove(cliente_acao)

                ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

                st.warning("Cliente removido.")
                st.rerun()

# ====================================
# CADASTRO INDIVIDUAL
# ====================================

st.divider()

with st.expander("➕ Cadastrar Cliente", expanded=False):

    with st.form("cadastro_cliente"):

        nome = st.text_input("Nome")
        whatsapp = st.text_input("WhatsApp")
        usuario = st.text_input("Usuário IPTV")
        senha = st.text_input("Senha IPTV")

        valor = st.number_input(
            "Valor Mensal",
            min_value=0.0,
            value=25.0,
            step=1.0
        )

        vencimento = st.date_input("Data de Vencimento")
        observacao = st.text_area("Observações")

        cadastrar = st.form_submit_button("Cadastrar Cliente")

    if cadastrar:

        clientes.append({
            "nome": nome,
            "whatsapp": whatsapp,
            "usuario": usuario,
            "senha": senha,
            "valor": valor,
            "observacao": observacao,
            "vencimento": vencimento.strftime("%d/%m/%Y"),
            "status": "Pendente"
        })

        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success("Cliente cadastrado com sucesso.")
        st.rerun()
