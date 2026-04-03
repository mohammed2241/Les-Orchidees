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
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTIONS D'OUVERTURE ---
def bouton_ouvrir_general(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    mime = "application/pdf" if file_name.lower().endswith('.pdf') else "image/jpeg"
    js = f"""<script>function openDoc(){{var b=atob("{b64}"),n=new Array(b.length);for(var i=0;i<b.length;i++)n[i]=b.charCodeAt(i);var blob=new Blob([new Uint8Array(n)],{{type:"{mime}"}});window.open(URL.createObjectURL(blob),'_blank');}}</script>
    <button onclick="openDoc()" style="background:#007bff;color:white;border:none;padding:10px;border-radius:5px;width:100%;cursor:pointer;font-weight:bold;">👁️ VOIR LE DOCUMENT</button>"""
    st.components.v1.html(js, height=50)

def bouton_excel_tablette(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    # Lien utilisant le protocole ms-excel pour forcer l'ouverture dans l'app
    href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}'
    html = f"""
    <a href="{href}" download="{file_name}" style="text-decoration:none;">
        <button style="background:#217346;color:white;border:none;padding:12px;border-radius:5px;width:100%;cursor:pointer;font-weight:bold;">
            📊 OUVRIR DANS EXCEL (TABLETTE)
        </button>
    </a>"""
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t1: # PLANS
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees()
            st.success("Plan enregistré !")
            
    with t2: # MARCHANDISES
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", type=['jpg','jpeg','png'], key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", type=['jpg','jpeg','png'], key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({
                "Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M"),
                "photo_bl": p_bl.getvalue() if p_bl else None,
                "photo_cam": p_cam.getvalue() if p_cam else None
            })
            sauvegarder_donnees()
            st.success("Réception enregistrée !")

    with t3: # SUIVI DÉTAILLÉ (RÉTABLI)
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec in ["Électricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for i in items:
                col1, col2, col3 = st.columns([2, 1, 2])
                q = col2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = col3.text_input("Détails", key=f"d_{i}")
                p_suivi = st.file_uploader(f"Photo {i}", type=['jpg','jpeg','png'], key=f"p_{i}")
                if st.button(f"Enregistrer {i}", key=f"btn_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit": i, "Qté": q, "Détail": dt, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_suivi.getvalue() if p_suivi else None})
                    sauvegarder_donnees()
                    st.toast(f"{i} validé !")
        elif spec == "Marbre":
            p = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            im = st.text_input("Immeuble")
            ap = st.text_input("Appartement")
            p_m = st.file_uploader("Photo Marbre", type=['jpg','jpeg','png'])
            if st.button("Valider Marbre"):
                data['marbre'].append({"Nom": p, "Lieu": f"Imm {im} - App {ap}", "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_m.getvalue() if p_m else None})
                sauvegarder_donnees()
                st.success("Marbre OK")
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_c = st.file_uploader("Photo Céramique", type=['jpg','jpeg','png'])
            if st.button("Valider Céramique"):
                data['ceram'].append({"Type": z,
