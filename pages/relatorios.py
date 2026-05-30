import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

st.title("📄 Relatórios")

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

# ======================================
# RESUMO GERAL
# ======================================

st.subheader("📊 Resumo Geral")

total_clientes = len(clientes)

receita_total = sum(
    float(
        c.get(
            "valor",
            0
        )
    )
    for c in clientes
)

receita_recebida = sum(
    float(
        h.get(
            "valor",
            0
        )
    )
    for h in historico
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Clientes",
        total_clientes
    )

with col2:

    st.metric(
        "Receita Prevista",
        f"R$ {receita_total:.2f}"
    )

with col3:

    st.metric(
        "Recebido",
        f"R$ {receita_recebida:.2f}"
    )

st.divider()

# ======================================
# CLIENTES
# ======================================

st.subheader("👥 Relatório de Clientes")

df_clientes = pd.DataFrame(
    clientes
)

if not df_clientes.empty:

    st.dataframe(
        df_clientes,
        use_container_width=True
    )

    excel_clientes = (
        df_clientes.to_csv(
            index=False
        )
    )

    st.download_button(
        "⬇️ Baixar Clientes CSV",
        excel_clientes,
        file_name="clientes.csv",
        mime="text/csv"
    )

else:

    st.info(
        "Nenhum cliente cadastrado."
    )

st.divider()

# ======================================
# HISTÓRICO
# ======================================

st.subheader(
    "💰 Histórico Financeiro"
)

df_historico = pd.DataFrame(
    historico
)

if not df_historico.empty:

    st.dataframe(
        df_historico,
        use_container_width=True
    )

    excel_historico = (
        df_historico.to_csv(
            index=False
        )
    )

    st.download_button(
        "⬇️ Baixar Financeiro CSV",
        excel_historico,
        file_name="financeiro.csv",
        mime="text/csv"
    )

else:

    st.info(
        "Nenhum recebimento registrado."
    )

st.divider()

# ======================================
# CLIENTES VENCIDOS
# ======================================

st.subheader(
    "🔴 Clientes Vencidos"
)

hoje = datetime.now().date()

vencidos = []

for cliente in clientes:

    try:

        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        if vencimento < hoje:

            vencidos.append(
                cliente
            )

    except:
        pass

if vencidos:

    df_vencidos = pd.DataFrame(
        vencidos
    )

    st.dataframe(
        df_vencidos,
        use_container_width=True
    )

    csv_vencidos = (
        df_vencidos.to_csv(
            index=False
        )
    )

    st.download_button(
        "⬇️ Baixar Vencidos CSV",
        csv_vencidos,
        file_name="clientes_vencidos.csv",
        mime="text/csv"
    )

else:

    st.success(
        "Nenhum cliente vencido."
    )

st.divider()

# ======================================
# CLIENTES VENCENDO
# ======================================

st.subheader(
    "🟡 Vencendo em até 2 dias"
)

vencendo = []

for cliente in clientes:

    try:

        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (
            vencimento - hoje
        ).days

        if dias <= 2 and dias >= 0:

            vencendo.append(
                cliente
            )

    except:
        pass

if vencendo:

    df_vencendo = pd.DataFrame(
        vencendo
    )

    st.dataframe(
        df_vencendo,
        use_container_width=True
    )

else:

    st.success(
        "Nenhum cliente próximo do vencimento."
    )

st.divider()

# ======================================
# EXPORTAÇÃO GERAL
# ======================================

st.subheader(
    "📥 Backup Geral"
)

backup = {

    "clientes": clientes,
    "historico": historico,
    "exportado_em": datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

}

st.download_button(

    "📦 Baixar Backup JSON",

    data=json.dumps(
        backup,
        indent=4,
        ensure_ascii=False
    ),

    file_name="backup_sistema.json",

    mime="application/json"

)
