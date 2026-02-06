import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Sistema de Gestión de Inversión", layout="wide")

# ---------------- ESTILOS ----------------
st.markdown("""
<style>

/* ==============================
   1) FORZAR MODO CLARO SIEMPRE
   ============================== */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #fffff !important;
    color: #111 !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background: transparent !important;
}

html, body { font-family: serif; background-color: #fffff; }

h1 { text-align: center; }
.subtitle { text-align: center; font-size: 14px; color: #555; margin-top: -8px; }

.info { font-size: 17px; margin-bottom: 6px; }

table {
    width: 100%;
    border-collapse: collapse;
    background-color: #f2f2f2;
    border: 1px solid #000;
}

th, td {
    text-align: center;
    padding: 10px;
}

.header-row th {
    background-color: #fff4cc;
    text-align: center;
}

/* ==============================
   4) RESULTADO CON FONDO Y TEXTO NEGRO
   ============================== */
.result-win {
    background-color: #93c47d;
    color: #000;
    font-weight: bold;
}
.result-loss {
    background-color: #e06666;
    color: #000;
    font-weight: bold;
}

/* Retorno sí puede seguir en verde/rojo */
.text-win { color: #93c47d; font-weight: bold; }
.text-loss { color: #e06666; font-weight: bold; }

.bold { font-weight: bold; }

/* -------- SCROLL HORIZONTAL -------- */
.table-container {
    width: 100%;
    overflow-x: auto;
    white-space: nowrap;
}

td, th, .info {
    white-space: nowrap;
}

.stButton {
    display: inline-block;
    margin-right: 6px;
}

[data-testid="column"] {
    min-width: fit-content;
}

/* -------- FIX BOTONES MÓVIL -------- */
.button-row {
    display: flex;
    flex-wrap: nowrap;
    gap: 10px;
    align-items: center;
}

/* Botones fijos */
.stButton > button {
    min-width: 90px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Evita que Streamlit rompa columnas en móvil */
@media (max-width: 768px) {
    [data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
    }
}

/* -------- BOTONES -------- */
.stButton > button {
    font-size: 15px;
    font-weight: 500;
    height: 2.6em;
    padding: 0 22px;
    border-radius: 10px;
    border: 1.5px solid #cfcfcf;
    background-color: #ffffff;
    color: #333333;
    transition: all 0.15s ease-in-out;
}

.stButton > button:hover {
    background-color: #f3f3f3;
}

/* -------- CAJA VACÍA -------- */
.empty-box {
    width: 100%;
    background-color: #f6f6f6;
    border: 1.5px solid #cfcfcf;
    padding: 18px;
    border-radius: 10px;
    text-align: center;
    font-size: 15px;
    font-weight: 500;
    color: #555555;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UTILIDADES ----------------
def formato_numero(v):
    if float(v).is_integer():
        return f"${int(v)}"
    return f"${v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_porcentaje(v):
    if float(v).is_integer():
        return f"{int(v)}%"
    return f"{str(v).replace('.', ',')}%"

def fecha():
    tz = ZoneInfo("America/Bogota")
    f = datetime.now(tz)

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    hora = f.strftime("%I:%M").lstrip("0")
    ampm = "a. m." if f.hour < 12 else "p. m."

    return f"{dias[f.weekday()]}, {f.day} de {meses[f.month-1]} - {hora} {ampm}"

def parse_money(s):
    # "$1.234,56" -> 1234.56
    return float(str(s).replace("$", "").replace(".", "").replace(",", "."))

# ---------------- CONFIG SISTEMA ----------------
PORCENTAJES = {
    1: [1, 2.13, 4.52],
    2: [2, 4.25, 9.03],
    3: [3, 6.38, 13.54],
    4: [4, 8.5, 18.05],
}

OBJETIVOS_REC = {2: 5, 3: 9, 4: 13}
PAGO_BROKER = 0.89

# ---------------- USUARIO ----------------
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if not st.session_state.usuario:
    st.title("Sistema de Gestión de Inversión")
    usuario = st.text_input("Nombre de usuario")

    if st.button("Entrar"):
        if usuario.strip() == "":
            st.warning("Ingresa un nombre de usuario")
        else:
            st.session_state.usuario = usuario.strip().lower().replace(" ", "_")
            st.rerun()

    st.stop()

# ---------------- ARCHIVOS POR USUARIO ----------------
HIST_FILE = f"historial_{st.session_state.usuario}.csv"

# (2) Guardar capital inicial real
CAPITAL_FILE = f"capital_inicial_{st.session_state.usuario}.csv"

# (3) Guardar estado real de recuperación
STATE_FILE = f"estado_{st.session_state.usuario}.csv"

# ---------------- ESTADO ----------------
if "init" not in st.session_state:
    st.session_state.update({
        "init": False,
        "capital": 0,
        "capital_ini": 0,
        "loss_trade": 0,
        "loss_consec": 0,
        "wins_rec": 0,
        "en_recuperacion": False,
        "capital_freeze": None,
        "hist": [],
        "contador": 0
    })

# Garantiza que las claves críticas siempre existan
st.session_state.setdefault("en_recuperacion", False)
st.session_state.setdefault("capital_freeze", None)
st.session_state.setdefault("loss_trade", 0)
st.session_state.setdefault("loss_consec", 0)
st.session_state.setdefault("wins_rec", 0)
st.session_state.setdefault("capital", 0)
st.session_state.setdefault("capital_ini", 0)

# ---------------- FUNCIONES DE GUARDADO/CARGA ----------------
def guardar_capital_inicial():
    pd.DataFrame([{"capital_inicial": st.session_state.capital_ini}]).to_csv(CAPITAL_FILE, index=False)

def cargar_capital_inicial():
    if os.path.exists(CAPITAL_FILE):
        df = pd.read_csv(CAPITAL_FILE)
        if not df.empty:
            st.session_state.capital_ini = float(df.loc[0, "capital_inicial"])

def guardar_estado():
    pd.DataFrame([{
        "capital": st.session_state.capital,
        "loss_trade": st.session_state.loss_trade,
        "loss_consec": st.session_state.loss_consec,
        "wins_rec": st.session_state.wins_rec,
        "en_recuperacion": int(st.session_state.en_recuperacion),
        "capital_freeze": "" if st.session_state.capital_freeze is None else st.session_state.capital_freeze
    }]).to_csv(STATE_FILE, index=False)

def cargar_estado():
    if os.path.exists(STATE_FILE):
        df = pd.read_csv(STATE_FILE)
        if not df.empty:
            st.session_state.capital = float(df.loc[0, "capital"])
            st.session_state.loss_trade = int(df.loc[0, "loss_trade"])
            st.session_state.loss_consec = int(df.loc[0, "loss_consec"])
            st.session_state.wins_rec = int(df.loc[0, "wins_rec"])
            st.session_state.en_recuperacion = bool(int(df.loc[0, "en_recuperacion"]))

            cf = df.loc[0, "capital_freeze"]
            st.session_state.capital_freeze = None if pd.isna(cf) or str(cf).strip() == "" else float(cf)

# ---------------- CARGAR ARCHIVOS (si existen) ----------------
# Capital inicial real
cargar_capital_inicial()

# Historial
if os.path.exists(HIST_FILE) and not st.session_state.hist:
    df = pd.read_csv(HIST_FILE)
    st.session_state.hist = df.to_dict("records")
    st.session_state.contador = len(st.session_state.hist)

# Estado real (recuperación, etc)
cargar_estado()

# ---------------- HEADER ----------------
st.title("Sistema de Gestión de Inversión")
st.markdown("<div class='subtitle'>Creado por Nathalie Franco Jiménez</div>", unsafe_allow_html=True)

# ---------------- CAPITAL ----------------
hist_guardado = os.path.exists(HIST_FILE)

if not st.session_state.init:

    # Si hay historial guardado, NO pedimos capital
    if hist_guardado and st.session_state.hist:

        # IMPORTANTE:
        # - El capital inicial se carga del CAPITAL_FILE (ya se hizo arriba)
        # - El capital actual se carga del STATE_FILE (ya se hizo arriba)
        # - Si por alguna razón no existe STATE_FILE, tomamos el último saldo
        if not os.path.exists(STATE_FILE):
            ultimo_saldo_str = st.session_state.hist[-1]['Saldo']
            saldo_num = parse_money(ultimo_saldo_str)
            st.session_state.capital = saldo_num

        st.session_state.init = True

    else:
        # Usuario nuevo o historial borrado: pedimos capital inicial
        cap = st.number_input("Capital inicial ($)", min_value=1, step=1, value=1)

        if st.button("Iniciar"):
            st.session_state.capital = float(cap)
            st.session_state.capital_ini = float(cap)

            # Guardar capital inicial REAL (para el punto 2)
            guardar_capital_inicial()

            # Guardar estado inicial (para el punto 3)
            st.session_state.loss_trade = 0
            st.session_state.loss_consec = 0
            st.session_state.wins_rec = 0
            st.session_state.en_recuperacion = False
            st.session_state.capital_freeze = None
            guardar_estado()

            st.session_state.init = True
            st.rerun()

        st.stop()

# ---------------- NIVEL ----------------
nuevo_nivel = min(4, st.session_state.loss_consec // 3 + 1)

# Reiniciar wins de recuperación si se sube de nivel
if "nivel_anterior" not in st.session_state:
    st.session_state.nivel_anterior = nuevo_nivel

if nuevo_nivel != st.session_state.nivel_anterior:
    st.session_state.wins_rec = 0
    st.session_state.nivel_anterior = nuevo_nivel

nivel = nuevo_nivel

# ---------------- CÁLCULO ----------------
base = st.session_state.capital_freeze if st.session_state.en_recuperacion else st.session_state.capital
idx = min(st.session_state.loss_trade, len(PORCENTAJES[nivel]) - 1)
porc = PORCENTAJES[nivel][idx]
monto = base * porc / 100
retorno = monto * PAGO_BROKER

# ---------------- INFO ----------------
st.markdown(
    f"<div class='info'><b>Capital:</b> {formato_numero(st.session_state.capital_ini)} → {formato_numero(st.session_state.capital)}</div>",
    unsafe_allow_html=True
)

st.markdown(f"<div class='info'><b>Inversión actual:</b> {formato_numero(monto)}</div>", unsafe_allow_html=True)

# Recuperaciones
if idx + 1 < len(PORCENTAJES[nivel]):
    next_porc = PORCENTAJES[nivel][idx + 1]
    next_monto = base * next_porc / 100
    if idx == 0:
        st.markdown(f"<div class='info'><b>1ra recuperación:</b> {formato_numero(next_monto)}</div>", unsafe_allow_html=True)
    elif idx == 1:
        st.markdown(f"<div class='info'><b>2da recuperación:</b> {formato_numero(next_monto)}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='info'><b>¡Último intento!</b></div>", unsafe_allow_html=True)

# Nivel con progreso de recuperación integrado
if st.session_state.en_recuperacion and nivel in OBJETIVOS_REC:
    st.markdown(
        f"<div class='info'><b>Nivel:</b> {nivel} → {st.session_state.wins_rec}/{OBJETIVOS_REC[nivel]} win</div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(f"<div class='info'><b>Nivel:</b> {nivel}</div>", unsafe_allow_html=True)

# ---------------- BOTONES ----------------
st.markdown("<div class='button-row'>", unsafe_allow_html=True)
c1, c2, _ = st.columns([1, 1, 10])
win = c1.button("Win")
loss = c2.button("Loss")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- WIN ----------------
if win:
    st.session_state.capital += retorno
    st.session_state.loss_trade = 0

    if st.session_state.en_recuperacion:
        st.session_state.wins_rec += 1
        if st.session_state.wins_rec >= OBJETIVOS_REC.get(nivel, 0):
            st.session_state.en_recuperacion = False
            st.session_state.loss_consec = 0
            st.session_state.wins_rec = 0
            st.session_state.capital_freeze = None

    st.session_state.contador += 1
    st.session_state.hist.insert(0, {
        "N°": st.session_state.contador,
        "Fecha": fecha(),
        "Nivel": nivel,
        "Resultado": "Win",
        "Inversión": formato_numero(monto),
        "Retorno": f"<span class='text-win'>{formato_numero(retorno)}</span>",
        "Saldo": formato_numero(st.session_state.capital)
    })

    pd.DataFrame(st.session_state.hist).to_csv(HIST_FILE, index=False)
    guardar_estado()
    st.rerun()

# ---------------- LOSS ----------------
if loss:
    if not st.session_state.en_recuperacion:
        st.session_state.en_recuperacion = True
        st.session_state.capital_freeze = st.session_state.capital
        st.session_state.wins_rec = 0

    st.session_state.capital -= monto
    st.session_state.loss_trade += 1

    if st.session_state.loss_trade == 3:
        st.session_state.loss_consec += 3
        st.session_state.loss_trade = 0

    st.session_state.contador += 1
    st.session_state.hist.insert(0, {
        "N°": st.session_state.contador,
        "Fecha": fecha(),
        "Nivel": nivel,
        "Resultado": "Loss",
        "Inversión": formato_numero(monto),
        "Retorno": f"<span class='text-loss'>-{formato_numero(monto)}</span>",
        "Saldo": formato_numero(st.session_state.capital)
    })

    pd.DataFrame(st.session_state.hist).to_csv(HIST_FILE, index=False)
    guardar_estado()
    st.rerun()

# ---------------- BOTONES HISTORIAL ----------------
st.markdown("<div class='button-row'>", unsafe_allow_html=True)

# 5) Botón Inicio al lado de Borrar
h1, h2, h3 = st.columns([10, 1, 1])
h1.subheader("Histórico")
inicio = h2.button("Inicio")
borrar = h3.button("Borrar")

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- INICIO ----------------
if inicio:
    # Borra TODO y vuelve como primera vez
    for f in [HIST_FILE, CAPITAL_FILE, STATE_FILE]:
        if os.path.exists(f):
            os.remove(f)

    st.session_state.usuario = ""
    st.session_state.init = False
    st.session_state.hist = []
    st.session_state.contador = 0
    st.session_state.capital = 0
    st.session_state.capital_ini = 0
    st.session_state.loss_trade = 0
    st.session_state.loss_consec = 0
    st.session_state.wins_rec = 0
    st.session_state.en_recuperacion = False
    st.session_state.capital_freeze = None
    st.rerun()

# ---------------- BORRAR ----------------
if borrar:
    # Borra solo historial, pero reinicia capital al INICIAL REAL
    if os.path.exists(HIST_FILE):
        os.remove(HIST_FILE)

    st.session_state['hist'] = []
    st.session_state['contador'] = 0

    # 2) Volver al capital inicial real
    st.session_state['capital'] = st.session_state.capital_ini

    # Reset recuperación
    st.session_state['loss_trade'] = 0
    st.session_state['loss_consec'] = 0
    st.session_state['wins_rec'] = 0
    st.session_state['en_recuperacion'] = False
    st.session_state['capital_freeze'] = None

    guardar_estado()
    st.rerun()

# ---------------- TABLA ----------------
if st.session_state.hist:
    df = pd.DataFrame(st.session_state.hist)

    html = "<table><thead><tr class='header-row'>" + "".join(f"<th>{c}</th>" for c in df.columns) + "</tr></thead><tbody>"

    for _, r in df.iterrows():
        html += "<tr>"
        for c, v in r.items():

            # 4) Resultado con fondo y letras negras
            if c == "Resultado":
                cls = "result-win" if v == "Win" else "result-loss"
                html += f"<td class='{cls}'>{v}</td>"

            elif c == "N°":
                html += f"<td class='bold'>{v}</td>"

            else:
                html += f"<td>{v}</td>"

        html += "</tr>"

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

else:
    st.markdown("<div class='empty-box'>Aún no hay operaciones registradas</div>", unsafe_allow_html=True)
