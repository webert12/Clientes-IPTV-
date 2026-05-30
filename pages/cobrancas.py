import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

st.title("📲 Central de Cobranças")

ARQ = Path("clientes.json")

if not ARQ.exists():
    ARQ.write_text("[]", encoding="utf-8")

clientes = json.loads(
    ARQ.read_text(encoding="utf-8")
)

hoje = datetime.now().date()

vencendo = []
vencidos = []

for cliente in clientes:

    try:

        vencimento = datetime.strptime(
            cliente["vencimento"],
            "%d/%m/%Y"
        ).date()

        dias = (vencimento - hoje).days

        if dias < 0:

            vencidos.append(cliente)

        elif dias <= 2:

            vencendo.append(cliente)

    except:
        pass

# ===================================
# VENCENDO
# ===================================

st.subheader("🟡 Clientes Vencendo")

if vencendo:

    for cliente in vencendo:

        whatsapp = str(
            cliente.get("whatsapp", "")
        ).replace("+", "").replace(" ", "")

        mensagem = quote(
            f"""Olá {cliente['nome']}.

Seu acesso Vision Play TV vence em breve.

📅 Vencimento: {cliente['vencimento']}

Entre em contato para renovar."""
        )

        col1, col2 = st.columns([4,1])

        with col1:

            st.info(
                f"{cliente['nome']} | {cliente['vencimento']}"
            )

        with col2:

            if whatsapp:

                st.link_button(
                    "📲",
                    f"https://wa.me/55{whatsapp}?text={mensagem}"
                )

else:

    st.success(
        "Nenhum cliente vencendo."
    )

# ===================================
# VENCIDOS
# ===================================

st.subheader("🔴 Clientes Vencidos")

if vencidos:

    for cliente in vencidos:

        whatsapp = str(
            cliente.get("whatsapp", "")
        ).replace("+", "").replace(" ", "")

        mensagem = quote(
            f"""Olá {cliente['nome']}.

Seu acesso Vision Play TV encontra-se vencido.

📅 Vencimento: {cliente['vencimento']}

Para evitar interrupções, realize a renovação."""
        )

        col1, col2 = st.columns([4,1])

        with col1:

            st.error(
                f"{cliente['nome']} | {cliente['vencimento']}"
            )

        with col2:

            if whatsapp:

                st.link_button(
                    "📲",
                    f"https://wa.me/55{whatsapp}?text={mensagem}"
                )

else:

    st.success(
        "Nenhum cliente vencido."
    )
