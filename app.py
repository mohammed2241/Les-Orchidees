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
        # FORMAT VALIDÉ : Groupé par intervenant
        df = pd.DataFrame(data_list)
        if not df.empty and 'Nom' in df.columns:
            for inter, group in df.groupby('Nom'):
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 10, f"Intervenant : {inter}", ln=True)
                
                cols = ['DATE', 'TYPE', 'LOT/REF', 'LIEU/APPT', 'M2']
                w = [25, 35, 35, 65, 30]
                for i, c in enumerate(cols): pdf.cell(w[i], 8, c, 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_font('Arial', '', 8)
                for _, r in group.iterrows():
                    pdf.cell(25, 7, str(r.get('Date', '-')), 1)
                    pdf.cell(35, 7, str(r.get('Type', '-')), 1)
                    pdf.cell(35, 7, str(r.get('Référence', '-')) if r.get('Référence') else '-', 1)
                    pdf.cell(65, 7, str(r.get('Lieu', '-'))[:45], 1)
                    pdf.cell(30, 7, str(r.get('Surface', '-')), 1, 1)
                pdf.ln(5)

    else: # Elec, Plomb, Ceram
        pdf.cell(30, 10, 'DATE', 1, 0, 'C', True)
        pdf.cell(50, 10, 'PRODUIT', 1, 0, 'C', True)
        pdf.cell(110, 10, 'DETAILS / LIEU', 1, 1, 'C', True)
        pdf.set_font('Arial', '', 9)
        for r in data_list:
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Produit', r.get('Type', '-'))), 1)
            pdf.cell(110, 8, str(r.get('Lieu', r.get('Détail', '-'))), 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])
    
    with tabs[0]: # Plans
        up = st.file_uploader("Upload Plan", type=['pdf','jpg','png','jpeg'])
        if st.button("Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue(), "type": up.type})
            sauvegarder_donnees(); st.success("Plan enregistré !")
            
    with tabs[1]: # Marchandises
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans", "Autre"])
        d = st.text_area("Désignation complète de la marchandise")
        p_bl = st.file_uploader("Photo du Bon de Livraison", key="bl_saisie")
        if st.button("Valider la Réception"):
            data['marchandises'].append({
                "Fournisseur": f, "Désignation": d, 
                "Date": pd.Timestamp.now().strftime("%d/%m/%Y"), 
                "photo_bl": p_bl.getvalue() if p_bl else None
            })
            sauvegarder_donnees(); st.success("Marchandise enregistrée dans le journal !")

    with tabs[2]: # Suivi métiers
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            fourn, ref_v, appt, surf, fini = None, None, None, 0.0, "Poli"
            
            if type_m == "Blanc Carrara":
                c1, c2 = st.columns(2)
                fourn = c1.selectbox("Fournisseur", ["Graziani", "Caro Colombi", "Lorenzoni"])
                ref_v = c2.text_input("Référence (Lot/Bloc)")
                appt = st.text_input("N° Appartement")
                surf = st.number_input("Surface (m²)", min_value=0.0)
                fini = st.selectbox("Finition", ["Poli", "Adouci", "Brut"])
            
            imm = st.text_input("Immeuble")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_m = st.file_uploader("Photo de la pose")
            
            if st.button("Enregistrer Marbre"):
                lieu = f"Imm {imm} - {etage}"
                if appt: lieu += f" - Appt {appt}"
                data['marbre'].append({
                    "Nom": interv, "Type": type_m, "Fournisseur": fourn, 
                    "Référence": ref_v, "Lieu": lieu, "Surface": surf, 
                    "Finition": fini, "Date": pd.Timestamp.now().strftime("%d/%m"), 
                    "photo": p_m.getvalue() if p_m else None
                })
                sauvegarder_donnees(); st.success("Saisie Marbre OK")
        
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            im = st.text_input("Immeuble")
            et = st.selectbox("Etage", ["RDC","1","2","3","4"])
            p_c = st.file_uploader("Photo Céramique")
            if st.button("Enregistrer Céramique"):
                data['ceram'].append({"Type":z, "Lieu":f"Imm {im} - {et}", "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_c.getvalue() if p_c else None})
                sauvegarder_donnees(); st.success("Céramique OK")
        else:
            items = ["Spot", "Prise TV", "Tableau"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinetterie"]
            for i in items:
                c1, c2, c3 = st.columns([2,1,2])
                q = c2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = c1.text_input(f"Détails {i}", key=f"d_{i}")
                p_s = c3.file_uploader(f"Photo {i}", key=f"ps_{i}")
                if st.button(f"Valider {i}", key=f"b_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit":i, "Qté":q, "Détail":dt, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo": p_s.getvalue() if p_s else None})
                    sauvegarder_donnees(); st.toast(f"{i} Enregistré")

    with tabs[3]: # Documents
        up_doc = st.file_uploader("Fichier Document", type=['pdf', 'xlsx', 'jpg', 'png'])
        titre_doc = st.text_input("Titre du document")
        if st.button("Ajouter Document") and up_doc:
            data['documents'].append({"nom": titre_doc if titre_doc else up_doc.name, "content": up_doc.getvalue(), "type": up_doc.type, "filename": up_doc.name})
            sauvegarder_donnees(); st.success("Document ajouté !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else: 
    st.header(f"🔍 Consultation - {tranche}")
    ctabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])

    with ctabs[0]: # Plans
        for i, p in enumerate(data['plans']):
            with st.expander(f"📄 {p['nom']}"):
                st.download_button("Ouvrir", data=p['content'], file_name=p['nom'], key=f"dl_p_{i}")
                if p.get('type','').startswith('image'): st.image(p['content'])
                if st.checkbox("Confirmer la suppression", key=f"conf_p_{i}"):
                    if st.button("🗑️ Supprimer ce plan", key=f"del_p_{i}"):
                        data['plans'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[1]: # Marchandises
        st.download_button("📥 Télécharger Rapport Marchandises (PDF)", 
                           data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), 
                           file_name=f"Marchandises_{tranche}.pdf", key="btn_pdf_march")
        st.divider()
        for i, m in enumerate(data['marchandises']):
            with st.expander(f"📦 {m.get('Fournisseur')} - {m.get('Date')}"):
                st.write(f"**Désignation :** {m.get('Désignation')}")
                if m.get('photo_bl'): st.image(m['photo_bl'], width=400, caption="Bon de Livraison")
                if st.checkbox("Confirmer la suppression", key=f"conf_m_{i}"):
                    if st.button("🗑️ Supprimer cette réception", key=f"del_m_{i}"):
                        data['marchandises'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[2]: # Suivi métiers
        m_sel = st.radio("Filtrer par métier", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        k_map = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}
        
        st.download_button(f"📥 Télécharger Rapport {m_sel} (PDF)", 
                           data=creer_pdf_section(m_sel.upper(), data[k_map[m_sel]], k_map[m_sel]), 
                           file_name=f"Rapport_{m_sel}_{tranche}.pdf", key="btn_pdf_suivi")
        st.divider()
        
        for i, entry in enumerate(data[k_map[m_sel]]):
            with st.expander(f"🛠️ {entry.get('Type', entry.get('Produit'))} - {entry.get('Nom', '')} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=450)
                st.write(f"**Lieu :** {entry.get('Lieu', entry.get('Détail', ''))}")
                if entry.get('Surface'): st.info(f"Surface: {entry['Surface']} m2 | Finition: {entry.get('Finition')}")
                if entry.get('Fournisseur'): st.write(f"Provenance: {entry['Fournisseur']} | Réf: {entry.get('Référence')}")
                
                if st.checkbox("Confirmer la suppression", key=f"conf_s_{m_sel}_{i}"):
                    if st.button("🗑️ Supprimer cette entrée", key=f"del_s_{m_sel}_{i}"):
                        data[k_map[m_sel]].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[3]: # Documents
        for i, d in enumerate(data['documents']):
            with st.expander(f"📑 {d['nom']}"):
                st.download_button("Ouvrir", data=d['content'], file_name=d.get('filename', d['nom']), key=f"dl_d_{i}")
                if d.get('filename', '').lower().endswith('.xlsx'):
                    try:
                        df = pd.read_excel(io.BytesIO(d['content']), engine='openpyxl')
                        st.dataframe(df, use_container_width=True)
                    except: pass
                if st.checkbox("Confirmer la suppression", key=f"conf_d_{i}"):
                    if st.button("🗑️ Supprimer ce document", key=f"del_d_{i}"):
                        data['documents'].pop(i); sauvegarder_donnees(); st.rerun()
