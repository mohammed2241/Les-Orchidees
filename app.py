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

# --- DESIGN & LOGO ---
st.title("🏗️ LES ORCHIDÉES")
st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"], key="mode")
st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"], key="tranche_active")

mode = st.session_state.mode
tranche = st.session_state.tranche_active
data = st.session_state.db[tranche]

# --- FONCTION DE LECTURE ---
def afficher_fichier(file_bytes, file_name):
    if file_name.lower().endswith('.pdf'):
        base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.image(file_bytes)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs[0]: # PLANS
        st.subheader(f"Upload Plans - {tranche}")
        up_p = st.file_uploader("Transférer PDF/Photo", type=['pdf', 'jpg', 'png'], key="up_p")
        if st.button("✅ CONFIRMER L'UPLOAD"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.read()})
                st.success("Plan enregistré !")

    with tabs[1]: # MARCHANDISES
        st.subheader("Entrée Marchandises")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_m")
        desig = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        bl = c1.file_uploader("Photo BL", key="up_bl")
        cam = c2.file_uploader("Photo Camion", key="up_cam")
        if st.button("Valider la Réception"):
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig})
            st.success("Réception archivée !")

    with tabs[2]: # SUIVIE
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec == "Électricité" or spec == "Plomberie":
            prods = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for p in prods:
                col_n, col_q, col_d = st.columns([2, 1, 2])
                col_n.write(f"**{p}**")
                q = col_q.number_input("Qté", min_value=0, key=f"q_{p}_{tranche}")
                d = col_d.text_input("Détails", key=f"d_{p}_{tranche}")
                if st.button(f"Enregistrer {p}"):
                    key_db = "electricite" if spec == "Électricité" else "plomberie"
                    data[key_db].append({"Produit": p, "Quantité": q, "Détail": d})
                    st.toast(f"{p} validé")

        elif spec == "Marbre":
            nom_m = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            bloc_m = st.text_input("N° de Bloc")
            imm_m = st.text_input("Immeuble")
            app_m = st.text_input("Appartement")
            ref_m = st.text_input("Référence utilisée")
            if st.button("Valider Marbre"):
                data['marbre'].append({"Nom": nom_m, "Bloc": bloc_m, "Imm": imm_m, "App": app_m, "Réf": ref_m})
                st.success("Saisie Marbre enregistrée !")

        elif spec == "Céramique":
            zone_c = st.selectbox("Type", ["Terrasse appart", "SDB", "Chambre", "Terrasse immeuble"])
            imm_c = st.text_input("Immeuble")
            etage_c = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            if st.button("Valider Céramique"):
                data['ceramique'].append({"Zone": zone_c, "Immeuble": imm_c, "Étage": etage_c})
                st.success("Saisie Céramique enregistrée !")

    with tabs[3]: # SALARIÉ
        up_s = st.file_uploader("Pointage XLSX/PDF", type=['xlsx', 'pdf'], key="up_s")
        if st.button("Confirmer Salarié"):
            if up_s:
                data['salaries'].append({"nom": up_s.name, "content": up_s.read()})
                st.success("Document salarié ajouté !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    tabs_c = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs_c[0]:
        for idx, p in enumerate(data['plans']):
            col_t, col_b = st.columns([4, 1])
            col_t.write(f"📄 {p['nom']}")
            if col_b.button("Lire", key=f"read_p_{idx}"):
                afficher_fichier(p['content'], p['nom'])

    with tabs_c[1]:
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with tabs_c[2]:
        spec_c = st.radio("Historique Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], key="spec_c")
        key_c = {"Électricité": "electricite", "Plomberie": "plomberie", "Marbre": "marbre", "Céramique": "ceramique"}[spec_c]
        if data[key_c]: st.table(pd.DataFrame(data[key_c]))

    with tabs_c[3]:
        for idx, s in enumerate(data['salaries']):
            col_t, col_b = st.columns([4, 1])
            col_t.write(f"📁 {s['nom']}")
            if col_b.button("Lire", key=f"read_s_{idx}"):
                afficher_fichier(s['content'], s['nom'])
