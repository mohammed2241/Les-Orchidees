import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION DE BASE ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION DU STOCKAGE (SÉPARÉ PAR TRANCHE) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }

# --- BARRE LATÉRALE : NAVIGATION ---
st.sidebar.title("LES ORCHIDÉES")
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE LECTURE SÉCURISÉE ---
def generer_lien_pdf(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="text-decoration:none;"><button style="background-color:#2e7d32; color:white; border:none; padding:8px; border-radius:5px; cursor:pointer;">👁️ Ouvrir {file_name}</button></a>'

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs[0]: # PLANS
        st.subheader(f"Dépôt Plans - {tranche}")
        up_p = st.file_uploader("Upload PDF/Photos", type=['pdf', 'jpg', 'png', 'jpeg'], key=f"up_p_{tranche}")
        if st.button("✅ CONFIRMER L'UPLOAD", key=f"btn_p_{tranche}"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                st.success("Plan enregistré !")

    with tabs[1]: # MARCHANDISES
        st.subheader("Entrée Fournisseurs")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key=f"f_m_{tranche}")
        desig = st.text_input("Désignation du matériel", key=f"des_m_{tranche}")
        c1, c2 = st.columns(2)
        bl = c1.file_uploader("Photo BL", key=f"bl_{tranche}")
        cam = c2.file_uploader("Photo Camion", key=f"cam_{tranche}")
        if st.button("Valider la Réception", key=f"btn_m_{tranche}"):
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            st.success("Réception ajoutée à l'historique !")

    with tabs[2]: # SUIVIE
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key=f"spec_{tranche}")
        
        if spec in ["Électricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for item in items:
                c_n, c_q, c_d = st.columns([2, 1, 2])
                c_n.write(f"**{item}**")
                q = c_q.number_input("Qté", min_value=0, key=f"q_{item}_{tranche}")
                d = c_d.text_input("Détails", key=f"d_{item}_{tranche}")
                if st.button(f"Valider {item}", key=f"btn_{item}_{tranche}"):
                    key_db = "elec" if spec == "Électricité" else "plomb"
                    data[key_db].append({"Produit": item, "Quantité": q, "Détail": d})
                    st.toast(f"{item} enregistré !")

        elif spec == "Marbre":
            pers = st.selectbox("Intervenant", ["FETTAH", "Simo"], key=f"m_pers_{tranche}")
            bloc = st.text_input("N° de Bloc", key=f"m_bloc_{tranche}")
            imm = st.text_input("Immeuble", key=f"m_imm_{tranche}")
            app = st.text_input("Appartement", key=f"m_app_{tranche}")
            ref = st.text_input("Référence utilisée", key=f"m_ref_{tranche}")
            if st.button("Enregistrer Marbre", key=f"btn_marbre_{tranche}"):
                data['marbre'].append({"Nom": pers, "Bloc": bloc, "Imm": imm, "App": app, "Réf": ref})
                st.success("Saisie Marbre validée !")

        elif spec == "Céramique":
            zone = st.selectbox("Type", ["Terrasse appart", "SDB", "Chambre", "Terrasse immeuble"], key=f"c_zone_{tranche}")
            imm_c = st.text_input("Immeuble", key=f"c_imm_{tranche}")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"], key=f"c_etage_{tranche}")
            if st.button("Enregistrer Céramique", key=f"btn_ceram_{tranche}"):
                data['ceram'].append({"Zone": zone, "Immeuble": imm_c, "Étage": etage})
                st.success("Saisie Céramique validée !")

    with tabs[3]: # SALARIÉ
        up_s = st.file_uploader("Fichier Pointage (XLSX/PDF)", type=['xlsx', 'pdf'], key=f"up_s_{tranche}")
        if st.button("Confirmer Salarié", key=f"btn_s_{tranche}"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
                st.success("Document enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    tabs_c = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs_c[0]: # CONSULTATION PLANS
        for idx, p in enumerate(data['plans']):
            col_t, col_b = st.columns([4, 2])
            col_t.write(f"📄 {p['nom']}")
            col_b.markdown(generer_lien_pdf(p['content'], p['nom']), unsafe_allow_html=True)

    with tabs_c[1]: # CONSULTATION MARCHANDISES
        if data['marchandises']: 
            st.dataframe(pd.DataFrame(data['marchandises']), use_container_width=True)

    with tabs_c[2]: # CONSULTATION SUIVIE
        spec_c = st.radio("Historique", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True, key=f"cons_{tranche}")
        key_c = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}[spec_c]
        if data[key_c]: 
            st.table(pd.DataFrame(data[key_c]))
