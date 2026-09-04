import os
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import streamlit as st
import urllib.parse

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dossiê Escolar 3.0", page_icon="🏫", layout="centered")

# --- CONFIGURAÇÕES DO SISTEMA ---
ARQUIVO_CSV = "ocorrencias.csv"
ARQUIVO_ALUNOS = "alunos.csv"
ARQUIVO_CATEGORIAS = "categorias.txt"
NOME_DA_ESCOLA = "Colégio Modelo"
ARQUIVO_LOGO = "logo.png"

SENHA_PROFESSOR = "prof123"
SENHA_COORDENACAO = "coord123"
SENHA_SECRETARIA = "sec123"
# --------------------------------

def inicializar_arquivos():
    if not os.path.exists(ARQUIVO_ALUNOS):
        df_inicial = pd.DataFrame({
            "Turma": ["1º Ano A", "1º Ano A", "2º Ano B"],
            "Aluno": ["Ana Silva", "Carlos Mendes", "Beatriz Costa"],
            "Responsavel1": ["43999991111", "43999992222", "43999993333"],
            "Responsavel2": ["", "43999994444", ""]
        })
        df_inicial.to_csv(ARQUIVO_ALUNOS, index=False)
        
    if not os.path.exists(ARQUIVO_CATEGORIAS):
        cats_iniciais = [
            "Atraso injustificado", 
            "Não entregue atividade", 
            "Indisciplina em sala", 
            "Dificuldade de aprendizagem", 
            "Conflito com colegas"
        ]
        with open(ARQUIVO_CATEGORIAS, "w", encoding="utf-8") as f:
            f.write("\n".join(cats_iniciais))

inicializar_arquivos()

def carregar_alunos():
    if os.path.exists(ARQUIVO_ALUNOS):
        df = pd.read_csv(ARQUIVO_ALUNOS)
        for col in ["Turma", "Aluno", "Responsavel1", "Responsavel2"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["Turma", "Aluno", "Responsavel1", "Responsavel2"])

