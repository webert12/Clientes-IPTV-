import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

st.title("👥 Gestão de Clientes")

# Configuração de fuso horário de Brasília
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
hoje = datetime.now(CORRETO_FUSO).date()

# ======================================
# CONEXÃO COM O BANCO DE DADOS (SUPABASE)
# ======================================
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], poolclass=NullPool)

engine = get_engine()

# Função para carregar os clientes direto do banco em tempo real
def carregar_clientes_supabase():
    with engine.connect() as conn:
        query = text("SELECT id, nome, whatsapp, vencimento, status, valor, telas FROM vision_clientes ORDER BY nome")
        df = pd.read_sql(query, conn)
    return df

df_clientes = carregar_clientes_supabase()

# Controle da exclusão em massa
if "show_delete" not in st.session_state:
    st.session_state["show_delete"] = False

# Criando abas para organizar a tela de forma profissional
tab_lista, tab_cadastro, tab_importacao = st.tabs([
    "📋 Lista de Clientes", 
    "➕ Cadastrar Individual", 
    "📥 Importação em Massa"
])

# ======================================
# ABA 1: LISTA DE CLIENTES ATUAIS (COM EDIÇÃO)
# ======================================
with tab_lista:
    st.subheader("Todos os Clientes Armazenados na Nuvem")
    
    if not df_clientes.empty:
        # Mostra a tabela limpa para o usuário
        st.dataframe(
            df_clientes[["nome", "whatsapp", "vencimento", "status", "valor", "telas"]], 
            use_container_width=True, 
            hide_index=True
        )
        
        st.divider()
        
        # --- NOVA SEÇÃO: EDICAO DE CLIENTE DIRETO NA LISTA ---
        with st.expander("✏️ Editar Cadastro de um Cliente"):
            nomes_clientes = df_clientes["nome"].tolist()
            cliente_para_editar = st.selectbox("Escolha o cliente que deseja modificar:", ["-- Selecione um Cliente --"] + nomes_clientes)
            
            if cliente_para_editar != "-- Selecione um Cliente --":
                # Filtra os dados atuais do cliente selecionado na tabela
                dados_cli = df_clientes[df_clientes["nome"] == cliente_para_editar].iloc[0]
                cliente_id = int(dados_cli["id"])
                
                with st.form("form_editar_cliente_lista", clear_on_submit=False):
                    st.markdown(f"**Modificando os dados de:** `{dados_cli['nome']}`")
                    
                    edit_nome = st.text_input("Nome do Cliente:", value=dados_cli["nome"])
                    edit_whatsapp = st.text_input("WhatsApp (com DDD):", value=dados_cli["whatsapp"])
                    edit_vencimento = st.text_input("Data de Vencimento:", value=dados_cli["vencimento"])
                    
                    lista_status = ["Em Dia", "Vencendo", "Vencidos"]
                    status_atual = dados_cli["status"]
                    idx_status = lista_status.index(status_atual) if status_atual in lista_status else 0
                    edit_status = st.selectbox("Status Atual:", lista_status, index=idx_status)
                    
                    edit_valor = st.number_input("Valor da Mensalidade (R$):", min_value=0.0, value=float(dados_cli["valor"]), step=5.0)
                    edit_telas = st.number_input("Quantidade de Telas:", min_value=1, value=int(dados_cli["telas"]), step=1)
                    
                    btn_atualizar = st.form_submit_button("💾 Salvar Alterações na Nuvem")
                    
                    if btn_atualizar:
                        if not edit_nome.strip():
                            st.error("O nome do cliente não pode ficar vazio.")
                        else:
                            try:
                                with engine.begin() as conn:
                                    conn.execute(text("""
                                        UPDATE vision_clientes 
                                        SET nome = :nome, whatsapp = :whatsapp, vencimento = :vencimento, 
                                            status = :status, valor = :valor, telas = :telas 
                                        WHERE id = :id
                                    """), {
                                        "nome": edit_nome.strip(),
                                        "whatsapp": edit_whatsapp.strip(),
                                        "vencimento": edit_vencimento.strip(),
                                        "status": edit_status,
                                        "valor": edit_valor,
                                        "telas": int(edit_telas),
                                        "id": cliente_id
                                    })
                                st.success(f"Alterações salvas! Os novos valores de '{edit_nome}' já estão valendo em todo o sistema.")
                                st.cache_resource.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erro ao atualizar: Verifique se o novo nome inserido já pertence a outro usuário.")
        
        st.divider()
        
        # Botão para ativar/desativar exclusão em massa
        if st.button("🚨 Alternar Modo de Exclusão em Massa"):
            st.session_state["show_delete"] = not st.session_state["show_delete"]
            st.rerun()
            
        if st.session_state["show_delete"]:
            st.warning("⚠️ Atenção: A exclusão em massa removerá permanentemente os usuários selecionados do banco de dados.")
            clientes_para_deletar = st.multiselect("Selecione os clientes que deseja apagar:", df_clientes["nome"].tolist())
            
            if st.button("❌ Confirmar Exclusão Definitiva"):
                if clientes_para_deletar:
                    with engine.begin() as conn:
                        for nome in clientes_para_deletar:
                            conn.execute(text("DELETE FROM vision_clientes WHERE nome = :nome"), {"nome": nome})
                    st.success(f"Sucesso! {len(clientes_para_deletar)} clientes foram removidos.")
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.info("Nenhum cliente foi selecionado para exclusão.")
    else:
        st.info("Nenhum cliente cadastrado no banco de dados ainda.")

