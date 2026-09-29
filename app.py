# ============================================================
# MEDILEMBRETE - V1
# Aplicativo de lembrete para medicamentos
# ============================================================

import streamlit as st
import sqlite3
from datetime import datetime, date, time, timedelta
import pandas as pd
import os

# ============================================================
# CONFIGURAÇÃO DA PÁGINA (Ajustado para Mobile)
# ============================================================

st.set_page_config(
    page_title="MediLembrete",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================

DB_NAME = "medilembrete.db"

def conectar_banco():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = conectar_banco()
    cursor = conn.cursor()

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
# ESTILO VISUAL
# ============================================================

st.markdown("""

""", unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DE BANCO
# ============================================================

def buscar_medicamentos(apenas_ativos=True):
    conn = conectar_banco()
    if apenas_ativos:
        dados = conn.execute("SELECT * FROM medicamentos WHERE ativo = 1 ORDER BY nome").fetchall()
    else:
        dados = conn.execute("SELECT * FROM medicamentos ORDER BY nome").fetchall()
    conn.close()
    return dados

def buscar_medicamento(medicamento_id):
    conn = conectar_banco()
    medicamento = conn.execute("SELECT * FROM medicamentos WHERE id = ?", (medicamento_id,)).fetchone()
    conn.close()
    return medicamento

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
