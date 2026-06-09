import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo # Define o fuso horário padrão (Python 3.9+)
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool # Evita o cacheamento de conexões do banco

st.title("📊 Dashboard Vision Play TV")

# Configuração do Fuso Horário de Brasília
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(CORRETO_FUSO)
hoje = agora_br.date()

# Botão de atualização manual no topo para garantir o sincronismo instantâneo
if st.sidebar.button("🔄 Atualizar Dados do Banco"):
    st.cache_resource.clear()
    st.rerun()

# ======================================
# CONEXÃO SEGURA COM O SUPABASE (VIA SECRETS)
# ======================================
@st.cache_resource
def get_engine():
    # Usamos 'NullPool' para forçar o Streamlit a buscar os dados mais recentes do Supabase a cada clique
    return create_engine(st.secrets["DATABASE_URL"], poolclass=NullPool)

engine = get_engine()

# Criação automática das tabelas persistentes no Supabase
def inicializar_banco():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE,
                whatsapp VARCHAR(255),
                vencimento VARCHAR(50),
                status VARCHAR(50),
                valor NUMERIC(10, 2)
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_historico (
                id SERIAL PRIMARY KEY,
                cliente VARCHAR(255),
                valor NUMERIC(10, 2),
                data VARCHAR(50)
            );
        """))

inicializar_banco()

# Sistema de migração automática
def migrar_dados_locais_para_supabase():
    with engine.connect() as conn:
        total_banco = conn.execute(text("SELECT COUNT(*) FROM vision_clientes")).scalar()
    
    if total_banco == 0:
        ARQ_CLIENTES = Path("clientes.json")
        ARQ_HISTORICO = Path("historico.json")
        
        if ARQ_CLIENTES.exists():
            try:
                dados_c = json.loads(ARQ_CLIENTES.read_text(encoding="utf-8"))
                with engine.begin() as conn:
                    for c in dados_c:
                        conn.execute(text("""
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor)
                            ON CONFLICT (nome) DO NOTHING
                        """), {
                            "nome": c.get("nome", ""),
                            "whatsapp": c.get("whatsapp", ""),
                            "vencimento": c.get("vencimento", ""),
                            "status": c.get("status", ""),
                            "valor": float(c.get("valor", 0))
                        })
            except:
                pass
                
        if ARQ_HISTORICO.exists():
            try:
                dados_h = json.loads(ARQ_HISTORICO.read_text(encoding="utf-8"))
                with engine.begin() as conn:
                    for h in dados_h:
                        conn.execute(text("""
                            INSERT INTO vision_historico (cliente, valor, data)
                            VALUES (:cliente, :valor, :data)
                        """), {
                            "cliente": h.get("cliente", ""),
                            "valor": float(h.get("valor", 0)),
                            "data": h.get("data", "")
                        })
            except:
                pass

migrar_dados_locais_para_supabase()

# Carregar dados diretamente do Supabase em tempo real
def carregar_dados_supabase():
    with engine.connect() as conn:
        res_clientes = conn.execute(text("SELECT nome, whatsapp, vencimento, status, valor FROM vision_clientes ORDER BY nome")).fetchall()
        res_historico = conn.execute(text("SELECT cliente, valor, data FROM vision_historico ORDER BY id ASC")).fetchall()
        
        lista_clientes = []
        for r in res_clientes:
            lista_clientes.append({
                "nome": r[0],
                "whatsapp": r[1],
                "vencimento": r[2],
                "status": r[3],
                "valor": float(r[4] if r[4] is not None else 0)
            })
            
        lista_historico = []
        for r in res_historico:
            lista_historico.append({
                "cliente": r[0],
                "valor": float(r[1] if r[1] is not None else 0),
                "data": r[2]
            })
            
        return lista_clientes, lista_historico

# Carrega os dados reais e ATUALIZADOS do banco de dados
clientes, historico = carregar_dados_supabase()

# ======================================
# LÓGICA DE PROCESSAMENTO DO DASHBOARD
# ======================================
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
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
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
    receita_recebida += float(item.get("valor", 0))

receita_pendente = receita_prevista - receita_recebida

# ==========================
# CARDS
# ==========================
c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 Clientes", total_clientes)
c2.metric("💰 Previsto", f"R$ {receita_prevista:.2f}")
c3.metric("✅ Recebido", f"R$ {receita_recebida:.2f}")
c4.metric("⚠️ Pendente", f"R$ {receita_pendente:.2f}")

st.divider()

# ==========================
# GRÁFICOS
# ==========================
col1, col2 = st.columns(2)

with col1:
    df_status = pd.DataFrame({
        "Status": ["Em Dia", "Vencendo", "Vencidos"],
        "Quantidade": [em_dia, vencendo, vencidos]
    })
    fig = px.pie(df_status, names="Status", values="Quantidade", title="Clientes")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_financeiro = pd.DataFrame({
        "Tipo": ["Recebido", "Pendente"],
        "Valor": [receita_recebida, receita_pendente]
    })
    fig2 = px.pie(df_financeiro, names="Tipo", values="Valor", title="Financeiro")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ==========================
# CLIENTES VENCENDO
# ==========================
st.subheader("⚠️ Clientes Próximos do Vencimento")
alertas = []

for cliente in clientes:
    try:
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (vencimento - hoje).days

        if dias <= 2:
            alertas.append({
                "Nome": cliente["nome"],
                "WhatsApp": cliente["whatsapp"],
                "Vencimento": cliente["vencimento"]
            })
    except:
        pass

if alertas:
    st.dataframe(pd.DataFrame(alertas), use_container_width=True, hide_index=True)
else:
    st.success("Nenhum cliente próximo do vencimento.")

# =========================
# RECEBER PAGAMENTO (AÇÕES)
# =========================
st.divider()
st.subheader("⚙️ Ações")

if clientes:
    nomes = [c["nome"] for c in clientes]
    sel = st.selectbox("Escolha o Cliente para registrar o pagamento:", nomes)
    cli = next(c for c in clientes if c["nome"] == sel)

    # Captura o valor cadastrado atualizado do cliente no banco
    valor_cadastrado = float(cli.get("valor", 25.00))
    
    # Campo profissional para conferir/alterar o valor pago (puxa o valor do banco automaticamente)
    valor_pago = st.number_input(f"Confirmar valor do pagamento para {cli['nome']} (R$):", min_value=0.0, value=valor_cadastrado, step=5.0)

    if st.button("💵 Confirmar Recebimento"):
        agora = datetime.now(CORRETO_FUSO)
        ano = agora.year
        mes = agora.month

        if agora.day > 10:
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        novo_vencimento = datetime(ano, mes, 10).strftime("%d/%m/%Y")
        data_historico = agora.strftime("%d/%m/%Y %H:%M")

        # Atualiza o cliente e insere o histórico com o valor dinâmico correto
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE vision_clientes 
                SET status = 'Recebido', vencimento = :vencimento 
                WHERE nome = :nome
            """), {"vencimento": novo_vencimento, "nome": cli["nome"]})

            conn.execute(text("""
                INSERT INTO vision_historico (cliente, valor, data) 
                VALUES (:cliente, :valor, :data)
            """), {"cliente": cli["nome"], "valor": valor_pago, "data": data_historico})

        st.success(f"Pagamento de R$ {valor_pago:.2f} confirmado para {cli['nome']} com Sucesso!")
        st.cache_resource.clear()
        st.rerun()

# ==========================
# ÚLTIMOS RECEBIMENTOS
# ==========================
st.subheader("💵 Últimos Recebimentos")

if historico:
    ultimos = list(reversed(historico))[:10]
    st.dataframe(pd.DataFrame(ultimos), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum recebimento registrado.")

# ======================================
# EXPORTAÇÃO GERAL (BACKUP)
# ======================================
st.subheader("📥 Backup Geral")
backup = {
    "clientes": clientes,
    "historico": historico,
    "exportado_em": datetime.now(CORRETO_FUSO).strftime("%d/%m/%Y %H:%M:%S")
}

st.download_button(
    "📦 Baixar Backup JSON",
    data=json.dumps(backup, indent=4, ensure_ascii=False),
    file_name="backup_sistema.json",
    mime="application/json"
)
