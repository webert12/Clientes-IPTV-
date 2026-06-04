import streamlit as st
import os
import hashlib
from datetime import datetime, timedelta, timezone
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, text
import pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Mendonça Poços", page_icon="💧", layout="centered", initial_sidebar_state="collapsed")
FUSO_BRASILIA = timezone(timedelta(hours=-3))
LIMITE_DINHEIRO_SEMANAL = 500.00
TURMAS = ["Rafael", "Ednaldo", "Luiz Felipe", "Carlos", "Cardoso", "Guilherme", "Paulo"]

# --- CONEXÃO COM BANCO DE DADOS (SQLAlchemy) ---
@st.cache_resource
def get_engine():
    # Use: postgresql://usuario:senha@host:5432/nome_banco
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- FUNÇÕES DE PERSISTÊNCIA SQL ---
def carregar_dados():
    with engine.connect() as conn:
        # Busca todas as equipes. Assume tabela 'equipes' com colunas correspondentes
        query = text("SELECT * FROM equipes")
        df = pd.read_sql(query, conn)
        
    dados_app = {}
    for t in TURMAS:
        row = df[df['nome'] == t]
        if not row.empty:
            # Aqui assumimos que o banco armazena o JSON na coluna 'data_json'
            import json
            dados_app[t] = json.loads(row.iloc[0]['data_json'])
        else:
            # Inicialização padrão se não existir
            dados_app[t] = {"senha_hash": gerar_hash("1234"), "transacoes": [], "historico": [], "pocos": [], "midias": []}
    return dados_app

def salvar_dados(dados):
    import json
    with engine.begin() as conn:
        for t, content in dados.items():
            json_str = json.dumps(content)
            sql = text("""
                INSERT INTO equipes (nome, data_json) 
                VALUES (:nome, :data_json)
                ON CONFLICT (nome) DO UPDATE SET data_json = EXCLUDED.data_json
            """)
            conn.execute(sql, {"nome": t, "data_json": json_str})

# --- FUNÇÕES AUXILIARES (Mantidas do original) ---
def gerar_hash(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def exportar_para_pdf(titulo, linhas_conteudo):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(titulo)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, titulo.upper())
    c.setFont("Helvetica", 11)
    y = 710
    for linha in linhas_conteudo:
        if y < 50:
            c.showPage(); y = 750
        c.drawString(50, y, str(linha))
        y -= 22
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def desenhar_logo():
    st.markdown("<h1 style='text-align: center;'>💧 MENDONÇA POÇOS</h1>", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADO ---
if 'dados' not in st.session_state: st.session_state.dados = carregar_dados()
if 'perfil' not in st.session_state: st.session_state.perfil = None

# --- FLUXO PRINCIPAL ---
# (O restante da lógica de interface permanece igual ao seu código, 
# apenas garantindo que sempre que houver alteração, você chame salvar_dados(st.session_state.dados))

# Exemplo de chamada na parte de Salvar:
# if st.button("Salvar"):
#     st.session_state.dados[t_ativa]["transacoes"].append(novo_item)
#     salvar_dados(st.session_state.dados)
#     st.rerun()

st.write("Sistema Conectado ao PostgreSQL via SQLAlchemy.")
