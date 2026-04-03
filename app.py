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

# --- FONCTION D'OUVERTURE JS (Pour les plans/salariés) ---
def bouton_ouvrir_onglet(file_bytes, file_name, label="👁️ VOIR"):
    b64 = base64.b64encode(file_bytes).decode()
    mime = "application/pdf" if file_name.lower().endswith('.pdf') else "image/jpeg"
    js = f"""<script>function openDoc(){{var b=atob("{b64}"),n=new Array(b.length);for(var i=0;i<b.length;i++)n[i]=b.charCodeAt(i);var blob=new Blob([new Uint8Array(n)],{{type:"{mime}"}});window.open(URL.createObjectURL(blob),'_blank');}}</script>
    <button onclick="openDoc()" style="background:#007bff;color:white;border:none;padding:10px;border-radius:5px;width:100%;cursor:pointer;font-weight:bold;">{label}</button>"""
    st.components.v1.html(js, height=50)

# --- NAVIGATION ---
mode = st.sidebar.radio("MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t1:
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees()
            st.success("Plan enregistré !")
            
    with t2:
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", type=['jpg','jpeg','png'], key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", type=['jpg','jpeg','png'], key="p_cam")
        
        if st.button("Valider Réception"):
            # On stocke les photos si elles existent
            bl_bytes = p_bl.getvalue() if p_bl else None
            cam_bytes = p_cam.getvalue() if p_cam else None
            
            data['marchandises'].append({
                "Fournisseur": f, 
                "Désignation": d, 
                "Date": pd.Timestamp.now().strftime("%d/%m %H:%M"),
                "photo_bl": bl_bytes,
                "photo_cam": cam_bytes
            })
            sauvegarder_donnees()
            st.success("Réception et Photos enregistrées !")

    with t3:
        m = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True)
        det = st.text_input("Détails (Imm/App)")
        p_chantier = st.file_uploader("Photo Travaux", type=['jpg','jpeg','png'], key="p_ch")
        if st.button("Enregistrer Suivi"):
            key = "marbre" if m == "Marbre" else "ceram"
            data[key].append({
                "Détails": det, 
                "Date": pd.Timestamp.now().strftime("%d/%m"),
                "photo": p_chantier.getvalue() if p_chantier else None
            })
            sauvegarder_donnees()
            st.success("Suivi enregistré !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"Consultation {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for p in data['plans']:
            with st.expander(f"📁 {p['nom']}"):
                bouton_ouvrir_onglet(p['content'], p['nom'])

    with c2:
        for idx, m in enumerate(data['marchandises']):
            with st.expander(f"📦 {m['Fournisseur']} - {m['Désignation']} ({m['Date']})"):
                col_a, col_b = st.columns(2)
                if m.get('photo_bl'):
                    col_a.image(m['photo_bl'], caption="Bon de Livraison")
                if m.get('photo_cam'):
                    col_b.image(m['photo_cam'], caption="Photo Camion")
                if not m.get('photo_bl') and not m.get('photo_cam'):
                    st.info("Aucune photo pour cette réception.")

    with c3:
        m_c = st.radio("Métier", ["Marbre", "Céramique"], horizontal=True)
        k = "marbre" if m_c == "Marbre" else "ceram"
        for entry in data[k]:
            with st.expander(f"🛠️ {entry['Détails']} ({entry.get('Date', '')})"):
                if entry.get('photo'):
                    st.image(entry['photo'], width=400)
                else:
                    st.write("Pas de photo disponible.")

    with c4:
        for s in data['salaries']:
            with st.expander(f"📁 {s['nom']}"):
                bouton_ouvrir_onglet(s['content'], s['nom'])
