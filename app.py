import streamlit as st
import pandas as pd
from PIL import Image

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# Style pour le logo et l'interface
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #e1e4e8; border-radius: 5px 5px 0 0; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #2e7d32 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DU STOCKAGE LOCAL (SESSION) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'plans': [], 'marchandises': [], 'elec': [], 'plomberie': [],
        'marbre': [], 'ceramique': [], 'salaries': []
    }

# --- EN-TÊTE ---
st.title("🏗️ LES ORCHIDÉES")
st.info("Portail de Gestion de Chantier - Tranches 3, 4 & 5")

# Choix du Mode (Lien entre Saisie et Consultation)
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

# --- FONCTION UTILITAIRE AFFICHAGE E-COMMERCE ---
def card_produit(nom, image_url, key_prefix, is_saisie=True):
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 2])
        col1.image("https://via.placeholder.com/100", width=80) # Remplacer par vos logos/photos
        col2.write(f"**{nom}**")
        if is_saisie:
            qte = col3.number_input("Qté", min_value=0, key=f"{key_prefix}_qte")
            det = col3.text_input("Détails", key=f"{key_prefix}_det")
            return {"produit": nom, "quantite": qte, "detail": det}
        else:
            # Mode consultation : on filtre les données existantes
            data = [d for d in st.session_state.db['elec'] if d['produit'] == nom]
            for d in data:
                col3.write(f"✅ {d['quantite']} unités ({d['detail']})")

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 Plans", "📦 Marchandises", "🛠️ Suivi Technique", "👥 Salarié"])

    with tabs[0]:
        st.subheader("Bouton d'Upload Plans")
        up_plan = st.file_uploader("Transférer PDF ou Photos", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_plan")
        if st.button("✅ CONFIRMER L'UPLOAD", type="primary"):
            if up_plan:
                st.session_state.db['plans'].append({"nom": up_plan.name, "tranche": tranche})
                st.success("Plan enregistré sur le portail !")

    with tabs[1]:
        st.subheader("Entrée Marchandises")
        fournisseur = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans", "Autre"], index=0)
        designation = st.text_input("Désignation de la marchandise")
        col_img1, col_img2 = st.columns(2)
        photo_bl = col_img1.file_uploader("Photo BL", type=['jpg', 'png'])
        photo_cam = col_img2.file_uploader("Photo Camion", type=['jpg', 'png'])
        
        if st.button("Valider la Réception"):
            st.session_state.db['marchandises'].append({
                "fournisseur": fournisseur, "designation": designation, "tranche": tranche
            })
            st.success("Réception enregistrée !")

    with tabs[2]:
        soustitre = st.radio("Spécialité", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if soustitre in ["Électricité", "Plomberie"]:
            prods = ["Prises", "Interrupteurs", "Câbles 1.5", "Vasques", "Toilettes"] if soustitre == "Plomberie" else ["Disjoncteur", "Spot", "Prise TV"]
            res = []
            for p in prods:
                res.append(card_produit(p, "", f"s_{p}"))
            if st.button(f"Enregistrer Consommation {soustitre}"):
                for r in res:
                    if r['quantite'] > 0:
                        st.session_state.db[soustitre.lower()].append(r)
                st.success("Consommation validée !")

        elif soustitre == "Marbre":
            pers = st.selectbox("Intervenant", ["FETTAH", "SIMO"])
            bloc = st.selectbox("Numéro de Bloc", ["Bloc A", "Bloc B", "Bloc C"])
            imm = st.text_input("Immeuble")
            app = st.text_input("Appartement")
            ref = st.text_input("Référence utilisée")
            if st.button("Enregistrer Marbre"):
                st.session_state.db['marbre'].append({"pers": pers, "bloc": bloc, "imm": imm, "app": app, "ref": ref})

    with tabs[3]:
        up_paie = st.file_uploader("Upload Pointage (XLSX/PDF)", type=['xlsx', 'pdf'])
        if st.button("Confirmer Pointage"):
            st.session_state.db['salaries'].append({"nom": up_paie.name})

# ==========================================
#             MODE CONSULTATION
# ==========================================
else:
    tabs = st.tabs(["📄 Plans", "📦 Marchandises", "🛠️ Suivi Technique", "👥 Salarié"])
    
    with tabs[0]:
        st.subheader("Consultation des Plans")
        for p in st.session_state.db['plans']:
            st.write(f"📄 {p['nom']} ({p['tranche']})")

    with tabs[1]:
        st.subheader("Historique Marchandises")
        df_m = pd.DataFrame(st.session_state.db['marchandises'])
        if not df_m.empty:
            st.table(df_m)

    with tabs[2]:
        soustitre_c = st.radio("Spécialité", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key="c_spec")
        if soustitre_c in ["Électricité", "Plomberie"]:
            prods = ["Prises", "Interrupteurs", "Câbles 1.5", "Vasques", "Toilettes"]
            for p in prods:
                card_produit(p, "", f"c_{p}", is_saisie=False)
        elif soustitre_c == "Marbre":
            st.table(pd.DataFrame(st.session_state.db['marbre']))

    with tabs[3]:
        st.subheader("Historique Salariés")
        for s in st.session_state.db['salaries']:
            st.write(f"📁 {s['nom']}")
