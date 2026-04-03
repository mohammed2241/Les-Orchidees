import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION DU STOCKAGE PAR TRANCHE ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []}
    }

# --- NAVIGATION ---
st.title("🏗️ LES ORCHIDÉES")
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE LECTURE OPTIMISÉE ---
def generer_lien_telechargement(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="text-decoration:none;"><button style="background-color:#2e7d32; color:white; border:none; padding:10px; border-radius:5px;">📥 Télécharger / Ouvrir</button></a>'
    return href

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs[0]: # PLANS [cite: 3, 4]
        st.subheader(f"Dépôt de Plans - {tranche}")
        up_p = st.file_uploader("Transférer PDF ou Photos", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ CONFIRMER L'UPLOAD", type="primary"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                st.success("Document enregistré sur le portail !")

    with tabs[1]: # MARCHANDISES [cite: 7, 9]
        st.subheader("Réception Fournisseurs")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_m")
        desig = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        bl = c1.file_uploader("Photo BL", key="bl_p")
        cam = c2.file_uploader("Photo Camion", key="cam_p")
        if st.button("Valider la Réception"):
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            st.success("Réception ajoutée à l'historique !")

    with tabs[2]: # SUIVIE [cite: 11]
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec in ["Électricité", "Plomberie"]: # [cite: 12, 17]
            prods = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for p in prods:
                c_n, c_q, c_d = st.columns([2, 1, 2])
                c_n.write(f"**{p}**")
                q = c_q.number_input("Qté", min_value=0, key=f"q_{p}_{tranche}")
                d = c_d.text_input("Détails", key=f"d_{p}_{tranche}")
                if st.button(f"Valider {p}", key=f"btn_{p}"):
                    key_db = "electricite" if spec == "Électricité" else "plomberie"
                    data[key_db].append({"Produit": p, "Quantité": q, "Détail": d})
                    st.toast(f"{p} enregistré !")

        elif spec == "Marbre": # [cite: 13, 14]
            nom_m = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            bloc_m = st.text_input("N° de Bloc")
            imm_m = st.text_input("Immeuble")
            app_m = st.text_input("Appartement")
            ref_m = st.text_input("Référence utilisée")
            if st.button("Enregistrer Marbre"):
                data['marbre'].append({"Nom": nom_m, "Bloc": bloc_m, "Imm": imm_m, "App": app_m, "Réf": ref_m})
                st.success("Saisie Marbre validée !")

        elif spec == "Céramique": # 
            zone_c = st.selectbox("Type", ["Terrasse appart", "SDB", "Chambre", "Terrasse immeuble"])
            imm_c = st.text_input("Immeuble")
            etage_c = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            if st.button("Enregistrer Céramique"):
                data['ceramique'].append({"Zone": zone_c, "Immeuble": imm_c, "Étage": etage_c})
                st.success("Saisie Céramique validée !")

    with tabs[3]: # SALARIÉ [cite: 18, 19]
        up_s = st.file_uploader("Pointage XLSX/PDF", type=['xlsx', 'pdf'], key="up_s")
        if st.button("Confirmer Salarié"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                st.success("Document pointage enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    tabs_c = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs_c[0]: # [cite: 6]
        for p in data['plans']:
            col_t, col_b = st.columns([4, 2])
            col_t.write(f"📄 {p['nom']}")
            col_b.markdown(generer_lien_telechargement(p['content'], p['nom']), unsafe_allow_html=True)

    with tabs_c[1]: # [cite: 9]
        if data['marchandises']: st.dataframe(pd.DataFrame(data['marchandises']), use_container_width=True)

    with tabs_c[2]: # [cite: 14]
        spec_c = st.radio("Historique", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        key_c = {"Électricité": "electricite", "Plomberie": "plomberie", "Marbre": "marbre", "Céramique": "ceramique"}[spec_c]
        if data[key_c]: st.table(pd.DataFrame(data[key_c]))

    with tabs_c[3]: # 
        for s in data['salaries']:
            col_t, col_b = st.columns([4, 2])
            col_t.write(f"📁 {s['nom']}")
            col_b.markdown(generer_lien_telechargement(s['content'], s['nom']), unsafe_allow_html=True)
