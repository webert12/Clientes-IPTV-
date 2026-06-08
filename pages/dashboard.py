import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime

st.title("📊 Dashboard Vision Play TV")

ARQ_CLIENTES = Path("clientes.json")
ARQ_HISTORICO = Path("historico.json")

if not ARQ_CLIENTES.exists():
    ARQ_CLIENTES.write_text("[]", encoding="utf-8")

if not ARQ_HISTORICO.exists():
    ARQ_HISTORICO.write_text("[]", encoding="utf-8")

clientes = json.loads(
    ARQ_CLIENTES.read_text(encoding="utf-8")
)

historico = json.loads(
    ARQ_HISTORICO.read_text(encoding="utf-8")
)

hoje = datetime.now().date()

total_clientes = len(clientes)

em_dia = 0
vencendo = 0
vencidos = 0

receita_prevista = 0
receita_recebida = 0

for cliente in clientes:
    valor = float(cliente.get("valor", 0))
    receita_prevista += valor

    try:
        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (vencimento - hoje).days

        if dias < 0:
            vencidos += 1
        elif dias <= 2:
            vencendo += 1
        else:
            em_dia += 1
    except:
        pass

for item in historico:
    receita_recebida += float(
        item.get("valor", 0)
    )

receita_pendente = (
    receita_prevista - receita_recebida
)

# ==========================
# CARDS
# ==========================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "👥 Clientes",
    total_clientes
)

c2.metric(
    "💰 Previsto",
    f"R$ {receita_prevista:.2f}"
)

c3.metric(
    "✅ Recebido",
    f"R$ {receita_recebida:.2f}"
)

c4.metric(
    "⚠️ Pendente",
    f"R$ {receita_pendente:.2f}"
)

st.divider()

# ==========================
# GRÁFICOS
# ==========================

col1, col2 = st.columns(2)

with col1:
    df_status = pd.DataFrame({
        "Status": [
            "Em Dia",
            "Vencendo",
            "Vencidos"
        ],
        "Quantidade": [
            em_dia,
            vencendo,
            vencidos
        ]
    })

    fig = px.pie(
        df_status,
        names="Status",
        values="Quantidade",
        title="Clientes"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with col2:
    df_financeiro = pd.DataFrame({
        "Tipo": [
            "Recebido",
            "Pendente"
        ],
        "Valor": [
            receita_recebida,
            receita_pendente
        ]
    })

    fig2 = px.pie(
        df_financeiro,
        names="Tipo",
        values="Valor",
        title="Financeiro"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

st.divider()

# ==========================
# CLIENTES VENCENDO
# ==========================

st.subheader("⚠️ Clientes Próximos do Vencimento")

alertas = []

for cliente in clientes:
    try:
        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (
            vencimento - hoje
        ).days

        if dias <= 2:
            alertas.append({
                "Nome": cliente["nome"],
                "WhatsApp": cliente["whatsapp"],
                "Vencimento": cliente["vencimento"]
            })
    except:
        pass

if alertas:
    st.dataframe(
        pd.DataFrame(alertas),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success(
        "Nenhum cliente próximo do vencimento."
    )

st.divider()

# =========================
# RECEBER PAGAMENTO
# =========================

st.divider()
st.subheader("⚙️ Ações")

if clientes:
    nomes = [c["nome"] for c in clientes]
    sel = st.selectbox("Cliente ação", nomes)

    cli = next(c for c in clientes if c["nome"] == sel)

    if st.button("💵 Receber pagamento"):
        cli["status"] = "Recebido"

        agora = datetime.now()
        ano = agora.year
        mes = agora.month

        # Se passou do dia 10, joga o vencimento para o mês seguinte
        if agora.day > 10:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        cli["vencimento"] = datetime(ano, mes, 10).strftime("%d/%m/%Y")

        # Salva o cliente com a nova data de vencimento
        ARQ_CLIENTES.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        # Salva o recebimento no histórico para atualizar o gráfico financeiro
        novo_recebimento = {
            "cliente": cli["nome"],
            "valor": float(cli.get("valor", 25.00)),
            "data": agora.strftime("%d/%m/%Y %H:%M")
        }
        historico.append(novo_recebimento)
        ARQ_HISTORICO.write_text(json.dumps(historico, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success("Pagamento confirmado!")
        st.rerun()


# ==========================
# ÚLTIMOS RECEBIMENTOS
# ==========================

st.subheader("💵 Últimos Recebimentos")

if historico:
    ultimos = list(
        reversed(historico)
    )[:10]

    st.dataframe(
        pd.DataFrame(ultimos),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info(
        "Nenhum recebimento registrado."
    )
