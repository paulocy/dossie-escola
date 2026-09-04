import os
import re
import json
import unicodedata
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import streamlit as st
import urllib.parse

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dossiê Escolar - SaaS", page_icon="🏫", layout="centered")

# --- FUNÇÃO DE SLUG E ISOLAMENTO MULTI-TENANT ---
def gerar_slug(texto):
    if not texto:
        return "geral"
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', sem_acento).lower().strip('_')
    return slug

def obter_caminho_arquivo(nome_arquivo):
    escola_nome = st.session_state.get('escola_nome', 'colegio_modelo')
    escola_cidade = st.session_state.get('escola_cidade', 'londrina_pr')
    
    identificador_unico = f"{gerar_slug(escola_nome)}_{gerar_slug(escola_cidade)}"
    
    diretorio_escola = os.path.join("dados_escolas", identificador_unico)
    os.makedirs(diretorio_escola, exist_ok=True)
    return os.path.join(diretorio_escola, nome_arquivo)

NOME_DA_ESCOLA = "Sistema de Gestão Pedagógica"
ARQUIVO_LOGO = "logo.png"

# --- GESTÃO DE CREDENCIAIS DINÂMICAS ---
def carregar_credenciais():
    caminho = obter_caminho_arquivo("config.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    # Credenciais padrão caso o arquivo não exista
    creds_iniciais = {
        "senha_professor": "prof123",
        "senha_coordenador": "coord123",
        "senha_secretaria": "sec123"
    }
    salvar_credenciais(creds_iniciais)
    return creds_iniciais

def salvar_credenciais(creds):
    caminho = obter_caminho_arquivo("config.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False, indent=4)

def inicializar_arquivos():
    # Garante a criação do config.json com as senhas da escola
    carregar_credenciais()
    
    caminho_alunos = obter_caminho_arquivo("alunos.csv")
    if not os.path.exists(caminho_alunos):
        df_inicial = pd.DataFrame({
            "Turma": ["1º Ano A", "1º Ano A", "2º Ano B"],
            "Aluno": ["Ana Silva", "Carlos Mendes", "Beatriz Costa"],
            "Responsavel1": ["Maria Silva", "João Mendes", "Ana Costa"],
            "telefone1": ["43999991111", "43999992222", "43999993333"],
            "Responsavel2": ["Pedro Silva", "", ""],
            "telefone2": ["43999994444", "", ""]
        })
        df_inicial.to_csv(caminho_alunos, index=False)
        
    caminho_cats = obter_caminho_arquivo("categorias.txt")
    if not os.path.exists(caminho_cats):
        cats_iniciais = [
            "Atraso injustificado", 
            "Não entregue atividade", 
            "Indisciplina em sala", 
            "Dificuldade de aprendizagem", 
            "Conflito com colegas"
        ]
        with open(caminho_cats, "w", encoding="utf-8") as f:
            f.write("\n".join(cats_iniciais))

def carregar_alunos():
    caminho = obter_caminho_arquivo("alunos.csv")
    if os.path.exists(caminho):
        df = pd.read_csv(caminho)
        for col in ["Turma", "Aluno", "Responsavel1", "telefone1", "Responsavel2", "telefone2"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["Turma", "Aluno", "Responsavel1", "telefone1", "Responsavel2", "telefone2"])

def carregar_categorias():
    caminho = obter_caminho_arquivo("categorias.txt")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Indisciplina em sala"]

def carregar_dados():
    caminho = obter_caminho_arquivo("ocorrencias.csv")
    if os.path.exists(caminho):
        df = pd.read_csv(caminho)
        if "Matéria" not in df.columns:
            df["Matéria"] = "Geral / Diversos"
        return df
    else:
        return pd.DataFrame(columns=["Data", "Turma", "Aluno", "Matéria", "Categoria", "Descrição"])

def gerar_pdf(dados_aluno, nome_aluno, turma):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    if os.path.exists(ARQUIVO_LOGO):
        pdf.image(ARQUIVO_LOGO, x=10, y=8, w=30)
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, st.session_state.get('escola_nome', NOME_DA_ESCOLA), ln=True, align="C")
    pdf.set_font("helvetica", "I", 12)
    pdf.cell(0, 10, "Dossiê de Ocorrências Escolares - Relatório Oficial", ln=True, align="C")
    pdf.ln(15) 
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, f"Aluno(a): {nome_aluno}", ln=True)
    pdf.cell(0, 8, f"Turma: {turma}", ln=True)
    pdf.cell(0, 8, f"Data de Emissão: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(25, 10, "Data", border=1, align="C")
    pdf.cell(40, 10, "Matéria", border=1, align="C")
    pdf.cell(50, 10, "Natureza", border=1, align="C")
    pdf.cell(75, 10, "Descrição", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    for _, linha in dados_aluno.iterrows():
        data_br = pd.to_datetime(linha['Data']).strftime('%d/%m/%Y')
        materia_val = str(linha.get('Matéria', 'Geral'))[:20]
        pdf.cell(25, 10, data_br, border=1, align="C")
        pdf.cell(40, 10, materia_val, border=1)
        pdf.cell(50, 10, str(linha['Categoria'])[:25], border=1) 
        pdf.cell(75, 10, str(linha['Descrição'])[:40], border=1)
        pdf.ln()
        
    pdf.ln(25)
    pdf.cell(95, 10, "___________________________________", align="C")
    pdf.cell(95, 10, "___________________________________", align="C", ln=True)
    pdf.cell(95, 10, "Coordenação Pedagógica", align="C")
    pdf.cell(95, 10, "Responsável Legal", align="C")
    
    return bytes(pdf.output())

# 2. LÓGICA DE LOGIN COM CREDENCIAIS DA ESCOLA
if "nivel_acesso" not in st.session_state:
    st.session_state.nivel_acesso = None
if "escola_nome" not in st.session_state:
    st.session_state.escola_nome = ""
if "escola_cidade" not in st.session_state:
    st.session_state.escola_cidade = ""

if st.session_state.nivel_acesso is None:
    st.markdown(f"<h1 style='text-align: center;'>🏫 Portal de Gestão Escolar</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Identifique sua instituição para acessar</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        nome_inst = st.text_input("🏢 Nome da Escola:", placeholder="Ex: Colégio Alfa").strip()
        cidade_inst = st.text_input("📍 Cidade / Estado:", placeholder="Ex: Londrina - PR").strip()
        senha_digitada = st.text_input("🔑 Senha de acesso:", type="password")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            if not nome_inst or not cidade_inst:
                st.error("Preencha o nome da escola e a cidade/estado.")
            else:
                st.session_state.escola_nome = nome_inst
                st.session_state.escola_cidade = cidade_inst
                inicializar_arquivos()
                
                # Carrega as senhas específicas desta escola
                creds = carregar_credenciais()
                
                if senha_digitada == creds.get("senha_professor"):
                    st.session_state.nivel_acesso = "Professor"
                    st.rerun()
                elif senha_digitada == creds.get("senha_coordenador"):
                    st.session_state.nivel_acesso = "Coordenador"
                    st.rerun()
                elif senha_digitada == creds.get("senha_secretaria"):
                    st.session_state.nivel_acesso = "Secretaria"
                    st.rerun()
                else:
                    st.error("Senha incorreta para esta instituição.")
    st.stop()

# Garante inicialização
inicializar_arquivos()

with st.sidebar:
    st.image(ARQUIVO_LOGO, width=150) if os.path.exists(ARQUIVO_LOGO) else None
    st.info(f"🏫 **{st.session_state.escola_nome}**\n📍 *{st.session_state.escola_cidade}*\n\n👤 Usuário: **{st.session_state.nivel_acesso}**")
    if st.button("Sair / Trocar Escola", use_container_width=True):
        st.session_state.nivel_acesso = None
        st.rerun()

# 3. FORMULÁRIO DO PROFESSOR
def exibir_formulario():
    st.markdown("### 📝 Registrar Nova Ocorrência")
    
    df_alunos = carregar_alunos()
    categorias_disponiveis = carregar_categorias()
    
    if df_alunos.empty:
        st.warning("⚠️ Nenhuma turma ou aluno cadastrado. Solicite à Secretaria.")
        return

    turmas_disponiveis = sorted(df_alunos["Turma"].dropna().unique().tolist())
    materias_disponiveis = [
        "Matemática", "Português", "Biologia", "História", "Geografia", 
        "Física", "Química", "Inglês", "Educação Física", "Sociologia", "Filosofia", "Geral / Diversos"
    ]

    with st.form("form_ocorrencia"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_registro = st.date_input("Data da Ocorrência", date.today())
        with col2:
            turma = st.selectbox("Turma", turmas_disponiveis)
        with col3:
            materia = st.selectbox("Matéria / Disciplina", materias_disponiveis)
        
        alunos_da_turma = sorted(df_alunos[df_alunos["Turma"] == turma]["Aluno"].dropna().unique().tolist())
        
        col4, col5 = st.columns(2)
        with col4:
            aluno = st.selectbox("Nome do Aluno", alunos_da_turma)
        with col5:
            categoria = st.selectbox("Natureza da Ocorrência", categorias_disponiveis)
            
        descricao = st.text_area("Descrição detalhada da ocorrência:")
        submit = st.form_submit_button("Salvar Registro", use_container_width=True)

    if submit:
        novo_dado = pd.DataFrame([{
            "Data": data_registro, "Turma": turma, "Aluno": aluno, 
            "Matéria": materia, "Categoria": categoria, "Descrição": descricao
        }])
        caminho_csv = obter_caminho_arquivo("ocorrencias.csv")
        novo_dado.to_csv(caminho_csv, mode='a', header=not os.path.exists(caminho_csv), index=False)
        st.success(f"✅ Ocorrência registrada com sucesso para {aluno}!")

# 4. PAINEL DA SECRETARIA (Com Gerenciamento de Senhas)
def exibir_painel_secretaria():
    st.markdown("### 🗂️ Gestão Administrativa")
    
    tab_alunos, tab_massa, tab_categorias, tab_senhas = st.tabs([
        "➕ Alunos e Turmas", "📤 Importação em Lote", "⚙️ Categorias", "🔑 Senhas de Acesso"
    ])
    
    df_alunos = carregar_alunos()

    with tab_alunos:
        with st.form("form_novo_aluno"):
            st.subheader("Matricular Aluno Individualmente")
            c1, c2 = st.columns(2)
            with c1:
                turmas_existentes = sorted(df_alunos["Turma"].dropna().unique().tolist())
                if turmas_existentes:
                    tipo_turma = st.radio("Destino", ["Turma Existente", "Nova Turma"])
                    turma_escolhida = st.selectbox("Turma", turmas_existentes) if tipo_turma == "Turma Existente" else st.text_input("Nova Turma:").strip()
                else:
                    turma_escolhida = st.text_input("Nome da Nova Turma:").strip()
                novo_aluno = st.text_input("Nome Completo do Aluno:").strip()
                resp1 = st.text_input("Nome Responsável 1:").strip()
                tel1 = st.text_input("Telefone 1 (Ex: 43999991111):").strip()
            with c2:
                st.write("")
                st.write("")
                resp2 = st.text_input("Nome Responsável 2 (Opcional):").strip()
                tel2 = st.text_input("Telefone 2 (Opcional):").strip()
            
            btn_cadastrar = st.form_submit_button("Cadastrar Aluno", use_container_width=True)
            if btn_cadastrar:
                if not turma_escolhida or not novo_aluno or not resp1 or not tel1:
                    st.error("Preencha obrigatoriamente a Turma, o Aluno, o Responsavel1 e o telefone1.")
                else:
                    novo_registro = pd.DataFrame([{
                        "Turma": turma_escolhida, 
                        "Aluno": novo_aluno.title(),
                        "Responsavel1": resp1.title(),
                        "telefone1": tel1,
                        "Responsavel2": resp2.title() if resp2 else "",
                        "telefone2": tel2 if tel2 else ""
                    }])
                    df_atualizado = pd.concat([df_alunos, novo_registro], ignore_index=True)
                    df_atualizado.to_csv(obter_caminho_arquivo("alunos.csv"), index=False)
                    st.success(f"Aluno(a) {novo_aluno.title()} cadastrado(a)!")
                    st.rerun()

    with tab_massa:
        st.subheader("Importação em Lote (Excel/CSV)")
        st.info("O arquivo deve conter obrigatoriamente as colunas: **Turma**, **Aluno**, **Responsavel1**, **telefone1**, e opcionalmente **Responsavel2**, **telefone2**.")
        arquivo_upload = st.file_uploader("Arquivo de matrículas", type=["csv", "xlsx"])
        if arquivo_upload is not None:
            try:
                df_importado = pd.read_csv(arquivo_upload) if arquivo_upload.name.endswith('.csv') else pd.read_excel(arquivo_upload)
                colunas_obrigatorias = ['Turma', 'Aluno', 'Responsavel1', 'telefone1']
                
                if all(col in df_importado.columns for col in colunas_obrigatorias):
                    if 'Responsavel2' not in df_importado.columns:
                        df_importado['Responsavel2'] = ""
                    if 'telefone2' not in df_importado.columns:
                        df_importado['telefone2'] = ""
                        
                    colunas_finais = ['Turma', 'Aluno', 'Responsavel1', 'telefone1', 'Responsavel2', 'telefone2']
                    df_importado = df_importado[colunas_finais]
                    
                    st.dataframe(df_importado.head(), use_container_width=True)
                    if st.button("Confirmar Importação", type="primary"):
                        df_importado.to_csv(obter_caminho_arquivo("alunos.csv"), index=False)
                        st.success("Base atualizada com sucesso!")
                        st.rerun()
                else:
                    st.error(f"O arquivo precisa conter obrigatoriamente as colunas: {colunas_obrigatorias}")
            except Exception as e:
                st.error(f"Erro: {e}")

    with tab_categorias:
        st.subheader("Personalização de Tipos de Ocorrência")
        cats_atuais = carregar_categorias()
        
        with st.form("form_nova_categoria"):
            nova_cat = st.text_input("Adicionar nova natureza de ocorrência:").strip()
            btn_add_cat = st.form_submit_button("Adicionar Categoria")
            if btn_add_cat and nova_cat:
                if nova_cat not in cats_atuais:
                    cats_atuais.append(nova_cat)
                    with open(obter_caminho_arquivo("categorias.txt"), "w", encoding="utf-8") as f:
                        f.write("\n".join(cats_atuais))
                    st.success(f"Categoria '{nova_cat}' adicionada!")
                    st.rerun()
                else:
                    st.warning("Essa categoria já existe.")
        
        st.write("Categorias ativas atualmente:")
        st.write(cats_atuais)

    with tab_senhas:
        st.subheader("🔑 Alterar Senhas de Acesso da Instituição")
        creds_atuais = carregar_credenciais()
        
        with st.form("form_alterar_senhas"):
            nova_s_prof = st.text_input("Nova Senha de Professor:", value=creds_atuais.get("senha_professor", ""), type="password")
            nova_s_coord = st.text_input("Nova Senha de Coordenação:", value=creds_atuais.get("senha_coordenador", ""), type="password")
            nova_s_sec = st.text_input("Nova Senha de Secretaria:", value=creds_atuais.get("senha_secretaria", ""), type="password")
            
            btn_salvar_senhas = st.form_submit_button("Salvar Novas Senhas", use_container_width=True)
            if btn_salvar_senhas:
                if not nova_s_prof or not nova_s_coord or not nova_s_sec:
                    st.error("Nenhuma das senhas pode ficar em branco.")
                else:
                    novas_creds = {
                        "senha_professor": nova_s_prof,
                        "senha_coordenador": nova_s_coord,
                        "senha_secretaria": nova_s_sec
                    }
                    salvar_credenciais(novas_creds)
                    st.success("🔒 Senhas atualizadas com sucesso para esta escola!")

    st.divider()
    st.subheader("📋 Base Atual de Alunos e Contatos")
    st.dataframe(df_alunos, use_container_width=True, hide_index=True)

# 5. GERENCIAMENTO DE PERFIS E TELAS
if st.session_state.nivel_acesso == "Professor":
    exibir_formulario()

elif st.session_state.nivel_acesso == "Secretaria":
    exibir_painel_secretaria()

elif st.session_state.nivel_acesso == "Coordenação" or st.session_state.nivel_acesso == "Coordenador":
    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "📝 Novo Registro", "📋 Dossiês & WhatsApp", "📊 Relatórios por Período", "⚙️ Gerenciar Ocorrências", "🗂️ Secretaria"
    ])
    
    with aba1:
        exibir_formulario()
        
    with aba2:
        st.markdown("### 🔍 Consulta de Dossiês e Canal Direto")
        dados_historico = carregar_dados()
        df_alunos = carregar_alunos()

        if dados_historico.empty:
            st.info("Nenhuma ocorrência registrada.")
        else:
            turmas_disponiveis = sorted(df_alunos["Turma"].dropna().unique().tolist())
            c1, c2 = st.columns(2)
            with c1:
                turma_busca = st.selectbox("Turma:", turmas_disponiveis, key="d_turma")
            with c2:
                alunos_turma = sorted(df_alunos[df_alunos["Turma"] == turma_busca]["Aluno"].dropna().unique().tolist())
                aluno_busca = st.selectbox("Aluno:", alunos_turma, key="d_aluno")
            
            dados_filtrados = dados_historico[dados_historico["Aluno"] == aluno_busca]
            st.dataframe(dados_filtrados, use_container_width=True, hide_index=True)
            
            if not dados_filtrados.empty:
                aluno_info = df_alunos[df_alunos["Aluno"] == aluno_busca]
                resp1_nome = str(aluno_info["Responsavel1"].values[0]) if not aluno_info.empty and pd.notna(aluno_info["Responsavel1"].values[0]) else "Responsável 1"
                tel1_raw = str(aluno_info["telefone1"].values[0]) if not aluno_info.empty and pd.notna(aluno_info["telefone1"].values[0]) else ""
                
                resp2_nome = str(aluno_info["Responsavel2"].values[0]) if not aluno_info.empty and pd.notna(aluno_info["Responsavel2"].values[0]) else "Responsável 2"
                tel2_raw = str(aluno_info["telefone2"].values[0]) if not aluno_info.empty and pd.notna(aluno_info["telefone2"].values[0]) else ""
                
                tel1 = re.sub(r'\D', '', tel1_raw)
                tel2 = re.sub(r'\D', '', tel2_raw)
                
                msg_whatsapp = f"Olá, responsável por {aluno_busca} ({turma_busca}). Segue o resumo das ocorrências registradas na escola:\n\n"
                for _, r in dados_filtrados.iterrows():
                    mat_txt = f"[{r.get('Matéria', 'Geral')}] " if 'Matéria' in r else ""
                    msg_whatsapp += f"- Data: {r['Data']} | {mat_txt}{r['Categoria']}: {r['Descrição']}\n"
                msg_encoded = urllib.parse.quote(msg_whatsapp)
                
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    if tel1.strip():
                        link_wa1 = f"https://wa.me/55{tel1}?text={msg_encoded}"
                        st.markdown(f'<a href="{link_wa1}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;width:100%;">💬 WhatsApp ({resp1_nome})</button></a>', unsafe_allow_html=True)
                    else:
                        st.info("Resp. 1 sem telefone cadastrado.")
                with col_w2:
                    if tel2.strip():
                        link_wa2 = f"https://wa.me/55{tel2}?text={msg_encoded}"
                        st.markdown(f'<a href="{link_wa2}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;width:100%;">💬 WhatsApp ({resp2_nome})</button></a>', unsafe_allow_html=True)
                    else:
                        st.caption("Resp. 2 sem telefone cadastrado.")

                st.write("")
                arquivo_pdf = gerar_pdf(dados_filtrados, aluno_busca, turma_busca)
                st.download_button(
                    label=f"📄 Baixar Relatório Oficial de {aluno_busca} (PDF)",
                    data=arquivo_pdf,
                    file_name=f"Relatorio_{aluno_busca.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )

    with aba3:
        st.markdown("### 📈 Indicadores Pedagógicos com Filtro por Período e Matéria")
        dados_historico = carregar_dados()
        
        if dados_historico.empty:
            st.info("Sem dados suficientes.")
        else:
            dados_historico['Data_Obj'] = pd.to_datetime(dados_historico['Data']).dt.date
            min_d = dados_historico['Data_Obj'].min()
            max_d = dados_historico['Data_Obj'].max()
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                data_inicio = st.date_input("Data Inicial", min_d)
            with c_f2:
                data_fim = st.date_input("Data Final", max_d)
                
            df_periodo = dados_historico[(dados_historico['Data_Obj'] >= data_inicio) & (dados_historico['Data_Obj'] <= data_fim)]
            
            if df_periodo.empty:
                st.warning("Nenhuma ocorrência encontrada no período selecionado.")
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Total no Período", len(df_periodo))
                with col_m2:
                    t_freq = df_periodo['Turma'].mode()[0] if not df_periodo.empty else "-"
                    st.metric("Turma Frequente", t_freq)
                with col_m3:
                    c_freq = df_periodo['Matéria'].mode()[0] if not df_periodo.empty else "-"
                    st.metric("Matéria Principal", c_freq)
                
                st.divider()
                cg1, cg2 = st.columns(2)
                with cg1:
                    st.subheader("Por Matéria")
                    st.bar_chart(df_periodo['Matéria'].value_counts())
                with cg2:
                    st.subheader("Por Natureza")
                    st.bar_chart(df_periodo['Categoria'].value_counts())

    with aba4:
        st.markdown("### ⚙️ Gestão, Edição e Exclusão de Ocorrências")
        dados_historico = carregar_dados()
        if dados_historico.empty:
            st.info("Nenhum registro para gerenciar.")
        else:
            st.write("Edite diretamente as informações ou exclua registros incorretos:")
            df_editado = st.data_editor(dados_historico, num_rows="dynamic", use_container_width=True)
            if st.button("Salvar Alterações no Banco de Ocorrências", type="primary"):
                df_editado.drop(columns=[c for c in df_editado.columns if 'Data_Obj' in c], errors='ignore').to_csv(obter_caminho_arquivo("ocorrencias.csv"), index=False)
                st.success("Alterações salvas com sucesso!")
                st.rerun()

    with aba5:
        exibir_painel_secretaria()
