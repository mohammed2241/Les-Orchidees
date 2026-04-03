import streamlit as st
import pandas as pd
import base64
import os
import pickle
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- SYSTÈME DE SAUVEGARDE ---
DB_FILE = "data_chantier.pkl"

def charger_donnees():
    structure_vide = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                data = pickle.load(f)
                for t in structure_vide:
                    if t not in data: data[t] = structure_vide[t]
                    for key in structure_vide[t]:
                        if key not in data[t]: data[t][key] = []
                return data
        except: return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# --- NAVIGATION ---
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION APERÇU EXCEL (SANS TÉLÉCHARGEMENT) ---
def apercu_excel_direct(file_bytes, file_name):
    # Pour un vrai aperçu sans téléchargement sur Streamlit Cloud, 
    # on affiche le tableau de données directement dans l'app
    try:
        df = pd.read_excel(file_bytes)
        st.write(f"**Aperçu du contenu : {file_name}**")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error("L'aperçu direct a échoué. Utilisez l'ouverture Excel.")

def bouton_ouvrir_excel_app(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'
    st.markdown(f"""
        <a href="{href}" download="{file_name}" style="text-decoration:none;">
            <button style="background:#217346;color:white;border:none;padding:12px;border-radius:5px;width:100%;cursor:pointer;font-weight:bold;">
                🟢 OUVRIR DANS L'APPLICATION EXCEL
            </button>
        </a>""", unsafe_allow_html=True)

# ==========================================
#      MODE CONSULTATION (PARTIE SALARIÉ)
# ==========================================
if mode == "🔍 CONSULTATION":
    st.header(f"🔍 Consultation - {tranche}")
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with tabs[3]: # ONGLET SALARIÉ
        if not data['salaries']:
            st.info("Aucun fichier enregistré.")
        for s in data['salaries']:
            with st.expander(f"📊 {s['nom']}"):
                if s['nom'].lower().endswith('.xlsx') or s['nom'].lower().endswith('.xls'):
                    # 1. Option Aperçu immédiat dans la page
                    apercu_excel_direct(s['content'], s['nom'])
                    st.divider()
                    # 2. Option Ouverture dans l'app de la tablette
                    bouton_ouvrir_excel_app(s['content'], s['nom'])
                else:
                    # Pour les PDF
                    b64 = base64.b64encode(s['content']).decode()
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)

# (Le reste du code pour la SAISIE et les autres onglets reste identique à votre version validée)
