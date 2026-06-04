import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from supabase import create_client, Client

# --- CONFIGURAÇÃO VISUAL ESTILO "APK" ---
st.set_page_config(page_title="Mendonça Poços", page_icon="💧", layout="centered", initial_sidebar_state="collapsed")

# CONFIGURAÇÃO DO FUSO HORÁRIO DE BRASÍLIA (UTC-3)
FUSO_BRASILIA = timezone(timedelta(hours=-3))

LIMITE_DINHEIRO_SEMANAL = 500.00

# Lista estática de equipes autorizadas no sistema
TURMAS = ["Rafael", "Ednaldo", "Luiz Felipe", "Carlos", "Cardoso", "Guilherme", "Paulo"]

# --- FUNÇÃO DE CONEXÃO COM O SUPABASE ---
def obter_cliente_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# --- FUNÇÃO DE CRIPTOGRAFIA (HASHING SHA-256) ---
def gerar_hash(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

# --- FUNÇÃO PARA GERAR PDF EM MEMÓRIA ---
def exportar_para_pdf(titulo, linhas_conteudo):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(titulo)
    
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.0, 0.28, 0.67)
    c.drawString(50, 750, titulo.upper())
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.line(50, 740, 550, 740)
    
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0, 0, 0)
    y = 710
    
    for linha in linhas_conteudo:
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = 750
        c.drawString(50, y, str(linha))
        y -= 22
        
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# --- FUNÇÕES DE ARMAZENAMENTO VIA SUPABASE ---
def carregar_dados():
    SENHA_PADRAO_PROVISORIA = gerar_hash("1234")
    dados_app = {}
    
    try:
        supabase = obter_cliente_supabase()
        response = supabase.table("equipes").select("*").execute()
        dados_db = response.data
        
        db_turmas = {row["nome"]: row for row in dados_db}
        
        for t in TURMAS:
            if t in db_turmas:
                row = db_turmas[t]
                dados_app[t] = {
                    "senha_hash": row.get("senha_hash", SENHA_PADRAO_PROVISORIA),
                    "transacoes": row.get("transacoes", []),
                    "historico": row.get("historico", []),
                    "pocos": row.get("pocos", []),
                    "midias": row.get("midias", [])
                }
            else:
                # Se a equipe não existe na tabela, inicializa no Supabase automaticamente
                nova_estrutura = {
                    "nome": t,
                    "senha_hash": SENHA_PADRAO_PROVISORIA,
                    "transacoes": [],
                    "historico": [],
                    "pocos": [],
                    "midias": []
                }
                supabase.table("equipes").insert(nova_estrutura).execute()
                dados_app[t] = {
                    "senha_hash": SENHA_PADRAO_PROVISORIA,
                    "transacoes": [],
                    "historico": [],
                    "pocos": [],
                    "midias": []
                }
        return dados_app
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        return {t: {"senha_hash": SENHA_PADRAO_PROVISORIA, "transacoes": [], "historico": [], "pocos": [], "midias": []} for t in TURMAS}

def salvar_dados(dados):
    try:
        supabase = obter_cliente_supabase()
        for t in TURMAS:
            if t in dados:
                payload = {
                    "nome": t,
                    "senha_hash": dados[t]["senha_hash"],
                    "transacoes": dados[t]["transacoes"],
                    "historico": dados[t]["historico"],
                    "pocos": dados[t]["pocos"],
                    "midias": dados[t]["midias"]
                }
                supabase.table("equipes").upsert(payload).execute()
    except Exception as e:
        st.error(f"Erro ao sincronizar dados com o Supabase: {e}")

# Inicialização do Estado da Sessão
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()
if 'perfil' not in st.session_state:
    st.session_state.perfil = None
if 'turma' not in st.session_state:
    st.session_state.turma = None
if 'selecionou_usuario' not in st.session_state:
    st.session_state.selecionou_usuario = None
if 'foto_key' not in st.session_state:
    st.session_state.foto_key = 0