def carregar_categorias():
    if os.path.exists(ARQUIVO_CATEGORIAS):
        with open(ARQUIVO_CATEGORIAS, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["Indisciplina em sala"]

def carregar_dados():
    if os.path.exists(ARQUIVO_CSV):
        return pd.read_csv(ARQUIVO_CSV)
    else:
        return pd.DataFrame(columns=["Data", "Turma", "Aluno", "Categoria", "Descrição"])

def gerar_pdf(dados_aluno, nome_aluno, turma):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    if os.path.exists(ARQUIVO_LOGO):
        pdf.image(ARQUIVO_LOGO, x=10, y=8, w=30)
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, NOME_DA_ESCOLA, ln=True, align="C")
    pdf.set_font("helvetica", "I", 12)
    pdf.cell(0, 10, "Dossiê de Ocorrências Escolares - Relatório Oficial", ln=True, align="C")
    pdf.ln(15) 
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, f"Aluno(a): {nome_aluno}", ln=True)
    pdf.cell(0, 8, f"Turma: {turma}", ln=True)
    pdf.cell(0, 8, f"Data de Emissão: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(30, 10, "Data", border=1, align="C")
    pdf.cell(60, 10, "Natureza", border=1, align="C")
    pdf.cell(100, 10, "Descrição", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 10)
    for _, linha in dados_aluno.iterrows():
        data_br = pd.to_datetime(linha['Data']).strftime('%d/%m/%Y')
        pdf.cell(30, 10, data_br, border=1, align="C")
        pdf.cell(60, 10, str(linha['Categoria'])[:30], border=1) 
        pdf.cell(100, 10, str(linha['Descrição'])[:55], border=1)
        pdf.ln()
        
    pdf.ln(30)
    pdf.cell(95, 10, "___________________________________", align="C")
    pdf.cell(95, 10, "___________________________________", align="C", ln=True)
    pdf.cell(95, 10, "Coordenação Pedagógica", align="C")
    pdf.cell(95, 10, "Responsável Legal", align="C")
    
    return bytes(pdf.output())

# 2. LÓGICA DE LOGIN
if "nivel_acesso" not in st.session_state:
    st.session_state.nivel_acesso = None

if st.session_state.nivel_acesso is None:
    st.markdown(f"<h1 style='text-align: center;'>🏫 {NOME_DA_ESCOLA}</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Sistema de Gestão Pedagógica 3.0</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        senha_digitada = st.text_input("🔑 Digite sua senha de acesso:", type="password")
        if st.button("Entrar no Sistema", use_container_width=True):
            if senha_digitada == SENHA_PROFESSOR:
                st.session_state.nivel_acesso = "Professor"
                st.rerun()
            elif senha_digitada == SENHA_COORDENACAO:
                st.session_state.nivel_acesso = "Coordenador"
                st.rerun()
            elif senha_digitada == SENHA_SECRETARIA:
                st.session_state.nivel_acesso = "Secretaria"
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

with st.sidebar:
    st.image(ARQUIVO_LOGO, width=150) if os.path.exists(ARQUIVO_LOGO) else None
    st.info(f"Usuário ativo: **{st.session_state.nivel_acesso}**")
    if st.button("Sair do Sistema", use_container_width=True):
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

    with st.form("form_ocorrencia"):
        col1, col2 = st.columns(2)
        with col1:
            data_registro = st.date_input("Data da Ocorrência", date.today())
        with col2:
            turma = st.selectbox("Turma", turmas_disponiveis)
        
        alunos_da_turma = sorted(df_alunos[df_alunos["Turma"] == turma]["Aluno"].dropna().unique().tolist())
        
        col3, col4 = st.columns(2)
        with col3:
            aluno = st.selectbox("Nome do Aluno", alunos_da_turma)
        with col4:
            categoria = st.selectbox("Natureza da Ocorrência", categorias_disponiveis)
            
        descricao = st.text_area("Descrição detalhada da ocorrência:")
        submit = st.form_submit_button("Salvar Registro", use_container_width=True)

    if submit:
        novo_dado = pd.DataFrame([{
            "Data": data_registro, "Turma": turma, "Aluno": aluno, 
            "Categoria": categoria, "Descrição": descricao
        }])
        novo_dado.to_csv(ARQUIVO_CSV, mode='a', header=not os.path.exists(ARQUIVO_CSV), index=False)
        st.success(f"✅ Ocorrência registrada com sucesso para {aluno}!")

# 4. PAINEL DA SECRETARIA (Com Gestão de Alunos, Turmas, Telefones e Categorias)
def exibir_painel_secretaria():
    st.markdown("### 🗂️ Gestão Administrativa")
    
    tab_alunos, tab_massa, tab_categorias = st.tabs([
        "➕ Alunos e Turmas", "📤 Importação em Lote", "⚙️ Categorias de Ocorrência"
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
            with c2:
                resp1 = st.text_input("Telefone Responsável 1 (Ex: 43999991111):").strip()
                resp2 = st.text_input("Telefone Responsável 2 (Opcional):").strip()
            
            btn_cadastrar = st.form_submit_button("Cadastrar Aluno", use_container_width=True)
            if btn_cadastrar:
                if not turma_escolhida or not novo_aluno:
                    st.error("Preencha a turma e o nome do aluno.")
                else:
                    novo_registro = pd.DataFrame([{
                        "Turma": turma_escolhida, 
                        "Aluno": novo_aluno.title(),
                        "Responsavel1": resp1,
                        "Responsavel2": resp2
                    }])
                    df_atualizado = pd.concat([df_alunos, novo_registro], ignore_index=True)
                    df_atualizado.to_csv(ARQUIVO_ALUNOS, index=False)
                    st.success(f"Aluno(a) {novo_aluno.title()} cadastrado(a)!")
                    st.rerun()

    with tab_massa:
        st.subheader("Importação em Lote (Excel/CSV)")
        st.info("O arquivo deve conter obrigatoriamente as colunas: **Turma**, **Aluno**, **Responsavel1**, **Responsavel2**.")
        arquivo_upload = st.file_uploader("Arquivo de matrículas", type=["csv", "xlsx"])
        if arquivo_upload is not None:
            try:
                df_importado = pd.read_csv(arquivo_upload) if arquivo_upload.name.endswith('.csv') else pd.read_excel(arquivo_upload)
                colunas_necessarias = ['Turma', 'Aluno', 'Responsavel1', 'Responsavel2']
                if all(col in df_importado.columns for col in colunas_necessarias):
                    st.dataframe(df_importado.head(), use_container_width=True)
                    if st.button("Confirmar Importação", type="primary"):
                        df_importado[colunas_necessarias].to_csv(ARQUIVO_ALUNOS, index=False)
                        st.success("Base atualizada com sucesso!")
                        st.rerun()
                else:
                    st.error(f"O arquivo precisa conter exatamente as colunas: {colunas_necessarias}")
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
                    with open(ARQUIVO_CATEGORIAS, "w", encoding="utf-8") as f:
                        f.write("\n".join(cats_atuais))
                    st.success(f"Categoria '{nova_cat}' adicionada!")
                    st.rerun()
                else:
                    st.warning("Essa categoria já existe.")
        
        st.write("Categorias ativas atualmente:")
        st.write(cats_atuais)

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
                tel1 = str(aluno_info["Responsavel1"].values[0]) if not aluno_info.empty and pd.notna(aluno_info["Responsavel1"].values[0]) else ""
                tel2 = str(aluno_info["Responsavel2"].values[0]) if not aluno_info.empty and pd.notna(aluno_info["Responsavel2"].values[0]) else ""
                
                msg_whatsapp = f"Olá, responsável por {aluno_busca} ({turma_busca}). Segue o resumo das ocorrências registradas na escola:\n\n"
                for _, r in dados_filtrados.iterrows():
                    msg_whatsapp += f"- Data: {r['Data']} | {r['Categoria']}: {r['Descrição']}\n"
                msg_encoded = urllib.parse.quote(msg_whatsapp)
                
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    if tel1.strip():
                        link_wa1 = f"https://wa.me/55{tel1.strip()}?text={msg_encoded}"
                        st.markdown(f'<a href="{link_wa1}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;width:100%;">💬 Enviar WhatsApp (Resp. 1)</button></a>', unsafe_allow_html=True)
                    else:
                        st.info("Resp. 1 sem telefone cadastrado.")
                with col_w2:
                    if tel2.strip():
                        link_wa2 = f"https://wa.me/55{tel2.strip()}?text={msg_encoded}"
                        st.markdown(f'<a href="{link_wa2}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 15px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;width:100%;">💬 Enviar WhatsApp (Resp. 2)</button></a>', unsafe_allow_html=True)
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
        st.markdown("### 📈 Indicadores Pedagógicos com Filtro por Período")
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
                    c_freq = df_periodo['Categoria'].mode()[0] if not df_periodo.empty else "-"
                    st.metric("Motivo Principal", c_freq)
                
                st.divider()
                cg1, cg2 = st.columns(2)
                with cg1:
                    st.subheader("Por Natureza")
                    st.bar_chart(df_periodo['Categoria'].value_counts())
                with cg2:
                    st.subheader("Por Turma")
                    st.bar_chart(df_periodo['Turma'].value_counts())

    with aba4:
        st.markdown("### ⚙️ Gestão, Edição e Exclusão de Ocorrências")
        dados_historico = carregar_dados()
        if dados_historico.empty:
            st.info("Nenhum registro para gerenciar.")
        else:
            st.write("Edite diretamente as informações ou exclua registros incorretos:")
            df_editado = st.data_editor(dados_historico, num_rows="dynamic", use_container_width=True)
            if st.button("Salvar Alterações no Banco de Ocorrências", type="primary"):
                df_editado.drop(columns=[c for c in df_editado.columns if 'Data_Obj' in c], errors='ignore').to_csv(ARQUIVO_CSV, index=False)
                st.success("Alterações salvas com sucesso!")
                st.rerun()

    with aba5:
        exibir_painel_secretaria()
