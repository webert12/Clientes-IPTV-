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

    texto = st.text_area(
        "Cole usuários e senhas aqui",
        height=250
    )

    valor_padrao = st.number_input(
        "Valor Mensal",
        value=25.0,
        step=1.0
    )

    if st.button("Importar Clientes"):

        linhas = [
            l.strip()
            for l in texto.splitlines()
            if l.strip()
        ]

        novos = 0
        i = 0

        while i < len(linhas)-1:

            usuario = linhas[i]
            senha = linhas[i+1]

            hoje = datetime.now()

            mes = hoje.month + 1
            ano = hoje.year

            if mes > 12:
                mes = 1
                ano += 1

            dia = min(
                hoje.day,
                monthrange(ano, mes)[1]
            )

            vencimento = datetime(
                ano,
                mes,
                dia
            ).strftime("%d/%m/%Y")

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

        ARQ.write_text(
            json.dumps(
                clientes,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        st.success(
            f"{novos} clientes importados."
        )

        st.rerun()

# ====================================
# PESQUISA
# ====================================

st.subheader("🔍 Pesquisa")

pesquisa = st.text_input(
    "Pesquisar cliente"
)

status_filtro = st.selectbox(

    "Filtrar por Status",

    [
        "Todos",
        "Em Dia",
        "Vencendo",
        "Vencido",
        "Recebido",
        "Pendente"
    ]

)

# ====================================
# FILTRAR
# ====================================

hoje = datetime.now().date()

dados = []

for i, cliente in enumerate(clientes):

    try:

        venc = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (
            venc - hoje
        ).days

        if dias < 0:
            situacao = "Vencido"

        elif dias <= 2:
            situacao = "Vencendo"

        else:
            situacao = "Em Dia"

    except:

        situacao = "Desconhecido"

    texto = (
        cliente["nome"]
        + cliente["usuario"]
        + cliente["whatsapp"]
    ).lower()

    if pesquisa.lower() not in texto:
        continue

    if status_filtro != "Todos":

        if status_filtro in [
            "Em Dia",
            "Vencendo",
            "Vencido"
        ]:

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
# TABELA PROFISSIONAL
# ====================================

st.subheader("📋 Lista de Clientes")

if dados:

    df = pd.DataFrame(dados)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "Nenhum cliente encontrado."
    )

# ====================================
# EDIÇÃO
# ====================================

st.divider()

st.subheader("✏️ Editar Cliente")

if clientes:

    nomes = [
        c["nome"]
        for c in clientes
    ]

    selecionado = st.selectbox(
        "Selecione o Cliente",
        nomes
    )

    cliente = next(
        c
        for c in clientes
        if c["nome"] == selecionado
    )

    novo_nome = st.text_input(
        "Nome",
        cliente["nome"]
    )

    novo_whatsapp = st.text_input(
        "WhatsApp",
        cliente["whatsapp"]
    )

    novo_usuario = st.text_input(
        "Usuário IPTV",
        cliente["usuario"]
    )

    nova_senha = st.text_input(
        "Senha IPTV",
        cliente["senha"]
    )

    novo_valor = st.number_input(
        "Valor",
        value=float(
            cliente["valor"]
        )
    )

    if st.button("Salvar Alterações"):

        cliente["nome"] = novo_nome
        cliente["whatsapp"] = novo_whatsapp
        cliente["usuario"] = novo_usuario
        cliente["senha"] = nova_senha
        cliente["valor"] = novo_valor

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
