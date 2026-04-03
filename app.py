import streamlit as st
import pandas as pd
import base64
import os
import pickle

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
                return data
        except: return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

# --- FONCTION D'OUVERTURE FORCEE (JS BLOB) ---
def bouton_ouvrir_onglet(file_bytes, file_name, label="👁️ VOIR LE DOCUMENT"):
    b64 = base64.b64encode(file_bytes).decode()
    mime_type = "application/pdf" if file_name.lower().endswith('.pdf') else "image/jpeg"
    
    # Script JavaScript pour contourner le blocage "about:blank#blocked"
    js_code = f"""
    <script>
    function openDoc() {{
        var byteCharacters = atob("{b64}");
        var byteNumbers = new Array(byteCharacters.length);
        for (var i = 0; i < byteCharacters.length; i++) {{
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }}
        var byteArray = new Uint8Array(byteNumbers);
        var blob = new Blob([byteArray], {{type: "{mime_type}"}});
        var fileURL = URL.createObjectURL(blob);
        window.open(fileURL, '_blank');
    }}
    </script>
    <button onclick="openDoc()" style="
        background-color: #007bff; 
        color: white; 
        border: none; 
        padding: 12px 24px; 
        border-radius: 8px; 
        cursor: pointer; 
        font-weight: bold;
        width: 100%;
        display: block;
    ">
        {label}
    </button>
    """
    st.components.v1.html(js_code, height=60)

# --- NAVIGATION ---
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE (Simplifié)
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t1:
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="u_p")
        if st.button("✅ Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees()
            st.success("Plan enregistré !")
            
    with t2:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        if st.button("Valider Marchandise"):
            data['marchandises'].append({"Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m")})
            sauvegarder_donnees()
            st.success("OK")

    with t3:
        m = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True)
        l = st.text_input("Détails (Immeuble/Appart)")
        if st.button("Enregistrer Suivi"):
            key = "marbre" if m == "Marbre" else "ceram"
            data[key].append({"Métier": m, "Détails": l})
            sauvegarder_donnees()
            st.success("Enregistré")

    with t4:
        up_s = st.file_uploader("Pointage", type=['pdf', 'xlsx'], key="u_s")
        if st.button("Confirmer Salarié") and up_s:
            data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
            sauvegarder_donnees()
            st.success("Pointage enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"Consultation {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for p in data['plans']:
            with st.expander(f"📁 {p['nom']}"):
                bouton_ouvrir_onglet(p['content'], p['nom'], "OUVRIR DANS UN NOUVEL ONGLET")
                st.download_button("📥 Télécharger si l'onglet ne s'ouvre pas", data=p['content'], file_name=p['nom'], key=os.urandom(4).hex())

    with c2:
        if data['marchandises']: st.table(pd.DataFrame(data['marchandises']))

    with c3:
        m_c = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True, key="c_m")
        k = "marbre" if m_c == "Marbre" else "ceram"
        if data[k]: st.table(pd.DataFrame(data[k]))

    with c4:
        for s in data['salaries']:
            with st.expander(f"📁 {s['nom']}"):
                bouton_ouvrir_onglet(s['content'], s['nom'], "CONSULTER LE POINTAGE")
                st.download_button("📥 Télécharger", data=s['content'], file_name=s['nom'], key=os.urandom(4).hex())
