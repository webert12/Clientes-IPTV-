import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text, exc

# Configuração
st.set_page_config(page_title="Gestão IPTV Pro", page_icon="👥", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- DADOS INICIAIS (50 Clientes Verificados - Sem registros "app") ---
CLIENTES_INICIAIS = [
    {"nome": "Rejane", "usuario": "Rejaneita", "senha": "1234052466960319", "status": "Pendente", "valor": 25.0},
    {"nome": "Regi", "usuario": "Regijr", "senha": "1234575761818", "status": "Pendente", "valor": 25.0},
    {"nome": "Igor", "usuario": "Teste24h", "senha": "9365318638", "status": "Pendente", "valor": 25.0},
    {"nome": "MariaEduarda", "usuario": "Mariaeduarda", "senha": "12639884293", "status": "Pendente", "valor": 25.0},
    {"nome": "Fatima", "usuario": "Fatima", "senha": "9228953758", "status": "Pendente", "valor": 25.0},
    {"nome": "PauloJunior", "usuario": "34112515116188972742", "senha": "20022026", "status": "Pendente", "valor": 25.0},
    {"nome": "Geraldo", "usuario": "GeraldoM3", "senha": "249591218", "status": "Pendente", "valor": 25.0},
    {"nome": "Kaio", "usuario": "Kaio123", "senha": "6487511788", "status": "Pendente", "valor": 25.0},
    {"nome": "Anderson", "usuario": "Anderson31441015", "senha": "31441015", "status": "Pendente", "valor": 25.0},
    {"nome": "Tania", "usuario": "Tania1234", "senha": "288363116", "status": "Pendente", "valor": 25.0},
    {"nome": "Guilherme", "usuario": "GuilhermeT3", "senha": "877877826", "status": "Pendente", "valor": 25.0},
    {"nome": "Guimba", "usuario": "Guimba2", "senha": "379875886", "status": "Pendente", "valor": 25.0},
    {"nome": "Ednaldo", "usuario": "Ednaldo9", "senha": "434838197", "status": "Pendente", "valor": 25.0},
    {"nome": "Mariana", "usuario": "Mariana5", "senha": "481718365", "status": "Pendente", "valor": 25.0},
    {"nome": "Cairo", "usuario": "Cairo12", "senha": "7858475797", "status": "Pendente", "valor": 25.0},
    {"nome": "Lauren", "usuario": "Lauren2", "senha": "615133128", "status": "Pendente", "valor": 25.0},
    {"nome": "Limarita", "usuario": "Limarita123", "senha": "3214987985", "status": "Pendente", "valor": 25.0},
    {"nome": "Maguila", "usuario": "Maguila15", "senha": "273754722", "status": "Pendente", "valor": 25.0},
    {"nome": "BrazGeraldo", "usuario": "Brazgeraldo4", "senha": "85969684554", "status": "Pendente", "valor": 25.0},
    {"nome": "AndreBernardes", "usuario": "Andrebernardes5", "senha": "489814998", "status": "Pendente", "valor": 25.0},
    {"nome": "Nilcio", "usuario": "25106846837670794071", "senha": "27062025", "status": "Pendente", "valor": 25.0},
    {"nome": "Alonso", "usuario": "Alonso2", "senha": "ck2ccgh235", "status": "Pendente", "valor": 25.0},
    {"nome": "Deivane", "usuario": "Deivanennqnu3", "senha": "th6m", "status": "Pendente", "valor": 25.0},
    {"nome": "NataliaMenezes", "usuario": "81821125638099462524", "senha": "26062025", "status": "Pendente", "valor": 25.0},
    {"nome": "Roseita", "usuario": "Roseita4", "senha": "78945185", "status": "Pendente", "valor": 25.0},
    {"nome": "Paulinho", "usuario": "Paulinho12", "senha": "tp3f9hhqq5", "status": "Pendente", "valor": 25.0},
    {"nome": "Walker", "usuario": "Walker1234", "senha": "yqrj8xv9k3", "status": "Pendente", "valor": 25.0},
    {"nome": "MariaClaudio", "usuario": "MariaClaudio5", "senha": "jxaxs7puu", "status": "Pendente", "valor": 25.0},
    {"nome": "Alonso1", "usuario": "Alonso12345", "senha": "2384y5rwh", "status": "Pendente", "valor": 25.0},
    {"nome": "Deivid", "usuario": "08578350209007893072", "senha": "18062025", "status": "Pendente", "valor": 25.0},
    {"nome": "Elizandra", "usuario": "Elizandra123", "senha": "7576594786", "status": "Pendente", "valor": 25.0},
    {"nome": "Douglas", "usuario": "Douglas123", "senha": "6860511987", "status": "Pendente", "valor": 25.0},
    {"nome": "Zepaulo", "usuario": "Zepaulo1", "senha": "165139999", "status": "Pendente", "valor": 25.0},
    {"nome": "AnnaLaura", "usuario": "AnnaLaura123", "senha": "124906705880", "status": "Pendente", "valor": 25.0},
    {"nome": "Diegoneomp", "usuario": "Diegoneomp9", "senha": "1kf7fnj", "status": "Pendente", "valor": 25.0},
    {"nome": "Diogodiv", "usuario": "Diogodiv4", "senha": "849606387", "status": "Pendente", "valor": 25.0},
    {"nome": "MariaRosa", "usuario": "MariaRosa9", "senha": "158788294", "status": "Pendente", "valor": 25.0},
    {"nome": "Luciano", "usuario": "Luciano123", "senha": "8866992981", "status": "Pendente", "valor": 25.0},
    {"nome": "AlinePrima", "usuario": "84604741183591874711", "senha": "10062025", "status": "Pendente", "valor": 25.0},
    {"nome": "Tamires", "usuario": "Tamires123", "senha": "n3ved26w1e1", "status": "Pendente", "valor": 25.0},
    {"nome": "Cassiano", "usuario": "Cassiano2", "senha": "43pprnj19bg", "status": "Pendente", "valor": 25.0},
    {"nome": "Manoelita", "usuario": "Manoelita1", "senha": "ep4a9mw6rs", "status": "Pendente", "valor": 25.0},
    {"nome": "AirtonCesar", "usuario": "Airtoncesar1", "senha": "937583748", "status": "Pendente", "valor": 25.0},
    {"nome": "Jefinho", "usuario": "Jefinho2", "senha": "2522695854", "status": "Pendente", "valor": 25.0},
    {"nome": "Fredinho", "usuario": "Fredinho6", "senha": "664090314", "status": "Pendente", "valor": 25.0},
    {"nome": "Lidiane", "usuario": "59048676357235395158", "senha": "02052025", "status": "Pendente", "valor": 25.0},
    {"nome": "Cida", "usuario": "89429163675233408932", "senha": "28042025", "status": "Pendente", "valor": 25.0},
    {"nome": "Adilson", "usuario": "Adilson4", "senha": "315751435", "status": "Pendente", "valor": 25.0},
    {"nome": "Natan", "usuario": "cgykd620zdgr", "senha": "rergmfsf", "status": "Pendente", "valor": 25.0},
    {"nome": "Renato", "usuario": "RenatoDel0", "senha": "997708882", "status": "Pendente", "valor": 25.0}
]

# --- PERSISTÊNCIA ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            if not result:
                # Se a tabela estiver vazia, popula com os dados iniciais padrão seguros
                with engine.begin() as tx:
                    for c in CLIENTES_INICIAIS:
                        tx.execute(text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)"), 
                                   {"nome": c['nome'], "data_json": json.dumps(c)})
                return CLIENTES_INICIAIS
            return [json.loads(r[0]) for r in result]
    except Exception as e:
        # Segurança: se falhar a conexão, NÃO retorna a lista padrão para não arriscar sobrescrever os dados reais em saves futuros
        st.error(f"⚠️ Erro temporário ao acessar o banco de dados. Tente atualizar a página. Detalhes: {e}")
        return None

