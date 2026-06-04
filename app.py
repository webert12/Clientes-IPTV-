import streamlit as st
import os
import hashlib
import json
import io
from datetime import datetime, timedelta, timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, text
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Mendonça Poços", page_icon="💧", layout="centered", initial_sidebar_state="collapsed")
FUSO_BRASILIA = timezone(timedelta(hours=-3))
LIMITE_DINHEIRO_SEMANAL = 500.00
TURMAS = ["Rafael", "Ednaldo", "Luiz Felipe", "Carlos", "Cardoso", "Guilherme", "Paulo"]

# --- CONEXÃO COM BANCO DE DADOS (SQLAlchemy) ---
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- FUNÇÕES DE DADOS (SQLAlchemy + Supabase Storage) ---
def carregar_dados():
    try:
        with engine.connect() as conn:
            query = text("SELECT nome, data_json FROM equipes")
            df = pd.read_sql(query, conn)
        
        dados_app = {}
        # Converte o que veio do banco
        for _, row in df.iterrows():
            dados_app[row['nome']] = json.loads(row['data_json'])
            
        # Garante que equipes sem dados no banco sejam criadas com estrutura inicial
        for t in TURMAS:
            if t not in dados_app:
                dados_app[t] = {"senha_hash": gerar_hash("1234"), "transacoes": [], "historico": [], "pocos": [], "midias": []}
        return dados_app
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {t: {"senha_hash": gerar_hash("1234"), "transacoes": [], "historico": [], "pocos": [], "midias": []} for t in TURMAS}

def salvar_dados(dados):
    with engine.begin() as conn:
        for t, content in dados.items():
            sql = text("""
                INSERT INTO equipes (nome, data_json) 
                VALUES (:nome, :data_json)
                ON CONFLICT (nome) DO UPDATE SET data_json = EXCLUDED.data_json
            """)
            conn.execute(sql, {"nome": t, "data_json": json.dumps(content)})

# --- DEMAIS FUNÇÕES ---
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
        if y < 50: c.showPage(); y = 750
        c.drawString(50, y, str(linha))
        y -= 22
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# --- INICIALIZAÇÃO DE ESTADO ---
if 'dados' not in st.session_state: st.session_state.dados = carregar_dados()
if 'perfil' not in st.session_state: st.session_state.perfil = None

# --- UI (EXEMPLO DE USO) ---
st.title("💧 Mendonça Poços")

if st.session_state.perfil is None:
    st.write("Bem-vindo! Selecione o perfil para continuar.")
    if st.button("Entrar"):
        st.session_state.perfil = "OPERADOR"
        st.rerun()
else:
    st.success("Conectado ao Banco de Dados.")
    if st.button("Salvar Teste"):
        # Exemplo de como usar a função em qualquer lugar do seu app:
        st.session_state.dados["Rafael"]["transacoes"].append({"valor": 10.0, "data": "2026-06-04"})
        salvar_dados(st.session_state.dados)
        st.rerun()
