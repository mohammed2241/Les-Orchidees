import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Les Orchidées - TEST", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E8449; font-size: 40px; font-weight: bold; }
    .f-card { border-left: 10px solid; padding: 15px; background: #f9f9f9; border-radius: 8px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Accueil"
if 'tranche' not in st.session_state:
    st.session_state.tranche = None

# --- DONNÉES DE TEST : 20 FOURNISSEURS ---
FOURNISSEURS = {
    "LafargeHolcim": {"c": "#E74C3C", "t": "Gros Œuvre"},
    "Ciments du Maroc": {"c": "#3498DB", "t": "Gros Œuvre"},
    "Maghreb Steel": {"c": "#F1C40F", "t": "Charpente/Fer"},
    "Sika Maroc": {"c": "#27AE60", "t": "Étanchéité"},
    "Induver": {"c": "#8E44AD", "t": "Vitrerie"},
    "Aluminium du Maroc": {"c": "#7F8C8D", "t": "Menuiserie Alu"},
    "Jacob Delafon": {"c": "#D35400", "t": "Sanitaire"},
    "Roca Maroc": {"c": "#2980B9", "t": "Sanitaire"},
    "Legrand": {"c": "#C0392B", "t": "Électricité"},
    "Ingelec": {"c": "#16A085", "t": "Électricité"},
    "Nexans": {"c": "#2C3E50", "t": "Câblage"},
    "Ventec": {"c": "#E67E22", "t": "Climatisation"},
    "Colorado Paints": {"c": "#E91E63", "t": "Peinture"},
    "Astral": {"c": "#673AB7", "t": "Peinture"},
    "Facemag": {"c": "#795548", "t": "Céramique"},
    "Super Cérame": {"c": "#607D8B", "t": "Céramique"},
    "Maroc Menuiserie": {"c": "#5D4037", "t": "Bois (Najar)"},
    "Bricoma Pro": {"c": "#FF5722", "t": "Outillage"},
    "Somat": {"c": "#4CAF50", "t": "Matériel Pompage"},
    "Auto-Hall (Camions)": {"c": "#000000", "t": "Logistique"}
}

# --- PAGE D'ACCUEIL ---
if st.session_state.page == "Accueil":
    st.markdown('<p class="main-title">LES ORCHIDÉES</p>', unsafe_allow_html=True)
    for t in ["Tranche 3", "Tranche 4", "Tranche 5"]:
        col1, col2 = st.columns([1, 3])
        col1.image("https://via.placeholder.com/200x120?text=Projet+3D", use_container_width=True)
        col2.subheader(t)
        if col2.button(f"Ouvrir {t}", key=t):
            st.session_state.tranche = t
            st.session_state.page = "Interne"
            st.rerun()
        st.divider()

# --- PAGE INTERNE ---
elif st.session_state.page == "Interne":
    if st.button("⬅ Retour"):
        st.session_state.page = "Accueil"
        st.rerun()

    st.title(f"📍 {st.session_state.tranche}")
    tabs = st.tabs(["📄 Plans PDF", "📦 Marchandises", "👥 Salariés", "🏗️ Finitions"])

    # --- ONGLET PLANS ---
    with tabs[0]:
        st.subheader("📁 Bibliothèque de Plans (Test)")
        up = st.file_uploader("Ajouter un plan", type=['pdf'])
        col_a, col_b = st.columns(2)
        with col_a:
            st.button("📄 Plan de Masse - Secteur A.pdf")
            st.button("📄 Plan Ferraillage Fondations.pdf")
        with col_b:
            st.button("📄 Plan Électricité R+1.pdf")
            st.button("📄 Détails Menuiserie Bois.pdf")

    # --- ONGLET MARCHANDISES (LES 20 FOURNISSEURS) ---
    with tabs[1]:
        search = st.text_input("🔍 Rechercher parmi les 20 fournisseurs...")
        for f, info in FOURNISSEURS.items():
            if search.lower() in f.lower():
                st.markdown(f"""
                    <div class="f-card" style="border-left-color: {info['c']};">
                        <strong style="font-size:18px;">{f}</strong> | <small>{info['t']}</small>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander(f"Détails livraisons {f}"):
                    c1, c2 = st.columns(2)
                    c1.text_input("N° BC", key=f"bc_{f}")
                    c2.camera_input("Scanner BL", key=f"cam_{f}")

    # --- ONGLET SALARIÉS ---
    with tabs[2]:
        st.subheader("👥 Historique de Paie")
        st.file_uploader("Transmettre Excel Quinzaine", type=['xlsx'])
        st.info("Bouton prêt pour réceptionner vos fichiers PC.")

    # --- ONGLET FINITIONS ---
    with tabs[3]:
        secteur = st.selectbox("Secteur", ["Marbre", "Céramique", "Menuiserie", "Électricité", "Plomberie"])
        st.write(f"Vérification technique : **{secteur}**")
        st.select_slider("Progression", options=["0%", "50%", "100%"])
        st.camera_input("Photo de l'avancement")
