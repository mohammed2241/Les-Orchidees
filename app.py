import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Portail Manesmane", layout="wide")

# Listes de secours (si le catalogue Sheets est vide)
DEF_FRS = ["INTERCABLE", "SOFA", "PROMELEC", "MG LIGHTING", "SARABO", "NOVACIM", "SAFI BAINS", "SUPER CERAME", "Autre"]
DEF_ELEC = ["SPOT", "DISJ", "LED", "SUPPORT 3 MOD", "PRISE 2P+T", "INTERR V&V", "Video phonique"]
DEF_PLOMB = ["TOILETTE", "VASQUE 60", "MIT DCH", "CHAUFFE EAU", "EVIER"]

# --- CONNEXION ---
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

# --- CHARGEMENT DYNAMIQUE ---
@st.cache_data(ttl=300)
def load_lists():
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        data = sh.worksheet("Catalogue").get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=['FRS', 'ELEC', 'PLOMB'])
            return {
                "frs": [x for x in df['FRS'] if x] or DEF_FRS,
                "elec": [x for x in df['ELEC'] if x] or DEF_ELEC,
                "plomb": [x for x in df['PLOMB'] if x] or DEF_PLOMB
            }
    except: pass
    return {"frs": DEF_FRS, "elec": DEF_ELEC, "plomb": DEF_PLOMB}

# --- ACTIONS ---
def save_row(onglet, ligne):
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        sh.worksheet(onglet).append_row(ligne)
        st.success(f"Enregistré dans {onglet} ✅")
    except Exception as e: st.error(f"Erreur : {e}")

def delete_last(onglet):
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        ws = sh.worksheet(onglet)
        rows = ws.get_all_values()
        if len(rows) > 1:
            ws.delete_rows(len(rows))
            st.warning("Dernière ligne supprimée 🗑️")
        else: st.info("Rien à supprimer")
    except Exception as e: st.error(f"Erreur : {e}")

# --- RAPPORT PDF ---
def export_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"RAPPORT {title.upper()}", ln=True, align='C')
    pdf.set_font("Arial", size=9)
    pdf.ln(5)
    for col in df.columns: pdf.cell(38, 10, str(col), border=1)
    pdf.ln()
    for _, row in df.iterrows():
        for val in row: pdf.cell(38, 8, str(val)[:20], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("🏗️ LES ORCHIDÉES - GESTION TECHNIQUE")
lists = load_lists()
mode = st.sidebar.radio("MENU", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

if mode == "📝 SAISIE":
    tabs = st.tabs(["📦 March.", "⚡ Elec", "🚰 Plomb", "💎 Marbre", "🧱 Céram"])
    date_now = datetime.date.today().strftime("%d/%m/%Y")

    with tabs[0]: # MARCHANDISES
        f = st.selectbox("Fournisseur", lists["frs"])
        d = st.text_area("Désignation")
        c1, c2 = st.columns(2)
        if c1.button("Valider March."): save_row("Marchandises", [date_now, tranche, f, d])
        if c2.button("Annuler March."): delete_last("Marchandises")

    with tabs[1]: # ELEC
        p = st.selectbox("Produit", lists["elec"])
        q = st.number_input("Qté", min_value=1, key="qe")
        l = st.text_input("Localisation (Imm/Appt)", key="le")
        c1, c2 = st.columns(2)
        if c1.button("Valider Élec"): save_row("Electricite", [date_now, tranche, p, q, l])
        if c2.button("Annuler Élec"): delete_last("Electricite")

    with tabs[2]: # PLOMB
        p = st.selectbox("Produit", lists["plomb"])
        q = st.number_input("Qté", min_value=1, key="qp")
        l = st.text_input("Localisation", key="lp")
        c1, c2 = st.columns(2)
        if c1.button("Valider Plomb"): save_row("Plomberie", [date_now, tranche, p, q, l])
        if c2.button("Annuler Plomb"): delete_last("Plomberie")

    with tabs[3]: # MARBRE
        inter = st.selectbox("Marbrier", ["FETTAH", "Simo"])
        m_type = st.selectbox("Marbre", ["Gris Bold", "White Sand", "Blanc Carrara"])
        
        # --- DÉTAIL BLANC CARRARA ---
        det_bc = ""
        if m_type == "Blanc Carrara":
            det_bc = st.selectbox("Élément BC", ["Dallage", "Seuil", "Niche", "Les douches"])
        
        imm = st.text_input("Immeuble / Étage")
        appt = st.text_input("N° Appt")
        surf = st.number_input("Surface m²", min_value=0.0)
        
        c1, c2 = st.columns(2)
        if c1.button("Valider Marbre"):
            final_type = f"{m_type} - {det_bc}" if det_bc else m_type
            lieu = f"{imm} / Appt {appt}"
            save_row("Marbre", [date_now, tranche, inter, final_type, lieu, surf])
        if c2.button("Annuler Marbre"): delete_last("Marbre")

    with tabs[4]: # CERAMIQUE
        z = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Salon"])
        loc = st.text_input("Détails Imm/Etage", key="lc")
        c1, c2 = st.columns(2)
        if c1.button("Valider Céram"): save_row("Ceramique", [date_now, tranche, z, loc])
        if c2.button("Annuler Céram"): delete_last("Ceramique")

elif mode == "🔍 CONSULTATION":
    onglet = st.selectbox("Choisir l'onglet", ["Marchandises", "Electricite", "Plomberie", "Marbre", "Ceramique"])
    try:
        client = get_gsheet_client()
        sh = client.open("BDD_Chantier_Manesmane")
        data = sh.worksheet(onglet).get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df_view = df[df["Tranche"] == tranche]
            st.dataframe(df_view, use_container_width=True)
            if not df_view.empty:
                pdf_bytes = export_pdf(df_view, onglet)
                st.download_button("📥 Télécharger Rapport PDF", pdf_bytes, f"{onglet}_{tranche}.pdf")
        else: st.info("Vide")
    except: st.error("Erreur de lecture")

elif mode == "⚙️ CATALOGUE":
    st.subheader("Configuration du Catalogue")
    cat_type = st.radio("Ajouter à :", ["Fournisseur", "Électricité", "Plomberie"])
    new_val = st.text_input("Nom de l'élément")
    if st.button("➕ Ajouter au Catalogue"):
        row = [new_val, "", ""] if cat_type == "Fournisseur" else (["", new_val, ""] if cat_type == "Électricité" else ["", "", new_val])
        save_row("Catalogue", row)
        st.cache_data.clear()
