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
/* -------- FORZAR MODO CLARO SIEMPRE -------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #f4f4f2 !important;
    color: #111 !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"] {
    background: transparent !important;
}

h1 { text-align: center; color: #111 !important; }
.subtitle { text-align: center; font-size: 14px; color: #555; margin-top: -8px; }

.info { font-size: 17px; margin-bottom: 6px; color: #111 !important; }

table {
    width: 100%;
    border-collapse: collapse;
    background-color: #f2f2f2;
    border: 1px solid #000;
}

th, td {
    text-align: center;
    padding: 10px;
    white-space: nowrap;
}

.header-row th {
    background-color: #fff4cc;
    text-align: center;
}

/* -------- RESULTADO CON FONDO Y TEXTO NEGRO -------- */
.result-win {
    background-color: #c8e6c9;
    color: #111;
    font-weight: bold;
}

.result-loss {
    background-color: #ffcdd2;
    color: #111;
    font-weight: bold;
}

.text-win { color: #2e7d32; font-weight: bold; }
.text-loss { color: #c62828; font-weight: bold; }

.bold { font-weight: bold; }

/* -------- SCROLL HORIZONTAL -------- */
.table-container {
    width: 100%;
    overflow-x: auto;
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
STATE_FILE = f"estado_{st.session_state.usuario}.csv"
CONFIG_FILE = f"config_{st.session_state.usuario}.csv"

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

# ---------------- CARGA DE CONFIG (capital inicial real) ----------------
if os.path.exists(CONFIG_FILE):
    df_conf = pd.read_csv(CONFIG_FILE)
    if not df_conf.empty:
        st.session_state.capital_ini = float(df_conf.loc[0, "capital_inicial"])

# ---------------- CARGA HISTORIAL ----------------
if os.path.exists(HIST_FILE) and not st.session_state.hist:
    df = pd.read_csv(HIST_FILE)
    st.session_state.hist = df.to_dict("records")
    st.session_state.contador = len(st.session_state.hist)

# ---------------- CARGA ESTADO COMPLETO ----------------
if os.path.exists(STATE_FILE):
    df_state = pd.read_csv(STATE_FILE)
    if not df_state.empty:
        st.session_state.capital = float(df_state.loc[0, "capital"])
        st.session_state.loss_trade = int(df_state.loc[0, "loss_trade"])
        st.session_state.loss_consec = int(df_state.loc[0, "loss_consec"])
        st.session_state.wins_rec = int(df_state.loc[0, "wins_rec"])
        st.session_state.en_recuperacion = bool(df_state.loc[0, "en_recuperacion"])
        cf = df_state.loc[0, "capital_freeze"]
        st.session_state.capital_freeze = None if pd.isna(cf) else float(cf)

# ---------------- HEADER ----------------
st.title("Sistema de Gestión de Inversión")
st.markdown("<div class='subtitle'>Creado por Nathalie Franco Jiménez</div>", unsafe_allow_html=True)

# ---------------- INICIO CAPITAL ----------------
if not st.session_state.init:

    # Si existe config y existe estado, ya iniciamos directo
    if os.path.exists(CONFIG_FILE) and os.path.exists(STATE_FILE):
        st.session_state.init = True

    else:
        cap = st.number_input("Capital inicial ($)", min_value=1, step=1, value=1)

        if st.button("Iniciar"):
            st.session_state.capital_ini = float(cap)
            st.session_state.capital = float(cap)

            # Guardar config (capital inicial real)
            pd.DataFrame([{"capital_inicial": st.session_state.capital_ini}]).to_csv(CONFIG_FILE, index=False)

            # Guardar estado inicial
            pd.DataFrame([{
                "capital": st.session_state.capital,
                "loss_trade": 0,
                "loss_consec": 0,
                "wins_rec": 0,
                "en_recuperacion": False,
                "capital_freeze": ""
            }]).to_csv(STATE_FILE, index=False)

            st.session_state.init = True
            st.rerun()

        st.stop()

# ---------------- NIVEL ----------------
nuevo_nivel = min(4, st.session_state.loss_consec // 3 + 1)

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

if idx + 1 < len(PORCENTAJES[nivel]):
    next_porc = PORCENTAJES[nivel][idx + 1]
    next_monto = base * next_porc / 100
    if idx == 0:
        st.markdown(f"<div class='info'><b>1ra recuperación:</b> {formato_numero(next_monto)}</div>", unsafe_allow_html=True)
    elif idx == 1:
        st.markdown(f"<div class='info'><b>2da recuperación:</b> {formato_numero(next_monto)}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='info'><b>¡Último intento!</b></div>", unsafe_allow_html=True)

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

def guardar_estado():
    pd.DataFrame([{
        "capital": st.session_state.capital,
        "loss_trade": st.session_state.loss_trade,
        "loss_consec": st.session_state.loss_consec,
        "wins_rec": st.session_state.wins_rec,
        "en_recuperacion": st.session_state.en_recuperacion,
        "capital_freeze": "" if st.session_state.capital_freeze is None else st.session_state.capital_freeze
    }]).to_csv(STATE_FILE, index=False)

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
h1, h2, h3 = st.columns([10, 1, 1])
h1.subheader("Histórico")
inicio = h2.button("Inicio")
borrar = h3.button("Borrar")
st.markdown("</div>", unsafe_allow_html=True)

# -------- INICIO: BORRA TODO Y VUELVE A LOGIN --------
if inicio:
    for f in [HIST_FILE, STATE_FILE, CONFIG_FILE]:
        if os.path.exists(f):
            os.remove(f)

    # Reinicio total
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

# -------- BORRAR: SOLO BORRA HISTORIAL Y REINICIA AL CAPITAL INICIAL REAL --------
if borrar:
    if os.path.exists(HIST_FILE):
        os.remove(HIST_FILE)

    st.session_state.hist = []
    st.session_state.contador = 0

    # Reinicia al capital inicial REAL (guardado en CONFIG_FILE)
    st.session_state.capital = st.session_state.capital_ini
    st.session_state.loss_trade = 0
    st.session_state.loss_consec = 0
    st.session_state.wins_rec = 0
    st.session_state.en_recuperacion = False
    st.session_state.capital_freeze = None

    guardar_estado()
    st.rerun()

# ---------------- TABLA ----------------
if st.session_state.hist:
    df = pd.DataFrame(st.session_state.hist)

    html = "<div class='table-container'>"
    html += "<table><thead><tr class='header-row'>" + "".join(f"<th>{c}</th>" for c in df.columns) + "</tr></thead><tbody>"

    for _, r in df.iterrows():
        html += "<tr>"
        for c, v in r.items():
            if c == "Resultado":
                cls = "result-win" if v == "Win" else "result-loss"
                html += f"<td class='{cls}'>{v}</td>"
            elif c == "N°":
                html += f"<td class='bold'>{v}</td>"
            else:
                html += f"<td>{v}</td>"
        html += "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)
else:
    st.markdown("<div class='empty-box'>Aún no hay operaciones registradas</div>", unsafe_allow_html=True)
