import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

st.title("📊 Dashboard Vision Play TV")

# Configuração do Fuso Horário de Brasília
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
agora_br = datetime.now(CORRETO_FUSO)
hoje = agora_br.date()

# Botão de atualização manual no topo para sincronismo instantâneo
if st.sidebar.button("🔄 Atualizar Dados do Banco"):
    st.cache_resource.clear()
    st.rerun()

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
        # Garante a criação da coluna 'telas' de forma segura caso ela ainda não exista
        conn.execute(text("""
            ALTER TABLE vision_clientes ADD COLUMN IF NOT EXISTS telas INTEGER DEFAULT 1;
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vision_historico (
                id SERIAL PRIMARY KEY,
                cliente VARCHAR(255),
                valor NUMERIC(10, 2),
                data VARCHAR(50)
            );
        """))

inicializar_banco()

# Sistema de migração automática
def migrar_dados_locais_para_supabase():
    with engine.connect() as conn:
        total_banco = conn.execute(text("SELECT COUNT(*) FROM vision_clientes")).scalar()
    
    if total_banco == 0:
        ARQ_CLIENTES = Path("clientes.json")
        ARQ_HISTORICO = Path("historico.json")
        
        if ARQ_CLIENTES.exists():
            try:
                dados_c = json.loads(ARQ_CLIENTES.read_text(encoding="utf-8"))
                with engine.begin() as conn:
                    for c in dados_c:
                        conn.execute(text("""
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas)
                            ON CONFLICT (nome) DO NOTHING
                        """), {
                            "nome": c.get("nome", ""),
                            "whatsapp": c.get("whatsapp", ""),
                            "vencimento": c.get("vencimento", ""),
                            "status": c.get("status", ""),
                            "valor": float(c.get("valor", 0)),
                            "telas": int(c.get("telas", 1))
                        })
            except:
                pass
                
        if ARQ_HISTORICO.exists():
            try:
                dados_h = json.loads(ARQ_HISTORICO.read_text(encoding="utf-8"))
                with engine.begin() as conn:
                    for h in dados_h:
                        conn.execute(text("""
                            INSERT INTO vision_historico (cliente, valor, data)
                            VALUES (:cliente, :valor, :data)
                        """), {
                            "cliente": h.get("cliente", ""),
                            "valor": float(h.get("valor", 0)),
                            "data": h.get("data", "")
                        })
            except:
                pass

migrar_dados_locais_para_supabase()

# Carregar dados diretamente do Supabase em tempo real (incluindo a coluna telas)
def carregar_dados_supabase():
    with engine.connect() as conn:
        res_clientes = conn.execute(text("SELECT nome, whatsapp, vencimento, status, valor, telas FROM vision_clientes ORDER BY nome")).fetchall()
        res_historico = conn.execute(text("SELECT cliente, valor, data FROM vision_historico ORDER BY id ASC")).fetchall()
        
        lista_clientes = []
        for r in res_clientes:
            lista_clientes.append({
                "nome": r[0],
                "whatsapp": r[1],
                "vencimento": r[2],
                "status": r[3],
                "valor": float(r[4] if r[4] is not None else 0),
                "telas": int(r[5] if r[5] is not None else 1)
            })
            
        lista_historico = []
        for r in res_historico:
            lista_historico.append({
                "cliente": r[0],
                "valor": float(r[1] if r[1] is not None else 0),
                "data": r[2]
            })
            
        return lista_clientes, lista_historico

# Carrega os dados reais e sincronizados do banco de dados
clientes, historico = carregar_dados_supabase()

# ======================================
# LÓGICA DE PROCESSAMENTO DO DASHBOARD
# ======================================
total_clientes = len(clientes)

em_dia = 0
vencendo = 0
vencidos = 0

receita_prevista = 0
receita_recebida = 0

for cliente in clientes:
    valor = float(cliente.get("valor", 0))
    receita_prevista += valor

    try:
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (vencimento - hoje).days

        if dias < 0:
            vencidos += 1
        elif dias <= 2:
            vencendo += 1
        else:
            em_dia += 1
    except:
        pass

for item in historico:
    receita_recebida += float(item.get("valor", 0))

receita_pendente = receita_prevista - receita_recebida

# ==========================
# CARDS INFORMATIVOS
# ==========================
c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 Clientes", total_clientes)
c2.metric("💰 Previsto", f"R$ {receita_prevista:.2f}")
c3.metric("✅ Recebido", f"R$ {receita_recebida:.2f}")
c4.metric("⚠️ Pendente", f"R$ {receita_pendente:.2f}")

st.divider()

# ==========================
# GRÁFICOS
# ==========================
col1, col2 = st.columns(2)

