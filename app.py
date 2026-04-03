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

# --- GÉNÉRATEUR PDF INTELLIGENT ---
class PDF_Rapport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'RAPPORT DE SITUATION MARBRE - LES ORCHIDÉES', 0, 1, 'C')
        self.ln(5)

    def tableau_header(self):
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(200, 220, 255)
        # Colonnes: Date(20) | Type(30) | Réf(25) | Imm(20) | Etage(20) | Appt(20) | Détails(55)
        self.cell(20, 8, 'DATE', 1, 0, 'C', True)
        self.cell(30, 8, 'TYPE', 1, 0, 'C', True)
        self.cell(25, 8, 'REF', 1, 0, 'C', True)
        self.cell(20, 8, 'IMM', 1, 0, 'C', True)
        self.cell(20, 8, 'ETAGE', 1, 0, 'C', True)
        self.cell(20, 8, 'APPT', 1, 0, 'C', True)
        self.cell(55, 8, 'DETAILS / FACADE', 1, 1, 'C', True)

def generer_pdf_intelligent(tranche_nom, data_tranche):
    pdf = PDF_Rapport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    if not data_tranche['marbre']:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "Aucune donnée marbre pour cette tranche.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    df = pd.DataFrame(data_tranche['marbre'])
    
    # 1. Grouper par Intervenant (FETTAH, SIMO, etc.)
    for intervenant, group_inter in df.groupby('Nom'):
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 51, 102) # Bleu foncé pour l'intervenant
        pdf.cell(0, 12, f"INTERVENANT : {intervenant}", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # 2. Sous-grouper par Type de Marbre
        for type_marbre, group_type in group_inter.groupby('Type'):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, f">> Catégorie : {type_marbre}", ln=True)
            
            pdf.tableau_header()
            pdf.set_font('Arial', '', 8)
            
            for _, row in group_type.iterrows():
                # Nettoyage et extraction
                d = str(row.get('Date', '-'))
                t = str(row.get('Type', '-'))
                r = str(row.get('Référence', '-')) if row.get('Référence') else '-'
                
                lieu_brut = str(row.get('Lieu', ''))
                imm = lieu_brut.split('Imm ')[1].split(' -')[0] if 'Imm ' in lieu_brut else '-'
                etage = lieu_brut.split(' - ')[1].split(' -')[0] if ' - ' in lieu_brut and 'Etage' in lieu_brut or 'RDC' in lieu_brut else '-'
                appt = lieu_brut.split('Appt ')[1] if 'Appt ' in lieu_brut else '-'
                details = "Façade" if "Façade" in lieu_brut else lieu_brut[:35]

                pdf.cell(20, 7, d, 1)
                pdf.cell(30, 7, t, 1)
                pdf.cell(25, 7, r, 1)
                pdf.cell(20, 7, imm, 1)
                pdf.cell(20, 7, etage, 1)
                pdf.cell(20, 7, appt, 1)
                pdf.cell(55, 7, details, 1, 1)
            
            # 3. Résumé intelligent par type
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, f"TOTAL {type_marbre} ({intervenant}) : {len(group_type)} unité(s)", 1, 1, 'R', True)
            pdf.ln(4)
        pdf.ln(6)
            
    return pdf.output(dest='S').encode('latin-1')

# --- NAVIGATION SIDEBAR ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t3: # MARBRE & CO
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_inter")
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"], key="m_type")
            
            fourn = None
            ref_val = None
            if type_m == "Blanc Carrara":
                fourn = st.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"], key="m_f")
                ref_val = st.text_input("Référence (Lot/Bloc)", key="m_ref")
            
            imm = st.text_input("Immeuble", key="m_imm")
            etage = None
            appt = None
            
            if type_m != "White Sand":
                etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"], key="m_et")
                if type_m == "Blanc Carrara":
                    appt = st.text_input("Appartement", key="m_ap")

            p_m = st.file_uploader("Photo", type=['jpg','png','jpeg'], key="p_marbre")
            
            if st.button("Valider Saisie Marbre"):
                lieu = f"Imm {imm}"
                if etage: lieu += f" - {etage}"
                if appt: lieu += f" - Appt {appt}"
                if type_m == "White Sand": lieu += " (Façade)"
                
                data['marbre'].append({
                    "Nom": interv, "Type": type_m, "Fournisseur": fourn, 
                    "Référence": ref_val, "Lieu": lieu, 
                    "Date": pd.Timestamp.now().strftime("%d/%m"), 
                    "photo": p_m.getvalue() if p_m else None
                })
                sauvegarder_donnees()
                st.success(f"Enregistré pour {interv}")

        # (Autres métiers élec, plomb, ceram restent identiques...)

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    
    # BOUTON PDF UNIQUE ET INTELLIGENT
    if st.button("📊 GÉNÉRER LE RAPPORT DE SITUATION (PDF)"):
        try:
            pdf_bytes = generer_pdf_intelligent(tranche, data)
            st.download_button(
                label="📥 TÉLÉCHARGER LE RAPPORT PDF",
                data=pdf_bytes,
                file_name=f"Situation_Chantier_{tranche}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")

    st.divider()
    # (Affichage des onglets plans, marchandises, etc. identique...)