# ======================================
# ABA 2: CADASTRO INDIVIDUAL
# ======================================
with tab_cadastro:
    st.subheader("Inserir Novo Cliente Manualmente")
    with st.form("form_individual", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente:")
        whatsapp = st.text_input("WhatsApp (com DDD):")
        vencimento = st.text_input("Data de Vencimento (Ex: 10/06/2026):", value=hoje.strftime("10/%m/%Y"))
        status = st.selectbox("Status Inicial:", ["Em Dia", "Vencendo", "Vencidos"])
        valor = st.number_input("Valor Mensal (R$):", min_value=0.0, value=25.0, step=5.0)
        telas = st.number_input("Quantidade de Telas:", min_value=1, value=1, step=1)
        
        enviar = st.form_submit_button("💾 Salvar Cliente no Banco")
        
        if enviar:
            if not nome.strip():
                st.error("O campo Nome é obrigatório.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas)
                        """), {
                            "nome": nome.strip(),
                            "whatsapp": whatsapp.strip(),
                            "vencimento": vencimento.strip(),
                            "status": status,
                            "valor": valor,
                            "telas": int(telas)
                        })
                    st.success(f"Cliente '{nome}' cadastrado com sucesso na nuvem!")
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error("Erro: Já existe um cliente com este nome cadastrado.")

# ======================================
# ABA 3: IMPORTAÇÃO EM MASSA (INTELIGENTE)
# ======================================
with tab_importacao:
    st.subheader("Processamento Inteligente de Listas")
    
    texto = st.text_area("Cole aqui a sua lista de usuários / senhas / nomes (um por linha):", height=250, placeholder="Exemplo:\nMaria da Silva\nRejaneita:senha123\nJoão IPTV / Plano 2")
    
    c1, c2 = st.columns(2)
    with c1:
        valor_padrao = st.number_input("Valor Mensal Padrão (R$):", value=25.0, step=1.0)
        venc_padrao = st.text_input("Vencimento Padrão:", value=hoje.strftime("10/%m/%Y"))
    with c2:
        telas_padrao = st.number_input("Telas Padrão:", min_value=1, value=1, step=1)
        status_padrao = st.selectbox("Status Padrão:", ["Em Dia", "Vencendo", "Vencidos"])

    if st.button("🚀 Processar Importação Inteligente"):
        if not texto.strip():
            st.error("Por favor, cole algum texto na caixa acima para que o sistema possa processar.")
        else:
            linhas = texto.split("\n")
            sucesso = 0
            duplicados = 0
            
            with engine.begin() as conn:
                for linha in linhas:
                    linha_limpa = linha.strip()
                    if not linha_limpa:
                        continue
                    
                    nome_extraido = linha_limpa
                    for separador in [":", "/", "|", "-", ";"]:
                        if separador in linha_limpa:
                            partes = linha_limpa.split(separador)
                            provisorio = partes[0].strip()
                            if provisorio and not provisorio.isdigit():
                                nome_extraido = provisorio
                                break
                    
                    nome_final = nome_extraido.strip()
                    
                    if nome_final:
                        result = conn.execute(text("""
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas)
                            ON CONFLICT (nome) DO NOTHING
                        """), {
                            "nome": nome_final,
                            "whatsapp": "",
                            "vencimento": venc_padrao,
                            "status": status_padrao,
                            "valor": valor_padrao,
                            "telas": int(telas_padrao)
                        })
                        
                        if result.rowcount > 0:
                            sucesso += 1
                        else:
                            duplicados += 1
            
            st.success(f"Importação concluída! {sucesso} novos clientes adicionados diretamente no banco de dados.")
            if duplicados > 0:
                st.info(f"Nota: {duplicados} nomes foram ignorados porque já constavam no sistema.")
                
            st.cache_resource.clear()
            st.rerun()
