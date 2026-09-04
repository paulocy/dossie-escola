import os
from datetime import date
import pandas as pd
from fpdf import FPDF
import streamlit as st

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dossiê Escolar", page_icon="🏫", layout="centered")

# --- CONFIGURAÇÕES DO SISTEMA ---
ARQUIVO_CSV = "ocorrencias.csv"
ARQUIVO_ALUNOS = "alunos.csv"
NOME_DA_ESCOLA = "Colégio Modelo"
ARQUIVO_LOGO = "logo.png"

SENHA_PROFESSOR = "prof123"
SENHA_COORDENACAO = "coord123"
SENHA_SECRETARIA = "sec123"
# --------------------------------


def inicializar_alunos():
  if not os.path.exists(ARQUIVO_ALUNOS):
    df_inicial = pd.DataFrame({
        "Turma": [
            "1º Ano A",
            "1º Ano A",
            "1º Ano A",
            "2º Ano B",
            "2º Ano B",
            "2º Ano B",
        ],
        "Aluno": [
            "Ana Silva",
            "Carlos Mendes",
            "João Silva",
            "Beatriz Costa",
            "Daniel Souza",
            "Joaquim Phoenix",
        ],
    })
    df_inicial.to_csv(ARQUIVO_ALUNOS, index=False)


inicializar_alunos()


def carregar_alunos():
  if os.path.exists(ARQUIVO_ALUNOS):
    return pd.read_csv(ARQUIVO_ALUNOS)
  return pd.DataFrame(columns=["Turma", "Aluno"])


def carregar_dados():
  if os.path.exists(ARQUIVO_CSV):
    return pd.read_csv(ARQUIVO_CSV)
  else:
    return pd.DataFrame(
        columns=["Data", "Turma", "Aluno", "Categoria", "Descrição"]
    )


def gerar_pdf(dados_aluno, nome_aluno, turma):
  pdf = FPDF(orientation="P", unit="mm", format="A4")
  pdf.add_page()
  if os.path.exists(ARQUIVO_LOGO):
    pdf.image(ARQUIVO_LOGO, x=10, y=8, w=30)

  pdf.set_font("helvetica", "B", 16)
  pdf.cell(0, 10, NOME_DA_ESCOLA, ln=True, align="C")
  pdf.set_font("helvetica", "I", 12)
  pdf.cell(
      0, 10, "Dossiê de Ocorrências Escolares - Relatório Oficial", ln=True, align="C"
  )
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
    data_br = pd.to_datetime(linha["Data"]).strftime("%d/%m/%Y")
    pdf.cell(30, 10, data_br, border=1, align="C")
    pdf.cell(60, 10, str(linha["Categoria"])[:30], border=1)
    pdf.cell(100, 10, str(linha["Descrição"])[:55], border=1)
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
  st.markdown(
      f"<h1 style='text-align: center;'>🏫 {NOME_DA_ESCOLA}</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h3 style='text-align: center; color: gray;'>Sistema de Gestão"
      " Pedagógica</h3>",
      unsafe_allow_html=True,
  )
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
  if df_alunos.empty:
    st.warning(
        "⚠️ Nenhuma turma ou aluno cadastrado no sistema. Solicite à Secretaria"
        " que realize o cadastro."
    )
    return

  turmas_disponiveis = sorted(df_alunos["Turma"].dropna().unique().tolist())

  with st.form("form_ocorrencia"):
    col1, col2 = st.columns(2)
    with col1:
      data_registro = st.date_input("Data da Ocorrência", date.today())
    with col2:
      turma = st.selectbox("Turma", turmas_disponiveis)

    alunos_da_turma = sorted(
        df_alunos[df_alunos["Turma"] == turma]["Aluno"].dropna().unique().tolist()
    )

    col3, col4 = st.columns(2)
    with col3:
      aluno = st.selectbox("Nome do Aluno", alunos_da_turma)
    with col4:
      categoria = st.selectbox(
          "Natureza da Ocorrência",
          [
              "Atraso injustificado",
              "Não entregue atividade",
              "Indisciplina em sala",
              "Dificuldade de aprendizagem",
              "Conflito com colegas",
          ],
      )

    descricao = st.text_area("Descrição detalhada da ocorrência:")
    submit = st.form_submit_button("Salvar Registro", use_container_width=True)

  if submit:
    novo_dado = pd.DataFrame([{
        "Data": data_registro,
        "Turma": turma,
        "Aluno": aluno,
        "Categoria": categoria,
        "Descrição": descricao,
    }])
    novo_dado.to_csv(
        ARQUIVO_CSV, mode="a", header=not os.path.exists(ARQUIVO_CSV), index=False
    )
    st.success(f"✅ Ocorrência registrada com sucesso para {aluno}!")


