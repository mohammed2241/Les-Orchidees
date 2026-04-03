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
        pdf.cell(0, 10, "Aucune donnee marbre.", ln=True)
        return pdf.output(dest='S').encode('latin-1')
    df = pd.DataFrame(data_tranche['marbre'])
    for intervenant, group_inter in df.groupby('Nom'):
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 12, f"INTERVENANT : {intervenant}", ln=True)
        pdf.set_text_color(0, 0, 0)
        for type_marbre, group_type in group_inter.groupby('Type'):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, f">> Categorie : {type_marbre}", ln=True)
            pdf.tableau_header()
            pdf.set_font('Arial', '', 8)
            for _, row in group_type.iterrows():
                d = str(row.get('Date', '-'))
                t = str(row.get('Type', '-'))
                r = str(row.get('Référence', '-')) if row.get('Référence') else '-'
                lieu_brut = str(row.get('Lieu', ''))
                imm = lieu_brut.split('Imm ')[1].split(' -')[0] if 'Imm ' in lieu_brut else '-'
                etage = lieu_brut.split(' - ')[1].split(' -')[0] if ' - ' in lieu_brut and ('Etage' in lieu_brut or 'RDC' in lieu_brut or '1er' in lieu_brut) else '-'
                appt = lieu_brut.split('Appt ')[1] if 'Appt ' in lieu_brut else '-'
                details = "Facade" if "Facade" in lieu_brut else lieu_brut[:35]
                pdf.cell(20, 7, d, 1)
                pdf.cell(30, 7, t, 1)
                pdf.cell(25, 7, r, 1)
                pdf.cell(20, 7, imm, 1)
                pdf.cell(20, 7, etage, 1)
                pdf.cell(20, 7, appt, 1)
                pdf.cell(55, 7, details, 1, 1)
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, f"TOTAL {type_marbre} ({intervenant}) : {len(group_type)} unite(s)", 1, 1, 'R', True)
            pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

# --- NAVIGATION ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with tabs[0]: # PLANS
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees()
            st.success("Plan enregistré !")
            
    with tabs[1]: # MARCHANDISES
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", type=['jpg','jpeg','png'], key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", type=['jpg','jpeg','png'], key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({
                "Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M"),
                "photo_bl": p_bl.getvalue() if p_bl else None,
                "photo_cam": p_cam.getvalue() if p_cam else None
            })
            sauvegarder_donnees()
            st.success("Réception enregistrée !")

    with tabs[2]: # SUIVI METIERS
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec in ["Électricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for i in items:
                col1, col2, col3 = st.columns([2, 1, 2])
                q = col2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = col3.text_input("Détails", key=f"d_{i}")
                p_s = st.file_uploader(f"Photo {i}", type=['jpg','png'], key=f"p_{i}")
                if st.button(f"Valider {i}", key=f"btn_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit": i, "Qté": q, "Détail": dt, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_s.getvalue() if p_s else None})
                    sauvegarder_donnees()
                    st.toast("Validé !")
        elif spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_inter")
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"], key="m_type")
            fourn, ref_v = None, None
            if type_m == "Blanc Carrara":
                fourn = st.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"], key="m_f")
                ref_v = st.text_input("Référence (Lot/Bloc)", key="m_ref")
            imm = st.text_input("Immeuble", key="m_imm")
            etage, appt = None, None
            if type_m != "White Sand":
                etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"], key="m_et")
                if type_m == "Blanc Carrara": appt = st.text_input("Appartement", key="m_ap")
            p_m = st.file_uploader("Photo", type=['jpg','png'], key="p_m")
            if st.button("Valider Marbre"):
                lieu = f"Imm {imm}"
                if etage: lieu += f" - {etage}"
                if appt: lieu += f" - Appt {appt}"
                if type_m == "White Sand": lieu += " (Facade)"
                data['marbre'].append({"Nom": interv, "Type": type_m, "Fournisseur": fourn, "Référence": ref_v, "Lieu": lieu, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_m.getvalue() if p_m else None})
                sauvegarder_donnees()
                st.success("Enregistré !")
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            im_c = st.text_input("Immeuble")
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_c = st.file_uploader("Photo", type=['jpg','png'], key="p_c")
            if st.button("Valider Céramique"):
                data['ceram'].append({"Type": z, "Lieu": f"Imm {im_c} - Etage {et}", "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_c.getvalue() if p_c else None})
                sauvegarder_donnees()
                st.success("Céramique OK")

    with tabs[3]: # SALARIÉ
        up_s = st.file_uploader("Pointage Excel/PDF", type=['pdf', 'xlsx'], key="up_sal")
        if st.button("Confirmer Salarié") and up_s:
            data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
            sauvegarder_donnees()
            st.success("Fiche enregistrée !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    if st.button("📊 GÉNÉRER LE RAPPORT MARBRE (PDF)"):
        st.download_button("📥 TÉLÉCHARGER LE PDF", data=generer_pdf_intelligent(tranche, data), file_name=f"Situation_{tranche}.pdf", mime="application/pdf")
    st.divider()
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
        sel = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key="c_radio")
        k_map = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        for entry in data[k_map[sel]]:
            title = f"{entry.get('Type', '')} {entry.get('Produit', '')} {entry.get('Nom', '')}"
            with st.expander(f"🛠️ {title} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                st.write(f"**Lieu/Détail :** {entry.get('Lieu') or entry.get('Détail', '')}")
                if entry.get('Fournisseur'): st.info(f"Fournisseur : {entry['Fournisseur']}")
    with c4:
        for s in data['salaries']:
            with st.expander(f"📊 {s['nom']}"):
                if s['nom'].lower().endswith('.xlsx'):
                    try:
                        df = pd.read_excel(io.BytesIO(s['content']), engine='openpyxl')
                        st.dataframe(df, use_container_width=True)
                    except: st.error("Aperçu impossible.")
                else:
                    b64 = base64.b64encode(s['content']).decode()
                    st.components.v1.html(f'<button onclick="window.open(URL.createObjectURL(new Blob([new Uint8Array(atob(\'{b64}\').split(\'\').map(c=>c.charCodeAt(0)))] , {{type:\'application/pdf\'}})), \'_blank\')" style="width:100%; padding:10px; background:#007bff; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">👁️ VOIR LE PDF</button>', height=50)