def salvar_no_banco(lista_clientes):
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clientes"))
            for c in lista_clientes:
                sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
                conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})
    except exc.SQLAlchemyError as e:
        st.error(f"Erro ao salvar alterações no banco: {e}")

# --- INICIALIZAÇÃO ---
if 'clientes' not in st.session_state:
    dados_carregados = carregar_clientes()
    if dados_carregados is not None:
        st.session_state.clientes = dados_carregados
    else:
        st.session_state.clientes = []
if 'marcar_todos' not in st.session_state:
    st.session_state.marcar_todos = False

st.title("👥 Gestão de Clientes IPTV")

# --- DASHBOARD FINANCEIRO ---
st.subheader("📊 Resumo Financeiro")
confirmados = [c for c in st.session_state.clientes if c.get('status') == 'Confirmado']
valor_total = sum(c.get('valor', 25.0) for c in confirmados)

col_m1, col_m2 = st.columns(2)
col_m1.metric("Pagamentos Recebidos", len(confirmados))
col_m2.metric("Valor Total Arrecadado", f"R$ {valor_total:.2f}")

st.divider()

# --- LISTAGEM AND EXCLUSÃO ---
if st.session_state.clientes:
    df = pd.DataFrame(st.session_state.clientes)
    df.insert(0, "🗑️", st.session_state.marcar_todos)
    
    # Exibe editor com suporte a edições diretas em texto e status
    edited_df = st.data_editor(df, hide_index=True, use_container_width=True)

    col1, col2, col3 = st.columns([1.5, 2, 4])
    with col1:
        if st.button("✅ Marcar Todos"):
            st.session_state.marcar_todos = not st.session_state.marcar_todos
            st.rerun()

    with col2:
        if st.button("🗑️ Excluir Selecionados"):
            selecionados = edited_df[edited_df["🗑️"] == True]
            if not len(selecionados) == 0:
                st.session_state.clientes = [c for c in st.session_state.clientes if c["nome"] not in selecionados["nome"].values]
                salvar_no_banco(st.session_state.clientes)
                st.session_state.marcar_todos = False
                st.success("Removidos com sucesso.")
                st.rerun()
                
    with col3:
        if st.button("💾 Salvar Modificações da Tabela"):
            # Coleta todas as modificações textuais feitas no st.data_editor e persiste no banco de dados permanentemente
            dados_atualizados = edited_df.drop(columns=["🗑️"]).to_dict(orient="records")
            st.session_state.clientes = dados_atualizados
            salvar_no_banco(dados_atualizados)
            st.success("Sincronização realizada com o banco de dados!")
            st.rerun()

    # --- REGISTRO DE PAGAMENTO ---
    st.divider()
    st.subheader("💳 Registrar Pagamento rápido")
    nome_sel = st.selectbox("Selecione o cliente para confirmar pagamento", [c['nome'] for c in st.session_state.clientes])
    cli = next((c for c in st.session_state.clientes if c['nome'] == nome_sel), None)

    if cli:
        st.write(f"Status atual de **{cli['nome']}**: {cli.get('status', 'Pendente')}")
        if st.button("✅ Confirmar Pagamento"):
            cli['status'] = "Confirmado"
            salvar_no_banco(st.session_state.clientes)
            st.success(f"Pagamento de {cli['nome']} confirmado com sucesso!")
            st.rerun()
else:
    st.info("Aguardando carregamento de clientes ou banco de dados vazio.")
