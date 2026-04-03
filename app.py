import streamlit as st
import pandas as pd
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées PRO", layout="wide")

# --- INITIALISATION SÉCURISÉE ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "Tranche 3": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []},
        "Tranche 4": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []},
        "Tranche 5": {"plans": [], "marchandises": [], "electricite": [], "plomberie": [], "marbre": [], "ceramique": [], "salaries": []}
    }

# --- NAVIGATION ---
st.sidebar.title("PROJET LES ORCHIDÉES")
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE DE TERRAIN", "🔍 CONSULTATION HISTORIQUE"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE LECTURE STABLE ---
def ouvrir_document(file_bytes, file_name, key):
    try:
        if file_name.lower().endswith('.pdf'):
            base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
            # Utilisation d'un lien HTML pour ouvrir sans faire planter le script
            pdf_link = f'<a href="data:application/pdf;base64,{base64_pdf}" target="_blank" style="text-decoration:none; background-color:#2e7d32; color:white; padding:10px; border-radius:5px;">📂 Cliquer ici pour ouvrir le PDF : {file_name}</a>'
            st.markdown(pdf_link, unsafe_allow_html=True)
        else:
            st.image(file_bytes, caption=file_name)
    except Exception as e:
        st.error(f"Erreur d'affichage : {e}")

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE DE TERRAIN":
    tabs = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVIE", "👥 SALARIÉ"])

    with tabs[0]: # PLANS
        st.subheader(f"Dépôt de Documents - {tranche}")
        up_p = st.file_uploader("Transférer PDF ou Photos", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p_unique")
        if st.button("✅ CONFIRMER L'UPLOAD", type="primary"):
            if up_p:
                data['plans'].append({"nom": up_p.name, "content": up_p.getvalue()})
                st.success(f"Plan '{up_p.name}' ajouté à la {tranche} !")

    with tabs[1]: # MARCHANDISES
        st.subheader("Réception de Marchandises")
        fourn = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"], key="f_select")
        desig = st.text_input("Désignation du matériel")
        col1, col2 = st.columns(2)
        bl = col1.file_uploader("Photo du BL", key="up_bl_unique")
        cam = col2.file_uploader("Photo du Camion", key="up_cam_unique")
        if st.button("Valider la Réception"):
            data['marchandises'].append({"Fournisseur": fourn, "Désignation": desig, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")})
            st.success("Réception enregistrée dans l'historique !")

    with tabs[2]: # SUIVIE
        spec = st.radio("Spécialité", ["Electricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        
        if spec in ["Electricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Electricité" else ["Vasque", "Toilette", "Robinet"]
            for item in items:
                c1, c2, c3 = st.columns([2,1,2])
                c1.write(f"**{item}**")
                q = c2.number_input("Qté", min_value=0, key=f"q_{item}_{tranche}")
                d = c3.text_input("Détails", key=f"d_{item}_{tranche}")
                if st.button(f
