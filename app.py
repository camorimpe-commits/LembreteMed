# ============================================================
# MEDILEMBRETE - V1 (Com Login e Suporte a Mobile)
# ============================================================

import streamlit as st
import sqlite3
from datetime import datetime, date, time, timedelta
import pandas as pd
import os

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="MediLembrete",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================

DB_NAME = "medilembrete.db"

def conectar_banco():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = conectar_banco()
    cursor = conn.cursor()

    # Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    # Tabela de Medicamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            dosagem TEXT,
            forma TEXT,
            paciente TEXT NOT NULL,
            quantidade_dose INTEGER DEFAULT 1,
            horarios TEXT NOT NULL,
            data_inicio TEXT NOT NULL,
            data_fim TEXT,
            estoque INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 5,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT
        )
    """)

    # Tabela de Doses Registradas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_doses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicamento_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            horario_previsto TEXT NOT NULL,
            horario_real TEXT,
            status TEXT NOT NULL,
            UNIQUE(medicamento_id, data, horario_previsto),
            FOREIGN KEY(medicamento_id) REFERENCES medicamentos(id)
        )
    """)

    conn.commit()
    conn.close()

criar_tabelas()

# ============================================================
# FUNÇÕES DE AUTENTICAÇÃO
# ============================================================

def cadastrar_usuario(nome, username, senha):
    conn = conectar_banco()
    try:
        conn.execute("""
            INSERT INTO usuarios (nome, username, senha)
            VALUES (?, ?, ?)
        """, (nome, username, senha))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def autenticar_usuario(username, senha):
    conn = conectar_banco()
    usuario = conn.execute("""
        SELECT * FROM usuarios
        WHERE username = ? AND senha = ?
    """, (username, senha)).fetchone()
    conn.close()
    return usuario

# ============================================================
# ESTILO VISUAL (CSS)
# ============================================================

st.markdown("""

""", unsafe_allow_html=True)

