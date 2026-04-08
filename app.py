import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
from fpdf import FPDF

# --- CONFIGURATION GOOGLE SHEETS ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

def add_to_sheet(sheet_name, row_data):
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open("BDD_Chantier_Manesmane")
            sheet = sh.worksheet(sheet_name)
            sheet.append_row(row_data)
            return True
    except Exception as e:
        st.error(f"Erreur d'écriture : {e}")
        return False

def delete_last_row(sheet_name):
    try:
        client = get_gsheet_client()
        if client:
            sh = client.open("BDD_Chantier_Manesmane")
            sheet = sh.worksheet(sheet_name)
            rows = sheet.get_all_values()
            if len(rows) > 1:
                sheet.delete_rows(len(rows))
                return True
    except Exception as e:
        st.error(f"Erreur : {e}")
    return False

# --- GÉNÉRATION PDF ---
def create_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"RAPPORT : {title.upper()}", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    
    col_width = 190 / len(df.columns)
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()
    for i in range(len(df)):
        for col in df.columns:
            pdf.cell(col_width, 10, str(df.iloc[i][col]), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- DONNÉES TECHNIQUES (DÉTAILS MÉTIERS) ---
DEFAUT_FRS = ["INTERCABLE", "SOFA", "PROMELEC", "MG LIGHTING", "KADIR DISTRIBUTION", "SARABO", "SOQOP", "FROIDEL", "NOVACIM", "RE SERVICE", "ATLAS MULTIMATERIEL", "SBBC", "LAFARGE", "SAFI BAINS", "INNOVA WOOD", "SINASTONE", "MEDIAL", "EXPLOMAR", "RIVA", "INTERSIG", "AQUAPLANET", "BEKO MAGHREB", "ISOLBOX", "PLATINOVA", "TAMAGROT", "AOC", "SOCODAM DAVUM", "HYDRAU MAC", "TRACTRAFFIC", "GOOD YEAR BAB DOKALA", "MULTICERAME", "MALL ZALLIJ", "SUPER CERAME", "PETROMIN OILS", "ALSINA", "PERI", "Autre"]

LISTE_ELEC = ["SPOT", "SPOT DOUBLE", "BLOC DE SECOURS", "DISJ", "APPLIQUE", "LED", "SUPPORT SURMOULE", "SUPPORT 3 MODULES", "SUPPORT 4 MODULES", "SUPPORT 6 MODULES", "PRISE 2P+T IP44", "Obturateur", "PRISE 2P+T 45", "Prise TV SAT", "Interr SVV", "Interr V&V", "Pousse à basc", "Inver volets roul", "Video phonique"]

LISTE_PLOMB = ["TOILETTE", "VASQUE 60 CM", "VASQUE 80 CM", "BIDETS", "DOUCHETTE", "POMPE DE DOUCHE", "MIT DCH", "MIT LVB", "MIT BIDET", "CHAUFFE EAU", "EVIER", "MIT EVIER"]

# --- INTERFACE ---
st.set_page_config(page_title="Suivi Manesmane", layout="wide")
st.title("🏗️ SUIVI TECHNIQUE - LES ORCHIDÉES")

menu = st.sidebar.radio("NAVIGATION", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

if menu == "📝 SAISIE":
    tabs = st.tabs(["📦 Marchandises", "⚡ Électricité", "🚰 Plomberie", "💎 Marbre", "🧱 Céramique"])

    with tabs[0]: # MARCHANDISES
        with st.form("form_march"):
            f = st.selectbox("Fournisseur", DEFAUT_FRS)
            d = st.text_area("Désignation du matériel")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Enregistrer"):
                if add_to_sheet("Marchandises", [datetime.date.today().strftime("%d/%m/%Y"), tranche, f, d]):
                    st.success("Enregistré !")
            if c2.form_submit_button("🗑️ Annuler dernier"):
                if delete_last_row("Marchandises"): st.warning("Supprimé")

    with tabs[1]: # ÉLECTRICITÉ
        with st.form("form_elec"):
            p = st.selectbox("Produit", LISTE_ELEC)
            q = st.number_input("Quantité", min_value=1)
            loc = st.text_input("Immeuble / Appt")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Valider Pose"):
                if add_to_sheet("Electricite", [datetime.date.today().strftime("%d/%m/%Y"), tranche, p, q, loc]):
                    st.success("Enregistré !")
            if c2.form_submit_button("🗑️ Annuler"):
                if delete_last_row("Electricite"): st.warning("Supprimé")

    with tabs[2]: # PLOMBERIE
        with st.form("form_plomb"):
            p = st.selectbox("Produit", LISTE_PLOMB)
            q = st.number_input("Quantité", min_value=1)
            loc = st.text_input("Immeuble / Appt / SDB")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Valider Pose"):
                if add_to_sheet("Plomberie", [datetime.date.today().strftime("%d/%m/%Y"), tranche, p, q, loc]):
                    st.success("Enregistré !")
            if c2.form_submit_button("🗑️ Annuler"):
                if delete_last_row("Plomberie"): st.warning("Supprimé")

    with tabs[3]: # MARBRE
        with st.form("form_marbre"):
            interv = st.selectbox("Marbrier", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            loc = st.text_input("Immeuble / Étage")
            surf = st.number_input("Surface (m²)", min_value=0.0)
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Valider Marbre"):
                if add_to_sheet("Marbre", [datetime.date.today().strftime("%d/%m/%Y"), tranche, interv, type_m, loc, surf]):
                    st.success("Enregistré !")
            if c2.form_submit_button("🗑️ Annuler"):
                if delete_last_row("Marbre"): st.warning("Supprimé")

    with tabs[4]: # CÉRAMIQUE
        with st.form("form_ceram"):
            zone = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Salon"])
            loc = st.text_input("Immeuble / Étage")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Valider Céram"):
                if add_to_sheet("Ceramique", [datetime.date.today().strftime("%d/%m/%Y"), tranche, zone, loc]):
                    st.success("Enregistré !")
            if c2.form_submit_button("🗑️ Annuler"):
                if delete_last_row("Ceramique"): st.warning("Supprimé")

else: # CONSULTATION
    st.header(f"Suivi {tranche}")
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        c_tabs = st.tabs(["📦 Marchandises", "⚡ Élec", "🚰 Plomb", "💎 Marbre", "🧱 Céram"])
        onglets = ["Marchandises", "Electricite", "Plomberie", "Marbre", "Ceramique"]
        cols = [["Date", "Tranche", "Fournisseur", "Désignation"], ["Date", "Tranche", "Produit", "Qté", "Lieu"], ["Date", "Tranche", "Produit", "Qté", "Lieu"], ["Date", "Tranche", "Nom", "Type", "Lieu", "Surface"], ["Date", "Tranche", "Zone", "Lieu"]]

        for i, tab in enumerate(c_tabs):
            with tab:
                data = sh.worksheet(onglets[i]).get_all_values()
                if len(data) > 1:
                    df = pd.DataFrame(data[1:], columns=cols[i])
                    df_f = df[df["Tranche"] == tranche]
                    st.dataframe(df_f, use_container_width=True, hide_index=True)
                    if not df_f.empty:
                        pdf = create_pdf(df_f, onglets[i])
                        st.download_button(f"📥 PDF {onglets[i]}", data=pdf, file_name=f"{onglets[i]}.pdf")
    except Exception as e:
        st.error(f"Erreur : {e}")
