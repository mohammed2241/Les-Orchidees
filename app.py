import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION DES LISTES (Pour que l'upload s'affiche) ---
if 'mes_plans' not in st.session_state:
    st.session_state.mes_plans = []

# --- NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Accueil"

# --- PAGE ACCUEIL ---
if st.session_state.page == "Accueil":
    st.title("🏗️ LES ORCHIDÉES")
    for t in ["Tranche 3", "Tranche 4", "Tranche 5"]:
        if st.button(f"ACCÉDER : {t}", use_container_width=True):
            st.session_state.tranche = t
            st.session_state.page = "Interne"
            st.rerun()

# --- PAGE INTERNE ---
elif st.session_state.page == "Interne":
    if st.button("⬅ RETOUR"):
        st.session_state.page = "Accueil"
        st.rerun()
    
    st.header(f"📍 {st.session_state.tranche}")
    tabs = st.tabs(["📄 PLANS PDF", "🚚 MARCHANDISES", "🏗️ FINITIONS", "👥 SALARIÉS"])

    # --- 1. PLANS PDF (Correction de l'enregistrement) ---
    with tabs[0]:
        st.subheader("📁 Ma Bibliothèque de Plans")
        fichier = st.file_uploader("Transmettre un plan PDF du projet", type=['pdf'])
        
        if fichier:
            # On ajoute le fichier à la liste si il n'y est pas déjà
            if fichier.name not in st.session_state.mes_plans:
                st.session_state.mes_plans.append(fichier.name)
                st.success(f"Plan '{fichier.name}' enregistré avec succès !")

        st.write("---")
        st.write("**Plans consultables :**")
        if st.session_state.mes_plans:
            for p in st.session_state.mes_plans:
                col_a, col_b = st.columns([3, 1])
                col_a.info(f"📄 {p}")
                if col_b.button("Ouvrir", key=p):
                    st.write(f"Ouverture de {p} en cours...")
        else:
            st.warning("Aucun plan n'a été téléversé pour le moment.")

    # --- 2. MARCHANDISES (Correction Caméra) ---
    with tabs[1]:
        st.subheader("🚛 Réception & BL")
        fournisseur = st.selectbox("Choisir le Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        
        st.write("**⚠️ Cliquez ci-dessous pour choisir 'Appareil Photo' :**")
        col1, col2 = st.columns(2)
        # file_uploader ne lance pas la caméra tout seul
        bl = col1.file_uploader("Photo du Bon de Livraison (BL)", type=['jpg', 'png'], key="bl_up")
        mat = col2.file_uploader("Photo de la Marchandise", type=['jpg', 'png'], key="mat_up")
        
        num_bl = st.text_input("Saisir le N° de BL")
        if st.button("Valider la réception"):
            st.success("Données envoyées vers le Drive !")

    # --- 3. FINITIONS (Détail par Appartement) ---
    with tabs[2]:
        st.subheader("🏘️ Suivi par Logement")
        c1, c2, c3 = st.columns(3)
        imm = c1.selectbox("Immeuble", [f"Bâtiment {i+1}" for i in range(15)])
        etg = c2.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
        apt = c3.text_input("N° Appartement")

        secteur = st.radio("Secteur", ["Électricité", "Marbre", "Menuiserie"], horizontal=True)

        if secteur == "Électricité":
            st.write("**État de pose :**")
            col_a, col_b = st.columns(2)
            col_a.checkbox("Câblage terminé")
            col_a.checkbox("Boîtiers posés")
            col_b.checkbox("Appareillage raccordé")
            col_b.checkbox("Tableau testé")
        elif secteur == "Marbre":
            st.multiselect("Zones terminées", ["Salon", "Hall", "Cuisine", "SDB"])

        st.file_uploader("Prendre une photo de l'appart", type=['jpg'])
        if st.button("Enregistrer Pointage"):
            st.balloons()
