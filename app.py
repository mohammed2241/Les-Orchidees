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

    def tableau_header(self, colonnes, largeurs):
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(200, 220, 255)
        for i, col in enumerate(colonnes):
            self.cell(largeurs[i], 8, col, 1, 0, 'C', True)
        self.ln()

def generer_pdf_complet(tranche_nom, data_tranche):
    pdf = PDF_Rapport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    sections = [
        ("MARBRE", "marbre", ['DATE', 'TYPE', 'REF', 'IMM', 'ETAGE', 'APPT', 'DETAILS'], [20, 30, 25, 20, 20, 20, 55]),
        ("CÉRAMIQUE", "ceram", ['DATE', 'ZONE', 'IMM', 'ETAGE', 'DETAILS'], [25, 35, 25, 25, 80]),
        ("ÉLECTRICITÉ", "elec", ['DATE', 'PRODUIT', 'QTÉ', 'DÉTAILS'], [25, 40, 20, 105]),
        ("PLOMBERIE", "plomb", ['DATE', 'PRODUIT', 'QTÉ', 'DÉTAILS'], [25, 40, 20, 105])
    ]

    for titre, key, cols, widths in sections:
        if data_tranche[key]:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f"SECTION : {titre}", ln=True)
            df = pd.DataFrame(data_tranche[key])
            
            # Groupement par intervenant si applicable (Marbre)
            if key == 'marbre':
                for inter, group in df.groupby('Nom'):
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(0, 8, f"Intervenant : {inter}", ln=True)
                    pdf.tableau_header(cols, widths)
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
                    pdf.ln(3)
            else:
                pdf.tableau_header(cols, widths)
                pdf.set_font('Arial', '', 8)
                for _, r in df.iterrows():
                    for i, col_name in enumerate(cols):
                        val = str(r.get(col_name.capitalize(), r.get('Produit', r.get('Type', '-')))) if i > 0 else str(r.get('Date', '-'))
                        if col_name == 'DÉTAILS': val = str(r.get('Détail', r.get('Lieu', '-')))
                        pdf.cell(widths[i], 7, val[:30], 1)
                    pdf.ln()
            pdf.ln(5)

    if data_tranche['marchandises']:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "RÉCEPTION MARCHANDISES", ln=True)
        for fourn, group in pd.DataFrame(data_tranche['marchandises']).groupby('Fournisseur'):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, f"Fournisseur : {fourn}", ln=True)
            pdf.tableau_header(['DATE', 'DÉSIGNATION'], [30, 160])
            pdf.set_font('Arial', '', 8)
            for _, r in group.iterrows():
                pdf.cell(30, 7, str(r.get('Date', '-')), 1)
                pdf.cell(160, 7, str(r.get('Désignation', '-')), 1, 1)
            pdf.ln(4)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t1:
        up = st.file_uploader("Plan", type=['pdf','jpg','png'], key="up_p")
        if st.button("Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees(); st.success("OK")
            
    with t2:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({"Fournisseur":f, "Désignation":d, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo_bl":p_bl.getvalue() if p_bl else None, "photo_cam":p_cam.getvalue() if p_cam else None})
            sauvegarder_donnees(); st.success("OK")

    with t3:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            fourn, ref_v = None, None
            if type_m == "Blanc Carrara":
                fourn = st.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"])
                ref_v = st.text_input("Référence (Lot/Bloc)")
            imm = st.text_input("Immeuble")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"]) if type_m != "White Sand" else None
            appt = st.text_input("Appartement") if type_m == "Blanc Carrara" else None
            p_m = st.file_uploader("Photo")
            if st.button("Valider Marbre"):
                lieu = f"Imm {imm}"
                if etage: lieu += f" - {etage}"
                if appt: lieu += f" - Appt {appt}"
                if type_m == "White Sand": lieu += " (Facade)"
                data['marbre'].append({"Nom":interv, "Type":type_m, "Fournisseur":fourn, "Référence":ref_v, "Lieu":lieu, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_m.getvalue() if p_m else None})
                sauvegarder_donnees(); st.success("OK")
        
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            im_c = st.text_input("Immeuble")
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_c = st.file_uploader("Photo")
            if st.button("Valider Céramique"):
                data['ceram'].append({"Type":z, "Lieu":f"Imm {im_c} - Etage {et}", "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_c.getvalue() if p_c else None})
                sauvegarder_donnees(); st.success("OK")

        else: # Elec / Plomb
            items = ["Spot", "Prise TV"] if spec == "Électricité" else ["Vasque", "Toilette"]
            for i in items:
                c1, c2 = st.columns([2,1])
                q = c2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = c1.text_input(f"Détails {i}", key=f"d_{i}")
                p_s = st.file_uploader(f"Photo {i}", key=f"ps_{i}")
                if st.button(f"Valider {i}", key=f"b_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit":i, "Qté":q, "Détail":dt, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_s.getvalue() if p_s else None})
                    sauvegarder_donnees(); st.toast("OK")

    with t4:
        up_s = st.file_uploader("Excel/PDF Salarié", type=['pdf', 'xlsx'])
        if st.button("Enregistrer Salarié") and up_s:
            data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
            sauvegarder_donnees(); st.success("OK")

else: # CONSULTATION
    st.header(f"🔍 Consultation - {tranche}")
    st.download_button("📊 TÉLÉCHARGER LE RAPPORT GLOBAL (PDF)", data=generer_pdf_complet(tranche, data), file_name=f"Rapport_{tranche}.pdf")
    
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    with c1:
        for p in data['plans']:
            with st.expander(f"📁 {p['nom']}"):
                b64 = base64.b64encode(p['content']).decode()
                st.components.v1.html(f'<button onclick="window.open(URL.createObjectURL(new Blob([new Uint8Array(atob(\'{b64}\').split(\'\').map(c=>c.charCodeAt(0)))] , {{type:\'application/pdf\'}})), \'_blank\')" style="width:100%; padding:10px; background:#007bff; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">👁️ VOIR LE DOCUMENT</button>', height=50)
    with c2:
        for m in data['marchandises']:
            with st.expander(f"📦 {m['Fournisseur']} - {m['Désignation']} ({m['Date']})"):
                ca, cb = st.columns(2)
                if m.get('photo_bl'): ca.image(m['photo_bl'], caption="BL")
                if m.get('photo_cam'): cb.image(m['photo_cam'], caption="Camion")
    with c3:
        sel = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        k_map = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        for entry in data[k_map[sel]]:
            title = f"{entry.get('Type', '')} {entry.get('Produit', '')} {entry.get('Nom', '')}"
            with st.expander(f"🛠️ {title} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                st.write(f"**Lieu/Détail :** {entry.get('Lieu') or entry.get('Détail', '')}")
    with c4:
        for s in data['salaries']:
            with st.expander(f"📊 {s['nom']}"):
                if s['nom'].lower().endswith('.xlsx'):
                    df = pd.read_excel(io.BytesIO(s['content']), engine='openpyxl')
                    st.dataframe(df, use_container_width=True)
                else:
                    b64 = base64.b64encode(s['content']).decode()
                    st.components.v1.html(f'<button onclick="window.open(URL.createObjectURL(new Blob([new Uint8Array(atob(\'{b64}\').split(\'\').map(c=>c.charCodeAt(0)))] , {{type:\'application/pdf\'}})), \'_blank\')" style="width:100%; padding:10px; background:#007bff; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">👁️ VOIR LE PDF</button>', height=50)
