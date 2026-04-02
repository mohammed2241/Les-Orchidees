import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# Simulation de connexion Drive (Via les Secrets)
if "gcp_service_account" in st.secrets:
    st.sidebar.success("✅ Connecté au Google Drive")
else:
    st.sidebar.warning("⚠️ Mode hors-ligne (Secrets non configurés)")

# --- NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Accueil"
if 'tranche' not in st.session_state: st.session_state.tranche = None

# --- ACCUEIL ---
if st.session_state.page == "Accueil":
    st.title("🏗️ LES ORCHIDÉES")
    for t in ["Tranche 3", "Tranche 4", "Tranche 5"]:
        if st.button(f"ACCÉDER À LA {t}", use_container_width=True):
            st.session_state.tranche = t
            st.session_state.page = "Interne"
            st.rerun()

# --- INTERNE ---
elif st.session_state.page == "Interne":
    col_nav, col_info = st.columns([1, 4])
    if col_nav.button("⬅ RETOUR"):
        st.session_state.page = "Accueil"
        st.rerun()
    
    col_info.subheader(f"📍 {st.session_state.tranche}")
    
    tabs = st.tabs(["📂 PLANS & BC", "🚚 LIVRAISONS", "🏗️ POINTAGE APPARTEMENTS", "👥 PAIE"])

    # --- 1. PLANS & BONS DE COMMANDE ---
    with tabs[0]:
        st.write("### 📤 Téléversement des Documents Sources")
        type_doc = st.radio("Type de document", ["Plan Technique", "Bon de Commande (BC)"], horizontal=True)
        doc = st.file_uploader(f"Choisir le {type_doc}", type=['pdf', 'jpg', 'png'])
        if doc:
            st.success(f"Document {doc.name} prêt à être archivé sur le Drive.")

    # --- 2. LIVRAISONS (BL) ---
    with tabs[1]:
        st.write("### 🚛 Réception Marchandise")
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans", "Colorado", "Menuisier"])
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Preuve de livraison**")
            # Utilisation de file_uploader pour éviter l'ouverture auto de la caméra
            bl_img = st.file_uploader("📸 Photo du BL (Appareil Arrière)", type=['jpg', 'png'])
        with c2:
            st.write("**Preuve Marchandise**")
            mat_img = st.file_uploader("📸 Photo des articles reçus", type=['jpg', 'png'])
        
        txt_bl = st.text_input("Numéro du BL saisi")
        if st.button("💾 Enregistrer la réception"):
            st.toast("Enregistrement en cours...")

    # --- 3. POINTAGE DÉTAILLÉ (PIÈCE PAR PIÈCE) ---
    with tabs[2]:
        st.write("### 🏘️ Suivi par Logement")
        
        # Sélection précise
        col_im, col_et, col_ap = st.columns(3)
        imm = col_im.selectbox("Immeuble", [f"Bâtiment {i+1}" for i in range(15)])
        etg = col_et.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "Terrasse"])
        apt = col_ap.text_input("Appartement N°")

        secteur = st.selectbox("Corps d'état", ["Électricité", "Plomberie", "Marbre", "Menuiserie"])

        if secteur == "Électricité":
            st.write("**Checklist Installation :**")
            # Liste détaillée au lieu d'un pourcentage
            c1, c2 = st.columns(2)
            c1.checkbox("Câblage tiré")
            c1.checkbox("Boîtiers encastrés")
            c2.checkbox("Appareillage (Prises/Inter) posé")
            c2.checkbox("Tableau raccordé")
            st.file_uploader("📸 Photo de vérification", type=['jpg'])
            
        elif secteur == "Marbre":
            piece = st.multiselect("Pièces terminées", ["Salon", "Hall", "Chambres", "Cuisine", "Salles de bain"])
            st.selectbox("État du ponçage", ["Non commencé", "Grain Gros", "Finition Miroir"])
        
        if st.button(f"Valider Pointage {secteur} - Appt {apt}"):
            st.success(f"Pointage enregistré pour l'appartement {apt}")

    # --- 4. PAIE ---
    with tabs[3]:
        st.write("### 📑 Gestion Quinzaine")
        file_paie = st.file_uploader("Charger Excel de paie (PC)", type=['xlsx'])
        if file_paie:
            df_paie = pd.read_excel(file_paie)
            st.dataframe(df_paie, use_container_width=True)