# ============================================================
# TELA DE LOGIN / CADASTRO
# ============================================================

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    st.title("💊 MediLembrete")
    st.caption("Seu cuidado, no horário certo.")
    
    aba_login, aba_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
    
    with aba_login:
        with st.form("form_login"):
            username = st.text_input("Usuário", placeholder="Ex.: joaosilva")
            senha = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_entrar:
                if not username.strip() or not senha.strip():
                    st.error("Preencha todos os campos.")
                else:
                    usuario = autenticar_usuario(username.strip(), senha.strip())
                    if usuario:
                        st.session_state["usuario_logado"] = dict(usuario)
                        st.success(f"Bem-vindo(a), {usuario['nome']}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                        
    with aba_cadastro:
        with st.form("form_cadastro"):
            novo_nome = st.text_input("Seu nome completo", placeholder="Ex.: João Silva")
            novo_username = st.text_input("Escolha um usuário", placeholder="Ex.: joaosilva")
            nova_senha = st.text_input("Escolha uma senha", type="password")
            confirmar_senha = st.text_input("Confirme a senha", type="password")
            btn_cadastrar = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if btn_cadastrar:
                if not novo_nome.strip() or not novo_username.strip() or not nova_senha.strip():
                    st.error("Preencha todos os campos obrigatórios.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem.")
                else:
                    sucesso = cadastrar_usuario(novo_nome.strip(), novo_username.strip(), nova_senha.strip())
                    if sucesso:
                        st.success("Conta criada com sucesso! Faça login na aba 'Entrar'.")
                    else:
                        st.error("Este nome de usuário já está em uso. Escolha outro.")

    st.stop()

# ============================================================
# FUNÇÕES DE BANCO (MEDICAMENTOS)
# ============================================================

def buscar_medicamentos(apenas_ativos=True):
    conn = conectar_banco()
    if apenas_ativos:
        dados = conn.execute("SELECT * FROM medicamentos WHERE ativo = 1 ORDER BY nome").fetchall()
    else:
        dados = conn.execute("SELECT * FROM medicamentos ORDER BY nome").fetchall()
    conn.close()
    return dados

def adicionar_medicamento(nome, dosagem, forma, paciente, quantidade_dose, horarios, data_inicio, data_fim, estoque, estoque_minimo):
    conn = conectar_banco()
    conn.execute("""
        INSERT INTO medicamentos (
            nome, dosagem, forma, paciente, quantidade_dose, horarios, data_inicio, data_fim, estoque, estoque_minimo, ativo, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (nome, dosagem, forma, paciente, quantidade_dose, horarios, data_inicio, data_fim, estoque, estoque_minimo, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def excluir_medicamento(medicamento_id):
    conn = conectar_banco()
    conn.execute("DELETE FROM registros_doses WHERE medicamento_id = ?", (medicamento_id,))
    conn.execute("DELETE FROM medicamentos WHERE id = ?", (medicamento_id,))
    conn.commit()
    conn.close()

def registrar_dose(medicamento_id, data_dose, horario_previsto):
    agora = datetime.now()
    conn = conectar_banco()

    existente = conn.execute("""
        SELECT * FROM registros_doses
        WHERE medicamento_id = ? AND data = ? AND horario_previsto = ?
    """, (medicamento_id, data_dose, horario_previsto)).fetchone()

    if existente:
        conn.close()
        return False

    conn.execute("""
        INSERT INTO registros_doses (medicamento_id, data, horario_previsto, horario_real, status)
        VALUES (?, ?, ?, ?, ?)
    """, (medicamento_id, data_dose, horario_previsto, agora.strftime("%H:%M"), "TOMADO"))

    conn.execute("""
        UPDATE medicamentos
        SET estoque = CASE WHEN estoque >= quantidade_dose THEN estoque - quantidade_dose ELSE 0 END
        WHERE id = ?
    """, (medicamento_id,))

    conn.commit()
    conn.close()
    return True

def dose_foi_tomada(medicamento_id, data_dose, horario):
    conn = conectar_banco()
    registro = conn.execute("""
        SELECT id FROM registros_doses
        WHERE medicamento_id = ? AND data = ? AND horario_previsto = ?
    """, (medicamento_id, data_dose, horario)).fetchone()
    conn.close()
    return registro is not None

def buscar_registros():
    conn = conectar_banco()
    registros = conn.execute("""
        SELECT r.id, r.data, r.horario_previsto, r.horario_real, r.status, m.nome, m.dosagem, m.paciente
        FROM registros_doses r
        INNER JOIN medicamentos m ON r.medicamento_id = m.id
        ORDER BY r.data DESC, r.horario_previsto DESC
    """).fetchall()
    conn.close()
    return registros

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def converter_horarios(texto):
    horarios = []
    partes = texto.split(",")
    for parte in partes:
        horario = parte.strip()
        try:
            datetime.strptime(horario, "%H:%M")
            horarios.append(horario)
        except:
            pass
    return sorted(list(set(horarios)))

def medicamento_ativo_na_data(medicamento, data_consulta):
    inicio = datetime.strptime(medicamento["data_inicio"], "%Y-%m-%d").date()
    if data_consulta < inicio:
        return False
    if medicamento["data_fim"]:
        fim = datetime.strptime(medicamento["data_fim"], "%Y-%m-%d").date()
        if data_consulta > fim:
            return False
    return True

def obter_doses_do_dia(data_consulta):
    medicamentos = buscar_medicamentos()
    doses = []
    for medicamento in medicamentos:
        if not medicamento_ativo_na_data(medicamento, data_consulta):
            continue
        horarios = converter_horarios(medicamento["horarios"])
        for horario in horarios:
            doses.append({
                "medicamento_id": medicamento["id"],
                "nome": medicamento["nome"],
                "dosagem": medicamento["dosagem"],
                "forma": medicamento["forma"],
                "paciente": medicamento["paciente"],
                "quantidade_dose": medicamento["quantidade_dose"],
                "horario": horario,
                "estoque": medicamento["estoque"],
                "estoque_minimo": medicamento["estoque_minimo"]
            })
    doses.sort(key=lambda x: x["horario"])
    return doses

def calcular_status_dose(dose):
    hoje = date.today()
    horario = datetime.strptime(dose["horario"], "%H:%M").time()
    tomada = dose_foi_tomada(dose["medicamento_id"], hoje.isoformat(), dose["horario"])

    if tomada:
        return "TOMADO"

    agora = datetime.now().time()
    if hoje == date.today():
        if agora > horario:
            return "PENDENTE"

    return "PROGRAMADO"

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("""
