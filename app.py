import streamlit as st
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text, exc

# Configuração
st.set_page_config(page_title="Gestão IPTV Pro", page_icon="👥", layout="wide")

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- DADOS INICIAIS (Os 50 clientes solicitados) ---
CLIENTES_INICIAIS = [
    {"nome": "Rejane", "usuario": "Rejaneita", "senha": "1234052466960319", "status": "Pendente"},
    {"nome": "Regi", "usuario": "Regijr", "senha": "1234575761818", "status": "Pendente"},
    {"nome": "Igor", "usuario": "Teste24h", "senha": "9365318638", "status": "Pendente"},
    {"nome": "MariaEduarda", "usuario": "Mariaeduarda", "senha": "12639884293", "status": "Pendente"},
    {"nome": "Fatima", "usuario": "Fatima", "senha": "9228953758", "status": "Pendente"},
    {"nome": "PauloJunior", "usuario": "34112515116188972742", "senha": "20022026", "status": "Pendente"},
    {"nome": "Geraldo", "usuario": "GeraldoM3", "senha": "249591218", "status": "Pendente"},
    {"nome": "Kaio", "usuario": "Kaio123", "senha": "6487511788", "status": "Pendente"},
    {"nome": "Anderson", "usuario": "Anderson31441015", "senha": "31441015", "status": "Pendente"},
    {"nome": "Tania", "usuario": "Tania1234", "senha": "288363116", "status": "Pendente"},
    {"nome": "Guilherme", "usuario": "GuilhermeT3", "senha": "877877826", "status": "Pendente"},
    {"nome": "Guimba", "usuario": "Guimba2", "senha": "379875886", "status": "Pendente"},
    {"nome": "Ednaldo", "usuario": "Ednaldo9", "senha": "434838197", "status": "Pendente"},
    {"nome": "Mariana", "usuario": "Mariana5", "senha": "481718365", "status": "Pendente"},
    {"nome": "Cairo", "usuario": "Cairo12", "senha": "7858475797", "status": "Pendente"},
    {"nome": "Lauren", "usuario": "Lauren2", "senha": "615133128", "status": "Pendente"},
    {"nome": "Limarita", "usuario": "Limarita123", "senha": "3214987985", "status": "Pendente"},
    {"nome": "Maguila", "usuario": "Maguila15", "senha": "273754722", "status": "Pendente"},
    {"nome": "BrazGeraldo", "usuario": "Brazgeraldo4", "senha": "85969684554", "status": "Pendente"},
    {"nome": "AndreBernardes", "usuario": "Andrebernardes5", "senha": "489814998", "status": "Pendente"},
    {"nome": "Nilcio", "usuario": "25106846837670794071", "senha": "27062025", "status": "Pendente"},
    {"nome": "Alonso", "usuario": "Alonso2", "senha": "ck2ccgh235", "status": "Pendente"},
    {"nome": "Deivane", "usuario": "Deivanennqnu3", "senha": "th6m", "status": "Pendente"},
    {"nome": "NataliaMenezes", "usuario": "81821125638099462524", "senha": "26062025", "status": "Pendente"},
    {"nome": "Roseita", "usuario": "Roseita4", "senha": "78945185", "status": "Pendente"},
    {"nome": "Paulinho", "usuario": "Paulinho12", "senha": "tp3f9hhqq5", "status": "Pendente"},
    {"nome": "Walker", "usuario": "Walker1234", "senha": "yqrj8xv9k3", "status": "Pendente"},
    {"nome": "MariaClaudio", "usuario": "MariaClaudio5", "senha": "jxaxs7puu", "status": "Pendente"},
    {"nome": "Alonso1", "usuario": "Alonso12345", "senha": "2384y5rwh", "status": "Pendente"},
    {"nome": "Deivid", "usuario": "08578350209007893072", "senha": "18062025", "status": "Pendente"},
    {"nome": "Elizandra", "usuario": "Elizandra123", "senha": "7576594786", "status": "Pendente"},
    {"nome": "Douglas", "usuario": "Douglas123", "senha": "6860511987", "status": "Pendente"},
    {"nome": "Zepaulo", "usuario": "Zepaulo1", "senha": "165139999", "status": "Pendente"},
    {"nome": "AnnaLaura", "usuario": "AnnaLaura123", "senha": "124906705880", "status": "Pendente"},
    {"nome": "Diegoneomp", "usuario": "Diegoneomp9", "senha": "1kf7fnj", "status": "Pendente"},
    {"nome": "Diogodiv", "usuario": "Diogodiv4", "senha": "849606387", "status": "Pendente"},
    {"nome": "MariaRosa", "usuario": "MariaRosa9", "senha": "158788294", "status": "Pendente"},
    {"nome": "Luciano", "usuario": "Luciano123", "senha": "8866992981", "status": "Pendente"},
    {"nome": "AlinePrima", "usuario": "84604741183591874711", "senha": "10062025", "status": "Pendente"},
    {"nome": "Tamires", "usuario": "Tamires123", "senha": "n3ved26w1e1", "status": "Pendente"},
    {"nome": "Cassiano", "usuario": "Cassiano2", "senha": "43pprnj19bg", "status": "Pendente"},
    {"nome": "Manoelita", "usuario": "Manoelita1", "senha": "ep4a9mw6rs", "status": "Pendente"},
    {"nome": "AirtonCesar", "usuario": "Airtoncesar1", "senha": "937583748", "status": "Pendente"},
    {"nome": "Jefinho", "usuario": "Jefinho2", "senha": "2522695854", "status": "Pendente"},
    {"nome": "Fredinho", "usuario": "Fredinho6", "senha": "664090314", "status": "Pendente"},
    {"nome": "Lidiane", "usuario": "59048676357235395158", "senha": "02052025", "status": "Pendente"},
    {"nome": "Cida", "usuario": "89429163675233408932", "senha": "28042025", "status": "Pendente"},
    {"nome": "Adilson", "usuario": "Adilson4", "senha": "315751435", "status": "Pendente"},
    {"nome": "Natan", "usuario": "cgykd620zdgr", "senha": "rergmfsf", "status": "Pendente"},
    {"nome": "Renato", "usuario": "RenatoDel0", "senha": "997708882", "status": "Pendente"}
]

# --- PERSISTÊNCIA ---
def carregar_clientes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT data_json FROM clientes")).fetchall()
            if not result:
                # Se estiver vazio, carrega os iniciais
                salvar_no_banco(CLIENTES_INICIAIS)
                return CLIENTES_INICIAIS
            return [json.loads(r[0]) for r in result]
    except: return CLIENTES_INICIAIS

def salvar_no_banco(lista_clientes):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes"))
        for c in lista_clientes:
            sql = text("INSERT INTO clientes (nome, data_json) VALUES (:nome, :data_json::jsonb)")
            conn.execute(sql, {"nome": c['nome'], "data_json": json.dumps(c)})

# --- INICIALIZAÇÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_clientes()

st.title("👥 Gestão de Clientes IPTV")

# --- LISTAGEM E EXCLUSÃO ---
df = pd.DataFrame(st.session_state.clientes)
df.insert(0, "🗑️", False)
edited_df = st.data_editor(df, hide_index=True, use_container_width=True)

if st.button("🗑️ Excluir Selecionados"):
    selecionados = edited_df[edited_df["🗑️"] == True]
    if not selecionados.empty:
        st.session_state.clientes = [c for c in st.session_state.clientes if c["nome"] not in selecionados["nome"].values]
        salvar_no_banco(st.session_state.clientes)
        st.rerun()
