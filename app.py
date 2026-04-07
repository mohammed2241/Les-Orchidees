import streamlit as st
import pandas as pd
import base64
import os
import pickle
import io
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées Manesmane", layout="wide")

# --- LISTES PAR DÉFAUT (Tirées de vos documents) ---
DEFAUT_FRS = ["INTERCABLE", "SOFA", "PROMELEC", "MG LIGHTING", "KADIR DISTRIBUTION", "SARABO", "SOQOP", "FROIDEL", "NOVACIM", "RE SERVICE", "ATLAS MULTIMATERIEL", "SBBC", "LAFARGE", "SAFI BAINS", "INNOVA WOOD", "SINASTONE", "MEDIAL", "EXPLOMAR", "RIVA", "INTERSIG", "AQUAPLANET", "BEKO MAGHREB", "ISOLBOX", "PLATINOVA", "TAMAGROT", "AOC", "SOCODAM DAVUM", "HYDRAU MAC", "TRACTRAFFIC", "GOOD YEAR BAB DOKALA", "MULTICERAME", "MALL ZALLIJ", "SUPER CERAME", "PETROMIN OILS", "ALSINA", "PERI", "Autre"]
DEFAUT_ELEC = ["SPOT", "SPOT DOUBLE", "BLOC DE SECOURS", "DISJ", "APPLIQUE", "LED", "SUPPORT SURMOULE", "SUPPORT 3 MODULES", "SUPPORT 4 MODULES", "SUPPORT 6 MODULES", "PRISE 2P+T à clapet IP44 45 Anthr", "Obturateur 22,5 Anthr", "PRISE 2P+T 45 Anthr", "Prise TV SAT 45 Anthr", "Interr SVV 45 Anthr", "Interr V&V 22,5 Anthr", "Pousse à basc 45 Anthr", "Inver volets roul 45 Anthr", "Video phonique"]
DEFAUT_PLOMB = ["TOILETTE", "VASQUE 60 CM", "VASQUE 80 CM", "BIDETS", "DOUCHETTE", "POMPE DE DOUCHE", "MIT DCH", "MIT LVB", "MIT BIDET", "CHAUFFE EAU", "EVIER", "MIT EVIER"]

# --- SYSTÈME DE SAUVEGARDE ---
DB_FILE = "data_chantier.pkl"

def charger_donnees():
    structure_vide = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "documents": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "documents": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "documents": []},
        "config": {"fournisseurs": DEFAUT_FRS.copy(), "produits_elec": DEFAUT_ELEC.copy(), "produits_plomb": DEFAUT_PLOMB.copy()}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                data = pickle.load(f)
                for t in ["Tranche 3", "Tranche 4", "Tranche 5"]:
                    if t not in data: data[t] = structure_vide[t]
                    for key in structure_vide[t]:
                        if key not in data[t]: data[t][key] = []
                # Migration de la configuration si ancien fichier
                if "config" not in data: data["config"] = structure_vide["config"]
                return data
        except: return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# Raccourcis pour les configurations
cfg = st.session_state.db["config"]

# --- GÉNÉRATEUR PDF ---
class PDF_Report(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'LES ORCHIDÉES MANESMANE - RAPPORT DE SITUATION', 0, 1, 'C')
        self.ln(5)

