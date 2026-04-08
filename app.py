import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées Manesmane", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            creds_dict, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
        return None

# --- CHARGEMENT DU CATALOGUE (DYNAMIQUE) ---
@st.cache_data(ttl=300)
def load_config():
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        data = sh.worksheet("Catalogue").get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=['FRS', 'ELEC', 'PLOMB'])
            return {
                "fournisseurs": [x for x in df['FRS'] if x],
                "produits_elec": [x for x in df['ELEC'] if x],
                "produits_plomb": [x for x in df['PLOMB'] if x]
            }
    except: pass
    return {"fournisseurs": ["Standard"], "produits_elec": ["Standard"], "produits_plomb": ["Standard"]}

# --- SAUVEGARDE DANS LE SHEET ---
def save_to_sheet(onglet, ligne):
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        sh.worksheet(onglet).append_row(ligne)
        st.success(f"Enregistré dans l'onglet {onglet} ! ✅")
    except Exception as e:
        st.error(f"Erreur d'écriture : {e}")

# --- SUPPRESSION DERNIÈRE LIGNE ---
def delete_last(onglet):
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        ws = sh.worksheet(onglet)
        res = ws.get_all_values()
        if len(res) > 1:
            ws.delete_rows(len(res))
            st.warning(f"Dernière ligne de {onglet} supprimée 🗑️")
        else: st.info("Rien à supprimer.")
    except Exception as e: st.error(f"Erreur : {e}")

# --- GÉNÉRATEUR PDF ---
def export_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"SITUATION : {title.upper()}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=8)
    # En-têtes
    for col in df.columns: pdf.cell(38, 10, str(col), border=1)
    pdf.ln()
    # Données
    for _, row in df.iterrows():
        for val in row: pdf.cell(38, 8, str(val)[:20], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
cfg = load_config()
mode = st.sidebar.radio("MENU", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
date_now = datetime.date.today().strftime("%d/%m/%Y")

# ================= MODE SAISIE =================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📦 MARCHANDISES", "⚡ ÉLEC", "🚰 PLOMB", "💎 MARBRE", "🧱 CÉRAMIQUE"])

    with tabs[0]: # MARCHANDISES
        f = st.selectbox("Fournisseur", cfg["fournisseurs"])
        d = st.text_area("Désignation")
        if st.button("Valider Réception"):
            save_to_sheet("Marchandises", [date_now, tranche, f, d])

    with tabs[1]: # ELEC
        p = st.selectbox("Produit", cfg["produits_elec"])
        q = st.number_input("Qté", min_value=1, key="qe")
        l = st.text_input("Localisation", key="le")
        if st.button("Valider Élec"):
            save_to_sheet("Electricite", [date_now, tranche, p, q, l])

    with tabs[2]: # PLOMB
        p = st.selectbox("Produit", cfg["produits_plomb"])
        q = st.number_input("Qté", min_value=1, key="qp")
        l = st.text_input("Localisation", key="lp")
        if st.button("Valider Plomb"):
            save_to_sheet("Plomberie", [date_now, tranche, p, q, l])

    with tabs[3]: # MARBRE (Détails Blanc Carrara inclus)
        inter = st.selectbox("Intervenant", ["FETTAH", "Simo"])
        m_type = st.selectbox("Type Marbre", ["Gris Bold", "White Sand", "Blanc Carrara"])
        
        # Sous-détails Blanc Carrara
        det_bc, appt, surf = "", "", 0.0
        if m_type == "Blanc Carrara":
            det_bc = st.selectbox("Élément BC", ["Dallage", "Seuil", "Niche", "Les douches"])
            if det_bc == "Dallage":
                appt = st.text_input("N° Appartement")
                surf = st.number_input("Surface m²", min_value=0.0)

        imm = st.text_input("Immeuble")
        etage = st.selectbox("Étage", ["RDC", "1", "2", "3", "4", "5"])
        
        if st.button("Valider Marbre"):
            type_final = f"{m_type} - {det_bc}" if det_bc else m_type
            lieu = f"Imm {imm} - Etage {etage} {' - Appt '+appt if appt else ''}"
            save_to_sheet("Marbre", [date_now, tranche, inter, type_final, lieu, surf])

    with tabs[4]: # CERAMIQUE
        z = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Salon"])
        loc = st.text_input("Détails")
        if st.button("Valider Céram"):
            save_to_sheet("Ceramique", [date_now, tranche, z, loc])

# ================= MODE CONSULTATION =================
elif mode == "🔍 CONSULTATION":
    onglet = st.selectbox("Onglet à consulter", ["Marchandises", "Electricite", "Plomberie", "Marbre", "Ceramique"])
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        data = sh.worksheet(onglet).get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df_view = df[df["Tranche"] == tranche]
            st.table(df_view.tail(15)) # Affiche les 15 derniers pour la vitesse
            
            if not df_view.empty:
                pdf_bytes = export_pdf(df_view, onglet)
                st.download_button(f"📥 Rapport {onglet} (PDF)", pdf_bytes, f"{onglet}.pdf")
            
            if st.button("🗑️ Supprimer la dernière ligne"):
                delete_last(onglet)
                st.rerun()
        else: st.info("Vide.")
    except: st.error("Impossible de lire les données.")

# ================= MODE CATALOGUE =================
elif mode == "⚙️ CATALOGUE":
    st.header("⚙️ Configuration du Catalogue")
    col_choice = st.radio("Ajouter dans :", ["Fournisseur", "Électricité", "Plomberie"])
    new_val = st.text_input("Nom du nouvel élément")
    if st.button("➕ Ajouter"):
        # Définit dans quelle colonne on écrit selon le choix
        row = [new_val, "", ""] if col_choice == "Fournisseur" else (["", new_val, ""] if col_choice == "Électricité" else ["", "", new_val])
        save_to_sheet("Catalogue", row)
        st.cache_data.clear()