with col1:
    df_status = pd.DataFrame({
        "Status": ["Em Dia", "Vencendo", "Vencidos"],
        "Quantidade": [em_dia, vencendo, vencidos]
    })
    fig = px.pie(df_status, names="Status", values="Quantidade", title="Clientes")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_financeiro = pd.DataFrame({
        "Tipo": ["Recebido", "Pendente"],
        "Valor": [receita_recebida, receita_pendente]
    })
    fig2 = px.pie(df_financeiro, names="Tipo", values="Valor", title="Financeiro")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ==========================
# CLIENTES VENCENDO
# ==========================
st.subheader("⚠️ Clientes Próximos do Vencimento")
alertas = []

for cliente in clientes:
    try:
        vencimento = datetime.strptime(cliente["vencimento"], "%d/%m/%Y").date()
        dias = (vencimento - hoje).days

        if dias <= 2:
            alertas.append({
                "Nome": cliente["nome"],
                "WhatsApp": cliente["whatsapp"],
                "Vencimento": cliente["vencimento"]
            })
    except:
        pass

if alertas:
    st.dataframe(pd.DataFrame(alertas), use_container_width=True, hide_index=True)
else:
    st.success("Nenhum cliente próximo do vencimento.")

# ======================================
# SEÇÃO PROFISSIONAL DE GERENCIAMENTO (ABAS)
# ======================================
st.divider()
st.subheader("⚙️ Gerenciamento do Sistema (Ações em Tempo Real)")

# Adicionada a quarta aba "🧹 Limpeza Mensal" na lista abaixo
tab_pagamento, tab_cadastro, tab_editar, tab_limpeza = st.tabs([
    "💵 Registrar Pagamento", 
    "➕ Cadastrar Novo Cliente", 
    "✏️ Editar / Excluir Cliente",
    "🧹 Limpeza Mensal"
])

# ABA 1: REGISTRAR PAGAMENTO (AUTOMATIZADO)
with tab_pagamento:
    if clientes:
        nomes = [c["nome"] for c in clientes]
        sel = st.selectbox("Escolha o Cliente para registrar o pagamento:", nomes, key="sel_pagamento")
        cli = next(c for c in clientes if c["nome"] == sel)

        # Detecta automaticamente os valores reais e atuais do banco de dados
        valor_pago = float(cli.get("valor", 25.00))
        telas_cliente = int(cli.get("telas", 1))

        # Exibe os dados detectados para conferência visual rápida
        st.markdown(f"📋 **Plano Detectado para {cli['nome']}:**")
        st.markdown(f"🖥️ **Quantidade de Telas:** `{telas_cliente}` | 💰 **Valor Mensal Cadastrado:** `R$ {valor_pago:.2f}`")
        
        st.info(f"Ao clicar no botão abaixo, o sistema confirmará o recebimento de **R$ {valor_pago:.2f}** automaticamente.")

        if st.button("⚡ Confirmar Recebimento Automático", key="btn_confirmar_pag"):
            agora = datetime.now(CORRETO_FUSO)
            ano = agora.year
            mes = agora.month

            if agora.day > 10:
                mes += 1
                if mes > 12:
                    mes = 1
                    ano += 1

            novo_vencimento = datetime(ano, mes, 10).strftime("%d/%m/%Y")
            data_historico = agora.strftime("%d/%m/%Y %H:%M")

            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE vision_clientes 
                    SET status = 'Recebido', vencimento = :vencimento 
                    WHERE nome = :nome
                """), {"vencimento": novo_vencimento, "nome": cli["nome"]})

                conn.execute(text("""
                    INSERT INTO vision_historico (cliente, valor, data) 
                    VALUES (:cliente, :valor, :data)
                """), {"cliente": cli["nome"], "valor": valor_pago, "data": data_historico})

            st.success(f"Sucesso! Pagamento de R$ {valor_pago:.2f} processado para {cli['nome']}.")
            st.cache_resource.clear()
            st.rerun()
    else:
        st.info("Nenhum cliente disponível para registrar pagamentos.")

# ABA 2: CADASTRAR NOVO CLIENTE DIRETO NO SUPABASE
with tab_cadastro:
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
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas)
                        """), {
                            "nome": novo_nome.strip(),
                            "whatsapp": novo_whatsapp.strip(),
                            "vencimento": novo_vencimento.strip(),
                            "status": novo_status,
                            "valor": novo_valor,
                            "telas": int(novo_telas)
                        })
                    st.success(f"Cliente '{novo_nome}' saved permanentemente na nuvem!")
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error("Erro: Já existe um cliente cadastrado com esse nome.")

