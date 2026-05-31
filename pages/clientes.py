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

# ====================================
# IMPORTAÇÃO EM MASSA
# ====================================

with st.expander("📥 Importar Clientes em Massa"):

    texto = st.text_area("Cole usuários e senhas aqui", height=250)
    valor_padrao = st.number_input("Valor Mensal", value=25.0, step=1.0)

    if st.button("Importar Clientes"):

        linhas = [l.strip() for l in texto.splitlines() if l.strip()]

        novos = 0
        i = 0

        while i < len(linhas) - 1:

            usuario = linhas[i]
            senha = linhas[i + 1]

            hoje = datetime.now()

            mes = hoje.month + 1
            ano = hoje.year

            if mes > 12:
                mes = 1
                ano += 1

            dia = min(hoje.day, monthrange(ano, mes)[1])

            vencimento = datetime(ano, mes, dia).strftime("%d/%m/%Y")

            clientes.append({
                "nome": usuario,
                "whatsapp": "",
                "usuario": usuario,
                "senha": senha,
                "valor": valor_padrao,
                "observacao": "",
                "vencimento": vencimento,
                "status": "Pendente"
            })

            novos += 1
            i += 2

        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success(f"{novos} clientes importados.")
        st.rerun()

# ====================================
# STATUS FORMATADO (NOVA MELHORIA)
# ====================================

def format_status(row):

    if row["Pagamento"] == "Recebido":
        return ["background-color: #2ecc71; color: white;"] * len(row)

    if row["Pagamento"] == "Pendente":
        return ["background-color: #f1c40f; color: black;"] * len(row)

    if row["Status"] == "Vencido":
        return ["background-color: #e74c3c; color: white;"] * len(row)

    if row["Status"] == "Em Dia":
        return ["background-color: #3498db; color: white;"] * len(row)

    return [""] * len(row)

# ====================================
# PESQUISA
# ====================================

st.subheader("🔍 Pesquisa")

pesquisa = st.text_input("Pesquisar cliente")

status_filtro = st.selectbox(
    "Filtrar por Status",
    ["Todos", "Em Dia", "Vencendo", "Vencido", "Recebido", "Pendente"]
)

# ====================================
# FILTRAR
# ====================================

hoje = datetime.now().date()
dados = []

for i, cliente in enumerate(clientes):

    try:
        venc = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (venc - hoje).days

        if dias < 0:
            situacao = "Vencido"
        elif dias <= 2:
            situacao = "Vencendo"
        else:
            situacao = "Em Dia"

    except:
        situacao = "Desconhecido"

    texto = (cliente["nome"] + cliente["usuario"] + cliente["whatsapp"]).lower()

    if pesquisa.lower() not in texto:
        continue

    if status_filtro != "Todos":

        if status_filtro in ["Em Dia", "Vencendo", "Vencido"]:

            if situacao != status_filtro:
                continue

        else:

            if cliente["status"] != status_filtro:
                continue

    # ÍCONES AUTOMÁTICOS
    if cliente["status"] == "Recebido":
        pagamento = "💰 Recebido"
    elif cliente["status"] == "Pendente":
        pagamento = "⏳ Pendente"
    else:
        pagamento = cliente["status"]

    dados.append({
        "ID": i,
        "Nome": cliente["nome"],
        "WhatsApp": cliente["whatsapp"],
        "Usuário IPTV": cliente["usuario"],
        "Valor": f"R$ {cliente['valor']:.2f}",
        "Vencimento": cliente["vencimento"],
        "Status": situacao,
        "Pagamento": pagamento
    })

# ====================================
# TABELA PROFISSIONAL (VISUAL PREMIUM)
# ====================================

st.subheader("📋 Lista de Clientes")

if dados:

    df = pd.DataFrame(dados)

    styled = df.style.apply(format_status, axis=1)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Nenhum cliente encontrado.")

# ====================================
# EDIÇÃO
# ====================================

st.divider()

with st.expander("✏️ Editar Cliente", expanded=False):

    if clientes:

        nomes = [c["nome"] for c in clientes]

        selecionado = st.selectbox("Selecione o Cliente", nomes)

        cliente = next(c for c in clientes if c["nome"] == selecionado)

        novo_nome = st.text_input("Nome", cliente["nome"])
        novo_whatsapp = st.text_input("WhatsApp", cliente["whatsapp"])
        novo_usuario = st.text_input("Usuário IPTV", cliente["usuario"])
        nova_senha = st.text_input("Senha IPTV", cliente["senha"])
        novo_valor = st.number_input("Valor", value=float(cliente["valor"]))

        if st.button("Salvar Alterações"):

            cliente.update({
                "nome": novo_nome,
                "whatsapp": novo_whatsapp,
                "usuario": novo_usuario,
                "senha": nova_senha,
                "valor": novo_valor
            })

            ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

            st.success("Cliente atualizado.")
            st.rerun()

# ====================================
# AÇÕES DO CLIENTE
# ====================================

st.divider()

st.subheader("⚙️ Ações do Cliente")