if 'video_key' not in st.session_state:
    st.session_state.video_key = 0
if 'msg_sucesso' not in st.session_state:
    st.session_state.msg_sucesso = None

# --- DESIGN DA LOGO DA EMPRESA ---
def desenhar_logo():
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.markdown("<h1 style='font-size: 50px; margin: 0;'>💧</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #0047AB; font-family: sans-serif; margin: 5px 0;'>MENDONÇA POÇOS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: gray; letter-spacing: 2px; font-size: 12px;'>======= GESTÃO CORPORATIVA =======</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- TELA DE LOGIN / SELEÇÃO DE EQUIPE ---
if st.session_state.perfil is None:
    desenhar_logo()
    if st.session_state.selecionou_usuario is None: 
        st.write("Identifique-se para entrar no aplicativo:") 
        if st.button("🔐 ACESSAR SISTEMA"): 
            st.session_state.selecionou_usuario = "FUNCIONARIO_FORM" 
            st.rerun() 
        st.divider() 
        if st.button("🔑 ACESSO ADMINISTRADOR (ADM)", type="secondary"): 
            st.session_state.selecionou_usuario = "ADM_SENHA" 
            st.rerun() 
    elif st.session_state.selecionou_usuario == "FUNCIONARIO_FORM": 
        st.subheader("Login de Colaborador") 
        usuario_digitado = st.text_input("Digite seu Nome (Usuário)") 
        senha_digitada = st.text_input("Digite sua Senha", type="password") 
        c_voltar, c_entrar = st.columns(2) 
        if c_voltar.button("Voltar"): 
            st.session_state.selecionou_usuario = None 
            st.rerun() 
        if c_entrar.button("Entrar"): 
            if usuario_digitado in TURMAS: 
                hash_digitada = gerar_hash(senha_digitada)
                hash_salva = st.session_state.dados[usuario_digitado].get("senha_hash")
                
                if hash_digitada == hash_salva: 
                    st.session_state.perfil = "TURMA" 
                    st.session_state.turma = usuario_digitado 
                    st.session_state.selecionou_usuario = None 
                    st.rerun() 
                else: 
                    st.error("Senha incorreta! Tente novamente.") 
            else: 
                st.error("Usuário não encontrado.")
    elif st.session_state.selecionou_usuario == "ADM_SENHA": 
        st.write("Digite a senha master para o perfil: **ADM**") 
        senha_adm = st.text_input("Senha ADM", type="password") 
        c_voltar, c_entrar = st.columns(2) 
        if c_voltar.button("Voltar"): 
            st.session_state.selecionou_usuario = None 
            st.rerun() 
        if c_entrar.button("Entrar como ADM"): 
            senha_adm_segura = st.secrets.get("SENHA_ADM", "adm9988")
            if senha_adm == senha_adm_segura: 
                st.session_state.perfil = "ADM" 
                st.session_state.selecionou_usuario = "ADM_MONITORAMENTO" 
                st.rerun() 
            else: 
                st.error("Senha de Administrador incorreta!")
    elif st.session_state.selecionou_usuario == "ADM_MONITORAMENTO": 
        st.subheader("Painel de Monitoramento (ADM)") 
        col1, col2 = st.columns(2) 
        for idx, t in enumerate(TURMAS): 
            c = col1 if idx % 2 == 0 else col2 
            if c.button(f"Ver {t}"): 
                st.session_state.perfil = "TURMA" 
                st.session_state.turma = t 
                st.session_state.selecionou_usuario = None 
                st.rerun() 
        st.divider() 
        if st.button("Ir para o Painel Geral Consolidado 📊"): 
            st.session_state.selecionou_usuario = None 
            st.rerun()

# --- INTERFACE PRINCIPAL OPERACIONAL ---
else:
    c_status, c_sair = st.columns([3, 1])
    with c_status:
        identificacao = st.session_state.turma if st.session_state.perfil == "TURMA" else "Gestor Geral (ADM)"
        st.markdown(f"🟢 Logado: {identificacao}")
    with c_sair:
        if st.button("Sair"):
            st.session_state.perfil = None
            st.session_state.turma = None
            st.session_state.selecionou_usuario = None
            st.rerun()
    
    desenhar_logo()
    
    if st.session_state.perfil == "ADM":
        aba_relatorio, aba_adm = st.tabs(["📅 Relatório Mensal", "⚙️ Painel ADM"])
        
        with aba_relatorio:
            st.subheader("📅 Histórico Mensal de Equipes") 
            target_turma = st.selectbox("Selecione o Colaborador para Auditar", TURMAS) 
            hist = st.session_state.dados[target_turma]["historico"] 
            pocos = st.session_state.dados[target_turma].get("pocos", []) 
            midias = st.session_state.dados[target_turma].get("midias", [])
            
            meses = sorted(list(set(t.get("ano_mes", datetime.now(FUSO_BRASILIA).strftime("%Y-%m")) for t in hist + pocos + midias)), reverse=True) 
            if meses: 
                mes_sel = st.selectbox("Escolha o mês", meses, key="mes_sel_adm") 
                sub_f, sub_p, sub_m = st.tabs(["💰 Custos", "🚰 Poços", "📷 Mídias"]) 
                
                with sub_f: 
                    t_mes = [t for t in hist if t.get("ano_mes") == mes_sel] 
                    dias_disponiveis = sorted(list(set(t['data'][:5] for t in t_mes if 'data' in t)), reverse=True)
                    
                    if dias_disponiveis:
                        dias_pdf_sel = st.multiselect("📄 Escolha os dias para incluir no PDF:", dias_disponiveis, default=dias_disponiveis, key="dias_pdf_adm")
                        if dias_pdf_sel:
                            t_filtrado_pdf = [t for t in t_mes if t.get('data', '')[:5] in dias_pdf_sel]
                            linhas_pdf_fin = [f"{t['data']} | {t['categoria']}: R${t['valor']:.2f}" for t in t_filtrado_pdf]
                            pdf_financeiro = exportar_para_pdf(f"Custos - {target_turma} - Filtro customizado", linhas_pdf_fin)
                            st.download_button("📥 Baixar Relatório Financeiro (PDF)", pdf_financeiro, f"financeiro_{target_turma}_{mes_sel}.pdf", "application/pdf")
                        else:
                            st.warning("Selecione ao menos 1 dia para gerar o PDF.")
                            
                        st.markdown("---")
                        dia_sel = st.selectbox("🔍 Escolha o dia para analisar custos na tela:", dias_disponiveis, key="dia_sel_adm_custos")
                        t_dia = [t for t in t_mes if t.get('data', '')[:5] == dia_sel]
                        for t in reversed(t_dia): 
                            st.write(f"💵 {t['data']} - {t['categoria']} - R${t['valor']:.2f}") 
                    else:
                        st.caption("Nenhum custo registrado.")
                
                with sub_p: 
                    p_mes = [p for p in pocos if p.get("ano_mes") == mes_sel] 
                    if p_mes: 
                        sel_poco = st.selectbox("Escolha o poço para analisar/baixar:", [f"{p['data']} - {p['cliente']}" for p in p_mes], key="sel_poco_adm") 
                        p_baixar = next(p for p in p_mes if f"{p['data']} - {p['cliente']}" == sel_poco) 
                        
                        st.markdown(f"""
                        <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #0047AB; margin-bottom: 15px;'>
                            <h4 style='margin-top:0;'>📋 Dados do Relatório</h4>
                            <b>📍 Cliente:</b> {p_baixar['cliente']}<br>
                            <b>🏙️ Cidade:</b> {p_baixar['cidade']}<br>
                            <b>📏 Metragem Perfurada:</b> {p_baixar['metragem']} metros<br>
                            <b>👥 Funcionários na Obra:</b> {p_baixar['funcionarios']}<br>
                            <b>🧱 Materiais Utilizados:</b><br>{p_baixar['material']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.checkbox("✏️ Corrigir/Editar este Relatório (ADM)", key="edit_mode_adm"):
                            with st.form("form_editar_poco_adm"):
                                novo_cl = st.text_input("Cliente", value=p_baixar['cliente'])
                                novo_ci = st.text_input("Cidade", value=p_baixar['cidade'])
                                novo_mt = st.text_input("Metragem", value=p_baixar['metragem'])
                                novo_fun = st.text_input("Funcionários", value=p_baixar['funcionarios'])
                                novo_mat = st.text_area("Material", value=p_baixar['material'])
                                
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    idx_original = next(i for i, p in enumerate(st.session_state.dados[target_turma]["pocos"]) if id(p) == id(p_baixar))
                                    st.session_state.dados[target_turma]["pocos"][idx_original].update({
                                        "cliente": novo_cl, "cidade": novo_ci, "metragem": novo_mt, "material": novo_mat, "funcionarios": novo_fun
                                    })
                                    salvar_dados(st.session_state.dados)
                                    st.success("Relatório atualizado com sucesso!")
                                    st.rerun()
                        
                        linhas_pdf_poco = [
                            f"Data de Registro: {p_baixar['data']}", f"Cliente: {p_baixar['cliente']}", f"Cidade: {p_baixar['cidade']}",
                            f"Metragem Perfurada: {p_baixar['metragem']} metros", f"Funcionarios na Obra: {p_baixar['funcionarios']}", f"Materiais Utilizados: {p_baixar['material']}"
                        ]
                        pdf_poco = exportar_para_pdf(f"Relatorio de Poco - {p_baixar['cliente']}", linhas_pdf_poco)
                        st.download_button("📥 Baixar este Poço (PDF)", pdf_poco, f"poco_{p_baixar['cliente']}_{p_baixar['data'].replace('/','-')}.pdf", "application/pdf") 
                    else: 
                        st.caption("Nenhum poço encontrado.")
                
                with sub_m:
                    m_mes = [m for m in midias if m.get("ano_mes") == mes_sel]
                    if m_mes:
                        pocos_disponiveis = sorted(list(set(m.get("poco", "Geral / Sem Poço Específico") for m in m_mes)))
                        poco_selecionado = st.selectbox("🔍 Escolha o Poço para visualizar fotos e vídeos:", pocos_disponiveis, key="poco_sel_midia_adm")
                        m_filtrado = [m for m in m_mes if m.get("poco", "Geral / Sem Poço Específico") == poco_selecionado]
                        
                        fotos_filtradas = [m for m in m_filtrado if "video" not in m.get("tipo", "").lower()]
                        videos_filtrados = [m for m in m_filtrado if "video" in m.get("tipo", "").lower()]
                        
                        st.markdown(f"### 📁 Arquivos de: *{poco_selecionado}*")
                        with st.expander("📸 FOTOS SALVAS"):
                            if fotos_filtradas:
                                for f in reversed(fotos_filtradas):
                                    st.write(f"📅 {f['data']}")
                                    st.image(f['caminho'], use_container_width=True)
                                    st.divider()
                            else: st.caption("Nenhuma foto localizada para este poço.")
                        
                        with st.expander("🎥 VÍDEOS SALVOS"):
                            if videos_filtrados:
                                for v in reversed(videos_filtrados):
                                    st.write(f"📅 {v['data']}")
                                    st.video(v['caminho'])
                                    st.divider()
                            else: st.caption("Nenhum vídeo localizado para este poço.")
            else:
                st.info("Nenhum registro encontrado para este colaborador.")

        with aba_adm:
            st.subheader("⚙️ Controle Global e Segurança")
            
            # --- GERENCIADOR DE SENHAS CRIPTOGRAFADAS ---
            st.markdown("### 🔑 Gerenciador de Senhas das Equipes")
            with st.form("form_mudar_senha"):
                func_sel = st.selectbox("Selecione o Funcionário", TURMAS)
                nova_senha = st.text_input("Definir Nova Senha", type="password")
                if st.form_submit_button("🔒 ATUALIZAR SENHA"):
                    if nova_senha.strip() != "":
                        st.session_state.dados[func_sel]["senha_hash"] = gerar_hash(nova_senha)
                        salvar_dados(st.session_state.dados)
                        st.success(f"Senha do colaborador {func_sel} modificada e criptografada!")
                    else:
                        st.error("A senha não pode ser enviada em branco.")
            
            st.divider()
            if st.button("❌ RESETAR GASTOS DA SEMANA (TODAS AS EQUIPES)", type="primary"): 
                for t in TURMAS: 
                    st.session_state.dados[t]["transacoes"] = [] 
                salvar_dados(st.session_state.dados)
                st.success("Limites semanais resetados com sucesso!")
                st.rerun()

    else:
        aba1, aba2 = st.tabs(["📝 Registrar", "📅 Relatório Mensal"])
        
        with aba1: 
            t_ativa = st.session_state.turma 
            trans_semana = st.session_state.dados[t_ativa]["transacoes"] 
            
            total_gasto_dinheiro = sum(t['valor'] for t in trans_semana if t.get('metodo') == 'Dinheiro')
            saldo_restante_dinheiro = LIMITE_DINHEIRO_SEMANAL - total_gasto_dinheiro
            
            c1, c2 = st.columns(2) 
            c1.metric("💵 Saldo Restante", f"R$ {saldo_restante_dinheiro:.2f}") 
            c2.metric("💳 Acumulado Cartão", f"R$ {sum(t['valor'] for t in trans_semana if t.get('metodo') == 'Cartão'):.2f}") 
            
            mostrar_painel = st.toggle("📝 Registrar Despesas", value=False) 
            if mostrar_painel: 
                cat_principal = st.selectbox("Categoria", ["Café da Manhã", "Almoço", "Cafe da tarde", "Jantar", "Outros"]) 
                categoria_final = cat_principal
                
                if cat_principal == "Outros":
                    sub_cat = st.selectbox("Detalhe do Gasto", ["Pedágio", "Oficinas", "Lojas", "Outro (Especificar)"])
                    if sub_cat == "Lojas":
                        nome_loja = st.text_input("Qual o nome da loja?")
                        categoria_final = f"Loja: {nome_loja}"
                    elif sub_cat == "Outro (Especificar)":
                        desc_gasto = st.text_input("O que foi gasto?")
                        categoria_final = f"Outro: {desc_gasto}"
                    else:
                        categoria_final = sub_cat

                with st.form("form_final_envio", clear_on_submit=True): 
                    opcao_pgto = st.radio("Método de Pagamento", ["💵 Dinheiro", "💳 Cartão"], horizontal=True) 
                    valor_input = st.text_input("Valor R$") 
                    
                    if st.form_submit_button("SALVAR"): 
                        if not valor_input:
                            st.error("Informe o valor!")
                        else:
                            valor_final = float(valor_input.replace(",", ".")) 
                            novo_trans = {
                                "data": datetime.now(FUSO_BRASILIA).strftime("%d/%m %H:%M"), 
                                "ano_mes": datetime.now(FUSO_BRASILIA).strftime("%Y-%m"), 
                                "categoria": categoria_final, 
                                "metodo": "Dinheiro" if "Dinheiro" in opcao_pgto else "Cartão", 
                                "valor": valor_final
                            } 
                            st.session_state.dados[t_ativa]["transacoes"].append(novo_trans) 
                            st.session_state.dados[t_ativa]["historico"].append(novo_trans) 
                            salvar_dados(st.session_state.dados)
                            st.success("Despesa salva!")
                            st.rerun() 
                        
            mostrar_pocos = st.toggle("🚰 Poços Perfurados", value=False) 
            if mostrar_pocos: 
                with st.form("form_pocos", clear_on_submit=True): 
                    cl = st.text_input("Cliente")
                    ci = st.text_input("Cidade")
                    mt = st.text_input("Metragem")
                    mat = st.text_area("Material")
                    fun = st.text_input("Funcionários")
                    
                    st.markdown("---")
                    st.write("**Anexar Mídias desta Obra 📷**")
                    
                    foto_capturada = st.file_uploader("Opção 1: Tirar ou escolher Foto:", type=["jpg", "jpeg", "png"], key=f"foto_auto_{st.session_state.foto_key}")
                    video_gravado = st.file_uploader("Opção 2: Filmar ou escolher Vídeo:", type=["mp4", "mov", "avi", "3gp"], key=f"video_auto_{st.session_state.video_key}")
                    
                    if st.form_submit_button("SALVAR RELATÓRIO"): 
                        st.session_state.dados[t_ativa]["pocos"].append({
                            "data": datetime.now(FUSO_BRASILIA).strftime("%d/%m/%Y"), 
                            "ano_mes": datetime.now(FUSO_BRASILIA).strftime("%Y-%m"), 
                            "cliente": cl, "cidade": ci, "metragem": mt, "material": mat, "funcionarios": fun
                        }) 
                        
                        nome_poco_vinculo = f"{cl} ({ci})" if (cl or ci) else "Geral / Sem Poço Específico"
                        
                        try:
                            supabase_client = obter_cliente_supabase()
                            
                            if foto_capturada is not None:
                                nome_arquivo_foto = f"{t_ativa}_{datetime.now(FUSO_BRASILIA).strftime('%Y%m%d_%H%M%S')}_camera.jpg"
                                bytes_foto = foto_capturada.getvalue()
                                
                                # Upload direto para o bucket público 'midias' do Supabase
                                supabase_client.storage.from_("midias").upload(
                                    path=nome_arquivo_foto,
                                    file=bytes_foto,
                                    file_options={"content-type": "image/jpeg"}
                                )
                                public_url_foto = supabase_client.storage.from_("midias").get_public_url(nome_arquivo_foto)
                                
                                st.session_state.dados[t_ativa]["midias"].append({
                                    "data": datetime.now(FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M"), 
                                    "ano_mes": datetime.now(FUSO_BRASILIA).strftime("%Y-%m"),
                                    "caminho": public_url_foto, "tipo": "image/jpeg", "poco": nome_poco_vinculo
                                })
                                st.session_state.foto_key += 1

                            if video_gravado is not None:
                                extensao = video_gravado.name.split(".")[-1]
                                nome_arquivo_video = f"{t_ativa}_{datetime.now(FUSO_BRASILIA).strftime('%Y%m%d_%H%M%S')}.{extensao}"
                                bytes_video = video_gravado.getvalue()
                                
                                # Upload de vídeo direto para o Supabase
                                supabase_client.storage.from_("midias").upload(
                                    path=nome_arquivo_video,
                                    file=bytes_video,
                                    file_options={"content-type": video_gravado.type}
                                )
                                public_url_video = supabase_client.storage.from_("midias").get_public_url(nome_arquivo_video)
                                
                                st.session_state.dados[t_ativa]["midias"].append({
                                    "data": datetime.now(FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M"), 
                                    "ano_mes": datetime.now(FUSO_BRASILIA).strftime("%Y-%m"),
                                    "caminho": public_url_video, "tipo": video_gravado.type, "poco": nome_poco_vinculo
                                })
                                st.session_state.video_key += 1
                                
                        except Exception as media_err:
                            st.error(f"Erro ao salvar mídias no Supabase Storage: {media_err}")

                        salvar_dados(st.session_state.dados)
                        st.session_state.msg_sucesso = "✅ Relatório e mídias salvos com sucesso!"
                        st.rerun()

                st.markdown("""
                    <iframe src="about:blank" style="display:none;" onload="
                        const doc = window.parent.document;
                        const aplicarFiltrosCamera = () => {
                            const inputs = doc.querySelectorAll('input[type=\"file\"]');
                            inputs.forEach(input => {
                                if (input.accept.includes('mp4') || input.accept.includes('video') || input.accept.includes('jpg')) {
                                    input.setAttribute('capture', 'environment');
                                }
                            });
                        };
                        setInterval(aplicarFiltrosCamera, 800);
                    "></iframe>
                """, unsafe_allow_html=True)

        with aba2: 
            st.subheader("📅 Histórico Mensal") 
            t_ativa = st.session_state.turma 
            
            if st.session_state.msg_sucesso:
                st.success(st.session_state.msg_sucesso)
                st.session_state.msg_sucesso = None
                
            hist = st.session_state.dados[t_ativa]["historico"] 
            pocos = st.session_state.dados[t_ativa].get("pocos", []) 
            midias = st.session_state.dados[t_ativa].get("midias", [])
            
            meses = sorted(list(set(t.get("ano_mes", datetime.now(FUSO_BRASILIA).strftime("%Y-%m")) for t in hist + pocos + midias)), reverse=True) 
            if meses: 
                mes_sel = st.selectbox("Escolha o mês", meses, key="mes_sel_turma") 
                sub_f, sub_p, sub_m = st.tabs(["💰 Custos", "🚰 Poços", "📷 Mídias"]) 
                
                with sub_f: 
                    t_mes = [t for t in hist if t.get("ano_mes") == mes_sel] 
                    dias_disponiveis = sorted(list(set(t['data'][:5] for t in t_mes if 'data' in t)), reverse=True)
                    
                    if dias_disponiveis:
                        dias_pdf_sel = st.multiselect("📄 Selecione os dias para incluir no PDF:", dias_disponiveis, default=dias_disponiveis, key="dias_pdf_turma")
                        if dias_pdf_sel:
                            t_filtrado_pdf = [t for t in t_mes if t.get('data', '')[:5] in dias_pdf_sel]
                            linhas_pdf_fin = [f"{t['data']} | {t['categoria']}: R${t['valor']:.2f}" for t in t_filtrado_pdf]
                            pdf_financeiro = exportar_para_pdf(f"Relatorio Financeiro - {t_ativa}", linhas_pdf_fin)
                            st.download_button("📥 Baixar Relatório Financeiro (PDF)", pdf_financeiro, f"financeiro_{t_ativa}_{mes_sel}.pdf", "application/pdf") 
                        else:
                            st.warning("Selecione pelo menos um dia para gerar o relatório PDF.")
                            
                        st.markdown("---")
                        dia_sel = st.selectbox("🔍 Escolha o dia para analisar custos na tela:", dias_disponiveis, key="dia_sel_turma_custos")
                        t_dia = [t for t in t_mes if t.get('data', '')[:5] == dia_sel]
                        for t in reversed(t_dia): 
                            st.write(f"💵 {t['data']} - {t['categoria']} - R${t['valor']:.2f}") 
                    else:
                        st.caption("Nenhum custo registrado.")
                
                with sub_p: 
                    p_mes = [p for p in pocos if p.get("ano_mes") == mes_sel] 
                    if p_mes: 
                        sel_poco = st.selectbox("Escolha o poço para analisar/baixar:", [f"{p['data']} - {p['cliente']}" for p in p_mes], key="sel_poco_turma") 
                        p_baixar = next(p for p in p_mes if f"{p['data']} - {p['cliente']}" == sel_poco) 
                        
                        st.markdown(f"""
                        <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #0047AB; margin-bottom: 15px;'>
                            <h4 style='margin-top:0;'>📋 Dados Atuais do Relatório</h4>
                            <b>📍 Cliente:</b> {p_baixar['cliente']}<br>
                            <b>🏙️ Cidade:</b> {p_baixar['cidade']}<br>
                            <b>📏 Metragem Perfurada:</b> {p_baixar['metragem']} metros<br>
                            <b>👥 Funcionários na Obra:</b> {p_baixar['funcionarios']}<br>
                            <b>🧱 Materiais Utilizados:</b><br>{p_baixar['material']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.checkbox("✏️ Editar este Relatório", key="edit_mode_turma"):
                            with st.form("form_editar_poco_turma"):
                                novo_cl = st.text_input("Cliente", value=p_baixar['cliente'])
                                novo_ci = st.text_input("Cidade", value=p_baixar['cidade'])
                                novo_mt = st.text_input("Metragem", value=p_baixar['metragem'])
                                novo_fun = st.text_input("Funcionários", value=p_baixar['funcionarios'])
                                novo_mat = st.text_area("Material", value=p_baixar['material'])
                                
                                if st.form_submit_button("💾 Salvar Alterações"):
                                    idx_original = next(i for i, p in enumerate(st.session_state.dados[t_ativa]["pocos"]) if id(p) == id(p_baixar))
                                    st.session_state.dados[t_ativa]["pocos"][idx_original].update({
                                        "cliente": novo_cl, "cidade": novo_ci, "metragem": novo_mt, "material": novo_mat, "funcionarios": novo_fun
                                    })
                                    salvar_dados(st.session_state.dados)
                                    st.success("Relatório corrigido com sucesso!")
                                    st.rerun()
                        
                        linhas_pdf_poco = [
                            f"Data de Registro: {p_baixar['data']}", f"Cliente: {p_baixar['cliente']}", f"Cidade: {p_baixar['cidade']}",
                            f"Metragem Perfurada: {p_baixar['metragem']} metros", f"Funcionarios na Obra: {p_baixar['funcionarios']}", f"Materiais Utilizados: {p_baixar['material']}"
                        ]
                        pdf_poco = exportar_para_pdf(f"Relatorio de Poco - {p_baixar['cliente']}", lines_pdf_poco)
                        st.download_button("📥 Baixar este Poço (PDF)", pdf_poco, f"poco_{p_baixar['cliente']}_{p_baixar['data'].replace('/','-')}.pdf", "application/pdf") 
                    else: 
                        st.caption("Nenhum poço encontrado.")
                
                with sub_m:
                    m_mes = [m for m in midias if m.get("ano_mes") == mes_sel]
                    if m_mes:
                        pocos_disponiveis = sorted(list(set(m.get("poco", "Geral / Sem Poço Específico") for m in m_mes)))
                        poco_selecionado = st.selectbox("🔍 Escolha o Poço para visualizar fotos e vídeos:", pocos_disponiveis, key="poco_sel_midia_turma")
                        m_filtrado = [m for m in m_mes if m.get("poco", "Geral / Sem Poço Específico") == poco_selecionado]
                        
                        fotos_filtradas = [m for m in m_filtrado if "video" not in m.get("tipo", "").lower()]
                        videos_filtrados = [m for m in m_filtrado if "video" in m.get("tipo", "").lower()]
                        
                        st.markdown(f"### 📁 Arquivos de: *{poco_selecionado}*")
                        with st.expander("📸 FOTOS SALVAS"):
                            if fotos_filtradas:
                                for f in reversed(fotos_filtradas):
                                    st.write(f"📅 {f['data']}")
                                    st.image(f['caminho'], use_container_width=True)
                                    st.divider()
                            else: st.caption("Nenhuma foto localizada para este poço.")
                        with st.expander("🎥 VÍDEOS SALVOS"):
                            if videos_filtrados:
                                for v in reversed(videos_filtrados):
                                    st.write(f"📅 {v['data']}")
                                    st.video(v['caminho'])
                                    st.divider()
                            else: st.caption("Nenhum vídeo localizado para este poço.")
                    else: st.caption("Nenhuma mídia registrada para este colaborador neste mês.")
