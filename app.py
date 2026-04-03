import streamlit as st
import pandas as pd
import base64
import os
import pickle

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- PERSISTENCE DES DONNÉES (Sauvegarde automatique) ---
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
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE LECTURE AUTOMATIQUE (NOUVEL ONGLET) ---
def bouton_lecture_directe(file_bytes, file_name, label="Lire le document"):
    b64 = base64.b64encode(file_bytes).decode()
    # Détection du type de fichier pour le navigateur
    mime_type = "application/pdf" if file_name.lower().endswith('.pdf') else "image/jpeg"
    
    # Lien HTML qui simule un bouton et ouvre dans un nouvel onglet (_blank)
    href = f'''
        <a href="data:{mime_type};base64,{b64}" target="_blank" style="text-decoration:none;">
            <div style="background-color:#2e7d32; color:white; padding:12px; border-radius:8px; text-align:center; font-weight:bold; cursor:pointer;">
                📖 {label}
            </div>
        </a>
    '''
    st.markdown(href, unsafe_allow_html=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

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
            st.success("Réception archivée !")

    with t3:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        # ... (Formulaires Marbre/Céram identiques au précédent)
        if spec == "Marbre":
            p = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_p")
            im = st.text_input("Immeuble", key="m_i")
            ap = st.text_input("Appart", key="m_a")
            if st.button("Valider Marbre", key="btn_marbre"):
                data['marbre'].append({"Nom": p, "Lieu": f"Imm {im} - App {ap}"})
                sauvegarder_donnees()
                st.success("Marbre enregistré")
        # (Note: Le reste du suivi technique est inclus dans le code complet)

    with t4:
        up_s = st.file_uploader("Fichier Salarié", type=['xlsx', 'pdf'], key="up_s")
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
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with c1:
        if data['plans']:
            for p in data['plans']:
                col_n, col_b = st.columns([3, 2])
                col_n.write(f"📄 **{p['nom']}**")
                with col_b:
                    bouton_lecture_directe(p['content'], p['nom'], "Ouvrir dans un onglet")
        else: st.write("Aucun plan.")

    with c2:
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with c3:
        sel = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key="r_c")
        k_map = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        if data[k_map[sel]]: st.table(pd.DataFrame(data[k_map[sel]]))

    with c4:
        if data['salaries']:
            for s in data['salaries']:
                col_n, col_b = st.columns([3, 2])
                col_n.write(f"📁 **{s['nom']}**")
                with col_b:
                    bouton_lecture_directe(s['content'], s['nom'], "Lire le pointage")
        else: st.write("Aucun document salarié.")
