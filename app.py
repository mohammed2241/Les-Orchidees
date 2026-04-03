import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION DES TRANCHES ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []}
    }

# --- NAVIGATION ---
st.title("🏗️ LES ORCHIDÉES") [cite: 1, 2]
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"]) [cite: 20]
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"]) [cite: 2]
data = st.session_state.db[tranche] [cite: 5]

# --- FONCTION D'OUVERTURE DIRECTE (SANS TÉLÉCHARGEMENT) ---
def visionneuse_directe(file_bytes, file_name):
    if file_name.lower().endswith('.pdf'):
        base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
        # PDF intégré dans une fenêtre ajustable
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        # Affichage direct de l'image
        st.image(file_bytes, use_container_width=True)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"]) [cite: 2, 20]

    with tabs[0]: # PLANS [cite: 3]
        st.subheader(f"Dépôt Plans - {tranche}")
        up_p = st.file_uploader("Upload PDF/Photos", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p") [cite: 4]
        if st.button("✅ CONFIRMER L'UPLOAD", type="primary"): [cite: 6]
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                st.success("Plan enregistré !")

    with tabs[1]: # MARCHANDISES [cite: 7]
        st.subheader("Réception")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_m") [cite: 8]
        desig = st.text_input("Désignation") [cite: 9]
        c1, c2 = st.columns(2)
        bl = c1.file_uploader("Photo BL", key="bl_p") [cite: 9]
        cam = c2.file_uploader("Photo Camion", key="cam_p") [cite: 9]
        if st.button("Valider la Réception"): [cite: 9]
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            st.success("Réception ajoutée !") [cite: 9]

    with tabs[2]: # SUIVIE [cite: 11]
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec in ["Électricité", "Plomberie"]: [cite: 12, 17]
            prods = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for p in prods:
                c_n, c_q, c_d = st.columns([2, 1, 2])
                c_n.write(f"**{p}**")
                q = c_q.number_input("Qté", min_value=0, key=f"q_{p}_{tranche}") [cite: 13]
                d = c_d.text_input("Détails", key=f"d_{p}_{tranche}") [cite: 13]
                if st.button(f"Valider {p}", key=f"btn_{p}"): [cite: 13]
                    key_db = "electricite" if spec == "Électricité" else "plomberie"
                    data[key_db].append({"Produit": p, "Quantité": q, "Détail": d})
                    st.toast(f"{p} enregistré !")

        elif spec == "Marbre": [cite: 13]
            nom_m = st.selectbox("Intervenant", ["FETTAH", "Simo"]) [cite: 13]
            bloc_m = st.text_input("N° de Bloc") [cite: 13]
            imm_m = st.text_input("Immeuble") [cite: 13]
            app_m = st.text_input("Appartement") [cite: 13]
            ref_m = st.text_input("Référence utilisée") [cite: 13]
            if st.button("Enregistrer Marbre"): [cite: 13, 14]
                data['marbre'].append({"Nom": nom_m, "Bloc": bloc_m, "Imm": imm_m, "App": app_m, "Réf": ref_m})
                st.success("Marbre validé !")

        elif spec == "Céramique": [cite: 15]
            zone_c = st.selectbox("Type", ["Terrasse appart", "SDB", "Chambre", "Terrasse immeuble"]) [cite: 15]
            imm_c = st.text_input("Immeuble") [cite: 16]
            etage_c = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"]) [cite: 16]
            if st.button("Enregistrer Céramique"): [cite: 16]
                data['ceramique'].append({"Zone": zone_c, "Immeuble": imm_c, "Étage": etage_c})
                st.success("Céramique validée !")

    with tabs[3]: # SALARIÉ [cite: 18]
        up_s = st.file_uploader("Pointage XLSX/PDF", type=['xlsx', 'pdf'], key="up_s") [cite: 19]
        if st.button("Confirmer Salarié"): [cite: 20]
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                st.success("Pointage enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}") [cite: 20]
    tabs_c = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"]) [cite: 20]

    with tabs_c[0]: # MIROIR PLANS
        for idx, p in enumerate(data['plans']):
            with st.expander(f"📄 Voir le plan : {p['nom']}"): # Ouverture en un clic
                visionneuse_directe(p['content'], p['nom'])

    with tabs_c[1]: # MIROIR MARCHANDISES
        if data['marchandises']: 
            st.dataframe(pd.DataFrame(data['marchandises']), use_container_width=True)

    with tabs_c[2]: # MIROIR SUIVIE
        spec_c = st.radio("Historique Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        key_c = {"Électricité": "electricite", "Plomberie": "plomberie", "Marbre": "marbre", "Céramique": "ceramique"}[spec_c]
        if data[key_c]: 
            st.table(pd.DataFrame(data[key_c]))

    with tabs_c[3]: # MIROIR SALARIÉ
        for idx, s in enumerate(data['salaries']):
            with st.expander(f"📁 Ouvrir Pointage : {s['nom']}"):
                visionneuse_directe(s['content'], s['nom'])
