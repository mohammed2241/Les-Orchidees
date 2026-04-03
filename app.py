import streamlit as st
import pandas as pd
import base64
import os
import pickle
import io
from fpdf import FPDF # Ajouter fpdf dans requirements.txt

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

# --- GÉNÉRATION DU PDF STRUCTURÉ ---
def generer_pdf_situation(tranche_nom, data_tranche):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"SITUATION DES TRAVAUX - {tranche_nom.upper()}", ln=True, align='C')
    pdf.ln(10)

    categories = {
        "MARBRE": "marbre",
        "ÉLECTRICITÉ": "elec",
        "PLOMBERIE": "plomb",
        "CÉRAMIQUE": "ceram"
    }

    for titre, key in categories.items():
        if data_tranche[key]:
            pdf.set_font("Arial", 'B', 14)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(190, 10, titre, ln=True, fill=True)
            pdf.ln(2)
            
            pdf.set_font("Arial", '', 10)
            # Entêtes selon la catégorie
            if key == "marbre":
                for item in data_tranche[key]:
                    txt = f"Date: {item['Date']} | Intervenant: {item['Nom']} | Type: {item['Type']} | Lieu: {item['Lieu']}"
                    if item.get('Fournisseur'): txt += f" | Fourn: {item['Fournisseur']}"
                    pdf.multi_cell(190, 8, txt, border=1)
            else:
                for item in data_tranche[key]:
                    nom_tache = item.get('Produit') or item.get('Type') or "Tâche"
                    detail = item.get('Lieu') or item.get('Détail') or ""
                    qte = f" | Qté: {item['Qté']}" if 'Qté' in item else ""
                    pdf.multi_cell(190, 8, f"Date: {item['Date']} | {nom_tache} | {detail}{qte}", border=1)
            pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin-1')

# --- NAVIGATION ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t1: # PLANS
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees()
            st.success("Plan enregistré !")
            
    with t2: # MARCHANDISES
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

    with t3: # SUIVI MARBRE DÉVELOPPÉ
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec in ["Électricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for i in items:
                col1, col2, col3 = st.columns([2, 1, 2])
                q = col2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = col3.text_input("Détails", key=f"d_{i}")
                p_suivi = st.file_uploader(f"Photo {i}", type=['jpg','jpeg','png'], key=f"p_{i}")
                if st.button(f"Enregistrer {i}", key=f"btn_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit": i, "Qté": q, "Détail": dt, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_suivi.getvalue() if p_suivi else None})
                    sauvegarder_donnees()
                    st.toast(f"{i} validé !")

        elif spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"], key="m_inter")
            type_m = st.selectbox("Type de Marbre", ["Gris Bold", "White Sand", "Blanc Carrara"], key="m_type")
            fourn = None
            ref_carrara = None
            if type_m == "Blanc Carrara":
                fourn = st.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"], key="m_fourn")
                ref_carrara = st.text_input("Référence (Lot/Bloc)", key="m_ref")
            imm = st.text_input("Immeuble", key="m_imm")
            etage = None
            appt = None
            if type_m != "White Sand":
                etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"], key="m_etage")
                if type_m == "Blanc Carrara":
                    appt = st.text_input("Appartement", key="m_appt")
            p_m = st.file_uploader("Photo Marbre", type=['jpg','jpeg','png'], key="p_m_up")
            if st.button("Valider Saisie Marbre"):
                lieu = f"Imm {imm}"
                if etage: lieu += f" - {etage}"
                if appt: lieu += f" - Appt {appt}"
                if type_m == "White Sand": lieu += " (Façade)"
                data['marbre'].append({"Nom": interv, "Type": type_m, "Fournisseur": fourn, "Référence": ref_carrara, "Lieu": lieu, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_m.getvalue() if p_m else None})
                sauvegarder_donnees()
                st.success(f"Saisie {type_m} enregistrée !")

        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            im_c = st.text_input("Immeuble")
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_c = st.file_uploader("Photo Céramique", type=['jpg','jpeg','png'], key="p_c_up")
            if st.button("Valider Céramique"):
                data['ceram'].append({"Type": z, "Lieu": f"Imm {im_c} - Etage {et}", "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_c.getvalue() if p_c else None})
                sauvegarder_donnees()
                st.success("Céramique OK")

    with t4: # SALARIÉ
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
    
    # --- BOUTON GÉNÉRATION RAPPORT PDF ---
    pdf_content = generer_pdf_situation(tranche, data)
    st.download_button(
        label="📥 TÉLÉCHARGER LE RAPPORT DE SITUATION (PDF)",
        data=pdf_content,
        file_name=f"Situation_{tranche}.pdf",
        mime="application/pdf"
    )
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
            with st.expander(f"🛠️ {title} - {entry.get('Lieu') or entry.get('Détail', '')} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                if entry.get('Fournisseur'): st.info(f"Fournisseur : {entry['Fournisseur']}")
                if entry.get('Référence'): st.warning(f"Référence : {entry['Référence']}")

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
