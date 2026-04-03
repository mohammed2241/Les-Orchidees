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
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE LECTURE INTÉGRÉE ---
def lecteur_integre(file_bytes, file_name):
    ext = file_name.lower().split('.')[-1]
    
    if ext in ['jpg', 'jpeg', 'png']:
        st.image(file_bytes, use_container_width=True)
    elif ext == 'pdf':
        # Encodage pour l'affichage intégré
        base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
        # Création d'une zone de lecture (Embed)
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning(f"Le format .{ext} ne peut pas être lu directement. Utilisez le bouton ci-dessous.")
    
    # On laisse quand même le bouton en bas au cas où
    st.download_button("📥 Télécharger une copie", data=file_bytes, file_name=file_name, key=os.urandom(5).hex())

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with t1:
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'])
        if st.button("✅ Enregistrer Plan"):
            if up:
                data['plans'].append({"nom": up.name, "content": up.getvalue()})
                sauvegarder_donnees()
                st.success("Plan enregistré !")

    with t2:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        if st.button("Valider Marchandise"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            sauvegarder_donnees()
            st.success("OK !")

    with t3:
        m = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True)
        if m == "Marbre":
            p = st.selectbox("Nom", ["FETTAH", "Simo"])
            l = st.text_input("Immeuble / Appart")
            if st.button("Enregistrer Marbre"):
                data['marbre'].append({"Nom": p, "Lieu": l})
                sauvegarder_donnees()
                st.success("OK")
        else:
            z = st.text_input("Zone")
            if st.button("Enregistrer Céramique"):
                data['ceram'].append({"Info": z})
                sauvegarder_donnees()
                st.success("OK")

    with t4:
        up_s = st.file_uploader("Pointage", type=['pdf', 'xlsx'])
        if st.button("Confirmer Salarié"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                sauvegarder_donnees()
                st.success("Enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"Consultation {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for p in data['plans']:
            with st.expander(f"👁️ VOIR : {p['nom']}", expanded=False):
                lecteur_integre(p['content'], p['nom'])

    with c2:
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with c3:
        m_c = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True, key="c_m")
        k = "marbre" if m_c == "Marbre" else "ceram"
        if data[k]: st.table(pd.DataFrame(data[k]))

    with c4:
        for s in data['salaries']:
            with st.expander(f"👁️ VOIR : {s['nom']}", expanded=False):
                lecteur_integre(s['content'], s['nom'])
