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

clientes = json.loads(ARQ.read_text(encoding="utf-8"))

# =========================
# IMPORTAÇÃO EM MASSA
# =========================

with st.expander("📥 Importar Clientes em Massa (Inteligente)"):
with st.expander("📥 Importar Clientes em Massa (Inteligente)"):

    texto = st.text_area(
        "Cole usuários / senhas / nomes (qualquer formato)",
        height=300
    )

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

            # =========================
            # VENCIMENTO DIA 10 CORRIGIDO
            # =========================
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
                "observacao": "",
                "vencimento": vencimento.strftime("%d/%m/%Y"),
                "status": "Pendente"
            })

            tabela_preview.append({
                "Nome": nome,
                "Usuário": usuario,
                "Senha": senha
            })

        clientes.extend(clientes_novos)

        ARQ.write_text(
            json.dumps(clientes, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        st.success(f"{len(clientes_novos)} clientes importados!")

        if tabela_preview:
            st.subheader("📋 Pré-visualização")
            st.dataframe(pd.DataFrame(tabela_preview), use_container_width=True, hide_index=True)

        st.rerun()
# =========================
# STATUS COLORIDO
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

dados = []

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
        "Valor": f"R$ {c['valor']:.2f}",
        "Vencimento": c["vencimento"],
        "Status": situacao,
        "Pagamento": pagamento
    })

# =========================
# TABELA
# =========================

st.subheader("📋 Lista de Clientes")

if dados:

    df = pd.DataFrame(dados)
    styled = df.style.apply(color_status, axis=1)

    st.dataframe(styled, use_container_width=True, hide_index=True)

else:
    st.warning("Nenhum cliente encontrado.")

# =========================
# COBRANÇA EM MASSA (WHATSAPP LIMPO)
# =========================

st.divider()
st.subheader("📣 Cobrança em Massa")

def msg(nome):
    return f"Olá {nome} 👋\n\nSeu acesso está pendente.\nRegularize por favor."

if clientes:

    if st.button("📲 Gerar Cobranças"):

        lista = []

        for c in clientes:
            try:
                venc = datetime.strptime(c["vencimento"], "%d/%m/%Y").date()
                if venc < hoje or c["status"] == "Pendente":
                    lista.append(c)
            except:
                pass

        st.session_state["cobranca"] = lista

if "cobranca" in st.session_state:

    lista = st.session_state["cobranca"]

    st.success(f"{len(lista)} clientes na cobrança")

    for c in lista:

        whatsapp = str(c.get("whatsapp", "")).replace("+", "").replace(" ", "")

        if whatsapp:
            st.link_button(
                f"📲 Cobrar {c['nome']}",
                f"https://wa.me/55{whatsapp}?text={msg(c['nome'])}"
            )

    if st.button("🧹 Limpar Lista"):
        del st.session_state["cobranca"]
        st.rerun()

# =========================
# EXCLUSÃO EM MASSA
# =========================

st.divider()
st.subheader("🗑️ Exclusão em Massa")

selecionados = []

for i, c in enumerate(clientes):
    col1, col2 = st.columns([0.1, 0.9])

    with col1:
        if st.checkbox("", key=f"del_{i}"):
            selecionados.append(c)

    with col2:
        st.write(f"{c['nome']} | {c.get('whatsapp','')}")

if selecionados:

    if st.button("🗑️ Excluir selecionados"):

        for c in selecionados:
            if c in clientes:
                clientes.remove(c)

        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success("Excluídos com sucesso")
        st.rerun()

# =========================
# EDIÇÃO
# =========================

st.divider()
st.subheader("✏️ Editar Cliente")

if clientes:

    nomes = [c["nome"] for c in clientes]
    sel = st.selectbox("Cliente", nomes)

    cli = next(c for c in clientes if c["nome"] == sel)

    cli["nome"] = st.text_input("Nome", cli["nome"])
    cli["whatsapp"] = st.text_input("WhatsApp", cli["whatsapp"])
    cli["usuario"] = st.text_input("Usuário", cli["usuario"])
    cli["senha"] = st.text_input("Senha", cli["senha"])

    if st.button("Salvar"):
        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")
        st.success("Atualizado")
        st.rerun()

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
        cli["vencimento"] = datetime(datetime.now().year, datetime.now().month, 10).strftime("%d/%m/%Y")

        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success("Pagamento confirmado")
        st.rerun()
