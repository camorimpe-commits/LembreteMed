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
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="MediLembrete",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
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

    # --------------------------------------------------------
    # Tabela de medicamentos
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Tabela de registros das doses
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_doses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            medicamento_id INTEGER NOT NULL,

            data TEXT NOT NULL,

            horario_previsto TEXT NOT NULL,

            horario_real TEXT,

            status TEXT NOT NULL,

            UNIQUE(
                medicamento_id,
                data,
                horario_previsto
            ),

            FOREIGN KEY(medicamento_id)
            REFERENCES medicamentos(id)
        )
    """)

    conn.commit()
    conn.close()


criar_tabelas()


# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown("""
<style>

    /* Fundo principal */

    .stApp {
        background-color: #f6f9fb;
    }


    /* Sidebar */

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e7edf1;
    }


    /* Título */

    .logo-title {
        font-size: 24px;
        font-weight: 700;
        color: #1598c5;
        margin-bottom: 0px;
    }

    .logo-subtitle {
        color: #7b8790;
        font-size: 13px;
        margin-bottom: 25px;
    }


    /* Cards */

    .card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #edf1f3;
        box-shadow: 0px 5px 18px rgba(20, 50, 70, 0.06);
        margin-bottom: 18px;
    }


    .medicine-name {
        font-size: 20px;
        font-weight: 700;
        color: #202b33;
    }


    .medicine-dose {
        color: #7c8790;
        font-size: 14px;
    }


    .patient-box {
        background-color: #f5f8fa;
        padding: 12px;
        border-radius: 10px;
        margin-top: 12px;
    }


    .stock-normal {
        color: #1598c5;
        font-weight: 700;
    }


    .stock-low {
        color: #e64b5d;
        font-weight: 700;
    }


    .status-taken {
        color: #1598c5;
        font-weight: 700;
    }


    .status-pending {
        color: #e99b20;
        font-weight: 700;
    }


    .status-missed {
        color: #e64b5d;
        font-weight: 700;
    }


    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #edf1f3;
        text-align: center;
        box-shadow: 0px 4px 14px rgba(20, 50, 70, 0.05);
    }


    .metric-number {
        font-size: 30px;
        font-weight: 700;
        color: #1598c5;
    }


    .metric-label {
        color: #78858e;
        font-size: 13px;
    }


    .next-dose {
        background: linear-gradient(
            135deg,
            #e8f8fc,
            #f7fcfd
        );

        border-left: 5px solid #1598c5;

        padding: 22px;

        border-radius: 16px;

        margin-bottom: 25px;
    }


    .warning {
        background-color: #fff1f2;
        border-left: 5px solid #e64b5d;
        padding: 15px;
        border-radius: 12px;
        color: #9d2637;
        margin-bottom: 15px;
    }


    .success {
        background-color: #eaf8f3;
        border-left: 5px solid #22a77a;
        padding: 15px;
        border-radius: 12px;
        color: #176d53;
        margin-bottom: 15px;
    }


    /* Botões */

    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNÇÕES DE BANCO
# ============================================================

def buscar_medicamentos(apenas_ativos=True):

    conn = conectar_banco()

    if apenas_ativos:

        dados = conn.execute("""
            SELECT *
            FROM medicamentos
            WHERE ativo = 1
            ORDER BY nome
        """).fetchall()

    else:

        dados = conn.execute("""
            SELECT *
            FROM medicamentos
            ORDER BY nome
        """).fetchall()

    conn.close()

    return dados


def buscar_medicamento(medicamento_id):

    conn = conectar_banco()

    medicamento = conn.execute("""
        SELECT *
        FROM medicamentos
        WHERE id = ?
    """, (medicamento_id,)).fetchone()

    conn.close()

    return medicamento


