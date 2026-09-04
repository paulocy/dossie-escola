import streamlit as st
import pandas as pd
from datetime import date
import os
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dossiê Escolar", page_icon="🏫", layout="centered")

# --- CONFIGURAÇÕES DO SISTEMA ---
ARQUIVO_CSV = "ocorrencias.csv"
NOME_DA_ESCOLA = "Colégio Modelo"
ARQUIVO_LOGO = "logo.png"

SENHA_PROFESSOR = "prof123"
SENHA_COORDENACAO = "coord123"
# --------------------------------

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

alunos_matriculados = {
    "1º Ano A": ["Ana Silva", "Carlos Mendes", "João Silva"],
    "2º Ano B": ["Beatriz Costa", "Daniel Souza", "Joaquim Phoenix"],
    "3º Ano A": ["Eduardo Lima", "Fernanda Montenegro", "Gabriel Pensador"]
}

# 2. LÓGICA DE LOGIN
if "nivel_acesso" not in st.session_state:
    st.session_state.nivel_acesso = None

if st.session_state.nivel_acesso is None:
    st.markdown(f"<h1 style='text-align: center;'>🏫 {NOME_DA_ESCOLA}</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Sistema de Gestão Pedagógica</h3>", unsafe_allow_html=True)
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
            else:
                st.error("Senha incorreta.")
    st.stop()

# Menu Lateral (Logout)
with st.sidebar:
    st.image(ARQUIVO_LOGO, width=150) if os.path.exists(ARQUIVO_LOGO) else None
    st.info(f"Usuário ativo: **{st.session_state.nivel_acesso}**")
    if st.button("Sair do Sistema", use_container_width=True):
        st.session_state.nivel_acesso = None
        st.rerun()

# 3. FUNÇÃO DO FORMULÁRIO
def exibir_formulario():
    st.markdown("### 📝 Registrar Nova Ocorrência")
    with st.form("form_ocorrencia"):
        col1, col2 = st.columns(2)
        with col1:
            data_registro = st.date_input("Data da Ocorrência", date.today())
        with col2:
            turma = st.selectbox("Turma", list(alunos_matriculados.keys()))
        
        col3, col4 = st.columns(2)
        with col3:
            lista_de_alunos = alunos_matriculados[turma]
            aluno = st.selectbox("Nome do Aluno", lista_de_alunos)
        with col4:
            categoria = st.selectbox("Natureza da Ocorrência", [
                "Atraso injustificado", "Não entregou atividade", 
                "Indisciplina em sala", "Dificuldade de aprendizagem", "Conflito com colegas"
            ])
            
        descricao = st.text_area("Descrição detalhada da ocorrência:")
        submit = st.form_submit_button("Salvar Registro", use_container_width=True)

    if submit:
        novo_dado = pd.DataFrame([{
            "Data": data_registro, "Turma": turma, "Aluno": aluno, 
            "Categoria": categoria, "Descrição": descricao
        }])
        novo_dado.to_csv(ARQUIVO_CSV, mode='a', header=not os.path.exists(ARQUIVO_CSV), index=False)
        st.success(f"✅ Ocorrência registrada com sucesso para {aluno}!")

# 4. GERENCIAMENTO DAS TELAS (Abas)
if st.session_state.nivel_acesso == "Professor":
    exibir_formulario()

elif st.session_state.nivel_acesso == "Coordenador":
    # Criamos três abas para a coordenação
    aba1, aba2, aba3 = st.tabs(["📝 Novo Registro", "📋 Painel de Dossiês", "📊 Relatórios e Análises"])
    
    with aba1:
        exibir_formulario()
        
    with aba2:
        st.markdown("### 🔍 Consulta de Dossiês Individuais")
        dados_historico = carregar_dados()

        if dados_historico.empty:
            st.info("Nenhuma ocorrência registrada ainda no sistema.")
        else:
            col_busca1, col_busca2 = st.columns(2)
            with col_busca1:
                turma_busca = st.selectbox("Filtrar por Turma:", list(alunos_matriculados.keys()))
            with col_busca2:
                aluno_busca = st.selectbox("Selecionar Aluno:", alunos_matriculados[turma_busca])
            
            dados_filtrados = dados_historico[dados_historico["Aluno"] == aluno_busca]
                
            st.dataframe(dados_filtrados, use_container_width=True, hide_index=True)
            
            if not dados_filtrados.empty:
                st.caption(f"Total de registros encontrados: {len(dados_filtrados)}")
                arquivo_pdf = gerar_pdf(dados_filtrados, aluno_busca, turma_busca)
                st.download_button(
                    label=f"📄 Baixar Relatório Oficial de {aluno_busca} (PDF)",
                    data=arquivo_pdf,
                    file_name=f"Relatorio_{aluno_busca.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
    with aba3:
        st.markdown("### 📈 Visão Geral e Indicadores Pedagógicos")
        dados_historico = carregar_dados()
        
        if dados_historico.empty:
            st.info("Ainda não há dados suficientes para gerar análises estatísticas.")
        else:
            # Métricas principais no topo
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total de Ocorrências", len(dados_historico))
            with col_m2:
                turma_mais_frequente = dados_historico['Turma'].mode()[0] if not dados_historico.empty else "-"
                st.metric("Turma com Mais Registros", turma_mais_frequente)
            with col_m3:
                cat_mais_frequente = dados_historico['Categoria'].mode()[0] if not dados_historico.empty else "-"
                st.metric("Motivo Mais Recorrente", cat_mais_frequente)
            
            st.divider()
            
            # Gráficos e Tabelas de Análise
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("Ocorrências por Natureza")
                contagem_cat = dados_historico['Categoria'].value_counts()
                st.bar_chart(contagem_cat)
                
            with col_g2:
                st.subheader("Ocorrências por Turma")
                contagem_turma = dados_historico['Turma'].value_counts()
                st.bar_chart(contagem_turma)
                
            st.divider()
            st.subheader("⚠️ Alunos com Maior Incidência de Registros")
            ranking_alunos = dados_historico[['Aluno', 'Turma']].value_counts().reset_index(name='Total de Ocorrências')
            st.dataframe(ranking_alunos, use_container_width=True, hide_index=True)    