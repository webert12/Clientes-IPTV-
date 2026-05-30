import streamlit as st, json
from pathlib import Path
from datetime import datetime
from calendar import monthrange

st.title("💰 Financeiro")

arq = Path("clientes.json")
hist = Path("historico.json")

if not arq.exists():
    arq.write_text("[]", encoding="utf-8")

if not hist.exists():
    hist.write_text("[]", encoding="utf-8")

clientes = json.loads(arq.read_text(encoding="utf-8"))
historico = json.loads(hist.read_text(encoding="utf-8"))

for i,c in enumerate(clientes):
    col1,col2 = st.columns([4,1])

    with col1:
        st.write(f"{c['nome']} - Vencimento: {c['vencimento']}")

    with col2:
        if st.button("Recebido", key=i):
            venc = datetime.strptime(c["vencimento"], "%d/%m/%Y")

            mes = venc.month + 1
            ano = venc.year

            if mes > 12:
                mes = 1
                ano += 1

            dia = min(venc.day, monthrange(ano, mes)[1])

            novo = datetime(ano, mes, dia)

            c["vencimento"] = novo.strftime("%d/%m/%Y")
            c["status"] = "Recebido"

            historico.append({
                "cliente": c["nome"],
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            })

            arq.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")
            hist.write_text(json.dumps(historico, indent=4, ensure_ascii=False), encoding="utf-8")

            st.rerun()