def creer_pdf_section(titre, data_list, type_rapport):
    pdf = PDF_Report()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"SECTION : {titre}", ln=True)
    pdf.ln(5)
    if not data_list:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "Aucune donnee enregistree.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 220, 255)

    if type_rapport == "marchandises":
        pdf.cell(30, 10, 'DATE', 1, 0, 'C', True)
        pdf.cell(50, 10, 'FOURNISSEUR', 1, 0, 'C', True)
        pdf.cell(110, 10, 'DESIGNATION', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 9)
        for r in data_list:
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Fournisseur', '-')), 1)
            pdf.cell(110, 8, str(r.get('Désignation', '-'))[:60], 1, 1)

    elif type_rapport == "marbre":
        df = pd.DataFrame(data_list)
        if not df.empty and 'Nom' in df.columns:
            for inter, group in df.groupby('Nom'):
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 10, f"Intervenant : {inter}", ln=True)
                cols = ['DATE', 'TYPE', 'LOT/REF', 'LIEU/APPT', 'M2']
                w = [25, 45, 25, 65, 30]
                for i, c in enumerate(cols): pdf.cell(w[i], 8, c, 1, 0, 'C', True)
                pdf.ln()
                pdf.set_font('Arial', '', 8)
                for _, r in group.iterrows():
                    pdf.cell(25, 7, str(r.get('Date', '-')), 1)
                    pdf.cell(45, 7, str(r.get('Type', '-'))[:25], 1)
                    pdf.cell(25, 7, str(r.get('Référence', '-')) if r.get('Référence') else '-', 1)
                    pdf.cell(65, 7, str(r.get('Lieu', '-'))[:45], 1)
                    surface_val = r.get('Surface')
                    pdf.cell(30, 7, f"{surface_val} m2" if surface_val else "-", 1, 1)
                pdf.ln(5)

    elif type_rapport in ["elec", "plomb"]:
        pdf.cell(30, 10, 'DATE', 1, 0, 'C', True)
        pdf.cell(50, 10, 'PRODUIT', 1, 0, 'C', True)
        pdf.cell(20, 10, 'QTE', 1, 0, 'C', True)
        pdf.cell(90, 10, 'DETAILS / LIEU', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 9)
        
        total_qte = 0
        for r in data_list:
            q = r.get('Qté', 0)
            try: total_qte += int(q)
            except: pass
                
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Produit', r.get('Type', '-')))[:25], 1)
            pdf.cell(20, 8, str(q), 1, 0, 'C')
            pdf.cell(90, 8, str(r.get('Lieu', r.get('Détail', '-')))[:45], 1, 1)
            
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 10, 'TOTAL DES QUANTITES :', 1, 0, 'R', True)
        pdf.cell(20, 10, str(total_qte), 1, 0, 'C', True)
        pdf.cell(90, 10, '', 1, 1, 'C', True)

    else:
        pdf.cell(30, 10, 'DATE', 1, 0, 'C', True)
        pdf.cell(50, 10, 'PRODUIT / ZONE', 1, 0, 'C', True)
        pdf.cell(110, 10, 'DETAILS / LIEU', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 9)
        for r in data_list:
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Produit', r.get('Type', '-'))), 1)
            pdf.cell(110, 8, str(r.get('Lieu', r.get('Détail', '-'))), 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE"])

# ==========================================
#                MODE CATALOGUE
# ==========================================
if mode == "⚙️ CATALOGUE":
    st.header("⚙️ Gestion du Catalogue")
    st.info("Ajoutez ici de nouveaux produits ou fournisseurs. Ils apparaîtront automatiquement dans vos menus de saisie.")
    
    cat1, cat2, cat3 = st.tabs(["🏭 Fournisseurs", "⚡ Produits Électricité", "🚰 Produits Plomberie"])
    
    with cat1:
        nouveau_f = st.text_input("Nouveau Fournisseur")
        if st.button("➕ Ajouter Fournisseur"):
            if nouveau_f and nouveau_f not in cfg["fournisseurs"]:
                cfg["fournisseurs"].append(nouveau_f)
                sauvegarder_donnees(); st.success("Fournisseur ajouté !")
        with st.expander("Voir la liste complète"):
            st.write(cfg["fournisseurs"])

    with cat2:
        nouveau_e = st.text_input("Nouveau Produit Électricité")
        if st.button("➕ Ajouter Produit Élec"):
            if nouveau_e and nouveau_e not in cfg["produits_elec"]:
                cfg["produits_elec"].append(nouveau_e)
                sauvegarder_donnees(); st.success("Produit ajouté !")
        with st.expander("Voir la liste complète"):
            st.write(cfg["produits_elec"])

    with cat3:
        nouveau_p = st.text_input("Nouveau Produit Plomberie")
        if st.button("➕ Ajouter Produit Plomberie"):
            if nouveau_p and nouveau_p not in cfg["produits_plomb"]:
                cfg["produits_plomb"].append(nouveau_p)
                sauvegarder_donnees(); st.success("Produit ajouté !")
        with st.expander("Voir la liste complète"):
            st.write(cfg["produits_plomb"])

# ==========================================
#                MODE SAISIE
# ==========================================
elif mode == "📝 SAISIE":
    tranche = st
