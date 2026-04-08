import streamlit as st
import pandas as pd
import os
import pickle
import io
import datetime
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées Manesmane", layout="wide")

# --- LISTES PAR DÉFAUT ---
DEFAUT_FRS = ["INTERCABLE", "SOFA", "PROMELEC", "MG LIGHTING", "KADIR DISTRIBUTION", "SARABO", "SOQOP", "FROIDEL", "NOVACIM", "RE SERVICE", "ATLAS MULTIMATERIEL", "SBBC", "LAFARGE", "SAFI BAINS", "INNOVA WOOD", "SINASTONE", "MEDIAL", "EXPLOMAR", "RIVA", "INTERSIG", "AQUAPLANET", "BEKO MAGHREB", "ISOLBOX", "PLATINOVA", "TAMAGROT", "AOC", "SOCODAM DAVUM", "HYDRAU MAC", "TRACTRAFFIC", "GOOD YEAR BAB DOKALA", "MULTICERAME", "MALL ZALLIJ", "SUPER CERAME", "PETROMIN OILS", "ALSINA", "PERI", "Autre"]
DEFAUT_ELEC = ["SPOT", "SPOT DOUBLE", "BLOC DE SECOURS", "DISJ", "APPLIQUE", "LED", "SUPPORT SURMOULE", "SUPPORT 3 MODULES", "SUPPORT 4 MODULES", "SUPPORT 6 MODULES", "PRISE 2P+T à clapet IP44", "Obturateur", "PRISE 2P+T", "Prise TV SAT", "Interr SVV", "Interr V&V", "Pousse à basc", "Inver volets roul", "Video phonique"]
DEFAUT_PLOMB = ["TOILETTE", "VASQUE 60 CM", "VASQUE 80 CM", "BIDETS", "DOUCHETTE", "POMPE DE DOUCHE", "MIT DCH", "MIT LVB", "MIT BIDET", "CHAUFFE EAU", "EVIER", "MIT EVIER"]

# --- SYSTÈME DE SAUVEGARDE (Local) ---
DB_FILE = "data_chantier_v2.pkl"

def charger_donnees():
    structure_vide = {
        "Tranche 3": {"marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": []},
        "Tranche 4": {"marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": []},
        "Tranche 5": {"marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": []},
        "config": {"fournisseurs": DEFAUT_FRS.copy(), "produits_elec": DEFAUT_ELEC.copy(), "produits_plomb": DEFAUT_PLOMB.copy()}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                data = pickle.load(f)
                # Assurer que la structure est complète après suppression de plans/docs
                for t in ["Tranche 3", "Tranche 4", "Tranche 5"]:
                    if t not in data: data[t] = structure_vide[t]
                if "config" not in data: data["config"] = structure_vide["config"]
                return data
        except: return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

cfg = st.session_state.db["config"]

# --- GÉNÉRATEUR PDF ---
def creer_pdf_section(titre, data_list, type_rapport):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"RAPPORT : {titre}", ln=True, align='C')
    pdf.ln(5)
    
    if not data_list:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "Aucune donnee enregistree.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(230, 230, 230)

    # En-têtes selon le type
    if type_rapport == "marchandises":
        cols = ["DATE", "FOURNISSEUR", "DESIGNATION"]
        w = [30, 50, 110]
        for i, c in enumerate(cols): pdf.cell(w[i], 10, c, 1, 0, 'C', True)
        pdf.ln()
        pdf.set_font('Arial', '', 8)
        for r in data_list:
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Fournisseur', '-'))[:25], 1)
            pdf.cell(110, 8, str(r.get('Désignation', '-'))[:65], 1, 1)

    elif type_rapport == "marbre":
        cols = ["DATE", "INTERV.", "TYPE", "LIEU", "M2"]
        w = [25, 30, 50, 60, 25]
        for i, c in enumerate(cols): pdf.cell(w[i], 10, c, 1, 0, 'C', True)
        pdf.ln()
        pdf.set_font('Arial', '', 7)
        for r in data_list:
            pdf.cell(25, 8, str(r.get('Date', '-')), 1)
            pdf.cell(30, 8, str(r.get('Nom', '-')), 1)
            pdf.cell(50, 8, str(r.get('Type', '-'))[:35], 1)
            pdf.cell(60, 8, str(r.get('Lieu', '-'))[:45], 1)
            pdf.cell(25, 8, f"{r.get('Surface', '0')} m2", 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MENU", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ================= MODE SAISIE =================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📦 MARCHANDISES", "🛠️ SUIVI CHANTIER"])

    with tabs[0]:
        f = st.selectbox("Fournisseur", cfg["fournisseurs"])
        d = st.text_area("Désignation complète")
        p_bl = st.file_uploader("Photo du Bon de Livraison", type=['jpg','png','jpeg'])
        if st.button("Valider Réception"):
            data['marchandises'].append({
                "Fournisseur": f, "Désignation": d, 
                "Date": datetime.date.today().strftime("%d/%m/%Y"), 
                "photo_bl": p_bl.getvalue() if p_bl else None
            })
            sauvegarder_donnees(); st.success("Enregistré !")

    with tabs[1]:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type Marbre", ["Gris Bold", "White Sand", "Blanc Carrara"])
            
            # Détails Blanc Carrara (Restaurés)
            fourn, ref_v, surf, fini, sous_type_bc, appt = None, None, 0.0, None, None, ""
            
            if type_m == "Blanc Carrara":
                sous_type_bc = st.selectbox("Élément Blanc Carrara", ["Dallage", "Seuil", "Niche", "Les douches"])
                if sous_type_bc == "Dallage":
                    appt = st.text_input("N° Appartement")
                    c1, c2 = st.columns(2)
                    fourn = c1.selectbox("Fournisseur Marbre", ["Graziani", "Caro Colombi", "Lorenzoni", "MARMI BIANCO"])
                    ref_v = c2.text_input("Référence (Lot/Bloc)")
                    surf = st.number_input("Surface (m²)", min_value=0.0)
                    fini = st.selectbox("Finition", ["Poli", "Adouci", "Brut"])
            
            imm = st.text_input("Immeuble")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "5ème"])
            p_m = st.file_uploader("Photo de la pose")
            
            if st.button("Enregistrer Marbre"):
                lieu_final = f"Imm {imm} - {etage}" + (f" - Appt {appt}" if appt else "")
                type_final = f"Blanc Carrara ({sous_type_bc})" if sous_type_bc else type_m
                data['marbre'].append({
                    "Nom": interv, "Type": type_final, "Fournisseur": fourn, 
                    "Référence": ref_v, "Lieu": lieu_final, "Surface": surf, 
                    "Finition": fini, "Date": datetime.date.today().strftime("%d/%m"), 
                    "photo": p_m.getvalue() if p_m else None
                })
                sauvegarder_donnees(); st.success("Saisie Marbre Validée")

        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Salon"])
            im = st.text_input("Immeuble")
            et = st.selectbox("Etage", ["RDC","1","2","3","4","5"])
            p_c = st.file_uploader("Photo")
            if st.button("Enregistrer Céramique"):
                data['ceram'].append({
                    "Type": z, "Lieu": f"Imm {im} - {et}", 
                    "Date": datetime.date.today().strftime("%d/%m"), 
                    "photo": p_c.getvalue() if p_c else None
                })
                sauvegarder_donnees(); st.success("Céramique Validée")

        else: # Elec / Plomb
            prods = cfg["produits_elec"] if spec == "Électricité" else cfg["produits_plomb"]
            p_sel = st.selectbox("Produit", prods)
            q = st.number_input("Quantité", min_value=1)
            loc = st.text_input("Localisation (ex: Imm 2 - Appt 4)")
            p_s = st.file_uploader("Photo")
            if st.button(f"Valider {spec}"):
                key = "elec" if spec == "Électricité" else "plomb"
                data[key].append({
                    "Produit": p_sel, "Qté": q, "Lieu": loc, 
                    "Date": datetime.date.today().strftime("%d/%m"), 
                    "photo": p_s.getvalue() if p_s else None
                })
                sauvegarder_donnees(); st.success("Enregistré !")