if clientes:

    nomes_clientes = [c["nome"] for c in clientes]

    cliente_acao_nome = st.selectbox("Selecionar Cliente", nomes_clientes, key="acoes_cliente")

    cliente_acao = next(c for c in clientes if c["nome"] == cliente_acao_nome)

    col1, col2, col3 = st.columns(3)

    with col1:

        whatsapp = str(cliente_acao.get("whatsapp", "")).replace("+", "").replace(" ", "")

        mensagem = (
            f"Olá {cliente_acao['nome']}.\n\n"
            f"Seu acesso Vision Play TV vence em breve.\n\n"
            f"Entre em contato para renovar."
        )

        if whatsapp:
            st.link_button("📲 WhatsApp", f"https://wa.me/55{whatsapp}?text={mensagem}")

    with col2:

        if st.button("💵 Receber Pagamento"):

            vencimento = datetime.strptime(cliente_acao["vencimento"], "%d/%m/%Y")

            mes = vencimento.month + 1
            ano = vencimento.year

            if mes > 12:
                mes = 1
                ano += 1

            dia = min(vencimento.day, monthrange(ano, mes)[1])

            novo_vencimento = datetime(ano, mes, dia)

            cliente_acao["vencimento"] = novo_vencimento.strftime("%d/%m/%Y")
            cliente_acao["status"] = "Recebido"

            ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

            st.success("Pagamento confirmado.")
            st.rerun()

    with col3:

        confirmar = st.checkbox("Confirmar exclusão")

        if confirmar:

            if st.button("🗑️ Excluir Cliente"):

                clientes.remove(cliente_acao)

                ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

                st.warning("Cliente removido.")
                st.rerun()

# ====================================
# EXCLUSÃO EM MASSA DE CLIENTES
# ====================================

st.divider()

st.subheader("🗑️ Exclusão em Massa de Clientes")

if clientes:

    st.write("Selecione os clientes que deseja excluir:")

    # cria lista de seleção
    selecionados = []

    for i, c in enumerate(clientes):

        col1, col2 = st.columns([0.1, 0.9])

        with col1:
            marcado = st.checkbox("", key=f"del_{i}")

        with col2:
            st.write(f"👤 {c['nome']} | 📱 {c.get('whatsapp','')} | 💰 {c.get('status')}")

        if marcado:
            selecionados.append(c)

    if selecionados:

        st.warning(f"{len(selecionados)} cliente(s) selecionado(s) para exclusão")

        if st.button("🗑️ Excluir Selecionados"):

            for c in selecionados:
                if c in clientes:
                    clientes.remove(c)

            ARQ.write_text(
                json.dumps(clientes, indent=4, ensure_ascii=False),
                encoding="utf-8"
            )

            st.success("Clientes excluídos com sucesso.")
            st.rerun()

# ====================================
# COBRAR TODOS (CORRIGIDO FINAL)
# ====================================

st.divider()

st.subheader("📣 Cobrança em Massa")

def mensagem_cobranca(nome):
    return (
        f"Olá {nome} 👋\n\n"
        f"Identificamos que seu acesso está pendente.\n"
        f"Solicitamos a regularização para evitar bloqueio.\n\n"
        f"Qualquer dúvida, estamos à disposição."
    )

if clientes:

    if st.button("📲 Gerar Lista de Cobrança"):

        inadimplentes = []

        hoje = datetime.now().date()

        for c in clientes:

            try:
                venc = datetime.strptime(c["vencimento"], "%d/%m/%Y").date()

                if venc < hoje or c["status"] == "Pendente":
                    inadimplentes.append(c)

            except:
                continue

        st.session_state["cobranca"] = inadimplentes

# ====================================
# LISTA GERADA
# ====================================

if "cobranca" in st.session_state:

    lista = st.session_state["cobranca"]

    st.success(f"{len(lista)} clientes na fila de cobrança")

    col1, col2 = st.columns(2)

    # BOTÃO NOVO: ABRIR EM MASSA (SEQUENCIAL)
    with col1:

        if st.button("🚀 Abrir cobranças em sequência"):

            for c in lista:

                whatsapp = str(c.get("whatsapp", "")).replace("+", "").replace(" ", "")

                if whatsapp:

                    msg = mensagem_cobranca(c["nome"])

                    st.markdown(
                        f"👉 https://wa.me/55{whatsapp}?text={msg}"
                    )

    # LIMPAR LISTA
    with col2:

        if st.button("🧹 Limpar Lista"):
            del st.session_state["cobranca"]
            st.rerun()

    st.divider()

    # BOTÕES INDIVIDUAIS (FALLBACK)
    for c in lista:

        whatsapp = str(c.get("whatsapp", "")).replace("+", "").replace(" ", "")

        if whatsapp:

            msg = mensagem_cobranca(c["nome"])

            st.link_button(
                f"📲 Cobrar {c['nome']}",
                f"https://wa.me/55{whatsapp}?text={msg}"
            )
        st.rerun()

# ====================================
# CADASTRO INDIVIDUAL
# ====================================

st.divider()

with st.expander("➕ Cadastrar Cliente", expanded=False):

    with st.form("cadastro_cliente"):

        nome = st.text_input("Nome")
        whatsapp = st.text_input("WhatsApp")
        usuario = st.text_input("Usuário IPTV")
        senha = st.text_input("Senha IPTV")

        valor = st.number_input(
            "Valor Mensal",
            min_value=0.0,
            value=25.0,
            step=1.0
        )

        vencimento = st.date_input("Data de Vencimento")
        observacao = st.text_area("Observações")

        cadastrar = st.form_submit_button("Cadastrar Cliente")

    if cadastrar:

        clientes.append({
            "nome": nome,
            "whatsapp": whatsapp,
            "usuario": usuario,
            "senha": senha,
            "valor": valor,
            "observacao": observacao,
            "vencimento": vencimento.strftime("%d/%m/%Y"),
            "status": "Pendente"
        })

        ARQ.write_text(json.dumps(clientes, indent=4, ensure_ascii=False), encoding="utf-8")

        st.success("Cliente cadastrado com sucesso.")
        st.rerun()
