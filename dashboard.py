import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Configuração da página - Iniciada como collapsed para o seu botão gerenciar
st.set_page_config(page_title="Vision Play TV", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# --- CSS REENGENHARADO PARA 100% DE VISIBILIDADE E ALTO CONTRASTE ---
st.markdown("""
    <style>
    /* Ocultar o botão de menu padrão do Streamlit */
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    
    /* Fundo Geral do App */
    .stApp { background-color: #0f172a !important; }
    
    /* Títulos e Textos Principais com Contraste Máximo */
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 700 !important; }
    p, label, .stMarkdown { color: #f1f5f9 !important; font-size: 15px !important; }
    
    /* Botões Ultra Visíveis (Azul Elétrico com Borda) */
    .stButton > button { 
        background-color: #2563eb !important; 
        color: #ffffff !important; 
        font-weight: bold !important;
        border: 2px solid #60a5fa !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        border-color: #93c5fd !important;
        color: #ffffff !important;
    }
    
    /* Inputs de Texto Corrigidos */
    .stTextInput input { 
        background-color: #1e293b !important; 
        color: #ffffff !important; 
        border: 2px solid #475569 !important; 
        border-radius: 6px !important;
    }
    
    /* Caixas de Seleção (Dropdowns) Corrigidas contra texto invisível */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 2px solid #475569 !important;
    }
    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }
    /* Lista de opções do dropdown */
    ul[role="listbox"] {
        background-color: #1e293b !important;
    }
    ul[role="listbox"] li {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }
    ul[role="listbox"] li:hover {
        background-color: #334155 !important;
    }
    
    /* Blocos de Métricas Destacados */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; 
        padding: 20px !important; 
        border-radius: 10px !important; 
        border: 2px solid #334155 !important; 
    }
    [data-testid="stMetricValue"] > div { color: #38bdf8 !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] > div { color: #94a3b8 !important; font-weight: bold !important; }
    
    /* Abas Visíveis e Modernas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b !important; 
        color: #94a3b8 !important; 
        border: 1px solid #334155 !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #2563eb !important; 
        color: #ffffff !important; 
        font-weight: bold !important;
        border-color: #60a5fa !important;
    }

    /* Popover do Menu */
    div[data-testid="stPopoverBody"] {
        background-color: #1e293b !important;
        border: 2px solid #475569 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Configuração do Fuso Horário de Brasília
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(CORRETO_FUSO)
hoje = agora_br.date()

# ======================================
# CONEXÃO SEGURA COM O SUPABASE
# ======================================
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], poolclass=NullPool)

engine = get_engine()

def inicializar_banco():
    with engine.begin() as conn:
        # Tabela de Usuários
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'USER'
            );
        """))
        conn.execute(text("ALTER TABLE vision_usuarios ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Ativo';"))
        conn.execute(text("ALTER TABLE vision_usuarios ADD COLUMN IF NOT EXISTS tipo_conta VARCHAR(50) DEFAULT 'Final';"))
        conn.execute(text("ALTER TABLE vision_usuarios ADD COLUMN IF NOT EXISTS vencimento_usuario VARCHAR(50);"))
        conn.execute(text("UPDATE vision_usuarios SET vencimento_usuario = '31/12/2030' WHERE vencimento_usuario IS NULL;"))
        
        # Garante o admin padrão
        total_usuarios = conn.execute(text("SELECT COUNT(*) FROM vision_usuarios")).scalar()
        if total_usuarios == 0:
            conn.execute(text("""
                INSERT INTO vision_usuarios (username, password, role, status, tipo_conta, vencimento_usuario)
                VALUES ('admin', 'admin123', 'ADM', 'Ativo', 'Final', '31/12/2030');
            """))

        # Tabela de Clientes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255),
                whatsapp VARCHAR(255),
                vencimento VARCHAR(50),
                status VARCHAR(50),
                valor NUMERIC(10, 2)
            );
        """))
        conn.execute(text("ALTER TABLE vision_clientes ADD COLUMN IF NOT EXISTS telas INTEGER DEFAULT 1;"))
        conn.execute(text("ALTER TABLE vision_clientes ADD COLUMN IF NOT EXISTS usuario_owner VARCHAR(255) DEFAULT 'admin';"))
        
        # Garante que clientes antigos que não tinham dono (NULL) virem do 'admin'
        conn.execute(text("UPDATE vision_clientes SET usuario_owner = 'admin' WHERE usuario_owner IS NULL OR TRIM(usuario_owner) = '';"))
        
        # Tabela de Histórico
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_historico (
                id SERIAL PRIMARY KEY,
                cliente VARCHAR(255),
                valor NUMERIC(10, 2),
                data VARCHAR(50)
            );
        """))
        conn.execute(text("ALTER TABLE vision_historico ADD COLUMN IF NOT EXISTS usuario_owner VARCHAR(255) DEFAULT 'admin';"))
        conn.execute(text("UPDATE vision_historico SET usuario_owner = 'admin' WHERE usuario_owner IS NULL OR TRIM(usuario_owner) = '';"))

