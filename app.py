import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }

# --- NAVIGATION ---
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE TÉLÉCHARGEMENT RAPIDE (AVEC CACHE) ---
@st.cache_data
def bouton_telechargement_rapide(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="text-decoration:none;"><button style="background-color:#2e7d32; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">📥 TÉLÉCHARGER / OUVRIR</button></a>'

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs[0]: # PLANS
        up_p = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png'], key=f"up_p_{tranche}")
        if st.button("✅ CONFIRMER", key=f"ok_p_{tranche}"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                st.success("Plan enregistré")

    with tabs[1]: # MARCHANDISES
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key=f"f_{tranche}")
        desig = st.text_input("Désignation", key=f"d_{tranche}")
        c1, c2 = st.columns(2)
        bl = c1.file_uploader("Photo BL", key=f"bl_{tranche}")
        cam = c2.file_uploader("Photo Camion", key=f"cam_{tranche}")
        if st.button("Valider la
