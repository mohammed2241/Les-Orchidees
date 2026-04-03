import streamlit as st
import pandas as pd
import base64
import os
import pickle

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- PERSISTENCE ---
DB_FILE = "data_chantier.pkl"

def charger_donnees():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                return pickle.load(f)
        except: pass
    return {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# --- NAVIGATION ---
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE VISUALISATION SANS BLOCAGE ---
def visualiser_document(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    if file_name.lower().endswith('.pdf'):
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.image(file_bytes, caption=file_name, use_container_width=True)
    
    # Bouton de secours pour télécharger
    st.download_button("📥 Télécharger le fichier", data=file_bytes, file_name=file_name)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with t1: # PLANS
        up_p = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ ENREGISTRER LE PLAN", key="btn_p"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                sauvegarder_donnees()
                st.success("Plan ajouté !")

    with t2: # MARCHANDISES
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_m")
        d = st.text_input("Désignation", key="des_m")
        if st.button("Valider Réception", key="btn_m"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            sauvegarder_donnees()
            st.success("Réception enregistrée !")

    with t3: # SUIVI
        spec = st.radio("Métier", ["Élec", "Plomb", "Marbre", "Céram"], horizontal=True)
        if spec == "Marbre":
            p = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_p")
            im = st.text_input("Immeuble", key="m_i")
            ap = st.text_input("Appartement", key="m_a")
            if st.button("Enregistrer Marbre", key="btn_marbre"):
                data['marbre'].append({"Nom": p, "Position": f"Imm {im} - App {ap}"})
                sauvegarder_donnees()
                st.success("Saisie Marbre OK !")
        elif spec == "Céram":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"], key="c_z")
            im_c = st.text_input("Immeuble", key="c_i")
            if st.button("Enregistrer Céram", key="btn_ceram"):
                data['ceram'].append({"Zone": z, "Lieu": f"Imm {im_c}"})
                sauvegarder_donnees()
                st.success("Saisie Céram OK !")

    with t4: # SALARIÉ
        up_s = st.file_uploader("Upload Pointage", type=['xlsx', 'pdf'], key="up_s")
        if st.button("Confirmer Salarié", key="btn_s"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                sauvegarder_donnees()
                st.success("Pointage ajouté !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for idx, p in enumerate(data['plans']):
            with st.expander(f"📄 Plan : {p['nom']}"):
                visualiser_document(p['content'], p['nom'])

    with c2:
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with c3:
        sel = st.radio("Métier", ["Élec", "Plomb", "Marbre", "Céram"], key="r_c")
        k_map = {"Élec": "elec", "Plomb": "plomb", "Marbre": "marbre", "Céram": "ceram"}
        if data[k_map[sel]]: st.table(pd.DataFrame(data[k_map[sel]]))

    with c4:
        for idx, s in enumerate(data['salaries']):
            with st.expander(f"👥 Pointage : {s['nom']}"):
                visualiser_document(s['content'], s['nom'])