def adicionar_medicamento(
    nome,
    dosagem,
    forma,
    paciente,
    quantidade_dose,
    horarios,
    data_inicio,
    data_fim,
    estoque,
    estoque_minimo
):

    conn = conectar_banco()

    conn.execute("""
        INSERT INTO medicamentos (

            nome,
            dosagem,
            forma,
            paciente,
            quantidade_dose,
            horarios,
            data_inicio,
            data_fim,
            estoque,
            estoque_minimo,
            ativo,
            criado_em

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (

        nome,
        dosagem,
        forma,
        paciente,
        quantidade_dose,
        horarios,
        data_inicio,
        data_fim,
        estoque,
        estoque_minimo,
        datetime.now().isoformat()

    ))

    conn.commit()
    conn.close()


def excluir_medicamento(medicamento_id):

    conn = conectar_banco()

    conn.execute("""
        DELETE FROM registros_doses
        WHERE medicamento_id = ?
    """, (medicamento_id,))

    conn.execute("""
        DELETE FROM medicamentos
        WHERE id = ?
    """, (medicamento_id,))

    conn.commit()
    conn.close()


def registrar_dose(
    medicamento_id,
    data_dose,
    horario_previsto
):

    agora = datetime.now()

    conn = conectar_banco()

    # --------------------------------------------------------
    # Verifica se já foi registrada
    # --------------------------------------------------------

    existente = conn.execute("""
        SELECT *
        FROM registros_doses

        WHERE medicamento_id = ?
        AND data = ?
        AND horario_previsto = ?

    """, (
        medicamento_id,
        data_dose,
        horario_previsto
    )).fetchone()

    if existente:

        conn.close()

        return False


    # --------------------------------------------------------
    # Registra a dose
    # --------------------------------------------------------

    conn.execute("""
        INSERT INTO registros_doses (

            medicamento_id,
            data,
            horario_previsto,
            horario_real,
            status

        )

        VALUES (?, ?, ?, ?, ?)
    """, (

        medicamento_id,
        data_dose,
        horario_previsto,
        agora.strftime("%H:%M"),
        "TOMADO"

    ))


    # --------------------------------------------------------
    # Diminui estoque
    # --------------------------------------------------------

    conn.execute("""
        UPDATE medicamentos

        SET estoque =
            CASE
                WHEN estoque >= quantidade_dose
                THEN estoque - quantidade_dose
                ELSE 0
            END

        WHERE id = ?
    """, (medicamento_id,))


    conn.commit()
    conn.close()

    return True


def dose_foi_tomada(
    medicamento_id,
    data_dose,
    horario
):

    conn = conectar_banco()

    registro = conn.execute("""
        SELECT id

        FROM registros_doses

        WHERE medicamento_id = ?
        AND data = ?
        AND horario_previsto = ?

    """, (
        medicamento_id,
        data_dose,
        horario
    )).fetchone()

    conn.close()

    return registro is not None


def buscar_registros():

    conn = conectar_banco()

    registros = conn.execute("""
        SELECT

            r.id,
            r.data,
            r.horario_previsto,
            r.horario_real,
            r.status,

            m.nome,
            m.dosagem,
            m.paciente

        FROM registros_doses r

        INNER JOIN medicamentos m
            ON r.medicamento_id = m.id

        ORDER BY
            r.data DESC,
            r.horario_previsto DESC

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

            datetime.strptime(
                horario,
                "%H:%M"
            )

            horarios.append(horario)

        except:

            pass

    return sorted(
        list(set(horarios))
    )


def medicamento_ativo_na_data(
    medicamento,
    data_consulta
):

    inicio = datetime.strptime(
        medicamento["data_inicio"],
        "%Y-%m-%d"
    ).date()

    if data_consulta < inicio:
        return False

    if medicamento["data_fim"]:

        fim = datetime.strptime(
            medicamento["data_fim"],
            "%Y-%m-%d"
        ).date()

        if data_consulta > fim:
            return False

    return True


def obter_doses_do_dia(data_consulta):

    medicamentos = buscar_medicamentos()

    doses = []

    for medicamento in medicamentos:

        if not medicamento_ativo_na_data(
            medicamento,
            data_consulta
        ):
            continue

        horarios = converter_horarios(
            medicamento["horarios"]
        )

        for horario in horarios:

            doses.append({

                "medicamento_id":
                    medicamento["id"],

                "nome":
                    medicamento["nome"],

                "dosagem":
                    medicamento["dosagem"],

                "forma":
                    medicamento["forma"],

                "paciente":
                    medicamento["paciente"],

                "quantidade_dose":
                    medicamento["quantidade_dose"],

                "horario":
                    horario,

                "estoque":
                    medicamento["estoque"],

                "estoque_minimo":
                    medicamento["estoque_minimo"]

            })

    doses.sort(
        key=lambda x: x["horario"]
    )

    return doses


def calcular_status_dose(dose):

    hoje = date.today()

    horario = datetime.strptime(
        dose["horario"],
        "%H:%M"
    ).time()

    tomada = dose_foi_tomada(
        dose["medicamento_id"],
        hoje.isoformat(),
        dose["horario"]
    )

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
        <div style="
            display:flex;
            align-items:center;
            gap:12px;
            margin-bottom:10px;
        ">

            <div style="
                background:#18a1ca;
                width:42px;
                height:42px;
                border-radius:12px;
                display:flex;
                align-items:center;
                justify-content:center;
                color:white;
                font-size:22px;
            ">
                💊
            </div>

            <div>
                <div class="logo-title">
                    MediLembrete
                </div>

                <div class="logo-subtitle">
                    Seu cuidado, no horário certo.
                </div>
            </div>

        </div>
    """, unsafe_allow_html=True)


    st.markdown("---")


    pagina = st.radio(

        "MENU",

        [
            "🏠 Início",
            "💊 Medicamentos",
            "📊 Histórico",
            "📦 Estoque"
        ],

        label_visibility="collapsed"

    )


    st.markdown("---")

    st.caption(
        "MediLembrete • V1"
    )

    st.caption(
        "Organização de horários e "
        "registro de medicamentos."
    )


# ============================================================
# PÁGINA INICIAL
# ============================================================

if pagina == "🏠 Início":

    hoje = date.today()

    doses = obter_doses_do_dia(hoje)

    st.title("Bom dia! 👋")

    st.write(
        "Aqui estão os medicamentos programados para hoje."
    )


    # --------------------------------------------------------
    # INDICADORES
    # --------------------------------------------------------

    total_doses = len(doses)

    tomadas = sum(
        1
        for dose in doses
        if calcular_status_dose(dose) == "TOMADO"
    )

    pendentes = sum(
        1
        for dose in doses
        if calcular_status_dose(dose) == "PENDENTE"
    )

    programadas = total_doses - tomadas - pendentes


    if total_doses > 0:

        percentual = round(
            (tomadas / total_doses) * 100
        )

    else:

        percentual = 0


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-number">
                {total_doses}
            </div>

            <div class="metric-label">
                Doses hoje
            </div>

        </div>
        """, unsafe_allow_html=True)


    with col2:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-number">
                {tomadas}
            </div>

            <div class="metric-label">
                Tomadas
            </div>

        </div>
        """, unsafe_allow_html=True)


    with col3:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-number">
                {pendentes}
            </div>

            <div class="metric-label">
                Pendentes
            </div>

        </div>
        """, unsafe_allow_html=True)


    with col4:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-number">
                {percentual}%
            </div>

            <div class="metric-label">
                Registradas hoje
            </div>

        </div>
        """, unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)


    # --------------------------------------------------------
    # PRÓXIMA DOSE
    # --------------------------------------------------------

    proxima = None

    agora = datetime.now()

    for dose in doses:

        if calcular_status_dose(dose) == "TOMADO":
            continue

        horario = datetime.strptime(
            dose["horario"],
            "%H:%M"
        ).time()

        momento = datetime.combine(
            hoje,
            horario
        )

        if momento >= agora:

            proxima = dose
            break


    if proxima:

        st.markdown(f"""
        <div class="next-dose">

            <div style="
                color:#1598c5;
                font-size:13px;
                font-weight:700;
            ">
                ⏰ PRÓXIMO MEDICAMENTO
            </div>

            <div style="
                font-size:26px;
                font-weight:700;
                margin-top:6px;
            ">
                {proxima["nome"]}
            </div>

            <div style="
                color:#707d85;
                margin-top:3px;
            ">
                {proxima["dosagem"]}
                •
                {proxima["quantidade_dose"]}
                unidade(s)
            </div>

            <div style="
                margin-top:15px;
                font-size:16px;
            ">
                👤 {proxima["paciente"]}
                &nbsp;&nbsp;&nbsp;
                ⏰ {proxima["horario"]}
            </div>

        </div>
        """, unsafe_allow_html=True)


    # --------------------------------------------------------
    # MEDICAMENTOS DE HOJE
    # --------------------------------------------------------

    st.subheader("📋 Medicamentos de hoje")


    if not doses:

        st.info(
            "Nenhum medicamento foi programado para hoje. "
            "Cadastre o primeiro medicamento no menu lateral."
        )


    for dose in doses:

        status = calcular_status_dose(dose)

        col1, col2 = st.columns([5, 1])


        with col1:

            if status == "TOMADO":

                simbolo = "✅"

            elif status == "PENDENTE":

                simbolo = "⚠️"

            else:

                simbolo = "⏰"


            st.markdown(f"""
            <div class="card">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">

                    <div>

                        <div class="medicine-name">
                            {simbolo}
                            {dose["nome"]}
                        </div>

                        <div class="medicine-dose">
                            {dose["dosagem"]}
                            •
                            {dose["forma"]}
                        </div>

                    </div>

                    <div style="
                        font-size:24px;
                        font-weight:700;
                        color:#1598c5;
                    ">
                        {dose["horario"]}
                    </div>

                </div>

                <div class="patient-box">

                    👤 <b>{dose["paciente"]}</b>

                    &nbsp;&nbsp;&nbsp;

                    💊 {dose["quantidade_dose"]}
                    unidade(s)

                </div>

            </div>
            """, unsafe_allow_html=True)


        with col2:

            st.write("")


            if status != "TOMADO":

                if st.button(
                    "✓ Tomei agora",
                    key=f"tomar_{dose['medicamento_id']}_{dose['horario']}",
                    use_container_width=True
                ):

                    sucesso = registrar_dose(

                        dose["medicamento_id"],

                        hoje.isoformat(),

                        dose["horario"]

                    )

                    if sucesso:

                        st.success(
                            "Dose registrada!"
                        )

                        st.rerun()

            else:

                st.success("Tomado")


# ============================================================
# PÁGINA MEDICAMENTOS
# ============================================================

elif pagina == "💊 Medicamentos":

    st.title("💊 Medicamentos")

    st.write(
        "Cadastre e organize os medicamentos e seus horários."
    )


    # --------------------------------------------------------
    # FORMULÁRIO
    # --------------------------------------------------------

    with st.expander(
        "➕ Cadastrar novo medicamento",
        expanded=True
    ):

        with st.form(
            "form_medicamento",
            clear_on_submit=True
        ):

            col1, col2 = st.columns(2)


            with col1:

                nome = st.text_input(
                    "Nome do medicamento *",
                    placeholder="Ex.: Losartana"
                )

                dosagem = st.text_input(
                    "Dosagem",
                    placeholder="Ex.: 50 mg"
                )

                forma = st.selectbox(
                    "Forma",
                    [
                        "Comprimido",
                        "Cápsula",
                        "Gotas",
                        "Xarope",
                        "Injeção",
                        "Outro"
                    ]
                )

                paciente = st.text_input(
                    "Paciente *",
                    placeholder="Ex.: João"
                )


            with col2:

                quantidade_dose = st.number_input(
                    "Quantidade por dose",
                    min_value=1,
                    value=1,
                    step=1
                )

                horarios = st.text_input(
                    "Horários *",
                    placeholder="Ex.: 08:00, 20:00"
                )

                st.caption(
                    "Para vários horários, separe por vírgula."
                )

                data_inicio = st.date_input(
                    "Data de início",
                    value=date.today()
                )

                usar_data_fim = st.checkbox(
                    "Definir data de término"
                )


                if usar_data_fim:

                    data_fim = st.date_input(
                        "Data de término",
                        value=date.today() + timedelta(days=30)
                    )

                else:

                    data_fim = None


            st.markdown("### 📦 Estoque")


            col3, col4 = st.columns(2)


            with col3:

                estoque = st.number_input(
                    "Quantidade atual",
                    min_value=0,
                    value=30,
                    step=1
                )


            with col4:

                estoque_minimo = st.number_input(
                    "Avisar quando chegar a",
                    min_value=0,
                    value=5,
                    step=1
                )


            salvar = st.form_submit_button(
                "💾 Salvar medicamento",
                use_container_width=True
            )


            if salvar:

                horarios_validos = converter_horarios(
                    horarios
                )


                if not nome.strip():

                    st.error(
                        "Informe o nome do medicamento."
                    )

                elif not paciente.strip():

                    st.error(
                        "Informe o paciente."
                    )

                elif not horarios_validos:

                    st.error(
                        "Informe pelo menos um horário válido. "
                        "Exemplo: 08:00 ou 08:00, 20:00"
                    )

                elif (
                    data_fim is not None
                    and data_fim < data_inicio
                ):

                    st.error(
                        "A data de término não pode ser anterior "
                        "à data de início."
                    )

                else:

                    adicionar_medicamento(

                        nome.strip(),

                        dosagem.strip(),

                        forma,

                        paciente.strip(),

                        quantidade_dose,

                        ", ".join(horarios_validos),

                        data_inicio.isoformat(),

                        data_fim.isoformat()
                        if data_fim
                        else None,

                        estoque,

                        estoque_minimo

                    )

                    st.success(
                        f"{nome} foi cadastrado com sucesso!"
                    )

                    st.rerun()


    st.markdown("---")


    # --------------------------------------------------------
    # LISTAGEM
    # --------------------------------------------------------

    medicamentos = buscar_medicamentos()


    if not medicamentos:

        st.info(
            "Nenhum medicamento cadastrado."
        )


    for medicamento in medicamentos:

        col1, col2 = st.columns([6, 1])


        with col1:

            estoque_atual = medicamento["estoque"]

            estoque_minimo = medicamento["estoque_minimo"]


            if estoque_atual <= estoque_minimo:

                estoque_html = f"""
                <div class="stock-low">
                    🔴 Estoque baixo:
                    {estoque_atual} unidade(s)
                </div>
                """

            else:

                estoque_html = f"""
                <div class="stock-normal">
                    🟢 Estoque:
                    {estoque_atual} unidade(s)
                </div>
                """


            fim = (
                medicamento["data_fim"]
                if medicamento["data_fim"]
                else "Sem data de término"
            )


            st.markdown(f"""
            <div class="card">

                <div class="medicine-name">
                    💊 {medicamento["nome"]}
                </div>

                <div class="medicine-dose">
                    {medicamento["dosagem"]}
                    •
                    {medicamento["forma"]}
                </div>

                <div class="patient-box">

                    👤 <b>{medicamento["paciente"]}</b>

                    <br><br>

                    ⏰ Horários:
                    <b>{medicamento["horarios"]}</b>

                    <br><br>

                    📅
                    {medicamento["data_inicio"]}
                    →
                    {fim}

                </div>

                <br>

                {estoque_html}

            </div>
            """, unsafe_allow_html=True)


        with col2:

            st.write("")

            st.write("")

            if st.button(
                "🗑️ Excluir",
                key=f"excluir_{medicamento['id']}",
                use_container_width=True
            ):

                excluir_medicamento(
                    medicamento["id"]
                )

                st.success(
                    "Medicamento excluído."
                )

                st.rerun()


# ============================================================
# HISTÓRICO
# ============================================================

elif pagina == "📊 Histórico":

    st.title("📊 Histórico")

    st.write(
        "Acompanhe os medicamentos registrados como tomados."
    )


    registros = buscar_registros()


    if not registros:

        st.info(
            "Ainda não existem doses registradas."
        )

    else:

        dados = []

        for registro in registros:

            dados.append({

                "Data":
                    datetime.strptime(
                        registro["data"],
                        "%Y-%m-%d"
                    ).strftime("%d/%m/%Y"),

                "Horário previsto":
                    registro["horario_previsto"],

                "Horário registrado":
                    registro["horario_real"],

                "Medicamento":
                    registro["nome"],

                "Dosagem":
                    registro["dosagem"],

                "Paciente":
                    registro["paciente"],

                "Status":
                    "✅ Tomado"

            })


        df = pd.DataFrame(dados)


        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


        # ----------------------------------------------------
        # INDICADOR
        # ----------------------------------------------------

        st.markdown("---")

        st.subheader(
            "📈 Resumo"
        )


        total_registros = len(df)

        st.metric(
            "Doses registradas",
            total_registros
        )


# ============================================================
# ESTOQUE
# ============================================================

elif pagina == "📦 Estoque":

    st.title("📦 Estoque")

    st.write(
        "Acompanhe a quantidade disponível de cada medicamento."
    )


    medicamentos = buscar_medicamentos()


    if not medicamentos:

        st.info(
            "Nenhum medicamento cadastrado."
        )

    else:

        dados = []


        for medicamento in medicamentos:

            estoque = medicamento["estoque"]

            minimo = medicamento["estoque_minimo"]


            if estoque <= minimo:

                status = "🔴 Estoque baixo"

            else:

                status = "🟢 Estoque normal"


            dados.append({

                "Medicamento":
                    medicamento["nome"],

                "Dosagem":
                    medicamento["dosagem"],

                "Paciente":
                    medicamento["paciente"],

                "Estoque":
                    estoque,

                "Estoque mínimo":
                    minimo,

                "Status":
                    status

            })


        df = pd.DataFrame(dados)


        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


        # ----------------------------------------------------
        # ALERTAS
        # ----------------------------------------------------

        baixos = [

            medicamento

            for medicamento in medicamentos

            if medicamento["estoque"]
            <= medicamento["estoque_minimo"]

        ]


        if baixos:

            st.markdown(
                "### ⚠️ Atenção"
            )


            for medicamento in baixos:

                st.markdown(f"""
                <div class="warning">

                    <b>
                        {medicamento["nome"]}
                    </b>

                    está com apenas

                    <b>
                        {medicamento["estoque"]}
                    </b>

                    unidade(s).

                    <br>

                    Estoque mínimo configurado:
                    <b>
                        {medicamento["estoque_minimo"]}
                    </b>

                </div>
                """, unsafe_allow_html=True)

        else:

            st.markdown("""
            <div class="success">

                ✅ Todos os medicamentos estão
                acima do estoque mínimo configurado.

            </div>
            """, unsafe_allow_html=True)


# ============================================================
# RODAPÉ
# ============================================================

st.markdown("---")

st.caption(
    "💊 MediLembrete V1 • "
    "Organização pessoal de medicamentos"
)
