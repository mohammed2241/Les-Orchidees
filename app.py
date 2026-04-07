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
    tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
    data = st.session_state.db[tranche]
    
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])
    
    with tabs[0]:
        up = st.file_uploader("Upload Plan", type=['pdf','jpg','png','jpeg'])
        if st.button("Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue(), "type": up.type})
            sauvegarder_donnees(); st.success("Plan enregistré !")
            
    with tabs[1]:
        f = st.selectbox("Fournisseur", cfg["fournisseurs"])
        d = st.text_area("Désignation complète de la marchandise")
        p_bl = st.file_uploader("Photo du Bon de Livraison", key="bl_saisie")
        if st.button("Valider la Réception"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m/%Y"), "photo_bl": p_bl.getvalue() if p_bl else None})
            sauvegarder_donnees(); st.success("Marchandise enregistrée dans le journal !")

    with tabs[2]:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type", ["Gris Bold", "White Sand", "Blanc Carrara"])
            
            fourn, ref_v, surf, fini, sous_type_bc, appt = None, None, None, None, None, None
            
            if type_m == "Blanc Carrara":
                sous_type_bc = st.selectbox("Élément Blanc Carrara", ["Dallage", "Seuil", "Niche", "Les douches"])
                
                if sous_type_bc == "Dallage":
                    appt = st.text_input("N° Appartement") # <-- RESTAURÉ ICI !
                    c1, c2 = st.columns(2)
                    fourn = c1.selectbox("Fournisseur Marbre", ["Graziani", "Caro Colombi", "Lorenzoni", "MARMI BIANCO"])
                    ref_v = c2.text_input("Référence (Lot/Bloc)")
                    surf = st.number_input("Surface (m²)", min_value=0.0)
                    fini = st.selectbox("Finition", ["Poli", "Adouci", "Brut"])
            
            imm = st.text_input("Immeuble")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "5ème"])
            p_m = st.file_uploader("Photo de la pose")
            
            if st.button("Enregistrer Marbre"):
                lieu = f"Imm {imm} - {etage}"
                if appt:
                    lieu += f" - Appt {appt}" # <-- AJOUTÉ DANS LE LIEU FINAL
                
                type_final = f"Blanc Carrara - {sous_type_bc}" if type_m == "Blanc Carrara" else type_m
                
                data['marbre'].append({"Nom": interv, "Type": type_final, "Fournisseur": fourn, "Référence": ref_v, "Lieu": lieu, "Surface": surf, "Finition": fini, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_m.getvalue() if p_m else None})
                sauvegarder_donnees(); st.success("Saisie Marbre OK")
        
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Terrasse de l'immeuble"])
            im = st.text_input("Immeuble")
            
            if z != "Terrasse de l'immeuble":
                et = st.selectbox("Etage", ["RDC","1","2","3","4","5"])
            else:
                et = None
                
            p_c = st.file_uploader("Photo Céramique")
            if st.button("Enregistrer Céramique"):
                lieu_c = f"Imm {im} - {et}" if et else f"Imm {im}"
                data['ceram'].append({"Type":z, "Lieu":lieu_c, "Date":pd.Timestamp.now().strftime("%d/%m"), "photo":p_c.getvalue() if p_c else None})
                sauvegarder_donnees(); st.success("Céramique OK")
        
        else: # Électricité / Plomberie
            produits_dispo = cfg["produits_elec"] if spec == "Électricité" else cfg["produits_plomb"]
            
            p_sel = st.selectbox("Sélectionner le produit", produits_dispo)
            c1, c2 = st.columns(2)
            q = c1.number_input("Qté", min_value=1)
            dt = c2.text_input("Détails / Lieu d'installation (ex: Imm 1 - 5ème)")
            p_s = st.file_uploader(f"Photo (optionnel)", key="photo_ep")
            
            if st.button(f"Valider {spec}"):
                k = "elec" if spec == "Électricité" else "plomb"
                data[k].append({"Produit": p_sel, "Qté": q, "Détail": dt, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_s.getvalue() if p_s else None})
                sauvegarder_donnees(); st.success("Enregistré avec succès !")

    with tabs[3]:
        up_doc = st.file_uploader("Fichier Document", type=['pdf', 'xlsx', 'jpg', 'png'])
        titre_doc = st.text_input("Titre du document")
        if st.button("Ajouter Document") and up_doc:
            data['documents'].append({"nom": titre_doc if titre_doc else up_doc.name, "content": up_doc.getvalue(), "type": up_doc.type, "filename": up_doc.name})
            sauvegarder_donnees(); st.success("Document ajouté !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
elif mode == "🔍 CONSULTATION":
    tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
    data = st.session_state.db[tranche]
    
    st.header(f"🔍 Consultation - {tranche}")
    ctabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "📂 DOCUMENTS"])

    with ctabs[0]:
        for i, p in enumerate(data['plans']):
            with st.expander(f"📄 {p['nom']}"):
                st.download_button("Ouvrir", data=p['content'], file_name=p['nom'], key=f"dl_p_{i}")
                if p.get('type','').startswith('image'): st.image(p['content'])
                if st.checkbox("Confirmer la suppression", key=f"conf_p_{i}"):
                    if st.button("🗑️ Supprimer", key=f"del_p_{i}"):
                        data['plans'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[1]:
        st.download_button("📥 Télécharger Rapport Marchandises (PDF)", data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), file_name=f"Marchandises_{tranche}.pdf", key="btn_pdf_march")
        st.divider()
        for i, m in enumerate(data['marchandises']):
            with st.expander(f"📦 {m.get('Fournisseur')} - {m.get('Date')}"):
                st.write(f"**Désignation :** {m.get('Désignation')}")
                if m.get('photo_bl'): st.image(m['photo_bl'], width=400, caption="Bon de Livraison")
                if st.checkbox("Confirmer la suppression", key=f"conf_m_{i}"):
                    if st.button("🗑️ Supprimer", key=f"del_m_{i}"):
                        data['marchandises'].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[2]:
        m_sel = st.radio("Filtrer par métier", ["Marbre", "Céramique", "Électricité", "Plomberie"], horizontal=True)
        k_map = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}
        
        st.download_button(f"📥 Télécharger Rapport {m_sel} (PDF)", data=creer_pdf_section(m_sel.upper(), data[k_map[m_sel]], k_map[m_sel]), file_name=f"Rapport_{m_sel}_{tranche}.pdf", key="btn_pdf_suivi")
        st.divider()
        
        for i, entry in enumerate(data[k_map[m_sel]]):
            titre_exp = f"🛠️ {entry.get('Type', entry.get('Produit'))}"
            if entry.get('Nom'): titre_exp += f" - {entry['Nom']}"
            titre_exp += f" ({entry.get('Date')})"
            
            with st.expander(titre_exp):
                if entry.get('Qté'): st.write(f"**Quantité :** {entry['Qté']}")
                if entry.get('photo'): st.image(entry['photo'], width=450)
                st.write(f"**Lieu/Détail :** {entry.get('Lieu', entry.get('Détail', ''))}")
                if entry.get('Surface'): st.info(f"Surface: {entry['Surface']} m2 | Finition: {entry.get('Finition')}")
                if entry.get('Fournisseur'): st.write(f"Provenance: {entry['Fournisseur']} | Réf: {entry.get('Référence')}")
                
                if st.checkbox("Confirmer la suppression", key=f"conf_s_{m_sel}_{i}"):
                    if st.button("🗑️ Supprimer", key=f"del_s_{m_sel}_{i}"):
                        data[k_map[m_sel]].pop(i); sauvegarder_donnees(); st.rerun()

    with ctabs[3]:
        for i, d in enumerate(data['documents']):
            with st.expander(f"📑 {d['nom']}"):
                st.download_button("Ouvrir", data=d['content'], file_name=d.get('filename', d['nom']), key=f"dl_d_{i}")
                if d.get('filename', '').lower().endswith('.xlsx'):
                    try: st.dataframe(pd.read_excel(io.BytesIO(d['content']), engine='openpyxl'), use_container_width=True)
                    except: pass
                if st.checkbox("Confirmer la suppression", key=f"conf_d_{i}"):
                    if st.button("🗑️ Supprimer", key=f"del_d_{i}"):
                        data['documents'].pop(i); sauvegarder_donnees(); st.rerun()
