import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION DE LA MÉMOIRE (PAR TRANCHE) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }

# --- BARRE LATÉRALE ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE TÉLÉCHARGEMENT (SANS RETARD) ---
def bouton_telecharger(file_bytes, file_name, key_id):
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}"><button style="background-color:#2e7d32; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer;">📥 Télécharger / Ouvrir</button></a>'
    st.markdown(href, unsafe_allow_html=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with t1: # PLANS
        up_p = st.file_uploader("Upload Plan (PDF/Photo)", type=['pdf', 'jpg', 'png', 'jpeg'], key="u1")
        if st.button("✅ CONFIRMER L'UPLOAD", key="b1"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                st.success("Plan enregistré !")

    with t2: # MARCHANDISES
