import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
@st.cache_resource
def get_engine():
    # Certifique-se que o DATABASE_URL está no seu Streamlit Secrets
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

def carregar_clientes():
    try:
        with engine.connect() as conn:
            query = text("SELECT data_json FROM clientes")
            result = conn.execute(query).fetchall()
            return [json.loads(r[0]) for r in result]
    except:
        return []

def salvar_no_banco(lista_clientes):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes"))
        for c in lista_clientes:
            sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

st.title("👥 Gestão de Clientes")

clientes = carregar_clientes()

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
        hoje = datetime.now()
        for linha in linhas:
            partes = linha.split()
            if len(partes) >= 3:
                a, b, c = partes[0], partes[1], " ".join(partes[2:])
                usuario, senha, nome = (a, b, c) if any(char.isdigit() for char in a) else (b, c, a)
            elif len(partes) == 2:
                usuario, senha, nome = partes[0], partes[1], partes[0]
            else: continue
            
            ano, mes = (hoje.year, hoje.month + 1) if hoje.day > 10 else (hoje.year, hoje.month)
            if mes > 12: mes, ano = 1, ano + 1
            
            clientes_novos.append({
                "nome": nome, "whatsapp": "", "usuario": usuario, "senha": senha,
                "valor": valor_padrao, "telas": 1, "observacao": "",
                "vencimento": datetime(ano, mes, 10).strftime("%d/%m/%Y"), "status": "Pendente"
            })
        clientes.extend(clientes_novos)
        salvar_no_banco(clientes)
        st.success(f"{len(clientes_novos)} clientes importados!")
        st.rerun()

# =========================
# STATUS E FILTRO
# =========================
def color_status(row):
    if "💰" in str(row["Pagamento"]): return ["background-color: #2ecc71; color: white;"] * len(row)
    if "Pendente" in str(row["Pagamento"]): return ["background-color: #f1c40f; color: black;"] * len(row)
    return [""] * len(row)

st.subheader("🔍 Pesquisa")
pesquisa = st.text_input("Pesquisar cliente")
status_filtro = st.selectbox("Filtrar", ["Todos", "Em Dia", "Vencendo", "Vencido", "Recebido", "Pendente"])
hoje = datetime.now().date()
dados = []

for i, c in enumerate(clientes):
    try:
        venc = datetime.strptime(c["vencimento"], "%d/%m/%Y").date()
        dias = (venc - hoje).days
        situacao = "Vencido" if dias < 0 else ("Vencendo" if dias <= 2 else "Em Dia")
    except: situacao = "Desconhecido"
    
    if pesquisa.lower() in (c["nome"] + c["usuario"] + c["whatsapp"]).lower():
        if status_filtro == "Todos" or (situacao == status_filtro if status_filtro in ["Em Dia", "Vencendo", "Vencido"] else c["status"] == status_filtro):
            dados.append({"ID": i, "Nome": c["nome"], "WhatsApp": c["whatsapp"], "Usuário IPTV": c["usuario"], "Valor": f"R$ {c['valor']:.2f}", "Telas": c.get("telas", 1), "Vencimento": c["vencimento"], "Status": situacao, "Pagamento": "💰 Recebido" if c["status"] == "Recebido" else "⏳ Pendente"})

st.subheader("📋 Lista de Clientes")
if dados:
    st.dataframe(pd.DataFrame(dados).style.apply(color_status, axis=1), use_container_width=True, hide_index=True)
else:
    st.warning("Nenhum cliente encontrado.")

# =========================
# AÇÕES (COBRANÇA, EXCLUSÃO, EDIÇÃO, PAGAMENTO)
# =========================
# (Aplique a lógica abaixo nos respectivos botões do seu código original)
if st.button("Salvar Edição/Pagamento"):
    salvar_no_banco(clientes)
    st.success("Alterações salvas!")
    st.rerun()
