import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
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

        # 2. TABELA DE CLIENTES
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
        
        # 3. TABELA DE HISTÓRICO DE PAGAMENTOS
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
                    row = conn.execute(
                        text("""
                            SELECT username, role, status, vencimento_usuario 
                            FROM vision_usuarios 
                            WHERE TRIM(LOWER(username)) = TRIM(LOWER(:u)) AND TRIM(password) = :p
                        """),
                        {"u": user_input, "p": pass_input}
                    ).mappings().fetchone()
                    
                    if row:
                        status_atual = str(row["status"]).strip()
                        venc_str = str(row["vencimento_usuario"]).strip()
                        role_atual = str(row["role"]).strip()
                        
                        conta_vencida = False
                        try:
                            data_venc = datetime.strptime(venc_str, "%d/%m/%Y").date()
                            if data_venc < hoje:
                                conta_vencida = True
                        except:
                            pass
                        
                        if status_atual == "Bloqueado" or (conta_vencida and role_atual != "ADM"):
                            if conta_vencida and status_atual != "Bloqueado":
                                with engine.begin() as up_conn:
                                    up_conn.execute(text("UPDATE vision_usuarios SET status = 'Bloqueado' WHERE TRIM(LOWER(username)) = TRIM(LOWER(:u))"), {"u": user_input})
                            st.error("🚫 Acesso Recusado: Esta conta está vencida ou foi bloqueada pelo Administrador!")
                        else:
                            st.session_state["logado"] = True
                            st.session_state["usuario_nome"] = str(row["username"]).strip().lower()
                            st.session_state["usuario_role"] = role_atual
                            st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                        
    st.stop()

# ==============================================================================
# ÁREA DO DASHBOARD (SÓ ACCESSÍVEL APÓS AUTENTICAÇÃO FILTRADA)
# ==============================================================================

# Captura segura das variáveis de sessão atuais
usuario_atual = st.session_state["usuario_nome"]
role_atual = st.session_state["usuario_role"]

st.title("📊 Dashboard Vision Play TV")

# Menu Lateral Restrito por Nível de Acesso
st.sidebar.markdown(f"# 🖥️ Menu de Controle")
st.sidebar.markdown(f"👤 **Usuário:** `{usuario_atual}`")
st.sidebar.markdown(f"🎖️ **Nível:** `{role_atual}`")
st.sidebar.divider()

# CAIXA POP-UP DE LIMPEZA COM FILTRO DE ISOLAMENTO POR USUÁRIO
@st.dialog("🧹 Escolha o Período para Limpar")
def abrir_popup_limpeza():
    st.write("Digite o **Dia/Mês** dos recebimentos que deseja deletar do histórico.")
    data_limpar = st.text_input("Data desejada (Ex: 10/06 ou /06):", value=hoje.strftime("%d/%m"), key=f"inp_clean_{usuario_atual}")
    
    if role_atual == "ADM":
        st.warning("⚠️ Você está logado como ADM. Isso apagará os dados globais do período digitado!")
    else:
        st.warning("⚠️ Isso apagará apenas os **seus** registros de recebimento do período digitado!")

    if st.button("🔥 Confirmar e Zerar Agora", use_container_width=True, key=f"btn_clean_exec_{usuario_atual}"):
        if data_limpar.strip():
            with engine.begin() as conn:
                if role_atual == "ADM":
                    conn.execute(text("DELETE FROM vision_historico WHERE data LIKE :padrao"), {"padrao": f"%{data_limpar.strip()}%"})
                else:
                    conn.execute(text("""
                        DELETE FROM vision_historico 
                        WHERE data LIKE :padrao AND TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:owner))
                    """), {"padrao": f"%{data_limpar.strip()}%", "owner": usuario_atual})
            st.rerun()

# --- BOTÕES DA BARRA LATERAL ---
if role_atual == "ADM":
    if st.sidebar.button("🔄 Sincronizar Banco de Dados", use_container_width=True, key=f"sync_adm_{usuario_atual}"):
        st.rerun()

if st.sidebar.button("🧹 Zerar Lançamentos por Data", use_container_width=True, key=f"clean_side_{usuario_atual}"):
    abrir_popup_limpeza()

if st.sidebar.button("🚪 Sair / Desconectar", use_container_width=True, key=f"logout_{usuario_atual}"):
    st.session_state["logado"] = False
    st.session_state["usuario_nome"] = ""
    st.session_state["usuario_role"] = ""
    st.rerun()

