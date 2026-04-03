import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION UNIQUE DU STOCKAGE ---
# On utilise des noms simples sans accents pour éviter les KeyError
if 'db' not in st.session_state:
    st.session_state.db = {
        'plans': [], 
        'marchandises': [], 
        'electricite': [], # Correction clé
        'plomberie': [], 
        'marbre': [], 
        'ceramique': [], 
        'salaries': []
    }

# --- DESIGN ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #2e7d32 !important; color: white !important; }
    div.stButton > button:first-child { background-color: #2e7d32; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ LES ORCHIDÉES")

# --- NAVIGATION ---
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

# --- FONCTION E-COMMERCE ---
def fiche_produit(nom, key_id, mode_saisie=True):
    col1, col2, col3 = st.columns([1, 2, 2])
    col1.markdown("🖼️") # Place pour le logo
    col2.write(f"**{nom}**")
    if mode_saisie:
        qte = col3.number_input("Qté", min_value=0, key=f"qte_{key_id}")
        det = col3.text_input("Détails", key=f"det_{key_id}")
        return {"produit": nom, "quantite": qte, "detail": det}
    return None

# ==========================================
#             MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE TECHNIQUE", "👥 SALARIÉ"])

    with tabs[0]:
        st.subheader("Bouton d'Upload Plans")
        up = st.file_uploader("Transférer PDF ou Photo", type=['pdf', 'jpg', 'png'])
        if st.button("✅ CONFIRMER L'UPLOAD"):
            if up:
                st.session_state.db['plans'].append({"nom": up.name, "date": "Aujourd'hui"})
                st.success(f"Plan {up.name} enregistré !")

    with tabs[1]:
        st.subheader("Entrée Marchandises")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        desig = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        f_bl = c1.file_uploader("Photo BL")
        f_cam = c2.file_uploader("Photo Camion")
        if st.button("Valider la réception"):
            st.session_state.db['marchandises'].append({"fournisseur": fourn, "desig": desig})
            st.success("Réception validée !")

    with tabs[2]:
        spec = st.radio("Spécialité", ["Electricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec == "Electricité":
            p1 = fiche_produit("Spot", "spot")
            p2 = fiche_produit("Prise TV", "ptv")
            if st.button("Enregistrer Consommation Électricité"):
                # On force l'ajout seulement si la quantité > 0
                for p in [p1, p2]:
                    if p["quantite"] > 0:
                        st.session_state.db['electricite'].append(p)
                st.success("Saisie Électricité enregistrée !")

        elif spec == "Plomberie":
            p1 = fiche_produit("Vasque", "vasq")
            p2 = fiche_produit("Toilette", "wc")
            if st.button("Enregistrer Plomberie"):
                for p in [p1, p2]:
                    if p["quantite"] > 0:
                        st.session_state.db['plomberie'].append(p)
                st.success("Saisie Plomberie enregistrée !")

        elif spec == "Marbre":
            pers = st.selectbox("Intervenant", ["FETTAH", "SIMO"])
            bloc = st.text_input("N° Bloc")
            imm = st.text_input("Immeuble")
            app = st.text_input("Appartement")
            if st.button("Valider Marbre"):
                st.session_state.db['marbre'].append({"nom": pers, "local": f"{imm}-{app}"})
                st.success("Pointage Marbre fait !")

        elif spec == "Céramique": # Correction page vide
            zone = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse Appart", "Terrasse Immeuble"])
            imm_c = st.text_input("Immeuble", key="imm_c")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            if st.button("Valider Céramique"):
                st.session_state.db['ceramique'].append({"zone": zone, "position": f"Imm {imm_c} - {etage}"})
                st.success("Position Céramique enregistrée !")

    with tabs[3]:
        sal = st.file_uploader("Upload Pointage Salarié", type=['xlsx', 'pdf'])
        if st.button("Confirmer Salarié"):
            if sal:
                st.session_state.db['salaries'].append({"nom": sal.name})
                st.success("Document Salarié ajouté !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    tabs_c = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE TECHNIQUE", "👥 SALARIÉ"])
    
    with tabs_c[0]:
        st.write("### Plans consultables")
        if st.session_state.db['plans']:
            for p in st.session_state.db['plans']:
                st.info(f"📄 {p['nom']}")
        else: st.warning("Aucun plan enregistré.")

    with tabs_c[1]:
        st.write("### Historique Marchandises")
        if st.session_state.db['marchandises']:
            st.table(pd.DataFrame(st.session_state.db['marchandises']))
        else: st.warning("Historique vide.")

    with tabs_c[2]:
        spec_c = st.radio("Consulter :", ["Electricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key="cons_radio")
        # On affiche le contenu selon la spécialité
        cle = spec_c.lower().replace("é", "e")
        if st.session_state.db[cle]:
            st.table(pd.DataFrame(st.session_state.db[cle]))
        else: st.warning(f"Pas de données pour {spec_c}")

    with tabs_c[3]:
        st.write("### Documents Salariés")
        for s in st.session_state.db['salaries']:
            st.success(f"📁 {s['nom']}")
