import streamlit as st
import pandas as pd
import base64
import os
import pickle

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
                # Vérification que toutes les clés existent pour éviter KeyError
                for t in structure_vide:
                    if t not in data: data[t] = structure_vide[t]
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

# --- FONCTION DE VISUALISATION (ANTI-PLANTAGE) ---
def afficher_fichier(file_bytes, file_name):
    ext = file_name.lower().split('.')[-1]
    
    if ext in ['jpg', 'jpeg', 'png']:
        st.image(file_bytes, caption=file_name)
    elif ext == 'pdf':
        try:
            b64 = base64.b64encode(file_bytes).decode()
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except:
            st.warning("Impossible d'afficher le PDF directement sur cet appareil.")
    else:
        st.info(f"Fichier {ext.upper()} : Utilisez le bouton ci-dessous pour l'ouvrir.")
    
    st.download_button(f"📥 Télécharger {file_name}", data=file_bytes, file_name=file_name, key=os.urandom(5).hex())

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with tabs[0]: # PLANS
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_plans")
        if st.button("✅ Enregistrer Plan"):
            if up:
                data['plans'].append({"nom": up.name, "content": up.getvalue()})
                sauvegarder_donnees()
                st.success("Plan enregistré !")

    with tabs[1]: # MARCHANDISES
        col1, col2 = st.columns(2)
        f = col1.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = col2.text_input("Désignation")
        if st.button("Valider Marchandise"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            sauvegarder_donnees()
            st.success("Enregistré !")

    with tabs[2]: # SUIVI
        metier = st.radio("Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        if metier == "Marbre":
            p = st.selectbox("Nom", ["FETTAH", "Simo"])
            l = st.text_input("Immeuble / Appart")
            if st.button("Enregistrer Marbre"):
                data['marbre'].append({"Nom": p, "Lieu": l})
                sauvegarder_donnees()
                st.success("OK")
        elif metier == "Céramique":
            z = st.text_input("Zone / Immeuble")
            if st.button("Enregistrer Céramique"):
                data['ceram'].append({"Info": z})
                sauvegarder_donnees()
                st.success("OK")

    with tabs[3]: # SALARIÉ
        up_s = st.file_uploader("Pointage", type=['pdf', 'xlsx'], key="up_sal")
        if st.button("Confirmer Salarié"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                sauvegarder_donnees()
                st.success("Pointage enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"Historique {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for p in data.get('plans', []):
            with st.expander(f"📁 Plan : {p['nom']}"):
                afficher_fichier(p['content'], p['nom'])

    with c2:
        if data.get('marchandises'): st.table(pd.DataFrame(data['marchandises']))

    with c3:
        m = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True, key="cons_m")
        key = "marbre" if m == "Marbre" else "ceram"
        if data.get(key): st.table(pd.DataFrame(data[key]))

    with c4:
        for s in data.get('salaries', []):
            with st.expander(f"📁 Document : {s['nom']}"):
                afficher_fichier(s['content'], s['nom'])
