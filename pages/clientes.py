
import streamlit as st, json
from pathlib import Path
from datetime import datetime
from calendar import monthrange

st.title("👥 Clientes")

arq = Path("clientes.json")
if not arq.exists():
    arq.write_text("[]", encoding="utf-8")

clientes = json.loads(arq.read_text(encoding="utf-8"))

with st.form("cad"):
    nome = st.text_input("Nome")
    whatsapp = st.text_input("WhatsApp")
    usuario = st.text_input("Usuário IPTV")
    senha = st.text_input("Senha IPTV")
    valor = st.number_input("Valor Mensal", min_value=0.0)
    data = st.date_input("Data de Criação")
    obs = st.text_area("Observações")

    enviar = st.form_submit_button("Cadastrar")

    if enviar:
        mes = data.month + 1
        ano = data.year
        if mes > 12:
            mes = 1
            ano += 1
        dia = min(data.day, monthrange(ano, mes)[1])

        vencimento = datetime(ano, mes, dia).strftime("%d/%m/%Y")

        clientes.append({
            "nome": nome,
            "whatsapp": whatsapp,
            "usuario": usuario,
            "senha": senha,
            "valor": valor,
            "observacao": obs,
            "vencimento": vencimento,
            "status": "Pendente"
        })

        arq.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")
        st.success("Cliente cadastrado")

st.divider()

for c in clientes:
    st.write(f"**{c['nome']}** | Vencimento: {c['vencimento']} | Status: {c['status']}")
