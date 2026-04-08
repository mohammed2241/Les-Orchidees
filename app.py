import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
from fpdf import FPDF
import io

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
            else:
                st.warning("L'onglet est déjà vide (hors entêtes).")
    except Exception as e:
        st.error(f"Erreur de suppression : {e}")
    return False

# --- GENERATION PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'RAPPORT TECHNIQUE - LES ORCHIDÉES', 0, 1, 'C')
        self.ln(5)

def create_pdf(df, title):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"Catégorie : {title}", 0, 1, 'L')
    pdf.set_font("Arial", size=8)
    
    # Largeur des colonnes
    col_width = 190 / len(df.columns)
    
    # Entêtes
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()
    
    # Données
    for i in range(len(df)):
        for col in df.columns:
            pdf.cell(col_width, 10, str(df.iloc[i][col]), border=1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.set_page_config(page_title="Portail Manesmane", layout="wide")

DEFAUT_FRS = ["INTERCABLE", "SOFA", "PROMELEC", "MG LIGHTING", "KADIR DISTRIBUTION", "SARABO", "SOQOP", "FROIDEL", "NOVACIM", "RE SERVICE", "ATLAS MULTIMATERIEL", "SBBC", "LAFARGE", "SAFI BAINS", "INNOVA WOOD", "SINASTONE", "MEDIAL", "EXPLOMAR", "RIVA", "INTERSIG", "AQUAPLANET", "BEKO MAGHREB", "ISOLBOX", "PLATINOVA", "TAMAGROT", "AOC", "SOCODAM DAVUM", "HYDRAU MAC", "TRACTRAFFIC", "GOOD YEAR BAB DOKALA", "MULTICERAME", "MALL ZALLIJ", "SUPER CERAME", "PETROMIN OILS", "ALSINA", "PERI"]

st.title("🏗️ PORTAIL TECHNIQUE - LES ORCHIDÉES")

menu = st.sidebar.radio("NAVIGATION", ["📝 SAISIE TERRAIN", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("CHOIX DE LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

# ==========================================
#                MODE SAISIE
# ==========================================
if menu == "📝 SAISIE TERRAIN":
    st.header(f"Nouvelle Saisie - {tranche}")
    tabs = st.tabs(["📦 Marchandises", "⚡ Électricité", "🚰 Plomberie", "💎 Marbre", "🧱 Céramique"])

    sections = [
        ("Marchandises", tabs[0], ["Fournisseur", "Désignation"]),
        ("Electricite", tabs[1], ["Produit", "Quantité", "Lieu"]),
        ("Plomberie", tabs[2], ["Produit", "Quantité", "Lieu"]),
        ("Marbre", tabs[3], ["Intervenant", "Type", "Lieu", "Surface"]),
        ("Ceramique", tabs[4], ["Zone", "Lieu"])
    ]

    for name, tab, labels in sections:
        with tab:
            with st.form(key=f"form_{name}"):
                if name == "Marchandises":
                    f = st.selectbox("Fournisseur", DEFAUT_FRS)
                    d = st.text_area("Désignation")
                    row = [datetime.datetime.now().strftime("%d/%m/%Y"), tranche, f, d]
                elif name == "Marbre":
                    i = st.selectbox("Intervenant", ["FETTAH", "Simo"])
                    t = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
                    l = st.text_input("Immeuble/Étage")
                    s = st.number_input("Surface (m²)", min_value=0.0)
                    row = [datetime.datetime.now().strftime("%d/%m/%Y"), tranche, i, t, l, s]
                else:
                    c1, c2 = st.columns(2)
                    v1 = c1.text_input(labels[0])
                    v2 = c2.number_input(labels[1], min_value=1) if "Quantité" in labels[1] else c2.text_input(labels[1])
                    v3 = st.text_input(labels[2]) if len(labels)>2 else ""
                    row = [datetime.datetime.now().strftime("%d/%m/%Y"), tranche, v1, v2, v3] if len(labels)>2 else [datetime.datetime.now().strftime("%d/%m/%Y"), tranche, v1, v2]

                col_btn1, col_btn2 = st.columns([1, 4])
                if col_btn1.form_submit_button("✅ Valider"):
                    if add_to_sheet(name, row): st.success(f"Enregistré dans {name}")
                
                if col_btn2.form_submit_button("🗑️ Supprimer dernière ligne"):
                    if delete_last_row(name): st.warning(f"Dernière ligne de {name} supprimée")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"Consultation & Rapports - {tranche}")
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
                    df_filtered = df[df["Tranche"] == tranche]
                    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
                    
                    if not df_filtered.empty:
                        pdf_data = create_pdf(df_filtered, onglets[i])
                        st.download_button(label="📥 Télécharger Rapport PDF", data=pdf_data, file_name=f"Rapport_{onglets[i]}_{tranche}.pdf", mime="application/pdf")
                else:
                    st.info("Aucune donnée.")
    except Exception as e:
        st.error(f"Erreur : {e}")
