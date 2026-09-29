# ============================================================
# MEDILEMBRETE - V1 (Com Tela de Entrada)
# Aplicativo de lembrete para medicamentos
# ============================================================

import streamlit as st
import sqlite3
from datetime import datetime, date, time, timedelta
import pandas as pd


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
    # Tabela de Usuários (NOVO)
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

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
            UNIQUE(medicamento_id, data, horario_previsto),
            FOREIGN KEY(medicamento_id) REFERENCES medicamentos(id)
        )
    """)

    conn.commit()
    conn.close()

criar_tabelas()


# ============================================================
# FUNÇÕES DE AUTENTICAÇÃO (NOVO)
# ============================================================

def cadastrar_usuario(nome, senha):
    conn = conectar_banco()
    try:
        conn.execute("INSERT INTO usuarios (nome, senha) VALUES (?, ?)", (nome, senha))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False # Nome já existe
    conn.close()
    return sucesso

def autenticar_usuario(nome, senha):
    conn = conectar_banco()
    usuario = conn.execute("SELECT * FROM usuarios WHERE nome = ? AND senha = ?", (nome, senha)).fetchone()
    conn.close()
    return usuario is not None


# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown("""
<style>
    /* Fundo principal */
    .stApp { background-color: #f6f9fb; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e7edf1;
    }

    /* Textos Grandes para melhor leitura */
    .big-text { font-size: 20px !important; }
    
    /* Cards */
    .card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #edf1f3;
        box-shadow: 0px 5px 18px rgba(20, 50, 70, 0.06);
        margin-bottom: 18px;
    }
    .medicine-name { font-size: 22px; font-weight: 700; color: #202b33; }
    .medicine-dose { color: #7c8790; font-size: 16px; }
    .patient-box {
        background-color: #f5f8fa;
        padding: 12px;
        border-radius: 10px;
        margin-top: 12px;
        font-size: 16px;
    }
    
    /* Cores e Status */
    .stock-normal { color: #1598c5; font-weight: 700; font-size: 16px; }
    .stock-low { color: #e64b5d; font-weight: 700; font-size: 16px; }
    
    /* Métricas */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #edf1f3;
        text-align: center;
        box-shadow: 0px 4px 14px rgba(20, 50, 70, 0.05);
    }
    .metric-number { font-size: 34px; font-weight: 700; color: #1598c5; }
    .metric-label { color: #78858e; font-size: 15px; font-weight: bold;}
    
    /* Próxima Dose */
    .next-dose {
        background: linear-gradient(135deg, #e8f8fc, #f7fcfd);
        border-left: 6px solid #1598c5;
        padding: 25px;
        border-radius: 16px;
        margin-bottom: 25px;
    }
    
    /* Alertas */
    .warning {
        background-color: #fff1f2;
        border-left: 5px solid #e64b5d;
        padding: 18px;
        border-radius: 12px;
        color: #9d2637;
        margin-bottom: 15px;
        font-size: 16px;
    }
    .success {
        background-color: #eaf8f3;
        border-left: 5px solid #22a77a;
        padding: 18px;
        border-radius: 12px;
        color: #176d53;
        margin-bottom: 15px;
        font-size: 16px;
    }

    /* Botões */
    div.stButton > button {
        border-radius: 12px;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# GERENCIAMENTO DE SESSÃO E TELA DE LOGIN (NOVO)
# ============================================================

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
        <h1 style="color: #1598c5; font-size: 3.5em;">💊 MediLembrete</h1>
        <p style="font-size: 1.5em; color: #555;">Sua saúde organizada de forma fácil e segura.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Criamos um layout centralizado para o login ficar bonito
    col1, col_center, col3 = st.columns([1, 2, 1])
    
    with col_center:
        aba_entrar, aba_cadastrar = st.tabs(["🔑 Já tenho conta", "📝 Quero me cadastrar"])
        
        with aba_entrar:
            with st.form("form_login"):
                st.write("### Acesse seu aplicativo")
                nome_login = st.text_input("Seu Nome (como se cadastrou)")
                senha_login = st.text_input("Sua Senha", type="password")
                btn_entrar = st.form_submit_button("Entrar no Aplicativo", use_container_width=True)
                
                if btn_entrar:
                    if not nome_login or not senha_login:
                        st.warning("⚠️ Por favor, preencha seu nome e senha.")
                    elif autenticar_usuario(nome_login, senha_login):
                        st.session_state["usuario_logado"] = nome_login
                        st.rerun()
                    else:
                        st.error("❌ Nome ou senha incorretos. Tente novamente.")
                        
        with aba_cadastrar:
            with st.form("form_cadastro"):
                st.write("### Primeira vez aqui?")
                st.write("Crie sua conta preenchendo os dados abaixo. É rápido!")
                nome_cad = st.text_input("Como você quer ser chamado? (Ex: Dona Maria)")
                senha_cad = st.text_input("Crie uma Senha fácil de lembrar", type="password")
                senha_cad_confirma = st.text_input("Repita a Senha para confirmar", type="password")
                btn_cadastrar = st.form_submit_button("Criar minha conta", use_container_width=True)
                
                if btn_cadastrar:
                    if not nome_cad or not senha_cad:
                        st.warning("⚠️ Preencha todos os campos para criar a conta.")
                    elif senha_cad != senha_cad_confirma:
                        st.error("❌ As senhas estão diferentes. Digite senhas iguais.")
                    else:
                        if cadastrar_usuario(nome_cad, senha_cad):
                            st.success("✅ Conta criada com sucesso! Agora clique na aba 'Já tenho conta' para entrar.")
                        else:
                            st.error("⚠️ Este nome já está sendo usado. Por favor, adicione um sobrenome.")
    
    # O st.stop() impede que o resto do código rode se não estiver logado
    st.stop()


# ============================================================
# FUNÇÕES DE BANCO (Mantidas com pequenos ajustes visuais)
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
        INSERT INTO medicamentos (nome, dosagem, forma, paciente, quantidade_dose, horarios, data_inicio, data_fim, estoque, estoque_minimo, ativo, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
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
    
    existente = conn.execute("SELECT * FROM registros_doses WHERE medicamento_id = ? AND data = ? AND horario_previsto = ?", (medicamento_id, data_dose, horario_previsto)).fetchone()
    if existente:
        conn.close()
        return False

    conn.execute("INSERT INTO registros_doses (medicamento_id, data, horario_previsto, horario_real, status) VALUES (?, ?, ?, ?, ?)", 
                 (medicamento_id, data_dose, horario_previsto, agora.strftime("%H:%M"), "TOMADO"))
    
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
    registro = conn.execute("SELECT id FROM registros_doses WHERE medicamento_id = ? AND data = ? AND horario_previsto = ?", (medicamento_id, data_dose, horario)).fetchone()
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
    if data_consulta < inicio: return False
    if medicamento["data_fim"]:
        fim = datetime.strptime(medicamento["data_fim"], "%Y-%m-%d").date()
        if data_consulta > fim: return False
    return True

def obter_doses_do_dia(data_consulta):
    medicamentos = buscar_medicamentos()
    doses = []
    for medicamento in medicamentos:
        if not medicamento_ativo_na_data(medicamento, data_consulta): continue
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
    
    if tomada: return "TOMADO"
    agora = datetime.now().time()
    if hoje == date.today():
        if agora > horario: return "PENDENTE"
    return "PROGRAMADO"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(f"""
        <h2 style='color: #1598c5; margin-bottom: 0px;'>Olá, {st.session_state["usuario_logado"]}!</h2>
        <p style='color: gray;'>Bem-vindo(a) ao seu MediLembrete.</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    pagina = st.radio("MENU", ["🏠 Início", "💊 Medicamentos", "📊 Histórico", "📦 Estoque"], label_visibility="collapsed")
    
    st.markdown("---")
    
    if st.button("🚪 Sair do Aplicativo", use_container_width=True):
        st.session_state["usuario_logado"] = None
        st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("MediLembrete • V1")


# ============================================================
# PÁGINA INICIAL
# ============================================================

if pagina == "🏠 Início":

    hoje = date.today()
    doses = obter_doses_do_dia(hoje)

    st.title("Bom dia! 👋")
    st.write("Aqui estão os medicamentos programados para hoje.")

    # INDICADORES
    total_doses = len(doses)
    tomadas = sum(1 for dose in doses if calcular_status_dose(dose) == "TOMADO")
    pendentes = sum(1 for dose in doses if calcular_status_dose(dose) == "PENDENTE")
    percentual = round((tomadas / total_doses) * 100) if total_doses > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{total_doses}</div><div class="metric-label">Doses hoje</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{tomadas}</div><div class="metric-label">Tomadas</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{pendentes}</div><div class="metric-label">Pendentes</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{percentual}%</div><div class="metric-label">Concluído</div></div>', unsafe_allow_html=True)

    # PRÓXIMA DOSE
    proxima = None
    agora = datetime.now()
    for dose in doses:
        if calcular_status_dose(dose) == "TOMADO": continue
        horario = datetime.strptime(dose["horario"], "%H:%M").time()
        momento = datetime.combine(hoje, horario)
        if momento >= agora:
            proxima = dose
            break

    if proxima:
        st.markdown(f"""
        <div class="next-dose">
            <div style="color:#1598c5; font-size:16px; font-weight:700;">⏰ SEU PRÓXIMO MEDICAMENTO</div>
            <div style="font-size:32px; font-weight:700; margin-top:6px;">{proxima["nome"]}</div>
            <div style="color:#707d85; margin-top:5px; font-size:18px;">
                {proxima["dosagem"]} • Tomar {proxima["quantidade_dose"]} unidade(s)
            </div>
            <div style="margin-top:15px; font-size:22px;">
                👤 {proxima["paciente"]} &nbsp;&nbsp;&nbsp; ⏰ <b>{proxima["horario"]}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # MEDICAMENTOS DE HOJE
    st.subheader("📋 Medicamentos de hoje")
    if not doses:
        st.info("Nenhum medicamento programado para hoje. Tudo certo!")

    for dose in doses:
        status = calcular_status_dose(dose)
        col1, col2 = st.columns([4, 1])

        with col1:
            if status == "TOMADO": simbolo = "✅"
            elif status == "PENDENTE": simbolo = "⚠️"
            else: simbolo = "⏰"

            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="medicine-name">{simbolo} {dose["nome"]}</div>
                        <div class="medicine-dose">{dose["dosagem"]} • {dose["forma"]}</div>
                    </div>
                    <div style="font-size:30px; font-weight:700; color:#1598c5;">{dose["horario"]}</div>
                </div>
                <div class="patient-box">
                    👤 <b>{dose["paciente"]}</b> &nbsp;&nbsp;&nbsp; 💊 Tomar {dose["quantidade_dose"]} unidade(s)
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.write("")
            st.write("")
            if status != "TOMADO":
                if st.button("✓ Tomei", key=f"tomar_{dose['medicamento_id']}_{dose['horario']}", use_container_width=True):
                    if registrar_dose(dose["medicamento_id"], hoje.isoformat(), dose["horario"]):
                        st.success("Muito bem! Registrado.")
                        st.rerun()
            else:
                st.success("Tomado!")


# ============================================================
# PÁGINA MEDICAMENTOS
# ============================================================

elif pagina == "💊 Medicamentos":

    st.title("💊 Medicamentos")
    st.write("Aqui você guarda as informações dos seus remédios.")

    with st.expander("➕ Cadastrar Novo Medicamento", expanded=True):
        with st.form("form_medicamento", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                nome = st.text_input("Qual o nome do remédio? *", placeholder="Ex.: Losartana")
                dosagem = st.text_input("Qual a dosagem?", placeholder="Ex.: 50 mg")
                forma = st.selectbox("Qual o formato?", ["Comprimido", "Cápsula", "Gotas", "Xarope", "Injeção", "Outro"])
                
                # Preenche automaticamente com o nome do usuário logado
                paciente = st.text_input("Quem vai tomar? *", value=st.session_state["usuario_logado"])

            with col2:
                quantidade_dose = st.number_input("Tomar quantas unidades por vez?", min_value=1, value=1, step=1)
                horarios = st.text_input("Que horas precisa tomar? *", placeholder="Ex.: 08:00, 20:00")
                st.caption("Para vários horários no mesmo dia, separe com vírgula.")
                data_inicio = st.date_input("A partir de qual dia?", value=date.today())
                usar_data_fim = st.checkbox("Este remédio tem data para acabar?")
                
                if usar_data_fim: data_fim = st.date_input("Termina em qual dia?", value=date.today() + timedelta(days=30))
                else: data_fim = None

            st.markdown("### 📦 Seu Estoque")
            col3, col4 = st.columns(2)
            with col3: estoque = st.number_input("Quantos você tem em casa agora?", min_value=0, value=30, step=1)
            with col4: estoque_minimo = st.number_input("Avisar quando sobrar quantos?", min_value=0, value=5, step=1)

            salvar = st.form_submit_button("💾 Salvar Medicamento", use_container_width=True)

            if salvar:
                horarios_validos = converter_horarios(horarios)
                if not nome.strip() or not paciente.strip():
                    st.error("Por favor, preencha o nome do remédio e quem vai tomar.")
                elif not horarios_validos:
                    st.error("Informe as horas no formato certo. Exemplo: 08:00 ou 08:00, 20:00")
                elif data_fim is not None and data_fim < data_inicio:
                    st.error("O dia de término não pode ser antes do dia de início.")
                else:
                    adicionar_medicamento(
                        nome.strip(), dosagem.strip(), forma, paciente.strip(), quantidade_dose,
                        ", ".join(horarios_validos), data_inicio.isoformat(), 
                        data_fim.isoformat() if data_fim else None, estoque, estoque_minimo
                    )
                    st.success(f"{nome} guardado com sucesso!")
                    st.rerun()

    st.markdown("---")
    
    medicamentos = buscar_medicamentos()
    if not medicamentos:
        st.info("Você ainda não guardou nenhum medicamento.")

    for medicamento in medicamentos:
        col1, col2 = st.columns([6, 1])
        with col1:
            estoque_atual = medicamento["estoque"]
            estoque_minimo = medicamento["estoque_minimo"]
            
            if estoque_atual <= estoque_minimo: estoque_html = f'<div class="stock-low">🔴 Atenção! O remédio está acabando. Só restam {estoque_atual}.</div>'
            else: estoque_html = f'<div class="stock-normal">🟢 Você tem {estoque_atual} guardados.</div>'

            fim = medicamento["data_fim"] if medicamento["data_fim"] else "Uso contínuo"

            st.markdown(f"""
            <div class="card">
                <div class="medicine-name">💊 {medicamento["nome"]}</div>
                <div class="medicine-dose">{medicamento["dosagem"]} • {medicamento["forma"]}</div>
                <div class="patient-box">
                    👤 <b>{medicamento["paciente"]}</b><br><br>
                    ⏰ Horários: <b>{medicamento["horarios"]}</b><br><br>
                    📅 De {medicamento["data_inicio"]} até {fim}
                </div>
                <br>{estoque_html}
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Apagar", key=f"excluir_{medicamento['id']}", use_container_width=True):
                excluir_medicamento(medicamento["id"])
                st.success("Medicamento apagado.")
                st.rerun()


# ============================================================
# HISTÓRICO
# ============================================================

elif pagina == "📊 Histórico":

    st.title("📊 Histórico")
    st.write("Veja tudo o que você já tomou.")
    registros = buscar_registros()

    if not registros:
        st.info("Ainda não temos registros para mostrar.")
    else:
        dados = []
        for registro in registros:
            dados.append({
                "Data": datetime.strptime(registro["data"], "%Y-%m-%d").strftime("%d/%m/%Y"),
                "Hora Esperada": registro["horario_previsto"],
                "Hora que Tomou": registro["horario_real"],
                "Medicamento": registro["nome"],
                "Dosagem": registro["dosagem"],
                "Para quem": registro["paciente"],
                "Situação": "✅ Tomou"
            })
        
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.metric("Total de Remédios Tomados", len(df))


# ============================================================
# ESTOQUE
# ============================================================

elif pagina == "📦 Estoque":

    st.title("📦 Controle de Remédios")
    st.write("Saiba a hora de comprar mais remédios.")
    medicamentos = buscar_medicamentos()

    if not medicamentos:
        st.info("Nenhum medicamento cadastrado.")
    else:
        dados = []
        for medicamento in medicamentos:
            estoque = medicamento["estoque"]
            minimo = medicamento["estoque_minimo"]
            status = "🔴 Comprar mais" if estoque <= minimo else "🟢 Tudo certo"
            
            dados.append({
                "Medicamento": medicamento["nome"],
                "Quantidade Atual": estoque,
                "Avisar Quando Chegar Em": minimo,
                "Situação": status
            })

        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ALERTAS
        baixos = [m for m in medicamentos if m["estoque"] <= m["estoque_minimo"]]
        if baixos:
            st.markdown("### ⚠️ Remédios Acabando:")
            for medicamento in baixos:
                st.markdown(f"""
                <div class="warning">
                    <b>{medicamento["nome"]}</b> está no fim! Só restam <b>{medicamento["estoque"]}</b>.<br>
                    Não se esqueça de comprar ou buscar no posto.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="success">✅ Você tem remédios suficientes por enquanto!</div>', unsafe_allow_html=True)


# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.caption("💊 MediLembrete V1 • Organização pessoal de medicamentos")
