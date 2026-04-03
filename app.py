import streamlit as st
import pandas as pd
import base64
import os
import pickle
import io
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées Manesmane", layout="wide")

# --- SYSTÈME DE SAUVEGARDE ---
DB_FILE = "data_chantier.pkl"

def charger_donnees():
    structure_vide = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "documents": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "documents": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "documents": []}
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
        pdf.cell(25, 10, 'DATE', 1, 0, 'C', True)
        pdf.cell(40, 10, 'TYPE', 1, 0, 'C', True)
        pdf.cell(85, 10, 'LIEU / APPT', 1, 0, 'C', True)
        pdf.cell(40, 10, 'SURFACE M2', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 8)
        for r in data_list:
            pdf.cell(25, 8, str(r.get('Date', '-')), 1)
            pdf.cell(40, 8, str(r.get('Type', '-')), 1)
            pdf.cell(85, 8, str(r.get('Lieu', '-'))[:50], 1)
            pdf.cell(40, 8, f"{r.get('Surface', '-')} m2", 1, 1)
    
    else:
        pdf.cell(30, 10, 'DATE', 1, 0, 'C', True)
        pdf.cell(50, 10, 'PRODUIT', 1, 0, 'C', True)
        pdf.cell(110, 10, 'DETAILS / LIEU', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 9)
        for r in data_list:
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Produit', r.get('Type', '-'))), 1)
            pdf.cell(110, 8, str(r.get('Lieu', r.get('Détail', '-'))), 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])
    # ... (Le code de saisie reste identique au précédent)
    with tabs[1]:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans", "Autre"])
        d = st.text_area("Désignation")
        if st.button("Valider Réception"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m/%Y")})
            sauvegarder_donnees(); st.success("Enregistré")

else: # CONSULTATION (Rapport PDF rétabli)
    st.header(f"🔍 Consultation - {tranche}")
    ctabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])

    with ctabs[0]: # Plans
        for i, p in enumerate(data['plans']):
            with st.expander(f"📄 {p['nom']}"):
                st.download_button("Ouvrir", data=p['content'], file_name=p['nom'], key=f"dl_p_{i}")
                if st.checkbox("Confirmer la suppression", key=f"conf_p_{i}"):
                    if st.button("🗑️ Supprimer ce plan", key=f"del_p_{i}"):
                        data['plans'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[1]: # Marchandises
        # BOUTON RAPPORT RÉTABLI ICI
        st.download_button("📥 Télécharger Rapport Marchandises (PDF)", 
                           data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), 
                           file_name=f"Marchandises_{tranche}.pdf", key="btn_pdf_march")
        st.divider()
        for i, m in enumerate(data['marchandises']):
            with st.expander(f"📦 {m.get('Fournisseur')} - {m.get('Date')}"):
                st.write(f"**Désignation :** {m.get('Désignation')}")
                if st.checkbox("Confirmer la suppression", key=f"conf_m_{i}"):
                    if st.button("🗑️ Supprimer cette réception", key=f"del_m_{i}"):
                        data['marchandises'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[2]: # Suivi métiers
        m_sel = st.radio("Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        k_map = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}
        
        # BOUTON RAPPORT RÉTABLI ICI POUR CHAQUE MÉTIER
        st.download_button(f"📥 Télécharger Rapport {m_sel} (PDF)", 
                           data=creer_pdf_section(m_sel.upper(), data[k_map[m_sel]], k_map[m_sel]), 
                           file_name=f"Rapport_{m_sel}_{tranche}.pdf", key="btn_pdf_suivi")
        st.divider()
        
        for i, entry in enumerate(data[k_map[m_sel]]):
            with st.expander(f"🛠️ {entry.get('Type', entry.get('Produit'))} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                st.write(f"**Lieu :** {entry.get('Lieu', entry.get('Détail'))}")
                if entry.get('Surface'): st.info(f"Surface: {entry['Surface']} m2 | Finition: {entry.get('Finition')}")
                if st.checkbox("Confirmer la suppression", key=f"conf_s_{m_sel}_{i}"):
                    if st.button("🗑️ Supprimer cette entrée", key=f"del_s_{m_sel}_{i}"):
                        data[k_map[m_sel]].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[3]: # Documents
        for i, d in enumerate(data['documents']):
            with st.expander(f"📑 {d['nom']}"):
                st.download_button("Ouvrir", data=d['content'], file_name=d.get('filename', d['nom']), key=f"dl_d_{i}")
                if st.checkbox("Confirmer la suppression", key=f"conf_d_{i}"):
                    if st.button("🗑️ Supprimer ce document", key=f"del_d_{i}"):
                        data['documents'].pop(i); sauvegarder_donnees(); st.rerun()
