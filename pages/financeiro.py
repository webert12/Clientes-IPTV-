import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from calendar import monthrange
import pandas as pd

st.title("💰 Financeiro")

ARQ_CLIENTES = Path("clientes.json")
ARQ_HISTORICO = Path("historico.json")

if not ARQ_CLIENTES.exists():
    ARQ_CLIENTES.write_text("[]", encoding="utf-8")

if not ARQ_HISTORICO.exists():
    ARQ_HISTORICO.write_text("[]", encoding="utf-8")

clientes = json.loads(
    ARQ_CLIENTES.read_text(
        encoding="utf-8"
    )
)

historico = json.loads(
    ARQ_HISTORICO.read_text(
        encoding="utf-8"
    )
)

# =====================================
# RESUMO FINANCEIRO
# =====================================

receita_prevista = 0
receita_recebida = 0
receita_pendente = 0

for cliente in clientes:

    valor = float(
        cliente.get("valor", 0)
    )

    receita_prevista += valor

    if cliente.get("status") == "Recebido":
        receita_recebida += valor
    else:
        receita_pendente += valor

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💰 Receita Prevista",
        f"R$ {receita_prevista:.2f}"
    )

with col2:
    st.metric(
        "✅ Recebido",
        f"R$ {receita_recebida:.2f}"
    )

with col3:
    st.metric(
        "⚠️ Pendente",
        f"R$ {receita_pendente:.2f}"
    )

st.divider()

# =====================================
# RECEBIMENTOS
# =====================================

st.subheader("💵 Receber Pagamentos")

for i, cliente in enumerate(clientes):

    col1, col2 = st.columns([4, 1])

    with col1:

        st.write(
            f"""
**{cliente['nome']}**

Valor: R$ {cliente['valor']:.2f}

Vencimento: {cliente['vencimento']}

Status: {cliente['status']}
"""
        )

    with col2:

        if st.button(
            "Receber",
            key=f"receber_{i}"
        ):

            try:

                vencimento = datetime.strptime(
                    cliente["vencimento"],
                    "%d/%m/%Y"
                )

                mes = vencimento.month + 1
                ano = vencimento.year

                if mes > 12:
                    mes = 1
                    ano += 1

                dia = min(
                    vencimento.day,
                    monthrange(
                        ano,
                        mes
                    )[1]
                )

                novo_vencimento = datetime(
                    ano,
                    mes,
                    dia
                )

                cliente["vencimento"] = (
                    novo_vencimento.strftime(
                        "%d/%m/%Y"
                    )
                )

                cliente["status"] = (
                    "Recebido"
                )

                historico.append({

                    "cliente":
                        cliente["nome"],

                    "valor":
                        cliente["valor"],

                    "data":
                        datetime.now().strftime(
                            "%d/%m/%Y %H:%M"
                        ),

                    "novo_vencimento":
                        cliente["vencimento"]

                })

                ARQ_CLIENTES.write_text(
                    json.dumps(
                        clientes,
                        indent=4,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

                ARQ_HISTORICO.write_text(
                    json.dumps(
                        historico,
                        indent=4,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

                st.success(
                    f"{cliente['nome']} renovado com sucesso."
                )

                st.rerun()

            except Exception as erro:

                st.error(
                    f"Erro: {erro}"
                )

    st.divider()

# =====================================
# HISTÓRICO
# =====================================

st.subheader("📋 Histórico de Recebimentos")

if historico:

    df = pd.DataFrame(
        historico
    )

    st.dataframe(
        df,
        use_container_width=True
    )

else:

    st.info(
        "Nenhum recebimento registrado."
    )

# =====================================
# FILTRO POR CLIENTE
# =====================================

st.divider()

st.subheader("🔎 Consultar Histórico")

if historico:

    nomes = sorted(
        list(
            set(
                [
                    item["cliente"]
                    for item in historico
                ]
            )
        )
    )

    cliente_filtro = st.selectbox(
        "Selecione o Cliente",
        ["Todos"] + nomes
    )

    if cliente_filtro == "Todos":

        resultado = historico

    else:

        resultado = [

            item

            for item in historico

            if item["cliente"]
            == cliente_filtro

        ]

    st.dataframe(
        pd.DataFrame(
            resultado
        ),
        use_container_width=True
    )

# =====================================
# ESTATÍSTICAS
# =====================================

st.divider()

st.subheader("📈 Estatísticas")

total_recebimentos = len(
    historico
)

total_valores = sum(

    float(
        item.get(
            "valor",
            0
        )
    )

    for item in historico

)

col4, col5 = st.columns(2)

with col4:

    st.metric(
        "Recebimentos",
        total_recebimentos
    )

with col5:

    st.metric(
        "Total Recebido",
        f"R$ {total_valores:.2f}"
    )