# 4. PAINEL DA SECRETARIA (Com Seleção/Criação Dinâmica de Turmas)
def exibir_painel_secretaria():
  st.markdown("### 🗂️ Gestão de Matrículas, Turmas e Alunos")

  tab_manual, tab_massa = st.tabs(
      ["➕ Cadastro Manual", "📤 Importar Planilha (Excel/CSV)"]
  )

  df_alunos = carregar_alunos()

  with tab_manual:
    with st.form("form_novo_aluno"):
      st.subheader("Matricular Aluno Individualmente")
      c1, c2 = st.columns(2)

      with c1:
        turmas_existentes = sorted(
            df_alunos["Turma"].dropna().unique().tolist()
        )
        if turmas_existentes:
          tipo_turma = st.radio(
              "Destino da Turma", ["Turma Existente", "Nova Turma"]
          )
          if tipo_turma == "Turma Existente":
            turma_escolhida = st.selectbox("Selecione a Turma", turmas_existentes)
          else:
            turma_escolhida = st.text_input("Nome da Nova Turma:").strip()
        else:
          st.info("Nenhuma turma cadastrada. Digite a primeira turma:")
          turma_escolhida = st.text_input("Nome da Nova Turma:").strip()

      with c2:
        st.write("")
        st.write("")
        novo_aluno = st.text_input("Nome Completo do Aluno:").strip()

      btn_cadastrar = st.form_submit_button(
          "Cadastrar Aluno", use_container_width=True
      )

      if btn_cadastrar:
        if not turma_escolhida or not novo_aluno:
          st.error(
              "Preencha ou selecione a turma e informe o nome do aluno."
          )
        else:
          novo_registro = pd.DataFrame(
              [{"Turma": turma_escolhida, "Aluno": novo_aluno.title()}]
          )
          df_atualizado = pd.concat([df_alunos, novo_registro], ignore_index=True)
          df_atualizado.to_csv(ARQUIVO_ALUNOS, index=False)
          st.success(f"Aluno(a) {novo_aluno.title()} adicionado(a) com sucesso!")
          st.rerun()

  with tab_massa:
    st.subheader("Importação em Lote de Turmas e Alunos")
    st.info(
        "Envie um arquivo Excel (.xlsx) ou CSV contendo obrigatoriamente duas"
        " colunas chamadas exatos: **Turma** e **Aluno**."
    )

    arquivo_upload = st.file_uploader(
        "Escolha o arquivo de matrículas", type=["csv", "xlsx"]
    )

    if arquivo_upload is not None:
      try:
        if arquivo_upload.name.endswith(".csv"):
          df_importado = pd.read_csv(arquivo_upload)
        else:
          df_importado = pd.read_excel(arquivo_upload)

        if "Turma" in df_importado.columns and "Aluno" in df_importado.columns:
          st.write("Prévia dos dados encontrados no arquivo:")
          st.dataframe(df_importado.head(), use_container_width=True)

          if st.button(
              "Confirmar Importação e Substituir/Atualizar Base", type="primary"
          ):
            df_importado[["Turma", "Aluno"]].to_csv(ARQUIVO_ALUNOS, index=False)
            st.success("Base de turmas e alunos atualizada com sucesso!")
            st.rerun()
        else:
          st.error(
              "O arquivo enviado precisa conter colunas com os nomes exatos:"
              " 'Turma' e 'Aluno'."
          )
      except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

  st.divider()
  st.subheader("📋 Base Atual de Alunos e Turmas Matriculadas")
  st.dataframe(df_alunos, use_container_width=True, hide_index=True)


# 5. GERENCIAMENTO DE PERFIS E TELAS
if st.session_state.nivel_acesso == "Professor":
  exibir_formulario()

elif st.session_state.nivel_acesso == "Secretaria":
  exibir_painel_secretaria()

elif st.session_state.nivel_acesso == "Coordenador":
  aba1, aba2, aba3, aba4 = st.tabs([
      "📝 Novo Registro",
      "📋 Painel de Dossiês",
      "📊 Relatórios e Análises",
      "🗂️ Secretaria (Alunos)",
  ])

  with aba1:
    exibir_formulario()

  with aba2:
    st.markdown("### 🔍 Consulta de Dossiês Individuais")
    dados_historico = carregar_dados()
    df_alunos = carregar_alunos()

    if dados_historico.empty:
      st.info("Nenhuma ocorrência registrada ainda no sistema.")
    elif df_alunos.empty:
      st.warning("Cadastre turmas e alunos na aba Secretaria.")
    else:
      turmas_disponiveis = sorted(df_alunos["Turma"].dropna().unique().tolist())
      col_busca1, col_busca2 = st.columns(2)
      with col_busca1:
        turma_busca = st.selectbox("Filtrar por Turma:", turmas_disponiveis)
      with col_busca2:
        alunos_turma_busca = sorted(
            df_alunos[df_alunos["Turma"] == turma_busca]["Aluno"]
            .dropna()
            .unique()
            .tolist()
        )
        aluno_busca = st.selectbox("Selecionar Aluno:", alunos_turma_busca)

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
            type="primary",
        )

  with aba3:
    st.markdown("### 📈 Visão Geral e Indicadores Pedagógicos")
    dados_historico = carregar_dados()

    if dados_historico.empty:
      st.info("Ainda não há dados suficientes para gerar análises estatísticas.")
    else:
      col_m1, col_m2, col_m3 = st.columns(3)
      with col_m1:
        st.metric("Total de Ocorrências", len(dados_historico))
      with col_m2:
        turma_mais_frequente = (
            dados_historico["Turma"].mode()[0]
            if not dados_historico.empty
            else "-"
        )
        st.metric("Turma com Mais Registros", turma_mais_frequente)
      with col_m3:
        cat_mais_frequente = (
            dados_historico["Categoria"].mode()[0]
            if not dados_historico.empty
            else "-"
        )
        st.metric("Motivo Mais Recorrente", cat_mais_frequente)

      st.divider()

      col_g1, col_g2 = st.columns(2)
      with col_g1:
        st.subheader("Ocorrências por Natureza")
        contagem_cat = dados_historico["Categoria"].value_counts()
        st.bar_chart(contagem_cat)

      with col_g2:
        st.subheader("Ocorrências por Turma")
        contagem_turma = dados_historico["Turma"].value_counts()
        st.bar_chart(contagem_turma)

      st.divider()
      st.subheader("⚠️ Alunos com Maior Incidência de Registros")
      ranking_alunos = (
          dados_historico[["Aluno", "Turma"]]
          .value_counts()
          .reset_index(name="Total de Ocorrências")
      )
      st.dataframe(ranking_alunos, use_container_width=True, hide_index=True)

  with aba4:
    exibir_painel_secretaria()
