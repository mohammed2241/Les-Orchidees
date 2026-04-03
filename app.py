import streamlit as st
import pandas as pd
import base64
import os
import pickle
import io
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- SYSTÈME DE SAUVEGARDE ---
DB_FILE = "data_chantier.pkl"

def charger_donnees():
    structure_vide = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                data = pickle.load(f)
                for t in structure_vide:
                    if t not in data: data[t] = structure_vide[t]
                    for key in structure_vide[t]:
                        if key not in data[t]: data[t][key] = []
                return data
        except: return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# --- GÉNÉRATEUR PDF UNIVERSEL ---
class PDF_Rapport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'RAPPORT DE SITUATION GLOBAL - LES ORCHIDÉES', 0, 1, 'C')
        self.ln(5)

    def tableau_header(self, colonnes):
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(200, 220, 255)
        largeurs = [20, 35, 25, 20, 20, 20, 50]
        for i, col in enumerate(colonnes):
            self.cell(largeurs[i], 8, col, 1, 0, 'C', True)
        self.ln()

def generer_pdf_complet(tranche_nom, data_tranche):
    pdf = PDF_Rapport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- SECTION MARBRE ---
    if data_tranche['marbre']:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "SECTION : MARBRE", ln=True)
        df_m = pd.DataFrame(data_tranche['marbre'])
        for inter, group in df_m.groupby('Nom'):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"Intervenant : {inter}", ln=True)
            pdf.tableau_header(['DATE', 'TYPE', 'REF', 'IMM', 'ETAGE', 'APPT', 'DETAILS'])
            pdf.set_font('Arial', '', 8)
            for _, r in group.iterrows():
                lieu = str(r.get('Lieu', ''))
                pdf.cell(20, 7, str(r.get('Date', '-')), 1)
                pdf.cell(35, 7, str(r.get('Type', '-')), 1)
                pdf.cell(25, 7, str(r.get('Référence', '-')) if r.get('Référence') else '-', 1)
                pdf.cell(20, 7, lieu.split('Imm ')[1].split(' -')[0] if 'Imm ' in lieu else '-', 1)
                pdf.cell(20, 7, 'Oui' if any(x in lieu for x in ['RDC','1er','2','3','4']) else '-', 1)
                pdf.cell(20, 7, lieu.split('Appt ')[1] if 'Appt ' in lieu else '-', 1)
                pdf.cell(50, 7, lieu[:30], 1, 1)
            pdf.ln(5)

    # --- SECTION CÉRAMIQUE ---
    if data_tranche['ceram']:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "SECTION : CÉRAMIQUE", ln=True)
        df_c = pd.DataFrame(data_tranche['ceram'])
        pdf.tableau_header(['DATE', 'ZONE', '-', 'IMM', 'ETAGE', '-', 'DETAILS'])
        pdf.set_font('Arial', '', 8)
        for _, r in df_c.iterrows():
            lieu = str(r.get('Lieu', ''))
            pdf.cell(20, 7, str(r.get('Date', '-')), 1)
            pdf.cell(35, 7, str(r.get('Type', '-')), 1)
            pdf.cell(25, 7, '-', 1)
            pdf.cell(20, 7, lieu.split('Imm ')[1].split(' -')[0] if 'Imm ' in lieu else '-', 1)
            pdf.cell(20, 7, lieu.split('Etage ')[1] if 'Etage ' in lieu else '-', 1)
            pdf.cell(20, 7, '-', 1)
            pdf.cell(50, 7, lieu[:30], 1, 1)
        pdf.ln(5)

    # --- SECTION MARCHANDISES ---
    if data_tranche['marchandises']:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "SECTION : RÉCEPTION MARCHANDISES", ln=True)
        df_ma = pd.DataFrame(data_tranche['marchandises'])
        for fourn, group in df_ma.groupby('Fournisseur'):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"Fournisseur : {fourn}", ln=True)
            pdf.set_font('Arial', 'B', 8)
            pdf.cell(30, 8, 'DATE', 1)
            pdf.cell(100, 8, 'DÉSIGNATION', 1, 1)
            pdf.set_font('Arial', '', 8)
            for _, r in group.iterrows():
                pdf.cell(30, 7, str(r.get('Date', '-')), 1)
                pdf.cell(100, 7, str(r.get('Désignation', '-')), 1, 1)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE STREAMLIT ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with tabs[1]: # Marchandises
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", type=['jpg','png'], key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", type=['jpg','png'], key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M"), "photo_bl": p_bl.getvalue() if p_bl else None, "photo_cam": p_cam.getvalue() if p_cam else None})
            sauvegarder_donnees()
            st.success("Réception enregistrée")

    with tabs[2]: # Suivi
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_inter")
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"], key="m_type")
            fourn, ref_v = None, None
            if type_m == "Blanc Carrara":
                fourn = st.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"], key="m_f")
                ref_v = st.text_input("Référence", key="m_ref")
            imm = st.text_input("Immeuble", key="m_imm")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"], key="m_et") if type_m != "White Sand" else None
            appt = st.text_input("Appartement", key="m_ap") if type_m == "Blanc Carrara" else None
            if st.button("Valider Marbre"):
                lieu = f"Imm {imm}"
                if etage: lieu += f" - {etage}"
                if appt: lieu += f" - Appt {appt}"
                if type_m == "White Sand": lieu += " (Facade)"
                data['marbre'].append({"Nom": interv, "Type": type_m, "Fournisseur": fourn, "Référence": ref_v, "Lieu": lieu, "Date": pd.Timestamp.now().strftime("%d/%m")})
                sauvegarder_donnees()
                st.success("Enregistré")

        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            im_c = st.text_input("Immeuble")
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            if st.button("Valider Céramique"):
                data['ceram'].append({"Type": z, "Lieu": f"Imm {im_c} - Etage {et}", "Date": pd.Timestamp.now().strftime("%d/%m")})
                sauvegarder_donnees()
                st.success("Céramique OK")

        elif spec in ["Électricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for i in items:
                col1, col2 = st.columns([2, 1])
                q = col2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = col1.text_input(f"Détails {i}", key=f"d_{i}")
                if st.button(f"Valider {i}", key=f"btn_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit": i, "Qté": q, "Détail": dt, "Date": pd.Timestamp.now().strftime("%d/%m")})
                    sauvegarder_donnees()
                    st.toast("Validé !")

else: # CONSULTATION
    st.header(f"🔍 Consultation - {tranche}")
    if st.button("📊 GÉNÉRER LE RAPPORT GLOBAL (PDF)"):
        pdf_bytes = generer_pdf_complet(tranche, data)
        st.download_button("📥 TÉLÉCHARGER LE RAPPORT COMPLET", data=pdf_bytes, file_name=f"Rapport_Chantier_{tranche}.pdf", mime="application/pdf")
    
    st.divider()
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    # ... (Affichage des données identique aux versions précédentes) ...
