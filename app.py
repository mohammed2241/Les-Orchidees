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
            cols = ['DATE', 'TYPE', 'IMM', 'DETAILS']
            w = [30, 40, 30, 90]
            for i, c in enumerate(cols): pdf.cell(w[i], 8, c, 1, 0, 'C', True)
            pdf.ln()
            pdf.set_font('Arial', '', 8)
            for _, r in group.iterrows():
                pdf.cell(30, 7, str(r.get('Date', '-')), 1)
                pdf.cell(40, 7, str(r.get('Type', '-')), 1)
                pdf.cell(30, 7, str(r.get('Lieu', '-')).split(' -')[0], 1)
                pdf.cell(90, 7, str(r.get('Lieu', '-')), 1, 1)
            pdf.ln(5)
    else:
        pdf.cell(30, 8, 'DATE', 1, 0, 'C', True)
        pdf.cell(50, 8, 'PRODUIT/ZONE', 1, 0, 'C', True)
        pdf.cell(110, 8, 'LIEU/DETAILS', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 8)
        for r in data_list:
            pdf.cell(30, 7, str(r.get('Date', '-')), 1)
            pdf.cell(50, 7, str(r.get('Produit', r.get('Type', '-'))), 1)
            pdf.cell(110, 7, str(r.get('Lieu', r.get('Détail', '-'))), 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])
    
    with t1: # Plans
        up = st.file_uploader("Upload Plan", type=['pdf','jpg','png','jpeg'], key="up_p")
        if st.button("Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue(), "type": up.type})
            sauvegarder_donnees(); st.success("Plan enregistré !")
            
    with t2: # Marchandises
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({"Fournisseur":f, "Désignation":d, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo_bl":p_bl.getvalue() if p_bl else None, "photo_cam":p_cam.getvalue() if p_cam else None})
            sauvegarder_donnees(); st.success("Réception enregistrée")

    with t3: # SUIVI (Partie corrigée)
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            imm = st.text_input("Immeuble")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_m = st.file_uploader("Photo Marbre")
            if st.button("Enregistrer Marbre"):
                data['marbre'].append({"Nom":interv, "Type":type_m, "Lieu":f"Imm {imm} - {etage}", "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_m.getvalue() if p_m else None})
                sauvegarder_donnees(); st.success(f"Marbre enregistré pour {interv}")
        
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            im_c = st.text_input("Immeuble")
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_c = st.file_uploader("Photo Céram")
            if st.button("Enregistrer Céramique"):
                data['ceram'].append({"Type":z, "Lieu":f"Imm {im_c} - {et}", "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_c.getvalue() if p_c else None})
                sauvegarder_donnees(); st.success("Céramique enregistrée")

        else: # Elec / Plomb
            items = ["Spot", "Prise TV", "Tableau"] if spec == "Électricité" else ["Vasque", "Toilette", "Mélangeur"]
            for i in items:
                c1, c2, c3 = st.columns([2,1,2])
                q = c2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = c1.text_input(f"Détails {i}", key=f"d_{i}")
                p_s = c3.file_uploader(f"Photo {i}", key=f"ps_{i}")
                if st.button(f"Valider {i}", key=f"b_{i}"):
                    key_m = "elec" if spec == "Électricité" else "plomb"
                    data[key_m].append({"Produit":i, "Qté":q, "Détail":dt, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_s.getvalue() if p_s else None})
                    sauvegarder_donnees(); st.toast(f"{i} validé !")

    with t4: # DOCUMENTS
        up_doc = st.file_uploader("Fichier (PDF, Excel, Img)", type=['pdf', 'xlsx', 'jpg', 'png', 'jpeg'])
        desc_doc = st.text_input("Titre du document")
        if st.button("Ajouter à la bibliothèque") and up_doc:
            data['documents'].append({"nom": desc_doc if desc_doc else up_doc.name, "content": up_doc.getvalue(), "type": up_doc.type, "filename": up_doc.name})
            sauvegarder_donnees(); st.success("Document enregistré")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])

    with c1:
        for p in data['plans']:
            with st.expander(f"📄 {p['nom']}"):
                st.download_button("📂 Télécharger", data=p['content'], file_name=p['nom'])
                if p.get('type', '').startswith('image'): st.image(p['content'])

    with c2:
        st.download_button("📥 Rapport Marchandises (PDF)", data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), file_name="Rapport_Marchandises.pdf")
        for m in data['marchandises']:
            with st.expander(f"📦 {m['Fournisseur']} - {m['Désignation']}"):
                if m.get('photo_bl'): st.image(m['photo_bl'], width=300, caption="BL")

    with c3:
        sel = st.radio("Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        k_map = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}
        st.download_button(f"📥 Rapport {sel} (PDF)", data=creer_pdf_section(sel.upper(), data[k_map[sel]], k_map[sel]), file_name=f"Rapport_{sel}.pdf")
        for entry in data[k_map[sel]]:
            with st.expander(f"🛠️ {entry.get('Type', entry.get('Produit', 'Suivi'))} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                st.write(f"**Lieu/Détail :** {entry.get('Lieu') or entry.get('Détail', '')}")

    with c4:
        for d in data['documents']:
            with st.expander(f"📑 {d['nom']}"):
                st.download_button("📂 Ouvrir", data=d['content'], file_name=d.get('filename', d['nom']))
                if d.get('filename', '').lower().endswith('.xlsx'):
                    df = pd.read_excel(io.BytesIO(d['content']), engine='openpyxl')
                    st.dataframe(df, use_container_width=True)
