import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- LOGO ---
st.image("https://via.placeholder.com/300x100?text=LOGO+LES+ORCHIDEES", width=300)

# --- INITIALISATION DU STOCKAGE PAR TRANCHE ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": [], "salaries": []}
    }

# --- NAVIGATION ---
st.sidebar.title("MENU PRINCIPAL")
mode = st.sidebar.radio("MODE", ["📝 SAISIE TERRAIN", "🔍 CONSULTATION"])
tranche_active = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])

# Tiroir de données pour la tranche choisie
data = st.session_state.db[tranche_active]

# --- FONCTION DE LECTURE PDF/PHOTO ---
def afficher_document(file_data, file_name):
    if file_name.lower().endswith('.pdf'):
        base64_pdf = base64.b64encode(file_data).decode('utf-8')
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="500" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.image(file_data, caption=file_name)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs[0]:
        st.subheader(f"Upload Plans - {tranche_active}")
        file = st.file_uploader("Transférer document", type=['pdf', 'jpg', 'png'], key="up_plans")
        if st.button("✅ CONFIRMER L'UPLOAD", type="primary"):
            if file:
                content = file.read()
                data['plans'].append({"nom": file.name, "bytes": content})
                st.success(f"Plan enregistré dans {tranche_active}")

    with tabs[1]:
        st.subheader("Entrée Marchandises")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_list")
        desig = st.text_input("Désignation Camion/Articles")
        c1, c2 = st.columns(2)
        bl_img = c1.file_uploader("Photo BL", type=['jpg', 'png'])
        cam_img = c2.file_uploader("Photo Camion", type=['jpg', 'png'])
        if st.button("Valider la Réception"):
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig, "Date": pd.Timestamp.now()})
            st.success("Enregistré dans l'historique local")

    with tabs[2]:
        spec = st.radio("Spécialité", ["Electricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec in ["Electricité", "Plomberie"]:
            prods = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Electricité" else ["Vasque", "Toilette", "Robinet"]
            for p in prods:
                col_img, col_txt, col_input = st.columns([1, 2, 2])
                col_img.write("🛒")
                col_txt.write(f"**{p}**")
                qte = col_input.number_input(f"Qté {p}", min_value=0, key=f"q_{p}")
                det = col_input.text_input(f"Détail {p}", key=f"d_{p}")
                if st.button(f"Valider {p}"):
                    key_db = "elec" if spec == "Electricité" else "plomb"
                    data[key_db].append({"Produit": p, "Quantité": qte, "Détail": det})
                    st.toast(f"{p} enregistré")

    with tabs[3]:
        sal_file = st.file_uploader("Excel ou PDF Pointage", type=['xlsx', 'pdf'])
        if st.button("Confirmer Salarié"):
            if sal_file:
                data['salaries'].append({"nom": sal_file.name, "bytes": sal_file.read()})
                st.success("Pointage archivé")

# ==========================================
#             MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Historique - {tranche_active}")
    tabs_c = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs_c[0]:
        if data['plans']:
            for idx, p in enumerate(data['plans']):
                col_n, col_v = st.columns([3, 1])
                col_n.write(f"📄 {p['nom']}")
                if col_v.button("👁️ Lire", key=f"read_p_{idx}"):
                    afficher_document(p['bytes'], p['nom'])
        else: st.info("Aucun plan dans cette tranche.")

    with tabs_c[1]:
        if data['marchandises']:
            st.table(pd.DataFrame(data['marchandises']))
        else: st.info("Aucune marchandise.")

    with tabs_c[2]:
        sub = st.radio("Détail par métier", ["Electricité", "Plomberie", "Marbre", "Céramique"])
        key_map = {"Electricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        if data[key_map[sub]]:
            st.table(pd.DataFrame(data[key_map[sub]]))
        else: st.info(f"Pas de données {sub} pour cette tranche.")