# ======================================
# CARREGAMENTO ISOLADO (ANTI-VAZAMENTO DE DADOS)
# ======================================
def carregar_dados_supabase():
    with engine.connect() as conn:
        if role_atual == "ADM":
            res_clientes = conn.execute(text("SELECT nome, whatsapp, vencimento, status, valor, telas FROM vision_clientes ORDER BY nome")).fetchall()
            res_historico = conn.execute(text("SELECT cliente, valor, data FROM vision_historico ORDER BY id ASC")).fetchall()
        else:
            # Filtro e isolamento absoluto via banco de dados
            res_clientes = conn.execute(text("""
                SELECT nome, whatsapp, vencimento, status, valor, telas 
                FROM vision_clientes 
                WHERE TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:u)) 
                ORDER BY nome
            """), {"u": usuario_atual}).fetchall()
            
            res_historico = conn.execute(text("""
                SELECT cliente, valor, data 
                FROM vision_historico 
                WHERE TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:u)) 
                ORDER BY id ASC
            """), {"u": usuario_atual}).fetchall()
        
        lista_clientes = [{"nome": r[0], "whatsapp": r[1], "vencimento": r[2], "status": r[3], "valor": float(r[4] or 0), "telas": int(r[5] or 1)} for r in res_clientes]
        lista_historico = [{"cliente": r[0], "valor": float(r[1] or 0), "data": r[2]} for r in res_historico]
        return lista_clientes, lista_historico

clientes, historico = carregar_dados_supabase()

# ======================================
# CÁLCULOS DO PAINEL DE CONTROLE
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

c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 Clientes", total_clientes)
c2.metric("💰 Previsto", f"R$ {receita_prevista:.2f}")
c3.metric("✅ Recebido", f"R$ {receita_recebida:.2f}")
c4.metric("⚠️ Pendente", f"R$ {receita_pendente:.2f}")

st.divider()

col1, col2 = st.columns(2)
with col1:
    df_status = pd.DataFrame({"Status": ["Em Dia", "Vencendo", "Vencidos"], "Quantidade": [em_dia, vencendo, vencidos]})
    st.plotly_chart(px.pie(df_status, names="Status", values="Quantidade", title="Clientes"), use_container_width=True)
with col2:
    df_financeiro = pd.DataFrame({"Tipo": ["Recebido", "Pendente"], "Valor": [receita_recebida, receita_pendente]})
    st.plotly_chart(px.pie(df_financeiro, names="Tipo", values="Valor", title="Financeiro"), use_container_width=True)

st.divider()

# ======================================
# ABA DE GESTÃO EM TEMPO REAL
# ======================================
st.subheader("⚙️ Gerenciamento do Sistema")
abas_disponiveis = ["💵 Registrar Pagamento", "➕ Cadastrar Novo Cliente", "✏️ Editar / Excluir Cliente"]
if role_atual == "ADM":
    abas_disponiveis.append("👤 Gerenciar Usuários do Sistema")

abas = st.tabs(abas_disponiveis)

# ABA 1: REGISTRAR PAGAMENTO
with abas[0]:
    if clientes:
        nomes = [c["nome"] for c in clientes]
        sel = st.selectbox("Escolha o Cliente para registrar o pagamento:", nomes, key=f"sel_pag_{usuario_atual}")
        cli = next(c for c in clientes if c["nome"] == sel)
        valor_pago = float(cli.get("valor", 25.00))

        st.markdown(f"🖥️ **Telas:** `{cli.get('telas', 1)}` | 💰 **Valor Mensal:** `R$ {valor_pago:.2f}`")
        
        if st.button("⚡ Confirmar Recebimento Automático", key=f"btn_pago_{usuario_atual}"):
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
                             {"cliente": cli["nome"], "valor": valor_pago, "data": data_historico, "owner": usuario_atual})

            st.success(f"Pagamento processado com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum cliente disponível.")

# ABA 2: CADASTRAR NOVO CLIENTE
with abas[1]:
    with st.form(f"form_cad_{usuario_atual}", clear_on_submit=False):
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
                            "status": novo_status, "valor": novo_valor, "telas": int(novo_telas), "owner": usuario_atual
                        })
                    st.success(f"Cliente cadastrado com sucesso!")
                    st.rerun()
                except:
                    st.error("Erro: Já existe um cliente com este nome cadastrado.")

# ABA 3: EDITAR OU DELETAR CLIENTE
with abas[2]:
    if clientes:
        nomes_edit = [c["nome"] for c in clientes]
        sel_edit = st.selectbox("Selecione o cliente que deseja modificar ou remover:", nomes_edit, key=f"sel_edit_{usuario_atual}")
        cli_edit = next(c for c in clientes if c["nome"] == sel_edit)
        
        with st.form(f"form_mod_cli_{usuario_atual}"):
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

