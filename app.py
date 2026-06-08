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

# --- FUNÇÃO AUXILIAR DE TRATAMENTO SEGURO DE VALORES ---
def converter_valor_seguro(val):
    """Garante que o valor financeiro seja sempre um float válido, evitando quebras (NaN) no dashboard."""
    try:
        if val is None or pd.isna(val):
            return 25.00
        return float(val)
    except:
        return 25.00

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

# --- CARREGAR DADOS DO BANCO ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes ORDER BY id ASC")).fetchall()
            clientes = [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in result]
            
            # Sanitização estrutural ao carregar para garantir consistência de colunas
            lista_limpa = []
            for c in clientes:
                lista_limpa.append({
                    "nome": str(c.get("nome", "Sem Nome")),
                    "usuario": str(c.get("usuario", "")),
                    "senha": str(c.get("senha", "")),
                    "status": str(c.get("status", "Pendente")),
                    "valor": converter_valor_seguro(c.get("valor", 25.00))
                })
            return lista_limpa
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados do banco: {e}")
        return []

# --- SALVAR DADOS NO BANCO ---
def salvar_no_banco(lista_clientes):
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clientes"))
            for c in lista_clientes:
                # Trata e limpa os dados individualmente antes de estruturar o JSONB definitivo
                cliente_sanitizado = {
                    "nome": str(c.get("nome", "Novo Cliente")).strip(),
                    "usuario": str(c.get("usuario", "")).strip(),
                    "senha": str(c.get("senha", "")).strip(),
                    "status": str(c.get("status", "Pendente")).strip(),
                    "valor": converter_valor_seguro(c.get("valor", 25.00))
                }
                sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, CAST(:data_json AS JSONB))")
                conn.execute(sql, {"nome": cliente_sanitizado['nome'], "data_json": json.dumps(cliente_sanitizado)})
    except exc.SQLAlchemyError as e:
        st.error(f"Erro ao salvar alterações no banco: {e}")

# --- CONTROLE DE SESSÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

# --- CALLBACK PARA SALVAMENTO AUTOMÁTICO COMPLETO ---
def ao_alterar_tabela():
    estado_editor = st.session_state.editor_principal
    clientes_atuais = list(st.session_state.clientes)
    
    # 1. Tratar edições de linhas existentes (Mudança de status, preço, nome...)
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
                "valor": converter_valor_seguro(nova_linha.get("valor", 25.00))
            }
            clientes_atuais.append(cliente)
            
    # 3. Tratar linhas excluídas na tabela
    if "deleted_rows" in estado_editor:
        for idx in sorted([int(i) for i in estado_editor["deleted_rows"]], reverse=True):
            if idx < len(clientes_atuais):
                clientes_atuais.pop(idx)
                
    # Atualiza o estado da sessão e commita diretamente no banco de dados
    st.session_state.clientes = clientes_atuais
    salvar_no_banco(clientes_atuais)
    
    # NOTA PROFISSIONAL: st.rerun() removido daqui. 
    # O Streamlit executará o recarregamento nativo imediatamente ao fechar este callback,
    # garantindo sincronização perfeita e instantânea dos valores do painel financeiro.

# --- CÁLCULO SEGURO DOS CARDS FINANCEIROS ---
total_clientes = len(st.session_state.clientes)
previsto = sum(converter_valor_seguro(c.get('valor')) for c in st.session_state.clientes)
recebido = sum(converter_valor_seguro(c.get('valor')) for c in st.session_state.clientes 
               if str(c.get('status', '')).strip().lower() == 'confirmado')
pendente = previsto - recebido

# --- LAYOUT DA TELA ---
st.title("📊 Dashboard Vision Play TV")

# Exibição limpa em colunas paralelas para apelo visual profissional
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👥 Total de Clientes", f"{total_clientes}")
with col2:
    st.metric("💰 Faturamento Previsto", f"R$ {previsto:.2f}")
with col3:
    st.metric("✅ Total Recebido", f"R$ {recebido:.2f}")
with col4:
    st.metric("⚠️ Valor Pendente", f"R$ {pendente:.2f}")

st.divider()

# --- TABELA DE GERENCIAMENTO CENTRALIZADA ---
st.subheader("👥 Gerenciamento de Clientes")

# Criação do DataFrame com proteção analítica contra dados faltantes
if not st.session_state.clientes:
    df = pd.DataFrame(columns=["nome", "usuario", "senha", "status", "valor"])
else:
    df = pd.DataFrame(st.session_state.clientes)
    # Garante a integridade técnica das colunas exibidas
    for col in ["nome", "usuario", "senha", "status", "valor"]:
        if col not in df.columns:
            df[col] = ""
    df = df[["nome", "usuario", "senha", "status", "valor"]]

st.data_editor(
    df,
    key="editor_principal",
    on_change=ao_alterar_tabela,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",  # Permite Adicionar (+) e Deletar linhas diretamente de forma limpa
    column_config={
        "nome": st.column_config.TextColumn("Nome do Cliente", required=True),
        "usuario": st.column_config.TextColumn("Usuário de Acesso", required=True),
        "senha": st.column_config.TextColumn("Senha", required=True),
        "status": st.column_config.SelectboxColumn(
            "Status do Pagamento",
            options=["Pendente", "Confirmado"],
            required=True
        ),
        "valor": st.column_config.NumberColumn("Valor Mensal (R$)", format="R$ %.2f", min_value=0.0, default=25.00)
    }
)
