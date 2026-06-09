import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Configuração da página (Inicia colapsado para evitar piscadas na tela de login)
st.set_page_config(page_title="Vision Play TV", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# Configuração do Fuso Horário de Brasília
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(CORRETO_FUSO)
hoje = agora_br.date()

# ======================================
# CONEXÃO SEGURA COM O SUPABASE (VIA SECRETS)
# ======================================
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], poolclass=NullPool)

engine = get_engine()

# Criação e atualização automática das tabelas persistentes no Supabase
def inicializar_banco():
    with engine.begin() as conn:
        # 1. TABELA DE USUÁRIOS DO SISTEMA
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'USER'
            );
        """))
        
        # Cria o Administrador Padrão caso o banco esteja totalmente vazio
        total_usuarios = conn.execute(text("SELECT COUNT(*) FROM vision_usuarios")).scalar()
        if total_usuarios == 0:
            conn.execute(text("""
                INSERT INTO vision_usuarios (username, password, role)
                VALUES ('admin', 'admin123', 'ADM');
            """))

        # 2. TABELA DE CLIENTES (Com identificador de dono)
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
        conn.execute(text("ALTER TABLE vision_clientes ADD COLUMN IF NOT EXISTS telas INTEGER DEFAULT 1;"))
        conn.execute(text("ALTER TABLE vision_clientes ADD COLUMN IF NOT EXISTS usuario_owner VARCHAR(255) DEFAULT 'admin';"))
        
        # 3. TABELA DE HISTÓRICO DE PAGAMENTOS (Com identificador de dono)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_historico (
                id SERIAL PRIMARY KEY,
                cliente VARCHAR(255),
                valor NUMERIC(10, 2),
                data VARCHAR(50)
            );
        """))
        conn.execute(text("ALTER TABLE vision_historico ADD COLUMN IF NOT EXISTS usuario_owner VARCHAR(255) DEFAULT 'admin';"))

inicializar_banco()

# ======================================
# SISTEMA DE CONTROLE DE LOGIN E SESSÃO
# ======================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_role"] = ""

