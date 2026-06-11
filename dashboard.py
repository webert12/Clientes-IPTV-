import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Configuração da página - Mantendo oculta por padrão para usar o layout customizado
st.set_page_config(page_title="Vision Play TV", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ULTRA REFORÇADO CONTRA FALHAS VISUAIS EM DISPOSITIVOS MÓVEIS ---
st.markdown("""
    <style>
    /* 1. APAGAR TOTALMENTE A BARRA CINZA SUPERIOR E ELEMENTOS DO GITHUB/DEPLOY */
    header, [data-testid="stHeader"], .stAppHeader, [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* 2. REPOSICIONAR AS SETAS DO MENU LATERAL (>>) PERTO DO TÍTULO */
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        visibility: visible !important;
        position: absolute !important;
        top: 15px !important;
        left: 15px !important;
        z-index: 99999 !important;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* 3. FUNDO DO APLICATIVO EM TOM ESCURO SÓLIDO */
    .stApp { background-color: #0b0f19 !important; }
    
    /* 4. TÍTULOS, TEXTOS E LABELS COM MÁXIMA NITIDEZ */
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 800 !important; }
    p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] p { color: #f1f5f9 !important; font-size: 16px !important; font-weight: 600 !important; }
    
    /* 5. CORREÇÃO COMPLETA DAS CAIXAS DE SELEÇÃO (SELECTBOX / DROPDOWN TEXTO INVISÍVEL) */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #64748b !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        color: #ffffff !important;
    }
    
    /* Opções internas do menu suspenso ao clicar no celular */
    div[data-baseweb="popover"] div[role="listbox"], div[role="listbox"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    div[role="listbox"] li, [data-baseweb="select"] li {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    div[role="listbox"] li:hover, [data-baseweb="select"] li:hover {
        background-color: #334155 !important;
    }

    /* 6. CORREÇÃO DOS TEXTOS DO POPOVER (MENU DO SISTEMA CORES) */
    div[data-testid="stPopover"] button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: 2px solid #ffffff !important;
        border-radius: 6px !important;
    }
    div[data-testid="stPopover"] button p {
        color: #ffffff !important;
    }
    div[data-baseweb="popover"] {
        background-color: #1e293b !important;
        border: 2px solid #475569 !important;
    }
    div[data-baseweb="popover"] * {
        color: #ffffff !important;
    }

    /* 7. INPUTS GERAIS E REMOÇÃO DO AUTOFILL DO NAVEGADOR */
    input, textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #64748b !important;
    }
    input:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 100px #1e293b inset !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* 8. ESTILIZAÇÃO DOS BOTÕES OPERACIONAIS DO SISTEMA */
    .stButton > button, [data-testid="stFormSubmitButton"] button { 
        background-color: #2563eb !important; 
        color: #ffffff !important; 
        font-weight: bold !important;
        border: 2px solid #ffffff !important;
        border-radius: 6px !important;
    }
    
    /* 9. LAYOUT DOS BLOCOS DE MÉTRICAS */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; 
        padding: 18px !important; 
        border-radius: 10px !important; 
        border: 2px solid #475569 !important; 
    }
    [data-testid="stMetricValue"] > div { color: #38bdf8 !important; font-weight: 800 !important; font-size: 26px !important; }
    [data-testid="stMetricLabel"] > div { color: #cbd5e1 !important; font-weight: bold !important; }
    
    /* 10. ESTILO DAS ABAS */
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b !important; 
        color: #ffffff !important; 
        border: 2px solid #475569 !important;
        border-radius: 6px 6px 0 0 !important;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #2563eb !important; 
        border-color: #ffffff !important;
    }
    
    /* Customização da Sidebar quando estiver aberta */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 2px solid #334155 !important;
    }

    /* 11. GARANTIR VISIBILIDADE ABSOLUTA DE TEXTOS DENTRO DE TABELAS */
    table, tr, td, th {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Configuração do Fuso Horário de Brasília
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(CORRETO_FUSO)
hoje = agora_br.date()

# ======================================
# CONEXÃO SEGURA COM O BANCO DE DADOS
# ======================================
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], poolclass=NullPool)

engine = get_engine()

def inicializar_banco():
    with engine.begin() as conn:
        # Tabela de Usuários / Revendedores
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
        conn.execute(text("UPDATE vision_clientes SET usuario_owner = 'admin' WHERE usuario_owner IS NULL OR TRIM(usuario_owner) = '';"))
        
        # Tabela de Histórico Financeiro
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
# CONTROLADOR DE LOGIN E ACESSO
# ======================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_role"] = ""

if not st.session_state["logado"]:
    st.markdown("<style>[data-testid='stMainBlockContainer'] { max-width: 520px !important; margin: 0 auto !important; padding-top: 6rem !important; }</style>", unsafe_allow_html=True)
    with st.form("form_login", clear_on_submit=True):
        st.markdown("<h2 style='text-align: center;'>🔒 Vision Play TV</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #cbd5e1 !important;'>Insira suas credenciais</p>", unsafe_allow_html=True)
        user_input = st.text_input("Usuário:").strip().lower()
        pass_input = st.text_input("Senha:", type="password").strip()
        if st.form_submit_button("Entrar no Sistema", use_container_width=True):
            with engine.connect() as conn:
                row = conn.execute(text("SELECT username, role, status, vencimento_usuario FROM vision_usuarios WHERE TRIM(LOWER(username)) = :u AND TRIM(password) = :p"), {"u": user_input, "p": pass_input}).mappings().fetchone()
                if row:
                    if str(row["status"]).strip() == "Bloqueado":
                        st.error("🚫 Conta bloqueada!")
                    else:
                        st.session_state["logado"] = True
                        st.session_state["usuario_nome"] = str(row["username"]).strip().lower()
                        st.session_state["usuario_role"] = str(row["role"]).strip()
                        st.rerun()
                else: st.error("Credenciais incorretas.")
    st.stop()

USUARIO_LOGADO = st.session_state["usuario_nome"]
ROLE_LOGADO = st.session_state["usuario_role"]

# --- LATERAL INFORMATIVA CORRIGIDA ---
with st.sidebar:
    st.markdown("## 📋 Menu Vision Play")
    st.markdown(f"👤 **Usuário:** `{USUARIO_LOGADO}`")
    st.markdown(f"🎖️ **Nível:** `{ROLE_LOGADO}`")
    st.divider()
    if st.button("🚪 Desconectar", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- HEADER COM O TÍTULO E RETORNO DO BOTÃO DE CONFIGURAÇÕES (POPOVER) ---
col_titulo, col_menu = st.columns([3, 1])
with col_titulo:
    st.markdown("<h1 style='padding-left: 55px; margin-top: -10px;'>📊 Dashboard Vision Play TV</h1>", unsafe_allow_html=True)

with col_menu:
    # Retorno do Botão de Menu com as Configurações originais via Popover solicitado
    with st.popover("⚙️ Configurações", use_container_width=True):
        st.markdown("<h4 style='margin:0; padding:0;'>Ajustes Globais</h4>", unsafe_allow_html=True)
        st.divider()
        if ROLE_LOGADO == "ADM":
            if st.button("🔄 Sincronizar Banco", use_container_width=True, key="pop_sync"):
                st.rerun()
        if st.button("🚪 Sair do Sistema", use_container_width=True, key="pop_sair"):
            st.session_state.clear()
            st.rerun()

def carregar_dados_privados(dono_da_conta):
    with engine.connect() as conn:
        # Uso do .mappings() para blindagem total contra nomes invisíveis ou desalinhados
        res_clientes = conn.execute(text("SELECT nome, whatsapp, vencimento, status, valor, telas FROM vision_clientes WHERE TRIM(LOWER(COALESCE(usuario_owner, 'admin'))) = TRIM(LOWER(:u)) ORDER BY nome"), {"u": dono_da_conta}).mappings().fetchall()
        res_historico = conn.execute(text("SELECT cliente, valor, data FROM vision_historico WHERE TRIM(LOWER(COALESCE(usuario_owner, 'admin'))) = TRIM(LOWER(:u)) ORDER BY id ASC"), {"u": dono_da_conta}).mappings().fetchall()
        
        return [
            {
                "nome": r["nome"], 
                "whatsapp": r["whatsapp"], 
                "vencimento": r["vencimento"], 
                "status": r["status"], 
                "valor": float(r["valor"] or 0), 
                "telas": int(r["telas"] or 1)
            } for r in res_clientes
        ], [
            {
                "cliente": r["cliente"], 
                "valor": float(r["valor"] or 0), 
                "data": r["data"]
            } for r in res_historico
        ]

clientes, historico = carregar_dados_privados(USUARIO_LOGADO)

# CÁLCULOS DOS CONTADORES DO PAINEL
total_clientes = len(clientes)
em_dia, vencendo, vencidos = 0, 0, 0
receita_prevista, receita_recebida = 0, 0

# Variáveis para cálculo financeiro preciso do gráfico de pizza
valor_pago = 0.0
valor_vencido = 0.0
valor_a_vencer = 0.0

for cl in clientes:
    receita_prevista += cl["valor"]
    status_limpo = str(cl["status"]).strip().lower()
    
    if status_limpo in ["em dia", "recebido", "pago"]:
        valor_pago += cl["valor"]
    elif status_limpo in ["vencido", "vencidos"]:
        valor_vencido += cl["valor"]
    else:
        valor_a_vencer += cl["valor"]

    try:
        v_dt = datetime.strptime(cl["vencimento"], "%d/%m/%Y").date()
        dias = (v_dt - hoje).days
        if dias < 0: vencidos += 1
        elif dias <= 2: vencendo += 1
        else: em_dia += 1
    except: em_dia += 1

for item in historico: receita_recebida += item["valor"]
receita_pendente = max(0.0, receita_prevista - receita_recebida)

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Seus Clientes", total_clientes)
    c2.metric("💰 Sua Previsão", f"R$ {receita_prevista:.2f}")
    c3.metric("✅ Seu Recebido", f"R$ {receita_recebida:.2f}")
    c4.metric("⚠️ Seu Pendente", f"R$ {receita_pendente:.2f}")

st.divider()

# --- GRÁFICOS EM PIZZA TRANSPARENTES ---
col1, col2 = st.columns(2)
with col1:
    if total_clientes > 0:
        df_cli = pd.DataFrame({"Status": ["Em Dia", "Vencendo", "Vencidos"], "Qtd": [em_dia, vencendo, vencidos]})
        df_cli = df_cli[df_cli["Qtd"] > 0]
        fig_cli = px.pie(df_cli, names="Status", values="Qtd", title="Situação dos Clientes (Quantidade)",
                         color="Status", color_discrete_map={"Em Dia": "#10b981", "Vencendo": "#f59e0b", "Vencidos": "#ef4444"})
        fig_cli.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', title_font_color='#ffffff', legend_font_color='#ffffff')
        st.plotly_chart(fig_cli, use_container_width=True, config={'displayModeBar': False})
    else: st.info("Nenhum cliente para gerar gráfico.")

with col2:
    if receita_prevista > 0:
        df_fin = pd.DataFrame({
            "Tipo": ["Pago", "Vencido", "A Vencer"], 
            "Valor": [valor_pago, valor_vencido, valor_a_vencer]
        })
        df_fin = df_fin[df_fin["Valor"] > 0]
        fig_fin = px.pie(df_fin, names="Tipo", values="Valor", title="Divisão Financeira (R$)",
                         color="Tipo", color_discrete_map={"Pago": "#10b981", "Vencido": "#ef4444", "A Vencer": "#f59e0b"})
        fig_fin.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#ffffff', title_font_color='#ffffff', legend_font_color='#ffffff')
        st.plotly_chart(fig_fin, use_container_width=True, config={'displayModeBar': False})
    else: st.info("Financeiro zerado.")

st.divider()

# --- TABELA COMPACTA COM CORREÇÃO E BLINDAGEM DE COR DOS NOMES ---
st.subheader("📋 Lista de Clientes e Situação")
with st.expander("👁️ Clique para Abrir / Esconder a Lista de Clientes", expanded=False):
    if clientes:
        html_table = '<div style="overflow-x:auto; background-color: #111827; padding: 6px; border-radius: 8px; border: 2px solid #334155;"><table style="width:100%; border-collapse: collapse; text-align: left;"><thead><tr style="background-color: #1e293b; border-bottom: 2px solid #64748b;"><th style="padding: 8px; color: #ffffff !important; font-size: 14px; font-weight: bold;">Nome</th><th style="padding: 8px; color: #ffffff !important; font-size: 14px; font-weight: bold;">WhatsApp</th><th style="padding: 8px; color: #ffffff !important; font-size: 14px; font-weight: bold;">Vencimento</th><th style="padding: 8px; color: #ffffff !important; font-size: 14px; font-weight: bold;">Status</th><th style="padding: 8px; color: #ffffff !important; font-size: 14px; font-weight: bold;">Valor</th><th style="padding: 8px; color: #ffffff !important; font-size: 14px; font-weight: bold;">Telas</th></tr></thead><tbody>'
        for c in clientes:
            status_limpo = str(c["status"]).strip().lower()
            
            if status_limpo in ["em dia", "recebido", "pago"]:
                bg = "#065f46"  
            elif status_limpo in ["vencido", "vencidos"]:
                bg = "#991b1b"  
            else:
                bg = "#854d0e"  
                
            # Estilo inline "color: #ffffff !important" reforçado em cada célula para máxima nitidez
            html_table += f'<tr style="background-color: {bg}; border-bottom: 1px solid #475569;">'
            html_table += f'<td style="padding: 8px; color: #ffffff !important; font-weight: bold; font-size: 14px;">{c["nome"]}</td>'
            html_table += f'<td style="padding: 8px; color: #ffffff !important; font-size: 14px;">{c["whatsapp"]}</td>'
            html_table += f'<td style="padding: 8px; color: #ffffff !important; font-size: 14px;">{c["vencimento"]}</td>'
            html_table += f'<td style="padding: 8px; color: #ffffff !important; font-size: 14px;">{c["status"]}</td>'
            html_table += f'<td style="padding: 8px; color: #ffffff !important; font-size: 14px;">R$ {c["valor"]:.2f}</td>'
            html_table += f'<td style="padding: 8px; color: #ffffff !important; font-size: 14px;">{c["telas"]}</td>'
            html_table += '</tr>'
            
        html_table += "</tbody></table></div>"
        st.markdown(html_table, unsafe_allow_html=True)
    else: st.info("Nenhum cliente cadastrado.")

st.divider()

# ======================================
# ABAS DE GESTÃO E CONTEÚDOS COMPLETOS
# ======================================
st.subheader("⚙️ Gerenciamento do Sistema")
abas_disponiveis = ["💵 Registrar Pagamento", "➕ Novo Cliente", "✏️ Editar / Excluir"]
if ROLE_LOGADO == "ADM": abas_disponiveis.append("👤 Painel ADM (Contas)")
abas = st.tabs(abas_disponiveis)

with abas[0]:
    if clientes:
        sel = st.selectbox("Escolha o Cliente para pagar:", [c["nome"] for c in clientes], key="sb_p")
        cli = next(c for c in clientes if c["nome"] == sel)
        st.write(f"💰 Valor da mensalidade: **R$ {cli['valor']:.2f}**")
        if st.button("⚡ Confirmar Pagamento", use_container_width=True):
            prox_venc = (datetime.strptime(cli["vencimento"], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
            with engine.begin() as conn:
                conn.execute(text("UPDATE vision_clientes SET status = 'Em Dia', vencimento = :v WHERE nome = :n AND usuario_owner = :o"), {"v": prox_venc, "n": cli["nome"], "o": USUARIO_LOGADO})
                conn.execute(text("INSERT INTO vision_historico (cliente, valor, data, usuario_owner) VALUES (:c, :v, :d, :o)"), {"c": cli["nome"], "v": cli["valor"], "d": agora_br.strftime("%d/%m/%Y %H:%M"), "o": USUARIO_LOGADO})
            st.success("Pagamento registrado com sucesso!")
            st.rerun()
    else: st.info("Sem clientes.")

with abas[1]:
    with st.form("f_cad", clear_on_submit=True):
        n_nome = st.text_input("Nome do Cliente:")
        n_whats = st.text_input("WhatsApp:")
        n_venc = st.text_input("Vencimento (DD/MM/AAAA):", value=hoje.strftime("10/%m/%Y"))
        n_status = st.selectbox("Status:", ["Em Dia", "Vencendo", "Vencidos"])
        n_telas = st.number_input("Quantidade de Telas:", min_value=1, value=1)
        n_val = st.number_input("Valor da Mensalidade:", min_value=0.0, value=25.0)
        if st.form_submit_button("➕ Salvar Cliente", use_container_width=True):
            if n_nome.strip():
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas, usuario_owner) VALUES (:n, :w, :v, :s, :val, :t, :o)"), {"n": n_nome.strip(), "w": n_whats.strip(), "v": n_venc.strip(), "s": n_status, "val": n_val, "t": int(n_telas), "o": USUARIO_LOGADO})
                st.success("Cliente salvo!")
                st.rerun()

with abas[2]:
    if clientes:
        sel_ed = st.selectbox("Selecione quem deseja alterar:", [c["nome"] for c in clientes], key="sb_e")
        cli_ed = next(c for c in clientes if c["nome"] == sel_ed)
        with st.form("f_ed"):
            e_w = st.text_input("WhatsApp:", value=cli_ed["whatsapp"])
            e_v = st.text_input("Vencimento:", value=cli_ed["vencimento"])
            e_s = st.selectbox("Status:", ["Em Dia", "Vencendo", "Vencidos"], index=["Em Dia", "Vencendo", "Vencidos"].index(cli_ed["status"]) if cli_ed["status"] in ["Em Dia", "Vencendo", "Vencidos"] else 0)
            e_t = st.number_input("Telas:", min_value=1, value=int(cli_ed["telas"]))
            e_val = st.number_input("Valor:", min_value=0.0, value=cli_ed["valor"])
            c_b1, c_b2 = st.columns(2)
            if c_b1.form_submit_button("💾 Atualizar", use_container_width=True):
                with engine.begin() as conn:
                    conn.execute(text("UPDATE vision_clientes SET whatsapp=:w, vencimento=:v, status=:s, valor=:val, telas=:t WHERE nome=:n AND usuario_owner=:o"), {"w": e_w, "v": e_v, "s": e_s, "val": e_val, "t": int(e_t), "n": cli_ed["nome"], "o": USUARIO_LOGADO})
                st.rerun()
            if c_b2.form_submit_button("🚨 Excluir", use_container_width=True):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM vision_clientes WHERE nome=:n AND usuario_owner=:o"), {"n": cli_ed["nome"], "o": USUARIO_LOGADO})
                st.rerun()

if ROLE_LOGADO == "ADM":
    with abas[3]:
        st.subheader("Gerenciar Revendedores / Usuários")
        with st.form("f_new_usr", clear_on_submit=True):
            u_nome = st.text_input("Login:").strip().lower()
            u_pass = st.text_input("Senha:").strip()
            u_role = st.selectbox("Nível de Acesso:", ["USER", "ADM"])
            u_dias = st.number_input("Dias de Vencimento da Conta:", min_value=1, value=30)
            if st.form_submit_button("Criar Nova Conta", use_container_width=True):
                venc = (hoje + timedelta(days=u_dias)).strftime("%d/%m/%Y")
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO vision_usuarios (username, password, role, status, tipo_conta, vencimento_usuario) VALUES (:u, :p, :r, 'Ativo', 'Final', :v)"), {"u": u_nome, "p": u_pass, "r": u_role, "v": venc})
                    st.success("Conta revendedor adicionada!")
                    st.rerun()
                except: st.error("Este login já existe.")
        st.divider()
        with engine.connect() as conn:
            df_users = pd.DataFrame(conn.execute(text("SELECT id, username, password, role, status, vencimento_usuario FROM vision_usuarios")).mappings().fetchall())
        if not df_users.empty:
            html_users = '<div style="overflow-x:auto; background-color: #111827; padding: 12px; border-radius: 8px; border: 2px solid #334155;"><table style="width:100%; border-collapse: collapse; text-align: left;"><thead><tr style="background-color: #1e293b; border-bottom: 2px solid #475569;"><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">ID</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Usuário</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Senha</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Nível</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Status</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Vencimento</th></tr></thead><tbody>'
            for idx, row in df_users.iterrows():
                html_users += f'<tr style="border-bottom: 1px solid #334155; background-color: #1e293b;"><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{row["id"]}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{row["username"]}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{row["password"]}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{row["role"]}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{row["status"]}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{row["vencimento_usuario"]}</td></tr>'
            html_users += "</tbody></table></div>"
            st.markdown(html_users, unsafe_allow_html=True)

st.divider()

# --- HISTÓRICO RECOLHIDO ---
st.subheader("💵 Seus Últimos Recebimentos")
with st.expander("👁️ Clique para Abrir / Esconder o Histórico de Recebimentos", expanded=False):
    if historico:
        html_hist = '<div style="overflow-x:auto; background-color: #111827; padding: 8px; border-radius: 8px; border: 2px solid #334155;"><table style="width:100%; border-collapse: collapse; text-align: left;"><thead><tr style="background-color: #1e293b; border-bottom: 2px solid #475569;"><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Cliente</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Valor</th><th style="padding: 6px; color: #ffffff !important; font-weight: bold;">Data</th></tr></thead><tbody>'
        for item in list(reversed(historico))[:10]:
            html_hist += f'<tr style="border-bottom: 1px solid #334155; background-color: #1e293b;"><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{item["cliente"]}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">R$ {item["valor"]:.2f}</td><td style="padding: 6px; color: #ffffff !important; font-weight: 600;">{item["data"]}</td></tr>'
        html_hist += "</tbody></table></div>"
        st.markdown(html_hist, unsafe_allow_html=True)
    else: 
        st.info("Nenhum registro seu encontrado.")
