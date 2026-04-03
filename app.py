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
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE TÉLÉCHARGEMENT RAPIDE ---
def bouton_telecharger(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}"><button style="background-color:#2e7d32; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; font-weight:bold;">📥 TÉLÉCHARGER / OUVRIR</button></a>'
    st.markdown(href, unsafe_allow_html=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with t1: # PLANS
        st.subheader("Upload des plans (PDF/Photos)")
        up_p = st.file_uploader("Choisir un fichier", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ CONFIRMER L'UPLOAD", key="btn_p"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up
