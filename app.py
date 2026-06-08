import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text, exc

# Configuração da página
st.set_page_config(page_title="Dashboard Vision Play TV", page_icon="📊", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- CRIAÇÃO AUTOMÁTICA DA TABELA ---
def inicializar_banco():
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255),
                    data_json JSONB
                );
            """))
    except Exception as e:
        st.error(f"⚠️ Erro crítico ao criar a estrutura do banco de dados: {e}")

inicializar_banco()

# --- CARREGAR DADOS DO BANCO (SEGURO E SEM FALLBACKS) ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes ORDER BY id ASC")).fetchall()
            # Retorna os dados puramente como vierem do banco de dados
            return [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in result]
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados do banco: {e}")
        return []

# --- SALVAR DADOS NO BANCO ---
def salvar_no_banco(lista_clientes):
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clientes"))
            for c in lista_clientes:
                sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, CAST(:data_json AS JSONB))")
                conn.execute(sql, {"nome": c.get('nome', 'Sem Nome'), "data_json": json.dumps(c)})
    except exc.SQLAlchemyError as e:
        st.error(f"Erro ao salvar alterações no banco: {e}")

# --- CONTROLE DE SESSÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

# --- CALLBACK PARA SALVAMENTO AUTOMÁTICO COMPLETO (EDIÇÃO, ADIÇÃO E EXCLUSÃO) ---
def ao_alterar_tabela():
    estado_editor = st.session_state.editor_principal
    clientes_atuais = list(st.session_state.clientes)
    
    # 1. Tratar edições de linhas existentes
    if "edited_rows" in estado_editor:
        for idx, mudancas in estado_editor["edited_rows"].items():
            idx_int = int(idx)
            if idx_int < len(clientes_atuais):
                clientes_atuais[idx_int].update(mudancas)
                
    # 2. Tratar novas linhas adicionadas na tabela
    if "added_rows" in estado_editor:
        for nova_linha in estado_editor["added_rows"]:
            cliente = {
                "nome": nova_linha.get("nome", "Novo Cliente"),
                "usuario": nova_linha.get("usuario", ""),
                "senha": nova_linha.get("senha", ""),
                "status": nova_linha.get("status", "Pendente"),
                "valor": float(nova_linha.get("valor", 25.90))
            }
            clientes_atuais.append(cliente)
            
    # 3. Tratar linhas excluídas na tabela
    if "deleted_rows" in estado_editor:
        for idx in sorted([int(i) for i in estado_editor["deleted_rows"]], reverse=True):
            if idx < len(clientes_atuais):
                clientes_atuais.pop(idx)
                
    # Salva o novo estado final no banco de dados permanentemente
    st.session_state.clientes = clientes_atuais
    salvar_no_banco(clientes_atuais)

# --- CÁLCULO DOS CARD FINANCEIROS ---
total_clientes = len(st.session_state.clientes)
previsto = sum(float(c.get('valor', 25.90)) for c in st.session_state.clientes)
recebido = sum(float(c.get('valor', 25.90)) for c in st.session_state.clientes 
               if str(c.get('status', '')).strip().lower() == 'confirmado')
pendente = previsto - recebido

# --- LOUYOUT DA TELA ---
st.title(" Dashboard Vision Play TV")

st.metric("👥 Clientes", f"{total_clientes}")
st.metric("💰 Previsto", f"R$ {previsto:.2f}")
st.metric("✅ Recebido", f"R$ {recebido:.2f}")
st.metric("⚠️ Pendente", f"R$ {pendente:.2f}")

st.divider()

# --- TABELA DE GERENCIAMENTO INTELIGENTE ---
st.subheader("👥 Lista de Clientes")
if st.session_state.clientes or True: # Mantém exibido para permitir adições mesmo se vazio
    df = pd.DataFrame(st.session_state.clientes)
    
    # Se o banco iniciar totalmente vazio, cria a estrutura de colunas vazia para o usuário preencher
    if df.empty:
        df = pd.DataFrame(columns=["nome", "usuario", "senha", "status", "valor"])
    else:
        df = df[["nome", "usuario", "senha", "status", "valor"]]
    
    st.data_editor(
        df,
        key="editor_principal",
        on_change=ao_alterar_tabela,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",  # LIBERADO: Agora permite Adicionar (+) e Deletar linhas direto na tabela
        column_config={
            "nome": st.column_config.TextColumn("Nome", required=True),
            "usuario": st.column_config.TextColumn("Usuário", required=True),
            "senha": st.column_config.TextColumn("Senha", required=True),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Pendente", "Confirmado"],
                required=True
            ),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0)
        }
    )

    # --- REGISTRADOR RÁPIDO PARALELO ---
    if st.session_state.clientes:
        st.divider()
        st.subheader("💳 Registrar Pagamento Rápido")
        nome_sel = st.selectbox("Selecione o cliente abaixo:", [c.get('nome', '') for c in st.session_state.clientes])
        
        if st.button("⚡ Confirmar Pagamento do Selecionado", use_container_width=True):
            for c in st.session_state.clientes:
                if c.get('nome', '') == nome_sel:
                    c['status'] = "Confirmado"
                    break
            salvar_no_banco(st.session_state.clientes)
            st.success(f"Sucesso! O pagamento de {nome_sel} foi processado.")
            st.rerun()
