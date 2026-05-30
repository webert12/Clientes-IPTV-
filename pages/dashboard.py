import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

st.set_page_config(layout="wide")

st.title("📊 Dashboard Gerencial")

ARQ = Path("clientes.json")

if not ARQ.exists():
    ARQ.write_text("[]", encoding="utf-8")

clientes = json.loads(
    ARQ.read_text(encoding="utf-8")
)

hoje = datetime.now().date()

total_clientes = len(clientes)

ativos = 0
vencendo = 0
vencidos = 0

receita_prevista = 0
receita_recebida = 0
receita_pendente = 0

for cliente in clientes:

    try:

        valor = float(cliente.get("valor", 0))

        receita_prevista += valor

        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (vencimento - hoje).days

        if dias < 0:

            vencidos += 1
            receita_pendente += valor

        elif dias <= 2:

            vencendo += 1
            receita_pendente += valor

        else:

            ativos += 1

        if cliente.get("status") == "Recebido":

            receita_recebida += valor

    except:
        pass

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "👥 Clientes",
        total_clientes
    )

with col2:
    st.metric(
        "🟢 Ativos",
        ativos
    )

with col3:
    st.metric(
        "🟡 Vencendo",
        vencendo
    )

with col4:
    st.metric(
        "🔴 Vencidos",
        vencidos
    )

st.divider()

col5, col6, col7 = st.columns(3)

with col5:
    st.metric(
        "💰 Receita Prevista",
        f"R$ {receita_prevista:,.2f}"
    )

with col6:
    st.metric(
        "✅ Recebido",
        f"R$ {receita_recebida:,.2f}"
    )

with col7:
    st.metric(
        "⚠️ Pendente",
        f"R$ {receita_pendente:,.2f}"
    )

st.divider()

st.subheader("📈 Clientes por Status")

dados_status = pd.DataFrame({
    "Status": [
        "Ativos",
        "Vencendo",
        "Vencidos"
    ],
    "Quantidade": [
        ativos,
        vencendo,
        vencidos
    ]
})

st.bar_chart(
    dados_status.set_index("Status")
)

st.divider()

st.subheader("💰 Receita")

dados_receita = pd.DataFrame({
    "Categoria": [
        "Prevista",
        "Recebida",
        "Pendente"
    ],
    "Valor": [
        receita_prevista,
        receita_recebida,
        receita_pendente
    ]
})

st.bar_chart(
    dados_receita.set_index("Categoria")
)

st.divider()

st.subheader("⚠️ Clientes que Exigem Atenção")

lista_alertas = []

for cliente in clientes:

    try:

        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (vencimento - hoje).days

        if dias <= 2:

            lista_alertas.append({
                "Cliente": cliente["nome"],
                "Vencimento": cliente["vencimento"],
                "Dias": dias
            })

    except:
        pass

if lista_alertas:

    st.dataframe(
        pd.DataFrame(lista_alertas),
        use_container_width=True
    )

else:

    st.success(
        "Nenhum cliente próximo do vencimento."
    )
