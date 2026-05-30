import streamlit as st, json
from pathlib import Path
from datetime import datetime

st.title("📊 Dashboard")

arq = Path("clientes.json")
if not arq.exists():
    arq.write_text("[]", encoding="utf-8")

clientes = json.loads(arq.read_text(encoding="utf-8"))

total = len(clientes)
vencidos = 0
vence2 = 0

hoje = datetime.now().date()

for c in clientes:
    try:
        venc = datetime.strptime(c["vencimento"], "%d/%m/%Y").date()
        dias = (venc - hoje).days
        if dias < 0:
            vencidos += 1
        if dias <= 2 and dias >= 0:
            vence2 += 1
    except:
        pass

c1,c2,c3 = st.columns(3)
c1.metric("Clientes", total)
c2.metric("Vencidos", vencidos)
c3.metric("Vence em até 2 dias", vence2)
