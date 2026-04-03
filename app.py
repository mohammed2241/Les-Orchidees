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
    # ... (Autres formats PDF conservés)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])
    
    with tabs[0]: # Saisie Plans
        up = st.file_uploader("Upload Plan", type=['pdf','jpg','png','jpeg'])
        if st.button("Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue(), "type": up.type})
            sauvegarder_donnees(); st.success("Plan enregistré !")
            
    with tabs[1]: # Saisie Marchandises
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans", "Autre"])
        d = st.text_area("Désignation")
        p_bl = st.file_uploader("Photo BL", key="bl_s")
        if st.button("Valider Réception"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m/%Y"), "photo_bl": p_bl.getvalue() if p_bl else None})
            sauvegarder_donnees(); st.success("Enregistré")

    with tabs[2]: # Saisie Suivi
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            fourn, ref_v, appt, surf, fini = None, None, None, 0.0, "Poli"
            if type_m == "Blanc Carrara":
                c1, c2 = st.columns(2)
                fourn = c1.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"])
                ref_v = c2.text_input("Lot/Bloc")
                appt = st.text_input("Appartement")
                surf = st.number_input("Surface (m²)", min_value=0.0)
                fini = st.selectbox("Finition", ["Poli", "Adouci", "Brut"])
            imm = st.text_input("Immeuble"); etage = st.selectbox("Etage", ["RDC","1","2","3","4"])
            p_m = st.file_uploader("Photo")
            if st.button("Enregistrer Marbre"):
                data['marbre'].append({"Nom": interv, "Type": type_m, "Fournisseur": fourn, "Référence": ref_v, "Lieu": f"Imm {imm} - {etage} - Appt {appt if appt else ''}", "Surface": surf, "Finition": fini, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_m.getvalue() if p_m else None})
                sauvegarder_donnees(); st.success("Marbre enregistré")
        # ... (Céram, Elec, Plomb restent identiques)
    
    with tabs[3]: # Saisie Documents
        up_doc = st.file_uploader("Fichier", type=['pdf', 'xlsx', 'jpg', 'png'])
        t_doc = st.text_input("Titre")
        if st.button("Ajouter Document") and up_doc:
            data['documents'].append({"nom": t_doc if t_doc else up_doc.name, "content": up_doc.getvalue(), "type": up_doc.type, "filename": up_doc.name})
            sauvegarder_donnees(); st.success("Document ajouté")

else: # CONSULTATION (Avec option de suppression)
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
        st.download_button("📥 Rapport Marchandises (PDF)", data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), file_name="Rapport.pdf")
        for i, m in enumerate(data['marchandises']):
            with st.expander(f"📦 {m.get('Fournisseur')} - {m.get('Date')}"):
                st.write(f"**Désignation :** {m.get('Désignation')}")
                if m.get('photo_bl'): st.image(m['photo_bl'], width=300)
                if st.checkbox("Confirmer la suppression", key=f"conf_m_{i}"):
                    if st.button("🗑️ Supprimer cette réception", key=f"del_m_{i}"):
                        data['marchandises'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[2]: # Suivi métiers
        m_sel = st.radio("Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        k_map = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}
        for i, entry in enumerate(data[k_map[m_sel]]):
            with st.expander(f"🛠️ {entry.get('Type', entry.get('Produit'))} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                st.write(f"**Lieu :** {entry.get('Lieu', entry.get('Détail'))}")
                if st.checkbox("Confirmer la suppression", key=f"conf_s_{m_sel}_{i}"):
                    if st.button("🗑️ Supprimer cette entrée", key=f"del_s_{m_sel}_{i}"):
                        data[k_map[m_sel]].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[3]: # Documents
        for i, d in enumerate(data['documents']):
            with st.expander(f"📑 {d['nom']}"):
                st.download_button("Ouvrir", data=d['content'], file_name=d.get('filename', d['nom']), key=f"dl_d_{i}")
                if d.get('filename', '').lower().endswith('.xlsx'):
                    df = pd.read_excel(io.BytesIO(d['content']), engine='openpyxl')
                    st.dataframe(df, use_container_width=True)
                if st.checkbox("Confirmer la suppression", key=f"conf_d_{i}"):
                    if st.button("🗑️ Supprimer ce document", key=f"del_d_{i}"):
                        data['documents'].pop(i); sauvegarder_donnees(); st.rerun()
