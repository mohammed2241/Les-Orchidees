import streamlit as st
import pandas as pd
import base64
import os
import pickle

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- PERSISTENCE DES DONNÉES ---
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
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION D'OUVERTURE (SÉCURISÉE) ---
def afficher_bouton_lecture(file_bytes, file_name, key):
    # Encodage seulement au moment de l'affichage pour éviter de bloquer l'onglet
    b64 = base64.b64encode(file_bytes).decode()
    if file_name.lower().endswith('.pdf'):
        # Utilisation de l'objet PDF natif pour éviter le blocage Chrome
        pdf_display = f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="text-decoration:none;"><div style="background-color:#1e88e5; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">📄 OUVRIR LE PDF</div></a>'
    else:
        # Pour les images (JPG/PNG)
        pdf_display = f'<a href="data:image/jpeg;base64,{b64}" target="_blank" style="text-decoration:none;"><div style="background-color:#43a047; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">🖼️ VOIR L\'IMAGE</div></a>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with t1:
        up_p = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ ENREGISTRER", key="btn_p"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                sauvegarder_donnees()
                st.success("Plan enregistré !")

    with t2:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_m")
        d = st.text_input("Désignation", key="des_m")
        if st.button("Valider Réception", key="btn_m"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            sauvegarder_donnees()
            st.success("Réception ajoutée !")

    with t3:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec == "Marbre":
            p = st.selectbox("Nom", ["FETTAH", "Simo"], key="m_p")
            im = st.text_input("Immeuble", key="m_i")
            ap = st.text_input("Appart", key="m_a")
            if st.button("Valider Marbre", key="btn_marbre"):
                data['marbre'].append({"Nom": p, "Lieu": f"Imm {im} - App {ap}"})
                sauvegarder_donnees()
                st.success("Enregistré")
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"], key="c_z")
            im_c = st.text_input("Immeuble", key="c_i")
            if st.button("Valider Céramique", key="btn_ceram"):
                data['ceram'].append({"Zone": z, "Lieu": f"Imm {im_c}"})
                sauvegarder_donnees()
                st.success("Enregistré")

    with t4:
        up_s = st.file_uploader("Fichier Salarié", type=['xlsx', 'pdf'], key="up_s")
        if st.button("Confirmer Salarié", key="btn_s"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                sauvegarder_donnees()
                st.success("Ajouté !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Historique - {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for idx, p in enumerate(data['plans']):
            with st.expander(f"📄 Plan : {p['nom']}"):
                # On n'affiche le bouton qu'à l'ouverture de l'expander pour gagner en vitesse
                afficher_bouton_lecture(p['content'], p['nom'], f"p_{idx}")

    with c2:
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with c3:
        sel = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key="r_c")
        k_map = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        if data[k_map[sel]]: st.table(pd.DataFrame(data[k_map[sel]]))

    with c4:
        for idx, s in enumerate(data['salaries']):
            with st.expander(f"👥 Salarié : {s['nom']}"):
                afficher_bouton_lecture(s['content'], s['nom'], f"s_{idx}")
