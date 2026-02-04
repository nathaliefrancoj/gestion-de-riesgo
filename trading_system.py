import streamlit as st
import pandas as pd
from datetime import datetime

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

/* -------- BOTONES UNIFICADOS -------- */
.stButton > button {
    font-size: 15px;
    font-weight: 500;
    height: 2.6em;
    padding: 0 22px;
    border-radius: 10px;
    border: 1.5px solid #cfcfcf;
    background-color: #ffffff;
    color: #333333;
    outline: none !important;
    box-shadow: none !important;
    transition: all 0.15s ease-in-out;
}

/* Hover sutil */
.stButton > button:hover {
    background-color: #f3f3f3;
}

/* WIN */
.win-btn button,
.win-btn button:hover,
.win-btn button:active,
.win-btn button:focus,
.win-btn button:focus-visible {
    background-color: #ffffff !important;
    color: #333333 !important;
    border: 1.5px solid #cfcfcf !important;
}

/* LOSS */
.loss-btn button,
.loss-btn button:hover,
.loss-btn button:active,
.loss-btn button:focus,
.loss-btn button:focus-visible {
    background-color: #ffffff !important;
    color: #333333 !important;
    border: 1.5px solid #cfcfcf !important;
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
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    f = datetime.now()
    return f"{meses[f.month-1]} {f.day} de {f.year} - {f.strftime('%I:%M %p').lower()}"

# ---------------- CONFIG SISTEMA ----------------
PORCENTAJES = {
    1: [1, 2.13, 4.52],
    2: [2, 4.25, 9.03],
    3: [3, 6.38, 13.54],
    4: [4, 8.5, 18.05],
}

PAGO_BROKER = 0.89

OBJETIVOS_REC = {
    2: 5,
    3: 9,
    4: 13,
}

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
base = (
    st.session_state.capital_freeze
    if st.session_state.en_recuperacion
    else st.session_state.capital
)

porc = PORCENTAJES[nivel][st.session_state.loss_trade]
monto = base * porc / 100
retorno = monto * PAGO_BROKER

# ---------------- INFO ----------------
st.markdown(f"""
<div class='info'><b>Capital inicial:</b> {formato_numero(st.session_state.capital_ini)}</div>
<div class='info'><b>Saldo actual:</b> {formato_numero(st.session_state.capital)}</div>
<div class='info'><b>Próxima inversión:</b> {formato_porcentaje(porc)} → {formato_numero(monto)}</div>
<div class='info'><b>Nivel:</b> {nivel}</div>
""", unsafe_allow_html=True)

if st.session_state.en_recuperacion and nivel in OBJETIVOS_REC:
    st.markdown(
        f"<div class='info'><b>Recuperación:</b> {st.session_state.wins_rec}/{OBJETIVOS_REC[nivel]} win</div>",
        unsafe_allow_html=True
    )

# ---------------- BOTONES ----------------
c1, c2, _ = st.columns([1,1,10])
win = c1.button("Win")
loss = c2.button("Loss")

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
        "Nivel": nivel,
        "Resultado": "Win",
        "Inversión": formato_numero(monto),
        "Retorno": f"<span class='text-win'>{formato_numero(retorno)}</span>",
        "Saldo": formato_numero(st.session_state.capital)
    })
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
        "Nivel": nivel,
        "Resultado": "Loss",
        "Inversión": formato_numero(monto),
        "Retorno": f"<span class='text-loss'>-{formato_numero(monto)}</span>",
        "Saldo": formato_numero(st.session_state.capital)
    })
    st.rerun()

# ---------------- HISTORICO + BORRAR ----------------
h1, h2 = st.columns([10,1])
h1.subheader("Histórico")

if h2.button("Borrar"):
    cap = st.session_state.capital_ini
    st.session_state.clear()
    st.session_state.update({
    "init": True,
    "capital": cap,
    "capital_ini": cap,
    "entrada": 0,
    "loss_trade": 0,
    "loss_consec": 0,
    "hist": [],
    "freeze": None,
    "objetivo_rec": None,
    "contador": 0,
    "en_recuperacion": False,
    "capital_freeze": None,
    "wins_rec": 0,
    "intentos_rec": 0
    })
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
    st.markdown(html, unsafe_allow_html=True)
else:

    st.markdown("<div class='empty-box'>Aún no hay operaciones registradas</div>", unsafe_allow_html=True)
