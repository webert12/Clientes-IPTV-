import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# ======================================
# BLOQUEIO DE SEGURANÇA (EXIGE LOGIN)
# ======================================
if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso Negado. Você precisa fazer o login no Dashboard principal primeiro.")
    st.stop()

# Captura estrita de quem está acessando a página
USUARIO_LOGADO = st.session_state["usuario_nome"]
ROLE_LOGADO = st.session_state["usuario_role"]

st.title("👥 Gestão de Clientes")
st.markdown(f"👤 **Sua Conta:** `{USUARIO_LOGADO}` | 🔒 **Acesso Isolado e Seguro**")

# Configuração de fuso horário
CORRETO_FUSO = ZoneInfo("America/Sao_Paulo")
hoje = datetime.now(CORRETO_FUSO).date()

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], poolclass=NullPool)

engine = get_engine()

# ======================================
# CARREGAMENTO TOTALMENTE ISOLADO POR USUÁRIO
# ======================================
def carregar_clientes_privados(dono):
    with engine.connect() as conn:
        # A MÁGICA DA BLINDAGEM: Filtra estritamente pelo dono da conta!
        # Se for um usuário novo, a tabela virá 100% vazia (virgem).
        res = conn.execute(text("""
            SELECT id, nome, whatsapp, vencimento, status, valor, telas 
            FROM vision_clientes 
            WHERE TRIM(LOWER(COALESCE(usuario_owner, 'admin'))) = TRIM(LOWER(:u))
            ORDER BY nome
        """), {"u": dono}).mappings().fetchall()
        return pd.DataFrame(res)

df_clientes = carregar_clientes_privados(USUARIO_LOGADO)

if "show_delete" not in st.session_state:
    st.session_state["show_delete"] = False

# Criando abas do gerenciador
tab_lista, tab_cadastro, tab_importacao, tab_limpeza = st.tabs([
    "📋 Sua Lista de Clientes", 
    "➕ Cadastrar Individual", 
    "📥 Importação em Massa",
    "🧹 Limpeza do Histórico"
])

