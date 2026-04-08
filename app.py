import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
from fpdf import FPDF
import io

# --- CONFIGURATION GOOGLE SHEETS ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "BDD_Chantier_Manesmane"

def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
        return None

# --- FONCTIONS DE LECTURE/ÉCRITURE ---
def add_to_sheet(worksheet_name, row_data):
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open(SHEET_NAME)
            sheet = sh.worksheet(worksheet_name)
            sheet.append_row(row_data)
            return True
    except Exception as e:
        st.error(f"Erreur d'écriture : {e}")
        return False

def get_all_data(worksheet_name):
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open(SHEET_NAME)
            sheet = sh.worksheet(worksheet_name)
            return sheet.get_all_values()
    except:
        return []
    return []

# --- GESTION DU CATALOGUE (DYNAMIQUE) ---
def get_catalogue(column_index):
    """Récupère les listes depuis l'onglet 'Catalogue' (Col 1: FRS, Col 2: ELEC, Col 3: PLOMB)"""
    data = get_all_data("Catalogue")
    if len(data) > 1:
        # On ignore l'entête et on filtre les cases vides
        return [row[column_index] for row in data[1:] if len(row) > column_index and row[column_index]]
    return []

# --- GÉNÉRATION PDF ---
def create_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"RAPPORT : {title.upper()}", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", size=9)
    col_width = 190 / len(df.columns)
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()
    for i in range(len(df)):
        for col in df.columns:
            pdf.cell(col_width, 8, str(df.iloc[i][col])[:30], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.set_page_config(page_title="Suivi Manesmane", layout="wide")
st.title("🏗️ LES ORCHIDÉES MANESMANE")

mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

# Chargement des listes depuis Google Sheets (Catalogue)
list_frs = get_catalogue(0) or ["Chargement..."]
list_elec = get_catalogue(1) or ["Chargement..."]
list_plomb = get_catalogue(2) or ["Chargement..."]

# ==========================================
#                MODE CATALOGUE
# ==========================================
if mode == "⚙️ CATALOGUE":
    st.header("⚙️ Gestion du Catalogue")
    st.info("Ajoutez des éléments ici. Ils seront enregistrés dans l'onglet 'Catalogue' de votre Google Sheets.")
    
    cat_col = st.columns(3)
    
    with cat_col[0]:
        new_f = st.text_input("Nouveau Fournisseur")
        if st.button("➕ Ajouter FRS") and new_f:
            if add_to_sheet("Catalogue", [new_f, "", ""]): st.success("Ajouté")

    with cat_col[1]:
        new_e = st.text_input("Nouveau Produit Élec")
        if st.button("➕ Ajouter Élec") and new_e:
            if add_to_sheet("Catalogue", ["", new_e, ""]): st.success("Ajouté")

    with cat_col[2]:
        new_p = st.text_input("Nouveau Produit Plomb")
        if st.button("➕ Ajouter Plomb") and new_p:
            if add_to_sheet("Catalogue", ["", "", new_p]): st.success("Ajouté")

# ==========================================
#                MODE SAISIE
# ==========================================
elif mode == "📝 SAISIE":
    st.header(f"Saisie de Terrain - {tranche}")
    tabs = st.tabs(["📦 MARCHANDISES", "⚡ ÉLECTRICITÉ", "🚰 PLOMBERIE", "💎 MARBRE", "🧱 CÉRAMIQUE"])

    with tabs[0]: # MARCHANDISES
        f = st.selectbox("Fournisseur", list_frs)
        d = st.text_area("Désignation complète")
        if st.button("Valider Réception"):
            row = [datetime.date.today().strftime("%d/%m/%Y"), tranche, f, d]
            if add_to_sheet("Marchandises", row): st.success("Enregistré ✅")

    with tabs[1]: # ELEC
        p = st.selectbox("Produit Élec", list_elec)
        q = st.number_input("Quantité", min_value=1, key="q_e")
        l = st.text_input("Lieu (Imm / Appt)", key="l_e")
        if st.button("Valider Pose Élec"):
            if add_to_sheet("Electricite", [datetime.date.today().strftime("%d/%m/%Y"), tranche, p, q, l]): st.success("Enregistré ✅")

    with tabs[2]: # PLOMB
        p = st.selectbox("Produit Plomb", list_plomb)
        q = st.number_input("Quantité", min_value=1, key="q_p")
        l = st.text_input("Lieu (Imm / Appt / SDB)", key="l_p")
        if st.button("Valider Pose Plomb"):
            if add_to_sheet("Plomberie", [datetime.date.today().strftime("%d/%m/%Y"), tranche, p, q, l]): st.success("Enregistré ✅")

    with tabs[3]: # MARBRE
        interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
        type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
        imm = st.text_input("Immeuble")
        etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "5ème"])
        appt = st.text_input("N° Appartement (Optionnel)")
        surf = st.number_input("Surface (m²)", min_value=0.0)
        
        if st.button("Enregistrer Marbre"):
            lieu = f"Imm {imm} - {etage}" + (f" - Appt {appt}" if appt else "")
            if add_to_sheet("Marbre", [datetime.date.today().strftime("%d/%m/%Y"), tranche, interv, type_m, lieu, surf]):
                st.success("Enregistré ✅")

    with tabs[4]: # CERAMIQUE
        z = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Salon"])
        l = st.text_input("Immeuble / Étage", key="l_c")
        if st.button("Enregistrer Céramique"):
            if add_to_sheet("Ceramique", [datetime.date.today().strftime("%d/%m/%Y"), tranche, z, l]): st.success("Enregistré ✅")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"Consultation - {tranche}")
    c_tabs = st.tabs(["📦 Marchandises", "⚡ Élec", "🚰 Plomb", "💎 Marbre", "🧱 Céram"])
    onglets = ["Marchandises", "Electricite", "Plomberie", "Marbre", "Ceramique"]
    cols = [
        ["Date", "Tranche", "Fournisseur", "Désignation"],
        ["Date", "Tranche", "Produit", "Qté", "Lieu"],
        ["Date", "Tranche", "Produit", "Qté", "Lieu"],
        ["Date", "Tranche", "Nom", "Type", "Lieu", "Surface"],
        ["Date", "Tranche", "Zone", "Lieu"]
    ]

    for i, tab in enumerate(c_tabs):
        with tab:
            raw_data = get_all_data(onglets[i])
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=cols[i])
                df_f = df[df["Tranche"] == tranche]
                st.dataframe(df_f, use_container_width=True, hide_index=True)
                
                if not df_f.empty:
                    pdf = create_pdf(df_f, onglets[i])
                    st.download_button(f"📥 Télécharger PDF {onglets[i]}", data=pdf, file_name=f"{onglets[i]}_{tranche}.pdf")
            else:
                st.info("Aucune donnée enregistrée.")