inicializar_banco()

# ======================================
# SISTEMA DE CONTROLE DE LOGIN E SESSÃO
# ======================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_role"] = ""

# SE NÃO ESTIVER LOGADO, MOSTRA SÓ O LOGIN
if not st.session_state["logado"]:
    st.markdown("""
        <style>
            .stAppHeader { display: none !important; }
            [data-testid="stMainBlockContainer"] {
                max-width: 520px !important;
                margin: 0 auto !important;
                padding-top: 8rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("form_login", clear_on_submit=True):
        st.markdown("<h2 style='text-align: center;'>🔒 Vision Play TV</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #f1f5f9 !important; font-size: 14px;'>Insira suas credenciais</p>", unsafe_allow_html=True)
        
        user_input = st.text_input("Usuário:").strip().lower()
        pass_input = st.text_input("Senha:", type="password").strip()
        btn_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
        
        if btn_login:
            if not user_input or not pass_input:
                st.error("Por favor, preencha todos os campos.")
            else:
                with engine.connect() as conn:
                    row = conn.execute(
                        text("""
                            SELECT username, role, status, vencimento_usuario 
                            FROM vision_usuarios 
                            WHERE TRIM(LOWER(username)) = :u AND TRIM(password) = :p
                        """), {"u": user_input, "p": pass_input}
                    ).mappings().fetchone()
                    
                    if row:
                        status_atual = str(row["status"]).strip()
                        venc_str = str(row["vencimento_usuario"]).strip()
                        role_atual = str(row["role"]).strip()
                        
                        conta_vencida = False
                        try:
                            data_venc = datetime.strptime(venc_str, "%d/%m/%Y").date()
                            if data_venc < hoje: conta_vencida = True
                        except: pass
                        
                        if status_atual == "Bloqueado" or (conta_vencida and role_atual != "ADM"):
                            st.error("🚫 Conta vencida ou bloqueada!")
                        else:
                            st.session_state["logado"] = True
                            st.session_state["usuario_nome"] = str(row["username"]).strip().lower()
                            st.session_state["usuario_role"] = role_atual
                            st.rerun()
                    else:
                        st.error("Credenciais incorretas.")
    st.stop()

# ==============================================================================
# ÁREA DO DASHBOARD
# ==============================================================================

USUARIO_LOGADO = st.session_state["usuario_nome"]
ROLE_LOGADO = st.session_state["usuario_role"]

# MENU CUSTOMIZADO
with st.popover("Menu"):
    st.markdown("### 📋 Menu Principal")
    st.markdown(f"👤 **Usuário:** `{USUARIO_LOGADO}`")
    st.markdown(f"🎖️ **Nível:** `{ROLE_LOGADO}`")
    st.divider()
    
    # Lógica do antigo sidebar dentro do popover
    if ROLE_LOGADO == "ADM":
        if st.button("🔄 Sincronizar Banco", use_container_width=True, key=f"sync_{USUARIO_LOGADO}"):
            st.rerun()

    if st.button("🧹 Limpar Histórico", use_container_width=True, key=f"clean_{USUARIO_LOGADO}"):
        st.session_state["abrir_limpeza"] = True
    
    if st.button("🚪 Sair", use_container_width=True, key=f"exit_{USUARIO_LOGADO}"):
        st.session_state.clear()
        st.rerun()

st.title("📊 Dashboard Vision Play TV")

def carregar_dados_privados(dono_da_conta):
    with engine.connect() as conn:
        res_clientes = conn.execute(text("""
            SELECT nome, whatsapp, vencimento, status, valor, telas 
            FROM vision_clientes 
            WHERE TRIM(LOWER(COALESCE(usuario_owner, 'admin'))) = TRIM(LOWER(:u)) 
            ORDER BY nome
        """), {"u": dono_da_conta}).fetchall()
        
        res_historico = conn.execute(text("""
            SELECT cliente, valor, data 
            FROM vision_historico 
            WHERE TRIM(LOWER(COALESCE(usuario_owner, 'admin'))) = TRIM(LOWER(:u)) 
            ORDER BY id ASC
        """), {"u": dono_da_conta}).fetchall()
        
        lst_clientes = [{"nome": r[0], "whatsapp": r[1], "vencimento": r[2], "status": r[3], "valor": float(r[4] or 0), "telas": int(r[5] or 1)} for r in res_clientes]
        lst_historico = [{"cliente": r[0], "valor": float(r[1] or 0), "data": r[2]} for r in res_historico]
        return lst_clientes, lst_historico

clientes, historico = carregar_dados_privados(USUARIO_LOGADO)

# Popup de Limpeza
if st.session_state.get("abrir_limpeza"):
    with st.dialog("🧹 Zerar Período"):
        st.write("Digite o **Dia/Mês** dos seus recebimentos que deseja limpar.")
        data_limpar = st.text_input("Data (Ex: 10/06 ou /06):", value=hoje.strftime("%d/%m"), key=f"inp_cl_{USUARIO_LOGADO}")
        st.warning("⚠️ Isso apagará APENAS os seus registros desta data!")

        if st.button("🔥 Confirmar", use_container_width=True, key=f"btn_cl_{USUARIO_LOGADO}"):
            if data_limpar.strip():
                with engine.begin() as conn:
                    conn.execute(text("""
                        DELETE FROM vision_historico 
                        WHERE data LIKE :padrao AND TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:owner))
                    """), {"padrao": f"%{data_limpar.strip()}%", "owner": USUARIO_LOGADO})
                st.session_state["abrir_limpeza"] = False
                st.rerun()

# ======================================
# CÁLCULOS DO PAINEL
# ======================================
total_clientes = len(clientes)
em_dia, vencendo, vencidos = 0, 0, 0
receita_prevista, receita_recebida = 0, 0

for cliente in clientes:
    receita_prevista += float(cliente.get("valor", 0))
    try:
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (vencimento - hoje).days
        if dias < 0: vencidos += 1
        elif dias <= 2: vencendo += 1
        else: em_dia += 1
    except: pass

for item in historico:
    receita_recebida += float(item.get("valor", 0))

receita_pendente = receita_prevista - receita_recebida

# CONTAINER DE MÉTRICAS
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Seus Clientes", total_clientes)
    c2.metric("💰 Sua Previsão", f"R$ {receita_prevista:.2f}")
    c3.metric("✅ Seu Recebido", f"R$ {receita_recebida:.2f}")
    c4.metric("⚠️ Seu Pendente", f"R$ {receita_pendente:.2f}")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if total_clientes > 0:
        st.plotly_chart(px.pie(pd.DataFrame({"Status": ["Em Dia", "Vencendo", "Vencidos"], "Quantidade": [em_dia, vencendo, vencidos]}), names="Status", values="Quantidade", title="Seus Clientes"), use_container_width=True)
    else:
        st.info("Nenhum cliente para gerar gráfico.")
with col2:
    if receita_prevista > 0:
        st.plotly_chart(px.pie(pd.DataFrame({"Tipo": ["Recebido", "Pendente"], "Valor": [receita_recebida, receita_pendente]}), names="Tipo", values="Valor", title="Seu Financeiro"), use_container_width=True)
    else:
        st.info("Financeiro zerado.")

st.divider()

# --- SITUAÇÃO DOS CLIENTES COM PALETA DE ALTO CONTRASTE ---
st.subheader("📋 Lista de Clientes e Situação")
if clientes:
    df_cli = pd.DataFrame(clientes)[["nome", "whatsapp", "vencimento", "status", "valor", "telas"]]
    df_cli.columns = ["Nome", "WhatsApp", "Vencimento", "Status", "Valor (R$)", "Telas"]
    
    def aplicar_cores_linhas(row):
        status = str(row["Status"]).strip().lower()
        if status in ["recebido", "em dia"]:
            # Verde esmeralda bem definido para leitura perfeita com texto branco
            return ["background-color: #065f46 !important; color: #ffffff !important; font-weight: bold; border-bottom: 1px solid #10b981;"] * len(row)
        else:
            # Laranja/âmbar queimado de alta visibilidade com texto branco
            return ["background-color: #9a3412 !important; color: #ffffff !important; font-weight: bold; border-bottom: 1px solid #f97316;"] * len(row)

    st.dataframe(df_cli.style.apply(aplicar_cores_linhas, axis=1), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum cliente cadastrado.")

st.divider()

# ABA DE GESTÃO
st.subheader("⚙️ Gerenciamento do Sistema")
abas_disponiveis = ["💵 Registrar Pagamento", "➕ Novo Cliente", "✏️ Editar / Excluir"]
if ROLE_LOGADO == "ADM": abas_disponiveis.append("👤 Painel ADM (Contas)")
abas = st.tabs(abas_disponiveis)

with abas[0]:
    if clientes:
        sel = st.selectbox("Escolha o Cliente:", [c["nome"] for c in clientes], key=f"sel_pag_{USUARIO_LOGADO}")
        cli = next(c for c in clientes if c["nome"] == sel)
        st.markdown(f"💰 **Mensalidade:** `R$ {float(cli.get('valor', 25.0)):.2f}`")
        if st.button("⚡ Confirmar Pagamento", key=f"btn_pag_{USUARIO_LOGADO}"):
            novo_mes = hoje.month + 1 if hoje.day > 10 else hoje.month
            novo_ano = hoje.year + (1 if novo_mes > 12 else 0)
            novo_mes = 1 if novo_mes > 12 else novo_mes
            novo_vencimento = datetime(novo_ano, novo_mes, 10).strftime("%d/%m/%Y")
            with engine.begin() as conn:
                conn.execute(text("UPDATE vision_clientes SET status = 'Recebido', vencimento = :vencimento WHERE nome = :nome AND TRIM(LOWER(usuario_owner)) = :owner"), {"vencimento": novo_vencimento, "nome": cli["nome"], "owner": USUARIO_LOGADO})
                conn.execute(text("INSERT INTO vision_historico (cliente, valor, data, usuario_owner) VALUES (:cliente, :valor, :data, :owner)"), {"cliente": cli["nome"], "valor": cli["valor"], "data": agora_br.strftime("%d/%m/%Y %H:%M"), "owner": USUARIO_LOGADO})
            st.success("Sucesso!")
            st.rerun()
    else: st.info("Sem clientes.")

with abas[1]:
    with st.form(f"form_cad_{USUARIO_LOGADO}", clear_on_submit=False):
        n_nome = st.text_input("Nome do Cliente:")
        n_whats = st.text_input("WhatsApp:")
        n_venc = st.text_input("Vencimento:", value=hoje.strftime("10/%m/%Y"))
        n_status = st.selectbox("Status:", ["Em Dia", "Vencendo", "Vencidos"])
        n_telas = st.number_input("Telas:", min_value=1, value=1)
        n_valor = st.number_input("Valor (R$):", min_value=0.0, value=25.0)
        if st.form_submit_button("➕ Salvar Cliente"):
            if n_nome.strip():
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas, usuario_owner) VALUES (:n, :w, :v, :s, :val, :t, :owner)"), {"n": n_nome.strip(), "w": n_whats.strip(), "v": n_venc.strip(), "s": n_status, "val": n_valor, "t": int(n_telas), "owner": USUARIO_LOGADO})
                    st.success("Salvo!")
                    st.rerun()
                except: st.error("Erro: Um cliente com esse nome já existe.")

with abas[2]:
    if clientes:
        sel_ed = st.selectbox("Selecione para editar:", [c["nome"] for c in clientes], key=f"sel_ed_{USUARIO_LOGADO}")
        cli_ed = next(c for c in clientes if c["nome"] == sel_ed)
        with st.form(f"form_ed_{USUARIO_LOGADO}"):
            e_w = st.text_input("WhatsApp:", value=cli_ed["whatsapp"])
            e_v = st.text_input("Vencimento:", value=cli_ed["vencimento"])
            e_s = st.selectbox("Status:", ["Em Dia", "Vencendo", "Vencidos"], index=["Em Dia", "Vencendo", "Vencidos"].index(cli_ed["status"]) if cli_ed["status"] in ["Em Dia", "Vencendo", "Vencidos"] else 0)
            e_t = st.number_input("Telas:", min_value=1, value=int(cli_ed.get("telas", 1)))
            e_val = st.number_input("Valor:", min_value=0.0, value=float(cli_ed["valor"]))
            c_ed1, c_ed2 = st.columns(2)
            if c_ed1.form_submit_button("💾 Atualizar"):
                with engine.begin() as conn:
                    conn.execute(text("UPDATE vision_clientes SET whatsapp=:w, vencimento=:v, status=:s, valor=:val, telas=:t WHERE nome=:n AND TRIM(LOWER(usuario_owner))=:owner"), {"w": e_w, "v": e_v, "s": e_s, "val": e_val, "t": int(e_t), "n": cli_ed["nome"], "owner": USUARIO_LOGADO})
                st.rerun()
            if c_ed2.form_submit_button("🚨 Excluir"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM vision_clientes WHERE nome=:n AND TRIM(LOWER(usuario_owner))=:owner"), {"n": cli_ed["nome"], "owner": USUARIO_LOGADO})
                st.rerun()

if ROLE_LOGADO == "ADM":
    with abas[3]:
        st.subheader("Gerenciar Revendedores/Usuários")
        with st.form(f"f_new_usr_{USUARIO_LOGADO}", clear_on_submit=True):
            u_nome = st.text_input("Login:").strip().lower()
            u_pass = st.text_input("Senha:").strip()
            u_role = st.selectbox("Nível:", ["USER", "ADM"])
            u_dias = st.number_input("Dias de Vencimento (Conta):", min_value=1, value=30)
            if st.form_submit_button("Criar Conta"):
                venc = (hoje + timedelta(days=u_dias)).strftime("%d/%m/%Y")
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO vision_usuarios (username, password, role, status, tipo_conta, vencimento_usuario) VALUES (:u, :p, :r, 'Ativo', 'Final', :v)"), {"u": u_nome, "p": u_pass, "r": u_role, "v": venc})
                    st.success("Conta criada!")
                    st.rerun()
                except: st.error("Login já existe.")
        st.divider()
        with engine.connect() as conn:
            df_users = pd.DataFrame(conn.execute(text("SELECT id, username, password, role, status, vencimento_usuario FROM vision_usuarios")).mappings().fetchall())
        if not df_users.empty: st.dataframe(df_users, hide_index=True)

st.divider()
st.subheader("💵 Seus Últimos Recebimentos")
if historico: st.dataframe(pd.DataFrame(list(reversed(historico))[:10]), use_container_width=True, hide_index=True)
else: st.info("Nenhum registro seu.")
