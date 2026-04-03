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
                # Migration auto si l'ancienne clé 'salaries' existe
                for t in data:
                    if 'salaries' in data[t] and 'documents' not in data[t]:
                        data[t]['documents'] = data[t].pop('salaries')
                return data
        except: return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# --- GÉNÉRATEUR PDF PAR SECTION ---
class PDF_Report(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'LES ORCHIDÉES MANESMANE - RAPPORT DE SITUATION', 0, 1, 'C')
        self.ln(5)

def creer_pdf_section(titre, data_list, type_rapport):
    pdf = PDF_Report()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"SITUATION : {titre}", ln=True)
    pdf.ln(5)
    
    if not data_list:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "Aucune donnée enregistrée.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(200, 220, 255)

    if type_rapport == "marbre":
        df = pd.DataFrame(data_list)
        for inter, group in df.groupby('Nom'):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, f"Intervenant : {inter}", ln=True)
            cols = ['DATE', 'TYPE', 'REF', 'IMM', 'ETAGE', 'APPT', 'DETAILS']
            w = [20, 30, 25, 20, 20, 20, 55]
            for i, c in enumerate(cols): pdf.cell(w[i], 8, c, 1, 0, 'C', True)
            pdf.ln()
            pdf.set_font('Arial', '', 8)
            for _, r in group.iterrows():
                lieu = str(r.get('Lieu', ''))
                pdf.cell(20, 7, str(r.get('Date', '-')), 1)
                pdf.cell(30, 7, str(r.get('Type', '-')), 1)
                pdf.cell(25, 7, str(r.get('Référence', '-')) if r.get('Référence') else '-', 1)
                pdf.cell(20, 7, lieu.split('Imm ')[1].split(' -')[0] if 'Imm ' in lieu else '-', 1)
                pdf.cell(20, 7, 'Oui' if any(x in lieu for x in ['RDC','1er','2','3','4']) else '-', 1)
                pdf.cell(20, 7, lieu.split('Appt ')[1] if 'Appt ' in lieu else '-', 1)
                pdf.cell(55, 7, lieu[:40], 1, 1)
            pdf.ln(5)

    elif type_rapport == "marchandises":
        pdf.cell(30, 8, 'DATE', 1, 0, 'C', True)
        pdf.cell(40, 8, 'FOURNISSEUR', 1, 0, 'C', True)
        pdf.cell(120, 8, 'DÉSIGNATION', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 8)
        for r in data_list:
            pdf.cell(30, 7, r['Date'], 1)
            pdf.cell(40, 7, r['Fournisseur'], 1)
            pdf.cell(120, 7, r['Désignation'], 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])
    
    with t1:
        up = st.file_uploader("Upload Plan", type=['pdf','jpg','png','jpeg'], key="up_p")
        if st.button("Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue(), "type": up.type})
            sauvegarder_donnees(); st.success("Plan enregistré !")
            
    with t2:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({"Fournisseur":f, "Désignation":d, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo_bl":p_bl.getvalue() if p_bl else None, "photo_cam":p_cam.getvalue() if p_cam else None})
            sauvegarder_donnees(); st.success("Réception enregistrée")

    with t3:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        # ... (Logique de saisie Marbre/Céram reste identique) ...
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            imm = st.text_input("Immeuble")
            if st.button("Valider Marbre"):
                data['marbre'].append({"Nom":interv, "Type":type_m, "Lieu":f"Imm {imm}", "Date":pd.Timestamp.now().strftime("%d/%m")})
                sauvegarder_donnees(); st.success("Marbre enregistré")

    with t4:
        up_doc = st.file_uploader("Upload Document (PDF, Excel, Img)", type=['pdf', 'xlsx', 'jpg', 'png', 'jpeg'])
        desc_doc = st.text_input("Nom ou description du document")
        if st.button("Enregistrer Document") and up_doc:
            nom_final = desc_doc if desc_doc else up_doc.name
            data['documents'].append({"nom": nom_final, "content": up_doc.getvalue(), "type": up_doc.type, "filename": up_doc.name})
            sauvegarder_donnees(); st.success("Document ajouté à la bibliothèque")

else: # CONSULTATION
    st.header(f"🔍 Consultation - {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])

    with c1:
        st.subheader("Plans Techniques")
        for p in data['plans']:
            with st.expander(f"📄 {p['nom']}"):
                st.download_button("📂 Ouvrir / Télécharger", data=p['content'], file_name=p['nom'], mime=p.get('type', 'application/octet-stream'))
                if p.get('type', '').startswith('image'):
                    st.image(p['content'])

    with c2:
        st.download_button("📥 Rapport Marchandises (PDF)", data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), file_name=f"Rapport_Marchandises_{tranche}.pdf")
        for m in data['marchandises']:
            with st.expander(f"📦 {m['Fournisseur']} - {m['Désignation']}"):
                ca, cb = st.columns(2)
                if m.get('photo_bl'): ca.image(m['photo_bl'], caption="BL")
                if m.get('photo_cam'): cb.image(m['photo_cam'], caption="Camion")

    with c3:
        sel = st.radio("Métier pour le rapport", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        k_map = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}
        st.download_button(f"📥 Rapport {sel} (PDF)", data=creer_pdf_section(sel.upper(), data[k_map[sel]], k_map[sel]), file_name=f"Rapport_{sel}_{tranche}.pdf")
        for entry in data[k_map[sel]]:
            with st.expander(f"🛠️ {entry.get('Type', 'Suivi')} ({entry.get('Date')})"):
                st.write(f"**Lieu :** {entry.get('Lieu')}")

    with c4:
        st.subheader("📁 Bibliothèque de Documents")
        if not data['documents']:
            st.info("Aucun document dans cette tranche.")
        for d in data['documents']:
            with st.expander(f"📑 {d['nom']}"):
                st.write(f"Fichier : `{d.get('filename', 'Inconnu')}`")
                st.download_button("📂 Télécharger / Lire le document", data=d['content'], file_name=d.get('filename', d['nom']), mime=d.get('type', 'application/octet-stream'))
                
                # Lecture directe si c'est un Excel
                if d.get('filename', '').lower().endswith('.xlsx'):
                    try:
                        df = pd.read_excel(io.BytesIO(d['content']), engine='openpyxl')
                        st.dataframe(df, use_container_width=True)
                    except Exception as e:
                        st.error("Aperçu du tableau impossible.")