# ======================================
# ABA 1: LISTA ISOLADA DE CLIENTES
# ======================================
with tab_lista:
    st.subheader("Todos os Seus Clientes Armazenados na Nuvem")
    
    if not df_clientes.empty:
        # Exibe apenas os clientes do usuário logado
        st.dataframe(
            df_clientes[["nome", "whatsapp", "vencimento", "status", "valor", "telas"]], 
            use_container_width=True, 
            hide_index=True
        )
        
        st.divider()
        
        # --- PAINEL DE EDIÇÃO RÁPIDA (BLINDADO) ---
        with st.expander("✏️ Painel de Edição Rápida", expanded=True):
            nomes_disponiveis = df_clientes["nome"].tolist()
            cliente_escolhido = st.selectbox("Selecione qual cliente deseja modificar:", ["-- Selecione um Cliente --"] + nomes_disponiveis, key=f"ed_rapida_{USUARIO_LOGADO}")
            
            if cliente_escolhido != "-- Selecione um Cliente --":
                dados_atuais = df_clientes[df_clientes["nome"] == cliente_escolhido].iloc[0]
                id_cliente = int(dados_atuais["id"])
                
                with st.form(f"form_ed_cli_lista_{USUARIO_LOGADO}"):
                    st.info(f"Modificando dados de: {cliente_escolhido}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        novo_nome = st.text_input("Nome do Cliente:", value=dados_atuais["nome"])
                        novo_whatsapp = st.text_input("WhatsApp:", value=dados_atuais.get("whatsapp", ""))
                        novo_vencimento = st.text_input("Vencimento:", value=dados_atuais.get("vencimento", ""))
                    with c2:
                        opcoes_status = ["Em Dia", "Vencendo", "Vencidos", "Recebido", "Pendente"]
                        stat_atual = dados_atuais.get("status", "Em Dia")
                        if stat_atual not in opcoes_status:
                            opcoes_status.append(stat_atual)
                        novo_status = st.selectbox("Status Atual:", opcoes_status, index=opcoes_status.index(stat_atual))
                        
                        novo_valor = st.number_input("Valor Mensal (R$):", min_value=0.0, value=float(dados_atuais.get("valor", 25.0)), step=5.0)
                        nova_tela = st.number_input("Quantidade de Telas:", min_value=1, value=int(dados_atuais.get("telas", 1)), step=1)
                    
                    if st.form_submit_button("💾 Confirmar e Salvar Alterações"):
                        if not novo_nome.strip():
                            st.error("O campo Nome não pode ficar vazio.")
                        else:
                            with engine.begin() as conn:
                                # A atualização só ocorre se o cliente pertencer de fato ao usuário logado
                                conn.execute(text("""
                                    UPDATE vision_clientes
                                    SET nome = :nome, whatsapp = :whatsapp, vencimento = :vencimento,
                                        status = :status, valor = :valor, telas = :telas
                                    WHERE id = :id AND TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:owner))
                                """), {
                                    "nome": novo_nome.strip(), "whatsapp": novo_whatsapp.strip(),
                                    "vencimento": novo_vencimento.strip(), "status": novo_status,
                                    "valor": novo_valor, "telas": int(nova_tela), "id": id_cliente, "owner": USUARIO_LOGADO
                                })
                            st.success("Alterações salvas com sucesso!")
                            st.rerun()
        
        st.divider()
        
        # --- EXCLUSÃO EM MASSA (BLINDADA) ---
        if st.button("🚨 Alternar Modo de Exclusão em Massa", key=f"btn_alt_del_{USUARIO_LOGADO}"):
            st.session_state["show_delete"] = not st.session_state["show_delete"]
            st.rerun()
            
        if st.session_state["show_delete"]:
            st.warning("⚠️ Atenção: A exclusão em massa removerá permanentemente os usuários selecionados da sua conta.")
            clientes_para_deletar = st.multiselect("Selecione os clientes que deseja apagar:", df_clientes["nome"].tolist(), key=f"ms_del_{USUARIO_LOGADO}")
            
            if st.button("❌ Confirmar Exclusão Definitiva", key=f"btn_del_def_{USUARIO_LOGADO}"):
                if clientes_para_deletar:
                    with engine.begin() as conn:
                        for nome in clientes_para_deletar:
                            # A exclusão também exige a chave do dono para não apagar cliente de outra pessoa
                            conn.execute(text("DELETE FROM vision_clientes WHERE nome = :nome AND TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:owner))"), {"nome": nome, "owner": USUARIO_LOGADO})
                    st.success(f"Sucesso! {len(clientes_para_deletar)} clientes foram removidos da sua conta.")
                    st.rerun()
    else:
        st.info("Sua lista está vazia. Comece a cadastrar seus clientes na aba ao lado!")

# ======================================
# ABA 2: CADASTRO INDIVIDUAL (Sempre salva no nome do logado)
# ======================================
with tab_cadastro:
    st.subheader("Inserir Novo Cliente na Sua Conta")
    with st.form(f"form_indiv_{USUARIO_LOGADO}", clear_on_submit=True):
        nome = st.text_input("Nome do Cliente:")
        whatsapp = st.text_input("WhatsApp (com DDD):")
        vencimento = st.text_input("Data de Vencimento (Ex: 10/06/2026):", value=hoje.strftime("10/%m/%Y"))
        status = st.selectbox("Status Inicial:", ["Em Dia", "Vencendo", "Vencidos"])
        valor = st.number_input("Valor Mensal (R$):", min_value=0.0, value=25.0, step=5.0)
        telas = st.number_input("Quantidade de Telas:", min_value=1, value=1, step=1)
        
        if st.form_submit_button("💾 Salvar Cliente"):
            if not nome.strip():
                st.error("O campo Nome é obrigatório.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas, usuario_owner)
                            VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas, :owner)
                        """), {
                            "nome": nome.strip(), "whatsapp": whatsapp.strip(), "vencimento": vencimento.strip(),
                            "status": status, "valor": valor, "telas": int(telas), "owner": USUARIO_LOGADO
                        })
                    st.success(f"Cliente '{nome}' adicionado à sua lista com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error("Erro: Um cliente com este nome já existe no sistema global.")

# ======================================
# ABA 3: IMPORTAÇÃO EM MASSA (BLINDADA)
# ======================================
with tab_importacao:
    st.subheader("Processamento Inteligente de Listas")
    
    texto = st.text_area("Cole aqui a sua lista (um por linha):", height=250, placeholder="Exemplo:\nMaria da Silva\nJoão IPTV / Plano 2", key=f"txt_imp_{USUARIO_LOGADO}")
    
    c1, c2 = st.columns(2)
    with c1:
        valor_padrao = st.number_input("Valor Mensal Padrão (R$):", value=25.0, step=1.0, key=f"val_imp_{USUARIO_LOGADO}")
        venc_padrao = st.text_input("Vencimento Padrão:", value=hoje.strftime("10/%m/%Y"), key=f"ven_imp_{USUARIO_LOGADO}")
    with c2:
        telas_padrao = st.number_input("Telas Padrão:", min_value=1, value=1, step=1, key=f"tel_imp_{USUARIO_LOGADO}")
        status_padrao = st.selectbox("Status Padrão:", ["Em Dia", "Vencendo", "Vencidos"], key=f"stat_imp_{USUARIO_LOGADO}")

    if st.button("🚀 Processar Importação Inteligente", key=f"btn_imp_{USUARIO_LOGADO}"):
        if not texto.strip():
            st.error("Por favor, cole algum texto na caixa acima.")
        else:
            linhas = texto.split("\n")
            sucesso, duplicados = 0, 0
            
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
                        # Checa duplicidade antes de inserir para evitar erros que travem o app
                        existe = conn.execute(text("SELECT id FROM vision_clientes WHERE nome = :n"), {"n": nome_final}).fetchone()
                        if existe:
                            duplicados += 1
                        else:
                            conn.execute(text("""
                                INSERT INTO vision_clientes (nome, whatsapp, vencimento, status, valor, telas, usuario_owner)
                                VALUES (:nome, :whatsapp, :vencimento, :status, :valor, :telas, :owner)
                            """), {
                                "nome": nome_final, "whatsapp": "", "vencimento": venc_padrao,
                                "status": status_padrao, "valor": valor_padrao, "telas": int(telas_padrao), "owner": USUARIO_LOGADO
                            })
                            sucesso += 1
            
            st.success(f"Importação concluída! {sucesso} clientes adicionados na sua conta.")
            if duplicados > 0:
                st.info(f"Nota: {duplicados} nomes foram ignorados porque já existem cadastrados.")
            st.rerun()

# ======================================
# ABA 4: LIMPEZA DE HISTÓRICO ISOLADA
# ======================================
with tab_limpeza:
    st.subheader("🧹 Limpar Seus Lançamentos Financeiros")
    st.markdown("Isso deletará apenas os lançamentos do **seu** painel financeiro para a data escolhida. Seus clientes continuarão cadastrados.")
    
    data_limpar = st.text_input("Data desejada (Ex: 10/06 ou /06 para o mês todo):", value=hoje.strftime("%d/%m"), key=f"inp_clean_aba_{USUARIO_LOGADO}")
    st.warning("⚠️ Isso apagará permanentemente apenas os **seus** registros de recebimento!")

    if st.button("🔥 Confirmar Limpeza", key=f"btn_clean_aba_{USUARIO_LOGADO}"):
        if data_limpar.strip():
            with engine.begin() as conn:
                conn.execute(text("""
                    DELETE FROM vision_historico 
                    WHERE data LIKE :padrao AND TRIM(LOWER(usuario_owner)) = TRIM(LOWER(:owner))
                """), {"padrao": f"%{data_limpar.strip()}%", "owner": USUARIO_LOGADO})
            st.success("Seu histórico foi atualizado/limpo com sucesso!")
            st.rerun()
