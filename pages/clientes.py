import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

st.title("👥 Gestão de Clientes")

ARQ = Path("clientes.json")

if not ARQ.exists():
    ARQ.write_text("[]", encoding="utf-8")


# 🔥 FUNÇÃO PARA CARREGAR SEMPRE ATUALIZADO
def carregar_clientes():
    return json.loads(ARQ.read_text(encoding="utf-8"))


def salvar_clientes(clientes):
    ARQ.write_text(
        json.dumps(clientes, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


clientes = carregar_clientes()

# controle da exclusão em massa (OCULTO POR PADRÃO)
if "show_delete" not in st.session_state:
    st.session_state["show_delete"] = False


# =========================
# IMPORTAÇÃO EM MASSA
# =========================
with st.expander("📥 Importar Clientes em Massa (Inteligente)"):

    texto = st.text_area("Cole usuários / senhas / nomes", height=300)
    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)

    if st.button("Processar Importação"):

        linhas = [l.strip() for l in texto.splitlines() if l.strip()]

        clientes_novos = []
        tabela_preview = []

        hoje = datetime.now()

        for linha in linhas:

            partes = linha.split()

            nome = ""
            usuario = ""
            senha = ""

            if len(partes) >= 3:
                a, b, c = partes[0], partes[1], " ".join(partes[2:])

                if any(char.isdigit() for char in a):
                    usuario = a
                    senha = b
                    nome = c
                else:
                    nome = a
                    usuario = b
                    senha = c

            elif len(partes) == 2:
                usuario = partes[0]
                senha = partes[1]
                nome = partes[0]
            else:
                continue

            ano = hoje.year
            mes = hoje.month

            if hoje.day > 10:
                mes += 1
                if mes > 12:
                    mes = 1
                    ano += 1

            vencimento = datetime(ano, mes, 10)

            clientes_novos.append({
                "nome": nome,
                "whatsapp": "",
                "usuario": usuario,
                "senha": senha,
                "valor": valor_padrao,
                "telas": 1,
                "observacao": "",
                "vencimento": vencimento.strftime("%d/%m/%Y"),
                "status": "Pendente"
            })

            tabela_preview.append({
                "Nome": nome,
                "Usuário": usuario,
                "Senha": senha,
                "Telas": 1
            })

        clientes.extend(clientes_novos)
        salvar_clientes(clientes)

        st.success(f"{len(clientes_novos)} clientes importados!")
        st.rerun()


# =========================
# STATUS
# =========================
def color_status(row):

    if "💰" in str(row["Pagamento"]):
        return ["background-color: #2ecc71; color: white;"] * len(row)

    if "Pendente" in str(row["Pagamento"]):
        return ["background-color: #f1c40f; color: black;"] * len(row)

    return [""] * len(row)


# =========================
# FILTRO
# =========================
st.subheader("🔍 Pesquisa")

pesquisa = st.text_input("Pesquisar cliente")

status_filtro = st.selectbox(
    "Filtrar",
    ["Todos", "Em Dia", "Vencendo", "Vencido", "Recebido", "Pendente"]
)

hoje = datetime.now().date()

clientes = carregar_clientes()

dados = []

# =========================
# CONSTRUÇÃO DOS DADOS
# =========================
for i, c in enumerate(clientes):

    try:
        venc = datetime.strptime(c["vencimento"], "%d/%m/%Y").date()
        dias = (venc - hoje).days

        if dias < 0:
            situacao = "Vencido"
        elif dias <= 2:
            situacao = "Vencendo"
        else:
            situacao = "Em Dia"
    except:
        situacao = "Desconhecido"

    texto = (c["nome"] + c["usuario"] + c["whatsapp"]).lower()

    if pesquisa.lower() not in texto:
        continue

    if status_filtro != "Todos":
        if status_filtro in ["Em Dia", "Vencendo", "Vencido"]:
            if situacao != status_filtro:
                continue
        else:
            if c["status"] != status_filtro:
                continue

    pagamento = "💰 Recebido" if c["status"] == "Recebido" else "⏳ Pendente"

    dados.append({
        "ID": i,
        "Nome": c["nome"],
        "WhatsApp": c["whatsapp"],
        "Usuário IPTV": c["usuario"],
        "Valor": f"R$ {c.get('valor',0):.2f}",
        "Telas": c.get("telas", 1),
        "Vencimento": c["vencimento"],
        "Status": situacao,
        "Pagamento": pagamento
    })


# =========================
# LISTA COM BOTÃO DE CONFIRMAR
# =========================
st.subheader("📋 Lista de Clientes")

if dados:

    for row in dados:

        i = row["ID"]

        col1, col2, col3, col4, col5, col6, col7 = st.columns([2,2,2,2,2,2,1])

        with col1:
            st.write(row["Nome"])

        with col2:
            st.write(row["WhatsApp"])

        with col3:
            st.write(row["Usuário IPTV"])

        with col4:
            st.write(row["Valor"])

        with col5:
            st.write(row["Telas"])

        with col6:
            st.write(row["Pagamento"])

        with col7:
            if st.button("✔", key=f"pay_{i}"):

                clientes[i]["status"] = "Recebido"

                hoje = datetime.now()
                ano = hoje.year
                mes = hoje.month

                if hoje.day > 10:
                    mes += 1
                    if mes > 12:
                        mes = 1
                        ano += 1

                clientes[i]["vencimento"] = datetime(ano, mes, 10).strftime("%d/%m/%Y")

                salvar_clientes(clientes)
                st.success(f"{row['Nome']} confirmado!")
                st.rerun()

else:
    st.warning("Nenhum cliente encontrado.")