# ABA 4 EXCLUSIVA: GERENCIAR USUÁRIOS (SÓ APARECE PARA ADM)
if role_atual == "ADM":
    with abas[3]:
        st.subheader("👤 Painel de Controle de Contas / Revendedores")
        
        with st.form(f"form_new_user_{usuario_atual}", clear_on_submit=False):
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                novo_user = st.text_input("Nome do Usuário (Login):").strip().lower()
                nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            with col_u2:
                novo_perfil = st.selectbox("Tipo de Conta:", ["USER", "ADM"])
                tipo_tempo = st.radio("Modalidade de Tempo:", ["Conta Teste", "Conta Final (30 dias)"], horizontal=True)
            with col_u3:
                dias_teste = st.number_input("Se for Teste, quantos dias?", min_value=1, max_value=90, value=1)
            
            btn_criar_user = st.form_submit_button("🚀 Gerar e Ativar Nova Conta")
            
            if btn_criar_user:
                if not novo_user or not nova_senha:
                    st.error("Preencha todos os campos do formulário.")
                else:
                    if tipo_tempo == "Conta Teste":
                        data_calculada = hoje + timedelta(days=int(dias_teste))
                        label_tipo = "Teste"
                    else:
                        data_calculada = hoje + timedelta(days=30)
                        label_tipo = "Final"
                        
                    venc_formatado = data_calculada.strftime("%d/%m/%Y")
                    
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("""
                                INSERT INTO vision_usuarios (username, password, role, status, tipo_conta, vencimento_usuario) 
                                VALUES (TRIM(LOWER(:u)), TRIM(:p), :r, 'Ativo', :tipo, :venc)
                            """), {"u": novo_user, "p": nova_senha, "r": novo_perfil, "tipo": label_tipo, "venc": venc_formatado})
                        st.success(f"Conta '{novo_user}' ativada com sucesso! Vencimento: {venc_formatado}")
                        st.rerun()
                    except:
                        st.error("Erro: Esse login já existe.")

        st.divider()
        st.subheader("📋 Lista Completa de Contas no Banco")
        
        with engine.connect() as conn:
            lista_raw = conn.execute(text("SELECT id, username, password, role, status, tipo_conta, vencimento_usuario FROM vision_usuarios ORDER BY id DESC")).mappings().fetchall()
            df_usuarios = pd.DataFrame(lista_raw)
            
        if not df_usuarios.empty:
            st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
            
            st.markdown("### ✏️ Modificar ou Remover Conta")
            seletor_user = st.selectbox("Escolha a conta que deseja gerenciar:", df_usuarios["username"].tolist(), key=f"sel_manage_user_{usuario_atual}")
            user_dados = df_usuarios[df_usuarios["username"] == seletor_user].iloc[0]
            
            with st.form(f"form_ed_user_{usuario_atual}"):
                c_ed1, c_ed2, c_ed3 = st.columns(3)
                with c_ed1:
                    ed_username = st.text_input("Nome do Usuário (Login):", value=user_dados["username"]).strip().lower()
                    ed_password = st.text_input("Senha de Acesso:", value=user_dados["password"]).strip()
                with c_ed2:
                    ed_vencimento = st.text_input("Data de Vencimento (DD/MM/AAAA):", value=user_dados["vencimento_usuario"]).strip()
                with c_ed3:
                    ed_status = st.selectbox("Status da Conta:", ["Ativo", "Bloqueado"], index=["Ativo", "Bloqueado"].index(user_dados["status"]))
                    ed_role = st.selectbox("Nível:", ["USER", "ADM"], index=["USER", "ADM"].index(user_dados["role"]))
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    btn_up_user = st.form_submit_button("💾 Atualizar Dados do Usuário")
                with col_btn2:
                    btn_del_user = st.form_submit_button("🔥 DELETAR USUÁRIO PERMANENTEMENTE")
                
                if btn_up_user:
                    with engine.begin() as conn:
                        if ed_username != user_dados["username"]:
                            conn.execute(text("UPDATE vision_clientes SET usuario_owner = :novo WHERE usuario_owner = :velho"), {"novo": ed_username, "velho": user_dados["username"]})
                            conn.execute(text("UPDATE vision_historico SET usuario_owner = :novo WHERE usuario_owner = :velho"), {"novo": ed_username, "velho": user_dados["username"]})
                        
                        conn.execute(text("""
                            UPDATE vision_usuarios 
                            SET username = :u, password = :p, vencimento_usuario = :v, status = :s, role = :r 
                            WHERE id = :id
                        """), {"u": ed_username, "p": ed_password, "v": ed_vencimento, "s": ed_status, "r": ed_role, "id": int(user_dados["id"])})
                    st.success("Conta atualizada!")
                    st.rerun()
                    
                if btn_del_user:
                    if user_dados["username"] == "admin":
                        st.error("Não é possível deletar o administrador master global.")
                    else:
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM vision_usuarios WHERE id = :id"), {"id": int(user_dados["id"])})
                        st.success("Conta removida do sistema.")
                        st.rerun()
        else:
            st.info("Nenhum usuário cadastrado.")

# Listagem de Últimos Recebimentos
st.divider()
st.subheader("💵 Últimos Recebimentos")
if historico:
    st.dataframe(pd.DataFrame(list(reversed(historico))[:10]), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum recebimento registrado.")

# Seção de Backup Geral
st.subheader("📥 Backup Geral")
st.download_button("📦 Baixar Backup JSON", data=json.dumps({"clientes": clientes, "historico": historico, "exportado_em": datetime.now(CORRETO_FUSO).strftime("%d/%m/%Y %H:%M:%S")}, indent=4, ensure_ascii=False), file_name="backup_sistema.json", mime="application/json", key=f"btn_bkp_{usuario_atual}")