# ================= MODE CONSULTATION =================
elif mode == "🔍 CONSULTATION":
    cat_consul = st.radio("Section", ["Marchandises", "Suivi Chantier"], horizontal=True)
    
    if cat_consul == "Marchandises":
        st.download_button("📥 Rapport PDF Marchandises", data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), file_name="Marchandises.pdf")
        for i, m in enumerate(reversed(data['marchandises'])):
            with st.expander(f"📦 {m['Fournisseur']} - {m['Date']}"):
                st.write(m['Désignation'])
                if m['photo_bl']: st.image(m['photo_bl'], width=300)
                if st.button("🗑️ Supprimer", key=f"del_m_{i}"):
                    data['marchandises'].pop(-(i+1)); sauvegarder_donnees(); st.rerun()

    else:
        m_filter = st.selectbox("Filtrer Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"])
        k = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}[m_filter]
        
        st.download_button(f"📥 Rapport PDF {m_filter}", data=creer_pdf_section(m_filter.upper(), data[k], k), file_name=f"{m_filter}.pdf")
        
        for i, entry in enumerate(reversed(data[k])):
            titre = f"{entry.get('Type', entry.get('Produit'))} - {entry['Date']}"
            with st.expander(titre):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Lieu:** {entry['Lieu']}")
                    if 'Qté' in entry: st.write(f"**Qté:** {entry['Qté']}")
                    if 'Surface' in entry: st.write(f"**Surface:** {entry['Surface']} m2")
                with col2:
                    if entry.get('photo'): st.image(entry['photo'], width=250)
                if st.button("🗑️ Supprimer", key=f"del_{k}_{i}"):
                    data[k].pop(-(i+1)); sauvegarder_donnees(); st.rerun()

# ================= MODE CATALOGUE =================
elif mode == "⚙️ CATALOGUE":
    st.header("⚙️ Configuration")
    c1, c2, c3 = st.tabs(["Fournisseurs", "Élec", "Plomb"])
    
    with c1:
        nf = st.text_input("Nouveau Fournisseur")
        if st.button("Ajouter FRS") and nf:
            cfg["fournisseurs"].append(nf); sauvegarder_donnees(); st.success("Ajouté")
        st.write(cfg["fournisseurs"])

    with c2:
        ne = st.text_input("Nouveau Produit Élec")
        if st.button("Ajouter Élec") and ne:
            cfg["produits_elec"].append(ne); sauvegarder_donnees(); st.success("Ajouté")
        st.write(cfg["produits_elec"])

    with c3:
        np = st.text_input("Nouveau Produit Plomb")
        if st.button("Ajouter Plomb") and np:
            cfg["produits_plomb"].append(np); sauvegarder_donnees(); st.success("Ajouté")
        st.write(cfg["produits_plomb"])
