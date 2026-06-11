import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Configuração da página
st.set_page_config(page_title="Vision Play TV", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA TRANSPARÊNCIA 100% E CORREÇÃO CRÍTICA DE VISIBILIDADE ---
st.markdown("""
    <style>
    /* Ocultar completamente o cabeçalho padrão, menu nativo, deploy e ícones do GitHub */
    .stAppHeader, [data-testid="stHeader"], [data-testid="stAppDeployButton"], #MainMenu { 
        display: none !important; 
    }
    
    /* Ocultar permanentemente a barra lateral nativa e as setas de controle */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"], .collapsedControl { 
        display: none !important; 
    }
    
    /* Ajuste de espaçamento superior devido à remoção do cabeçalho */
    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
    }

    /* Fundo Geral do App */
    .stApp { background-color: #0b0f19 !important; }
    
    /* Forçar cores de textos e títulos específicos */
    h1, h2, h3, h4, p, label, .stMetric label { 
        color: #ffffff !important; 
    }
    
    /* Botões - 100% Transparentes com Bordas Destacadas */
    button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-formSubmit"] { 
        background-color: transparent !important; 
        color: #ffffff !important; 
        font-weight: bold !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 8px !important;
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }
    button:hover {
        background-color: rgba(59, 130, 246, 0.2) !important;
        border-color: #60a5fa !important;
    }
    
    /* CORREÇÃO CRÍTICA DE VISIBILIDADE DOS INPUTS */
    input, textarea, [data-baseweb="select"] {
        background-color: #131a2c !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextArea textarea { 
        background-color: #131a2c !important; 
        color: #ffffff !important; 
        -webkit-text-fill-color: #ffffff !important;
        border: 1px solid #3b82f6 !important; 
        border-radius: 8px !important;
    }
    
    /* Formulários 100% Transparentes */
    div[data-testid="stForm"] {
        background-color: transparent !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
    }
    
    /* CORREÇÃO DO POPOVER (MENU) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-testid="stPopoverBody"] {
        background-color: #0b0f19 !important;
        background: #0b0f19 !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }
    
    /* Dropdowns de Opções */
    ul[data-baseweb="menu"], 
    li[role="option"] {
        background-color: #0b0f19 !important;
        color: #ffffff !important;
    }
    li[role="option"]:hover {
        background-color: #3b82f6 !important;
    }

    /* Métricas 100% Transparentes */
    [data-testid="stMetric"] { 
        background-color: transparent !important; 
        padding: 15px !important; 
        border-radius: 10px !important; 
        border: 2px solid #3b82f6 !important; 
    }
    
    /* Abas (Tabs) 100% Transparentes */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: transparent !important; 
        gap: 10px; 
    }
    .stTabs [data-baseweb="tab"] { 
        background-color: transparent !important; 
        color: #ffffff !important; 
        border: 1px solid transparent !important;
    }
    .stTabs [aria-selected="true"] { 
        background-color: rgba(59, 130, 246, 0.2) !important; 
        color: #ffffff !important; 
        border: 2px solid #3b82f6 !important;
        border-radius: 6px !important;
    }

    /* CORREÇÃO CRÍTICA DA TABELA */
    div[data-testid="stDataFrame"], 
    div[data-testid="stDataFrame"] > div {
        background-color: transparent !important;
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
            [data-testid="stMainBlockContainer"] {
                max-width: 520px !important;
                margin: 0 auto !important;
                padding-top: 8rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("form_login", clear_on_submit=True):
        st.markdown("<h2 style='text-align: center;'>🔒 Vision Play TV</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #ffffff !important; font-size: 14px;'>Insira suas credenciais</h4>", unsafe_allow_html=True)
        
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

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "dashboard"

menu_opcoes = st.popover("📋 Menu", use_container_width=False)
menu_opcoes.markdown("### 📋 Menu Principal")
menu_opcoes.markdown(f"👤 **Usuário:** `{USUARIO_LOGADO}`")
menu_opcoes.markdown(f"🎖️ **Nível:** `{ROLE_LOGADO}`")
menu_opcoes.divider()

if menu_opcoes.button("👥 Clientes", use_container_width=True, key=f"nav_cli_{USUARIO_LOGADO}"):
    st.session_state["pagina_atual"] = "clientes"
    st.rerun()

if menu_opcoes.button("📊 Dashboard", use_container_width=True, key=f"nav_dash_{USUARIO_LOGADO}"):
    st.session_state["pagina_atual"] = "dashboard"
    st.rerun()

menu_opcoes.divider()

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

@st.dialog("🧹 Zerar Período")
def abrir_popup_limpeza():
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
            st.rerun()

if ROLE_LOGADO == "ADM":
    if menu_opcoes.button("🔄 Sincronizar Banco", use_container_width=True, key=f"sync_{USUARIO_LOGADO}"):
        st.rerun()

if menu_opcoes.button("🧹 Limpar Histórico", use_container_width=True, key=f"clean_{USUARIO_LOGADO}"):
    abrir_popup_limpeza()

if menu_opcoes.button("🚪 Sair", use_container_width=True, key=f"exit_{USUARIO_LOGADO}"):
    st.session_state.clear()
    st.rerun()

# CÁLCULOS DO PAINEL
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

# ==============================================================================
# RENDERIZAÇÃO CONDICIONAL DE TELAS
# ==============================================================================

if st.session_state["pagina_atual"] == "dashboard":
    st.title("📊 Dashboard Vision Play TV")
    
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
    st.subheader("💵 Seus Últimos Recebimentos")
    if historico: st.dataframe(pd.DataFrame(list(reversed(historico))[:10]), use_container_width=True, hide_index=True)
    else: st.info("Nenhum registro seu.")

elif st.session_state["pagina_atual"] == "clientes":
    st.title("👥 Gerenciamento de Clientes")
    
    st.subheader("📋 Status Geral de Pagamentos")
    if clientes:
        df_status = pd.DataFrame(clientes)[["nome", "status", "vencimento"]]
        df_status.columns = ["Nome do Cliente", "Status Atual", "Vencimento"]
        
        def aplicar_cores_status(row):
            cor_pago = "background-color: rgba(16, 185, 129, 0.2); color: #10b981; font-weight: bold;"
            cor_pendente = "background-color: rgba(239, 68, 68, 0.2); color: #ef4444; font-weight: bold;"
            stilo = cor_pago if row["Status Atual"] in ["Recebido", "Em Dia"] else cor_pendente
            return [stilo] * len(row)
            
        st.dataframe(df_status.style.apply(aplicar_cores_status, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum cliente cadastrado.")

    st.divider()

    st.subheader("⚙️ Gerenciamento do Sistema")
    abas_disponiveis = ["💵 Registrar Pagamento", "➕ Novo Cliente", "🚀 Cadastro em Massa", "✏️ Editar / Excluir"]
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

    # --- NOVA ABA: CADASTRO EM MASSA ---
    with abas[2]:
        st.markdown("### 🚀 Importar Lista de Clientes em Massa")
        st.markdown("Cole os seus clientes abaixo seguindo o formato padrão: `Nome, WhatsApp` (um cliente por linha).")
        st.caption("Exemplo de formato válido:\nJoão da Silva, 5511999999999\nMaria de Souza, 5521988888888")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_venc = st.text_input("Vencimento Padrão:", value=hoje.strftime("10/%m/%Y"), key="m_venc")
            m_status = st.selectbox("Status Padrão:", ["Em Dia", "Vencendo", "Vencidos"], key="m_status")
        with col_m2:
            m_telas = st.number_input("Telas Padrão:", min_value=1, value=1, key="m_telas")
            m_valor = st.number_input("Valor Padrão (R$):", min_value=0.0, value=25.0, key="m_valor")
            
        lista_massa = st.text_area("Cole os dados aqui:", height=250, placeholder="Nome do Cliente, WhatsApp", key="txt_lista_massa")
        
        if st.button("🚀 Processar e Salvar Tudo", use_container_width=True, key="btn_salvar_massa"):
            if lista_massa.strip():
                linhas = lista_massa.strip().split("\n")
                sucessos = 0
                falhas = 0
                
                with engine.begin() as conn:
                    for linha in linhas:
                        if not linha.strip():
                            continue
                        
                        # Tenta separar por vírgula ou ponto e vírgula
                        if "," in linha:
                            partes = linha.split(",", 1)
                            nome_c = partes[0].strip()
                            whats_c = partes[1].strip()
                        elif ";" in linha:
                            partes = linha.split(";", 1)
                            nome_c = partes[0].strip()
                            whats_c = partes[1].strip()
                        else:
                            nome_c = linha.strip()
                            whats_c = ""
                            
                        if nome_c:
                            try:
                                conn.execute(text("""
                                    INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas, usuario_owner) 
                                    VALUES (:n, :w, :v, :s, :val, :t, :owner)
                                """), {
                                    "n": nome_c, 
                                    "w": whats_c, 
                                    "v": m_venc.strip(), 
                                    "s": m_status, 
                                    "val": m_valor, 
                                    "t": int(m_telas), 
                                    "owner": USUARIO_LOGADO
                                })
                                sucessos += 1
                            except:
                                falhas += 1
                                
                st.success(f"🔥 Importação finalizada! {sucessos} clientes foram adicionados com sucesso.")
                if falhas > 0:
                    st.warning(f"⚠️ {falhas} registros foram pulados (nomes repetidos ou inválidos).")
                st.rerun()
            else:
                st.error("Por favor, preencha a caixa de texto antes de salvar.")

    with abas[3]:
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

    # --- EDICÃO E EXCLUSÃO DE REVENDEDORES (PAINEL ADM) ---
    if ROLE_LOGADO == "ADM":
        with abas[4]:
            st.subheader("Gerenciar Revendedores/Usuários")
            col_u1, col_u2 = st.columns(2)
            
            with col_u1:
                st.markdown("### ➕ Criar Conta")
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
            
            with engine.connect() as conn:
                lista_usuarios = conn.execute(text("SELECT username, password, role, status, vencimento_usuario FROM vision_usuarios ORDER BY username")).mappings().fetchall()
            
            with col_u2:
                st.markdown("### ✏️ Editar / Excluir Revendedor")
                if lista_usuarios:
                    u_seletor = [usr["username"] for usr in lista_usuarios]
                    sel_usr_nome = st.selectbox("Selecione o Usuário:", u_seletor, key=f"sel_usr_{USUARIO_LOGADO}")
                    usr_ed = next(usr for usr in lista_usuarios if usr["username"] == sel_usr_nome)
                    
                    with st.form(f"f_ed_usr_{sel_usr_nome}"):
                        e_u_pass = st.text_input("Senha Atual/Nova:", value=usr_ed["password"])
                        e_u_role = st.selectbox("Nível:", ["USER", "ADM"], index=["USER", "ADM"].index(usr_ed["role"]) if usr_ed["role"] in ["USER", "ADM"] else 0)
                        e_u_status = st.selectbox("Status:", ["Ativo", "Bloqueado"], index=["Ativo", "Bloqueado"].index(usr_ed["status"]) if usr_ed["status"] in ["Ativo", "Bloqueado"] else 0)
                        e_u_venc = st.text_input("Vencimento (dd/mm/aaaa):", value=usr_ed["vencimento_usuario"])
                        
                        c_ubtn1, c_ubtn2 = st.columns(2)
                        if c_ubtn1.form_submit_button("💾 Salvar Alterações"):
                            with engine.begin() as conn:
                                conn.execute(text("""
                                    UPDATE vision_usuarios 
                                    SET password = :p, role = :r, status = :s, vencimento_usuario = :v 
                                    WHERE username = :u
                                """), {"p": e_u_pass, "r": e_u_role, "s": e_u_status, "v": e_u_venc, "u": sel_usr_nome})
                            st.success("Usuário atualizado!")
                            st.rerun()
                            
                        if c_ubtn2.form_submit_button("🚨 Deletar Conta"):
                            if sel_usr_nome == USUARIO_LOGADO:
                                st.error("Você não pode deletar a sua própria conta em uso!")
                            else:
                                with engine.begin() as conn:
                                    conn.execute(text("DELETE FROM vision_usuarios WHERE username = :u"), {"u": sel_usr_nome})
                                st.success(f"Conta '{sel_usr_nome}' removida!")
                                st.rerun()
                else:
                    st.info("Nenhum usuário cadastrado para edição.")
            
            st.divider()
            st.markdown("### 📋 Lista Geral de Contas Cadastradas")
            if lista_usuarios:
                df_users = pd.DataFrame(lista_usuarios)
                st.dataframe(df_users, hide_index=True, use_container_width=True)
