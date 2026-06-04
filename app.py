import streamlit as st
import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão IPTV", page_icon="👥", layout="centered")

# --- CONEXÃO COM BANCO DE DADOS ---
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- FUNÇÕES DE PERSISTÊNCIA SQL ---
def carregar_dados():
    try:
        with engine.connect() as conn:
            # Tenta buscar a tabela de clientes
            query = text("SELECT nome, data_json FROM clientes")
            df = pd.read_sql(query, conn)
            
            dados = {}
            for _, row in df.iterrows():
                dados[row['nome']] = json.loads(row['data_json'])
            return dados
    except:
        # Se a tabela não existir ou estiver vazia, retorna estrutura vazia
        return {}

def salvar_dados(nome, dados_cliente):
    with engine.begin() as conn:
        sql = text("""
            INSERT INTO clientes (nome, data_json) 
            VALUES (:nome, :data_json)
            ON CONFLICT (nome) DO UPDATE SET data_json = EXCLUDED.data_json
        """)
        conn.execute(sql, {"nome": nome, "data_json": json.dumps(dados_cliente)})

# --- INICIALIZAÇÃO ---
if 'clientes' not in st.session_state:
    st.session_state.clientes = carregar_dados()

# --- INTERFACE ---
st.title("👥 Gestão de Clientes IPTV")

nome_cliente = st.text_input("Nome do Cliente")
valor = st.number_input("Valor", value=25.0)

if st.button("Salvar Cliente"):
    if nome_cliente:
        novo_registro = {"valor": valor, "status": "Pendente", "data": datetime.now().strftime("%d/%m/%Y")}
        st.session_state.clientes[nome_cliente] = novo_registro
        salvar_dados(nome_cliente, novo_registro)
        st.success("Cliente salvo no banco!")
    else:
        st.error("Preencha o nome!")

st.write("### Lista de Clientes")
st.json(st.session_state.clientes)
