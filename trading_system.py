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
html, body { font-family: serif; background-color: #f4f4f2; }

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

.text-win { color: #2e7d32; font-weight: bold; }
.text-loss { color: #c62828; font-weight: bold; }

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

# ---------------- HISTORIAL POR USUARIO ----------------
HIST_FILE = f"historial_{st.session_state.usuario}.csv"

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

# Cargar histórico guardado
if os.path.exists(HIST_FILE) and not st.session_state.hist:
    df = pd.read_csv(HIST_FILE)
    st.session_state.hist = df.to_dict("records")
    st.session_state.contador = len(st.session_state.hist)

# ---------------- HEADER ----------------
st.title("Sistema de Gestión de Inversión")
st.markdown("<div class='subtitle'>Creado por Nathalie Franco Jiménez</div>", unsafe_allow_html=True)

# ---------------- CAPITAL ----------------
if not st.session_state.init:
    cap = st.number_input("Capital inicial ($)", min_value=1, step=1, value=1)
    if st.button("Iniciar"):
        st.session_state.capital = cap
        st.session_state.capital_ini = cap
        st.session_state.init = True
        st.rerun()
    st.stop()

# ---------------- NIVEL ----------------
nivel = min(4, st.session_state.loss_consec // 3 + 1)

# ---------------- CÁLCULO ----------------
base = st.session_state.capital_freeze if st.session_state.en_recuperacion else st.session_state.capital
idx = min(st.session_state.loss_trade, len(PORCENTAJES[nivel]) - 1)
porc = PORCENTAJES[nivel][idx]
monto = base * porc / 100
retorno = monto * PAGO_BROKER

# ---------------- INFO ----------------
# Cálculo base
base = st.session_state.capital_freeze if st.session_state.en_recuperacion else st.session_state.capital
idx = min(st.session_state.loss_trade, len(PORCENTAJES[nivel]) - 1)
porc = PORCENTAJES[nivel][idx]
monto = base * porc / 100
retorno = monto * PAGO_BROKER

# Capital inicial y saldo actual
st.markdown(f"<div class='info'><b>Capital inicial:</b> {formato_numero(st.session_state.capital_ini)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='info'><b>Saldo actual:</b> {formato_numero(st.session_state.capital)}</div>", unsafe_allow_html=True)

# Próxima inversión
st.markdown(f"<div class='info'><b>Próxima inversión:</b> {formato_numero(monto)}</div>", unsafe_allow_html=True)

# Preparar recuperación
if idx + 1 < len(PORCENTAJES[nivel]):
    next_porc = PORCENTAJES[nivel][idx + 1]
    next_monto = base * next_porc / 100
    st.markdown(f"<div class='info'><b>Preparar recuperación:</b> {formato_numero(next_monto)}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='info'><b>Preparar recuperación:</b> No hay más recuperaciones.</div>", unsafe_allow_html=True)

# Nivel
st.markdown(f"<div class='info'><b>Nivel:</b> {nivel}</div>", unsafe_allow_html=True)

# Recuperación: solo si está en recuperación y hay un objetivo definido
if st.session_state.en_recuperacion and nivel in OBJETIVOS_REC:
    st.markdown(
        f"<div class='info'><b>Recuperación:</b> {st.session_state.wins_rec}/{OBJETIVOS_REC[nivel]} win</div>",
        unsafe_allow_html=True
    )
# ---------------- BOTONES ----------------
st.markdown("<div class='button-row'>", unsafe_allow_html=True)
c1, c2, _ = st.columns([1,1,10])
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
    st.rerun()

# ---------------- HISTÓRICO ----------------
# ---------------- BOTONES HISTORIAL ----------------
st.markdown("<div class='button-row'>", unsafe_allow_html=True)
h1, h2 = st.columns([10,1])
h1.subheader("Histórico")
borrar = h2.button("Borrar")
st.markdown("</div>", unsafe_allow_html=True)

if borrar:
    # Mantener saldo inicial ingresado
    cap_ini = st.session_state.capital_ini
    # Borrar archivo histórico si existe
    if os.path.exists(HIST_FILE):
        os.remove(HIST_FILE)

    # Limpiar solo el histórico, mantener saldo inicial
    st.session_state['hist'] = []
    st.session_state['contador'] = 0
    st.session_state['capital'] = cap_ini
    st.session_state['loss_trade'] = 0
    st.session_state['loss_consec'] = 0
    st.session_state['wins_rec'] = 0
    st.session_state['en_recuperacion'] = False
    st.session_state['capital_freeze'] = None
    st.rerun()

if st.session_state.hist:
    df = pd.DataFrame(st.session_state.hist)
    html = "<table><thead><tr class='header-row'>" + "".join(f"<th>{c}</th>" for c in df.columns) + "</tr></thead><tbody>"
    for _, r in df.iterrows():
        html += "<tr>"
        for c, v in r.items():
            if c == "Resultado":
                cls = "text-win" if v == "Win" else "text-loss"
                html += f"<td class='{cls}'>{v}</td>"
            elif c == "N°":
                html += f"<td class='bold'>{v}</td>"
            else:
                html += f"<td>{v}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(f"<div class='table-container'>{html}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='empty-box'>Aún no hay operaciones registradas</div>", unsafe_allow_html=True)