# ABA 3: EDITAR OU DELETAR CLIENTE
with tab_editar:
    if clientes:
        nomes_edit = [c["nome"] for c in clientes]
        sel_edit = st.selectbox("Selecione o cliente que deseja modificar ou remover:", nomes_edit, key="sel_edicao")
        cli_edit = next(c for c in clientes if c["nome"] == sel_edit)
        
        with st.form("form_modificar_cliente"):
            st.markdown(f"**Modificando dados de:** {cli_edit['nome']}")
            edit_whatsapp = st.text_input("WhatsApp cadastrado:", value=cli_edit["whatsapp"])
            edit_vencimento = st.text_input("Data de Vencimento:", value=cli_edit["vencimento"])
            edit_status = st.selectbox("Status Atual:", ["Em Dia", "Vencendo", "Vencidos"], index=["Em Dia", "Vencendo", "Vencidos"].index(cli_edit["status"]) if cli_edit["status"] in ["Em Dia", "Vencendo", "Vencidos"] else 0)
            edit_telas = st.number_input("Quantidade de Telas:", min_value=1, value=int(cli_edit.get("telas", 1)), step=1)
            edit_valor = st.number_input("Valor da Mensalidade (R$):", min_value=0.0, value=float(cli_edit["valor"]), step=5.0)
            
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                btn_atualizar = st.form_submit_button("💾 Salvar Alterações")
            with c_b2:
                btn_deletar = st.form_submit_button("🚨 EXCLUIR CLIENTE DO BANCO")
            
            if btn_atualizar:
                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE vision_clientes 
                        SET whatsapp = :whatsapp, vencimento = :vencimento, status = :status, valor = :valor, telas = :telas 
                        WHERE nome = :nome
                    """), {
                        "whatsapp": edit_whatsapp,
                        "vencimento": edit_vencimento,
                        "status": edit_status,
                        "valor": edit_valor,
                        "telas": int(edit_telas),
                        "nome": cli_edit["nome"]
                    })
                st.success(f"Os dados de {cli_edit['nome']} foram atualizados na nuvem!")
                st.cache_resource.clear()
                st.rerun()
                
            if btn_deletar:
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM vision_clientes WHERE nome = :nome"), {"nome": cli_edit["nome"]})
                st.success(f"Cliente {cli_edit['nome']} foi permanentemente removido.")
                st.cache_resource.clear()
                st.rerun()
    else:
        st.info("Nenhum cliente cadastrado.")

# ABA 4: 🧹 LIMPEZA MENSAL / RESET FINANCEIRO DO MÊS
with tab_limpeza:
    st.subheader("🧹 Resetar Recebimentos Mensais")
    st.markdown("""
    Use esta aba se quiser apagar os pagamentos registrados em um mês específico para reiniciar a contagem do faturamento. 
    **Isso NÃO apaga seus clientes**, apenas limpa o histórico de faturamento do período escolhido para que os gráficos comecem do zero.
    """)
    
    dict_meses = {
        "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
        "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
        "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
    }
    
    col_m, col_a = st.columns(2)
    with col_m:
        mes_sel = st.selectbox("Mês para limpar:", list(dict_meses.keys()), format_func=lambda x: dict_meses[x], index=int(hoje.strftime("%m")) - 1, key="limpeza_mes")
    with col_a:
        ano_sel = st.selectbox("Ano para limpar:", [hoje.year, hoje.year - 1, hoje.year + 1], key="limpeza_ano")
        
    padrao_data_busca = f"/%s/%s " % (mes_sel, ano_sel) # Busca pelo padrão '/MM/YYYY ' contido na string de data
    
    st.warning(f"⚠️ **Atenção:** Você está prestes a deletar todos os recebimentos de **{dict_meses[mes_sel]}/{ano_sel}**. O painel desse mês será zerado!")
    confirmar_check = st.checkbox(f"Confirmo que desejo zerar o histórico de {dict_meses[mes_sel]}/{ano_sel}.", key="chk_limpeza")
    
    if st.button("🔥 Confirmar Limpeza e Limpar Painel", key="btn_executar_limpeza"):
        if not confirmar_check:
            st.error("Você precisa marcar a caixa de seleção acima para autorizar a limpeza.")
        else:
            with engine.begin() as conn:
                # Remove os registros do histórico baseados no mês e ano selecionados
                resultado = conn.execute(
                    text("DELETE FROM vision_historico WHERE data LIKE :padrao"),
                    {"padrao": f"%{padrao_data_busca}%"}
                )
            
            st.success(f"💥 Sucesso! O faturamento de {dict_meses[mes_sel]}/{ano_sel} foi limpo do banco de dados!")
            st.cache_resource.clear()
            st.rerun()

# ==========================
# ÚLTIMOS RECEBIMENTOS
# ==========================
st.divider()
st.subheader("💵 Últimos Recebimentos")

if historico:
    ultimos = list(reversed(historico))[:10]
    st.dataframe(pd.DataFrame(ultimos), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum recebimento registrado.")

# ==========================
# BACKUP
# ==========================
st.subheader("📥 Backup Geral")
backup = {
    "clientes": clientes,
    "historico": historico,
    "exportado_em": datetime.now(CORRETO_FUSO).strftime("%d/%m/%Y %H:%M:%S")
}

st.download_button(
    "📦 Baixar Backup JSON",
    data=json.dumps(backup, indent=4, ensure_ascii=False),
    file_name="backup_sistema.json",
    mime="application/json"
)