# SE NÃO ESTIVER LOGADO, DESTRÓI O MENU LATERAL VISUALMENTE E MOSTRA SÓ O LOGIN
if not st.session_state["logado"]:
    # CSS Avançado: Força o sumiço completo de qualquer estrutura lateral e centraliza o formulário
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; width: 0px !important; }
            [data-testid="stSidebarCollapseButton"] { display: none !important; }
            .collapsedControl { display: none !important; }
            .stAppHeader { display: none !important; }
            [data-testid="stMainBlockContainer"] {
                max-width: 520px !important;
                margin: 0 auto !important;
                padding-top: 8rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.form("form_login", clear_on_submit=False):
        st.markdown("<h2 style='text-align: center; color: #1E3A8A; margin-bottom: 0px;'>🔒 Vision Play TV</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px;'>Insira suas credenciais para acessar o painel</p>", unsafe_allow_html=True)
        st.write("")
        
        user_input = st.text_input("Usuário:").strip().lower()
        pass_input = st.text_input("Senha:", type="password").strip()
        btn_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
        
        if btn_login:
            if not user_input or not pass_input:
                st.error("Por favor, preencha todos os campos.")
            else:
                with engine.connect() as conn:
                    # Correção Definitiva: TRIM e LOWER eliminam espaços fantasmas e problemas de caixa alta/baixa
                    row = conn.execute(
                        text("SELECT username, password, role FROM vision_usuarios WHERE TRIM(LOWER(username)) = :u"),
                        {"u": user_input}
                    ).mappings().fetchone()
                    
                    # Validação blindada usando chaves nominais textuais puras e remoção de espaços
                    if row and str(row["password"]).strip() == pass_input:
                        st.session_state["logado"] = True
                        st.session_state["usuario_nome"] = str(row["username"]).strip()
                        st.session_state["usuario_role"] = str(row["role"]).strip()
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                        
    st.stop()

# ==============================================================================
# ÁREA DO DASHBOARD (SÓ EXISTE E SÓ APARECE APÓS O LOGIN CORRETO)
# ==============================================================================

st.title("📊 Dashboard Vision Play TV")

# Menu Lateral de Identificação e Logout (Reaparece perfeitamente aqui)
st.sidebar.markdown(f"# 🖥️ Menu de Controle")
st.sidebar.markdown(f"👤 **Usuário:** `{st.session_state['usuario_nome']}`")
st.sidebar.markdown(f"🎖️ **Nível:** `{st.session_state['usuario_role']}`")
st.sidebar.divider()

# ======================================
# CAIXA POP-UP DE DIÁLOGO PARA LIMPEZA
# ======================================
@st.dialog("🧹 Escolha o Período para Limpar")
def abrir_popup_limpeza():
    st.write("Digite o **Dia/Mês** dos recebimentos que deseja deletar permanentemente do histórico.")
    data_limpar = st.text_input("Data desejada (Exemplo: 10/06 ou apenas /06 para o mês todo):", value=hoje.strftime("%d/%m"))
    
    st.warning("⚠️ Esta ação vai apagar o faturamento correspondente ao período e atualizará o painel imediatamente!")
    
    if st.button("🔥 Confirmar e Zerar Agora", use_container_width=True):
        if not data_limpar.strip():
            st.error("Insira um formato de data válido para prosseguir.")
        else:
            with engine.begin() as conn:
                if st.session_state["usuario_role"] == "ADM":
                    conn.execute(text("DELETE FROM vision_historico WHERE data LIKE :padrao"), {"padrao": f"%{data_limpar.strip()}%"})
                else:
                    conn.execute(text("""
                        DELETE FROM vision_historico 
                        WHERE data LIKE :padrao AND usuario_owner = :owner
                    """), {"padrao": f"%{data_limpar.strip()}%", "owner": st.session_state["usuario_nome"]})
            st.rerun()

# Botões de controle na barra lateral
if st.sidebar.button("🔄 Sincronizar Banco de Dados", use_container_width=True):
    st.rerun()

if st.sidebar.button("🧹 Zerar Lançamentos por Data", use_container_width=True):
    abrir_popup_limpeza()

if st.sidebar.button("🚪 Sair / Desconectar", use_container_width=True):
    st.session_state["logado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_role"] = ""
    st.rerun()

# ======================================
# CARREGAMENTO FILTRADO POR USUÁRIO (MULTI-TENANCY)
# ======================================
def carregar_dados_supabase():
    role = st.session_state["usuario_role"]
    username = st.session_state["usuario_nome"]
    
    with engine.connect() as conn:
        if role == "ADM":
            res_clientes = conn.execute(text("SELECT nome, whatsapp, vencimento, status, valor, telas FROM vision_clientes ORDER BY nome")).fetchall()
            res_historico = conn.execute(text("SELECT cliente, valor, data FROM vision_historico ORDER BY id ASC")).fetchall()
        else:
            res_clientes = conn.execute(text("SELECT nome, whatsapp, vencimento, status, valor, telas FROM vision_clientes WHERE usuario_owner = :u ORDER BY nome"), {"u": username}).fetchall()
            res_historico = conn.execute(text("SELECT cliente, valor, data FROM vision_historico WHERE usuario_owner = :u ORDER BY id ASC"), {"u": username}).fetchall()
        
        lista_clientes = [{"nome": r[0], "whatsapp": r[1], "vencimento": r[2], "status": r[3], "valor": float(r[4] or 0), "telas": int(r[5] or 1)} for r in res_clientes]
        lista_historico = [{"cliente": r[0], "valor": float(r[1] or 0), "data": r[2]} for r in res_historico]
        return lista_clientes, lista_historico

clientes, historico = carregar_dados_supabase()

# ======================================
# LÓGICA DE PROCESSAMENTO DO DASHBOARD
# ======================================
total_clientes = len(clientes)
em_dia, vencendo, vencidos = 0, 0, 0
receita_prevista, receita_recebida = 0, 0

for cliente in clientes:
    valor = float(cliente.get("valor", 0))
    receita_prevista += valor

    try:
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (vencimento - hoje).days
        if dias < 0: vencidos += 1
        elif dias <= 2: vencendo += 1
        else: em_dia += 1
    except:
        pass

for item in historico:
    receita_recebida += float(item.get("valor", 0))

receita_pendente = receita_prevista - receita_recebida

# Cards Informativos reajustados dinamicamente
c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 Clientes", total_clientes)
c2.metric("💰 Previsto", f"R$ {receita_prevista:.2f}")
c3.metric("✅ Recebido", f"R$ {receita_recebida:.2f}")
c4.metric("⚠️ Pendente", f"R$ {receita_pendente:.2f}")

st.divider()

# Gráficos Dinâmicos em Tempo Real
col1, col2 = st.columns(2)
with col1:
    df_status = pd.DataFrame({"Status": ["Em Dia", "Vencendo", "Vencidos"], "Quantidade": [em_dia, vencendo, vencidos]})
    st.plotly_chart(px.pie(df_status, names="Status", values="Quantidade", title="Clientes"), use_container_width=True)
with col2:
    df_financeiro = pd.DataFrame({"Tipo": ["Recebido", "Pendente"], "Valor": [receita_recebida, receita_pendente]})
    st.plotly_chart(px.pie(df_financeiro, names="Tipo", values="Valor", title="Financeiro"), use_container_width=True)

st.divider()

# Listagem de Vencimentos Próximos
st.subheader("⚠️ Clientes Próximos do Vencimento")
alertas = []
for cliente in clientes:
    try:
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        if (vencimento - hoje).days <= 2:
            alertas.append({"Nome": cliente["nome"], "WhatsApp": cliente["whatsapp"], "Vencimento": cliente["vencimento"]})
    except:
        pass

if alertas:
    st.dataframe(pd.DataFrame(alertas), use_container_width=True, hide_index=True)
else:
    st.success("Nenhum cliente próximo do vencimento.")

st.divider()
st.subheader("⚙️ Gerenciamento do Sistema (Ações em Tempo Real)")

# Definição das Abas Dinâmicas baseadas no Perfil Logado
abas_disponiveis = ["💵 Registrar Pagamento", "➕ Cadastrar Novo Cliente", "✏️ Editar / Excluir Cliente"]
if st.session_state["usuario_role"] == "ADM":
    abas_disponiveis.append("👤 Criar Contas de Usuários")

abas = st.tabs(abas_disponiveis)

# ABA 1: REGISTRAR PAGAMENTO
with abas[0]:
    if clientes:
        nomes = [c["nome"] for c in clientes]
        sel = st.selectbox("Escolha o Cliente para registrar o pagamento:", nomes, key="sel_pagamento")
        cli = next(c for c in clientes if c["nome"] == sel)
        valor_pago = float(cli.get("valor", 25.00))

        st.markdown(f"🖥️ **Telas:** `{cli.get('telas', 1)}` | 💰 **Valor Mensal:** `R$ {valor_pago:.2f}`")
        
        if st.button("⚡ Confirmar Recebimento Automático", key="btn_confirmar_pag"):
            agora = datetime.now(CORRETO_FUSO)
            ano, mes = agora.year, agora.month
            if agora.day > 10:
                mes += 1
                if mes > 12: mes = 1; ano += 1

            novo_vencimento = datetime(ano, mes, 10).strftime("%d/%m/%Y")
            data_historico = agora.strftime("%d/%m/%Y %H:%M")

            with engine.begin() as conn:
                conn.execute(text("UPDATE vision_clientes SET status = 'Recebido', vencimento = :vencimento WHERE nome = :nome"), {"vencimento": novo_vencimento, "nome": cli["nome"]})
                conn.execute(text("INSERT INTO vision_historico (cliente, valor, data, usuario_owner) VALUES (:cliente, :valor, :data, :owner)"), 
                             {"cliente": cli["nome"], "valor": valor_pago, "data": data_historico, "owner": st.session_state["usuario_nome"]})

            st.success(f"Pagamento de R$ {valor_pago:.2f} processado com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum cliente disponível.")

# ABA 2: CADASTRAR NOVO CLIENTE
with abas[1]:
    with st.form("form_novo_cadastro", clear_on_submit=True):
        novo_nome = st.text_input("Nome Completo do Cliente:")
        novo_whatsapp = st.text_input("WhatsApp (com DDD):")
        novo_vencimento = st.text_input("Data de Vencimento (Ex: 10/06/2026):", value=hoje.strftime("10/%m/%Y"))
        novo_status = st.selectbox("Status Inicial do Cliente:", ["Em Dia", "Vencendo", "Vencidos"])
        novo_telas = st.number_input("Quantidade de Telas do Cliente:", min_value=1, value=1, step=1)
        novo_valor = st.number_input("Valor Cobrado Mensalmente (R$):", min_value=0.0, value=25.00, step=5.0)
        
        btn_salvar_cadastro = st.form_submit_button("➕ Salvar Cliente na Nuvem")
        
        if btn_salvar_cadastro:
            if not novo_nome.strip():
                st.error("Por favor, preencha o nome do cliente.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas, usuario_owner)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas, :owner)
                        """), {
                            "nome": novo_nome.strip(), "whatsapp": novo_whatsapp.strip(), "vencimento": novo_vencimento.strip(),
                            "status": novo_status, "valor": novo_valor, "telas": int(novo_telas), "owner": st.session_state["usuario_nome"]
                        })
                    st.success(f"Cliente cadastrado com sucesso!")
                    st.rerun()
                except:
                    st.error("Erro: Já existe um cliente com este nome cadastrado.")

# ABA 3: EDITAR OU DELETAR CLIENTE
with abas[2]:
    if clientes:
        nomes_edit = [c["nome"] for c in clientes]
        sel_edit = st.selectbox("Selecione o cliente que deseja modificar ou remover:", nomes_edit, key="sel_edicao")
        cli_edit = next(c for c in clientes if c["nome"] == sel_edit)
        
        with st.form("form_modificar_cliente"):
            edit_whatsapp = st.text_input("WhatsApp cadastrado:", value=cli_edit["whatsapp"])
            edit_vencimento = st.text_input("Data de Vencimento:", value=cli_edit["vencimento"])
            edit_status = st.selectbox("Status Atual:", ["Em Dia", "Vencendo", "Vencidos"], index=["Em Dia", "Vencendo", "Vencidos"].index(cli_edit["status"]) if cli_edit["status"] in ["Em Dia", "Vencendo", "Vencidos"] else 0)
            edit_telas = st.number_input("Quantidade de Telas:", min_value=1, value=int(cli_edit.get("telas", 1)), step=1)
            edit_valor = st.number_input("Valor da Mensalidade (R$):", min_value=0.0, value=float(cli_edit["valor"]), step=5.0)
            
            c_b1, c_b2 = st.columns(2)
            with c_b1: btn_atualizar = st.form_submit_button("💾 Salvar Alterações")
            with c_b2: btn_deletar = st.form_submit_button("🚨 EXCLUIR CLIENTE DO BANCO")
            
            if btn_atualizar:
                with engine.begin() as conn:
                    conn.execute(text("UPDATE vision_clientes SET whatsapp = :w, vencimento = :v, status = :s, valor = :val, telas = :t WHERE nome = :n"),
                                 {"w": edit_whatsapp, "v": edit_vencimento, "s": edit_status, "val": edit_valor, "t": int(edit_telas), "n": cli_edit["nome"]})
                st.success("Dados atualizados na nuvem!")
                st.rerun()
                
            if btn_deletar:
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM vision_clientes WHERE nome = :nome"), {"nome": cli_edit["nome"]})
                st.success("Cliente removido permanentemente.")
                st.rerun()
    else:
        st.info("Nenhum cliente cadastrado.")

# ABA 4 EXCLUSIVA: GERENCIAR CONTAS DE USUÁRIOS (SÓ APARECE PARA ADM)
if st.session_state["usuario_role"] == "ADM":
    with abas[3]:
        st.subheader("👤 Cadastro de Novos Usuários / Parceiros")
        with st.form("form_novo_usuario", clear_on_submit=True):
            novo_user = st.text_input("Nome do Usuário (Login):").strip().lower()
            nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            novo_perfil = st.selectbox("Tipo de Conta / Permissão:", ["USER", "ADM"])
            btn_criar_user = st.form_submit_button("👤 Criar Conta")
            
            if btn_criar_user:
                if not novo_user or not nova_senha:
                    st.error("Preencha todos os campos corretamente.")
                else:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO vision_usuarios (username, password, role) VALUES (:u, :p, :r)"),
                                         {"u": novo_user, "p": nova_senha, "r": novo_perfil})
                        st.success(f"Conta para o usuário '{novo_user}' criada com sucesso!")
                        st.rerun()
                    except:
                        st.error("Erro: Esse nome de usuário já está sendo utilizado.")

# Listagem de Últimos Recebimentos Filtrados
st.divider()
st.subheader("💵 Últimos Recebimentos")
if historico:
    st.dataframe(pd.DataFrame(list(reversed(historico))[:10]), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum recebimento registrado.")

# Seção de Backup Geral
st.subheader("📥 Backup Geral")
st.download_button("📦 Baixar Backup JSON", data=json.dumps({"clientes": clientes, "historico": historico, "exportado_em": datetime.now(CORRETO_FUSO).strftime("%d/%m/%Y %H:%M:%S")}, indent=4, ensure_ascii=False), file_name="backup_sistema.json", mime="application/json")
