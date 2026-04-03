import streamlit as st
import pandas as pd
import base64
import os
import pickle

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- SYSTÈME DE SAUVEGARDE PERMANENTE (FICHIER LOCAL) ---
DB_FILE = "data_chantier.pkl"

def charger_donnees():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            return pickle.load(f)
    return {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

# Initialisation au démarrage
if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# --- BARRE LATÉRALE ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE TÉLÉCHARGEMENT ---
def bouton_telecharger(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}"><button style="background-color:#2e7d32; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; font-weight:bold;">📥 OUVRIR {file_name}</button></a>'
    st.markdown(href, unsafe_allow_html=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with t1: # PLANS [cite: 3, 4]
        st.subheader("Transfert des plans (PDF/Photos)")
        up_p = st.file_uploader("Upload", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ CONFIRMER L'UPLOAD", key="btn_p"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                sauvegarder_donnees() # Sauvegarde immédiate 
                st.success("Plan sauvegardé sur le portail !")

    with t2: # MARCHANDISES [cite: 7, 8, 9]
        st.subheader("Entrée Marchandises")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_m")
        desig = st.text_input("Désignation", key="des_m")
        c1, c2 = st.columns(2)
        bl = c1.file_uploader("Photo BL", key="up_bl")
        cam = c2.file_uploader("Photo Camion", key="up_cam")
        if st.button("Valider la réception", key="btn_m"):
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            sauvegarder_donnees() # Sauvegarde immédiate [cite: 9]
            st.success("Réception ajoutée à l'historique !")

    with t3: # SUIVIE [cite: 11, 12, 13, 15, 17]
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec in ["Électricité", "Plomberie"]: # [cite: 12, 17]
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for i in items:
                col1, col2, col3 = st.columns([2, 1, 2])
                col1.write(f"**{i}**")
                q = col2.number_input("Qté", min_value=0, key=f"q_{i}_{tranche}")
                d = col3.text_input("Détails", key=f"d_{i}_{tranche}")
                if st.button(f"Enregistrer {i}", key=f"b_{i}"):
                    key_db = "elec" if spec == "Électricité" else "plomb"
                    data[key_db].append({"Produit": i, "Quantité": q, "Détail": d})
                    sauvegarder_donnees() # Sauvegarde immédiate [cite: 13]
                    st.toast(f"{i} enregistré")

        elif spec == "Marbre": # [cite: 13, 14]
            p = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_p")
            bl = st.selectbox("N° Bloc", ["Bloc 1", "Bloc 2", "Bloc 3"], key="m_b")
            im = st.text_input("Immeuble", key="m_i")
            ap = st.text_input("Appartement", key="m_a")
            if st.button("Valider Marbre", key="btn_marbre"):
                data['marbre'].append({"Nom": p, "Bloc": bl, "Immeuble": im, "Appart": ap})
                sauvegarder_donnees()
                st.success("Saisie Marbre validée !")

        elif spec == "Céramique": # [cite: 15, 16]
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse appart", "Terrasse immeuble"], key="c_z")
            im_c = st.text_input("Immeuble", key="c_i")
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"], key="c_e")
            if st.button("Valider Céramique", key="btn_ceram"):
                data['ceram'].append({"Type": z, "Lieu": f"Imm {im_c} - Etage {et}"})
                sauvegarder_donnees()
                st.success("Saisie Céramique validée !")

    with t4: # SALARIÉ [cite: 18, 19]
        st.subheader("Historique du pointage")
        up_s = st.file_uploader("Fichier XLSX/PDF", type=['xlsx', 'pdf'], key="up_s")
        if st.button("Confirmer Salarié", key="btn_s"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                sauvegarder_donnees() # Sauvegarde immédiate [cite: 19]
                st.success("Pointage enregistré !")

# ==========================================
#           MODE CONSULTATION [cite: 20]
# ==========================================
else:
    st.header(f"🔍 Historique - {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with c1: # 
        for p in data['plans']:
            col_n, col_b = st.columns([3, 1])
            col_n.write(f"📄 **{p['nom']}**")
            with col_b: bouton_telecharger(p['content'], p['nom'])

    with c2: # [cite: 9]
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with c3: # [cite: 13, 14, 16]
        sel = st.radio("Consulter :", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key="r_c")
        k_map = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        if data[k_map[sel]]: st.table(pd.DataFrame(data[k_map[sel]]))

    with c4: # [cite: 19]
        for s in data['salaries']:
            col_n, col_b = st.columns([3, 1])
            col_n.write(f"📁 **{s['nom']}**")
            with col_b: bouton_telecharger(s['content'], s['nom'])
