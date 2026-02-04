import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ================= CONFIG =================
st.set_page_config(page_title="Sistema de Gestión de Inversión", layout="wide")

ARCHIVO_HIST = "historial.csv"

# ================= ESTILOS =================
st.markdown("""
<style>
html, body { font-family: serif; background-color: #f4f4f2; }

h1 { text-align: center; }
.subtitle { text-align: center; font-size: 14px; color: #555; margin-top: -8px; }
.info { font-size: 17px; margin-bottom: 6px; }

.stButton > button {
    font-size: 15px;
    height: 2.6em;
    padding: 0 22px;
    border-radius: 10px;
    border: 1.5px solid #cfcfcf;
    background-color: #ffffff;
    color: #333;
}

.buttons-row {
    display: flex;
    gap: 12px;
}

.buttons-row .stButton {
    flex: 1;
}

.hist-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

table {
    width: 100%;
    border-collapse: collapse;
    background-color: #f2f2f2;
}

th, td {
    padding: 10px;
    text-align: center;
}

.header-row th {
    background-color: #fff4cc;
}

.text-win { color: #2e7d32; font-weight: bold; }
.text-loss { color: #c62828; font-weight: bold; }

.empty-box {
    background-color: #f6f6f6;
    border: 1.5px solid #cfcfcf;
    padding: 18px;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ================= UTILIDADES =================
def formato_numero(v):
    return f"${v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_porcentaje(v):
    return f"{str(v).replace('.', ',')}%"

def fecha():
    f = datetime.now()
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    return f"{meses[f.month-1]} {f.day} de {f.year} - {f.strftime('%I:%M %p').lower()}"

def guardar_historial(hist):
    pd.DataFrame(hist).to_csv(ARCHIVO_HIST, index=False)

def cargar_historial():
    if os.path.exists(ARCHIVO_HIST):
        return pd.read_csv(ARCHIVO_HIST).to_dict("records")
    return []

# ================= SISTEMA =================
PORCENTAJES = {1:[1,2.13,4.52], 2:[2,4.25,9.03], 3:[3,6.38,13.54], 4:[4,8.5,18.05]}
PAGO_BROKER = 0.89

# ================= ESTADO =================
if "init" not in st.session_state:
    hist = cargar_historial()
    st.session_state.update({
        "init": False,
        "capital": 0,
        "capital_ini": 0,
        "loss_trade": 0,
        "loss_consec": 0,
        "hist": hist,
        "contador": len(hist)
    })

# ================= HEADER =================
st.title("Sistema de Gestión de Inversión")
st.markdown("<div class='subtitle'>Creado por Nathalie Franco Jiménez</div>", unsafe_allow_html=True)

# ================= CAPITAL =================
if not st.session_state.init:
    cap = st.number_input("Capital inicial ($)", min_value=1, step=1)
    if st.button("Iniciar"):
        st.session_state.capital = cap
        st.session_state.capital_ini = cap
        st.session_state.init = True
        st.rerun()
    st.stop()

# ================= CALCULO =================
nivel = min(4, st.session_state.loss_consec // 3 + 1)
porc = PORCENTAJES[nivel][st.session_state.loss_trade]
monto = st.session_state.capital * porc / 100
retorno = monto * PAGO_BROKER

# ================= INFO =================
st.markdown(f"""
<div class='info'><b>Capital inicial:</b> {formato_numero(st.session_state.capital_ini)}</div>
<div class='info'><b>Saldo actual:</b> {formato_numero(st.session_state.capital)}</div>
<div class='info'><b>Próxima inversión:</b> {formato_porcentaje(porc)} → {formato_numero(monto)}</div>
<div class='info'><b>Nivel:</b> {nivel}</div>
""", unsafe_allow_html=True)

# ================= BOTONES WIN / LOSS =================
st.markdown("<div class='buttons-row'>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    win = st.button("Win")
with c2:
    loss = st.button("Loss")
st.markdown("</div>", unsafe_allow_html=True)

# ================= WIN =================
if win:
    st.session_state.capital += retorno
    st.session_state.loss_trade = 0
    st.session_state.contador += 1
    st.session_state.hist.insert(0,{
        "N°": st.session_state.contador,
        "Fecha": fecha(),
        "Resultado": "Win",
        "Inversión": formato_numero(monto),
        "Retorno": formato_numero(retorno),
        "Saldo": formato_numero(st.session_state.capital)
    })
    guardar_historial(st.session_state.hist)
    st.rerun()

# ================= LOSS =================
if loss:
    st.session_state.capital -= monto
    st.session_state.loss_trade += 1
    if st.session_state.loss_trade == 3:
        st.session_state.loss_consec += 3
        st.session_state.loss_trade = 0

    st.session_state.contador += 1
    st.session_state.hist.insert(0,{
        "N°": st.session_state.contador,
        "Fecha": fecha(),
        "Resultado": "Loss",
        "Inversión": formato_numero(monto),
        "Retorno": f"-{formato_numero(monto)}",
        "Saldo": formato_numero(st.session_state.capital)
    })
    guardar_historial(st.session_state.hist)
    st.rerun()

# ================= HISTORICO =================
st.markdown("<div class='hist-header'>", unsafe_allow_html=True)
c1, c2 = st.columns([8,1])
with c1:
    st.subheader("Histórico")
with c2:
    borrar = st.button("Borrar")
st.markdown("</div>", unsafe_allow_html=True)

if borrar:
    if os.path.exists(ARCHIVO_HIST):
        os.remove(ARCHIVO_HIST)
    st.session_state.clear()
    st.rerun()

if st.session_state.hist:
    df = pd.DataFrame(st.session_state.hist)
    html = "<table><thead><tr class='header-row'>" + "".join(f"<th>{c}</th>" for c in df.columns) + "</tr></thead><tbody>"
    for _, r in df.iterrows():
        html += "<tr>"
        for c, v in r.items():
            cls = "text-win" if v=="Win" else "text-loss" if v=="Loss" else ""
            html += f"<td class='{cls}'>{v}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)
else:
    st.markdown("<div class='empty-box'>Aún no hay operaciones registradas</div>", unsafe_allow_html=True)