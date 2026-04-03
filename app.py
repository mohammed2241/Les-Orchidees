import streamlit as st
import pandas as pd
import base64
import os
import pickle
import io

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

# --- NAVIGATION ---
mode = st.sidebar.radio("SÉLECTIONNER LE MODE", ["📝 SAISIE", "🔍 CONSULTATION"])
tranche = st.sidebar.selectbox("CHOISIR LA TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data = st.session_state.db[tranche]

# --- FONCTION DE CONSULTATION SANS TÉLÉCHARGEMENT ---
def consulter_excel(file_bytes, file_name):
    try:
        # On utilise io.BytesIO pour lire le fichier en mémoire vive
        df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        st.success(f"Affichage de : {file_name}")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error("L'affichage automatique a échoué. Cliquez sur le bouton bleu pour voir le fichier.")
        # Solution de secours : Bouton de visualisation JS
        b64 = base64.b64encode(file_bytes).decode()
        js = f"""
        <script>
        function openExcel() {{
            var blob = new Blob([new Uint8Array(atob("{b64}").split("").map(c => c.charCodeAt(0)))], {{type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}});
            window.open(URL.createObjectURL(blob), '_blank');
        }}
        </script>
        <button onclick="openExcel()" style="background:#007bff;color:white;border:none;padding:12px;border-radius:5px;width:100%;cursor:pointer;font-weight:bold;">
            👁️ VOIR DANS UN NOUVEL ONGLET (SANS TÉLÉCHARGER)
        </button>
        """
        st.components.v1.html(js, height=60)

# ==========================================
#                MODE SAISIE
# ==========================================
if mode == "📝 SAISIE":
    t1, t2, t3, t4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])
    
    with t1: # PLANS
        up = st.file_uploader("Upload Plan", type=['pdf', 'jpg', 'png', 'jpeg'], key="up_p")
        if st.button("✅ Enregistrer Plan") and up:
            data['plans'].append({"nom": up.name, "content": up.getvalue()})
            sauvegarder_donnees()
            st.success("Plan enregistré !")
            
    with t2: # MARCHANDISES
        f = st.selectbox("Fournisseur", ["Lafarge", "Ingelec", "Roca", "Nexans"])
        d = st.text_input("Désignation")
        c1, c2 = st.columns(2)
        p_bl = c1.file_uploader("Photo BL", type=['jpg','jpeg','png'], key="p_bl")
        p_cam = c2.file_uploader("Photo Camion", type=['jpg','jpeg','png'], key="p_cam")
        if st.button("Valider Réception"):
            data['marchandises'].append({
                "Fournisseur": f, "Désignation": d, "Date": pd.Timestamp.now().strftime("%d/%m %H:%M"),
                "photo_bl": p_bl.getvalue() if p_bl else None,
                "photo_cam": p_cam.getvalue() if p_cam else None
            })
            sauvegarder_donnees()
            st.success("Réception enregistrée !")

    with t3: # SUIVI DÉTAILLÉ
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        if spec in ["Électricité", "Plomberie"]:
            items = ["Spot", "Prise TV", "Disjoncteur"] if spec == "Électricité" else ["Vasque", "Toilette", "Robinet"]
            for i in items:
                col1, col2, col3 = st.columns([2, 1, 2])
                q = col2.number_input("Qté", min_value=0, key=f"q_{i}")
                dt = col3.text_input("Détails", key=f"d_{i}")
                p_suivi = st.file_uploader(f"Photo {i}", type=['jpg','jpeg','png'], key=f"p_{i}")
                if st.button(f"Enregistrer {i}", key=f"btn_{i}"):
                    k = "elec" if spec == "Électricité" else "plomb"
                    data[k].append({"Produit": i, "Qté": q, "Détail": dt, "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_suivi.getvalue() if p_suivi else None})
                    sauvegarder_donnees()
                    st.toast(f"{i} validé !")
        elif spec == "Marbre":
            p = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            im = st.text_input("Immeuble")
            ap = st.text_input("Appartement")
            p_m = st.file_uploader("Photo Marbre", type=['jpg','jpeg','png'])
            if st.button("Valider Marbre"):
                data['marbre'].append({"Nom": p, "Lieu": f"Imm {im} - App {ap}", "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_m.getvalue() if p_m else None})
                sauvegarder_donnees()
                st.success("Marbre OK")
        elif spec == "Céramique":
            z = st.selectbox("Zone", ["SDB", "Chambre", "Terrasse"])
            et = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème"])
            p_c = st.file_uploader("Photo Céramique", type=['jpg','jpeg','png'])
            if st.button("Valider Céramique"):
                data['ceram'].append({"Type": z, "Lieu": f"Etage {et}", "Date": pd.Timestamp.now().strftime("%d/%m"), "photo": p_c.getvalue() if p_c else None})
                sauvegarder_donnees()
                st.success("Céramique OK")

    with t4: # SALARIÉ
        up_s = st.file_uploader("Pointage Excel/PDF", type=['pdf', 'xlsx'], key="up_sal")
        if st.button("Confirmer Salarié") and up_s:
            data['salaries'].append({"nom": up_s.name, "content": up_s.getvalue()})
            sauvegarder_donnees()
            st.success("Fiche salarié enregistrée !")

# ==========================================
#           MODE CONSULTATION
# ==========================================
else:
    st.header(f"🔍 Consultation - {tranche}")
    c1, c2, c3, c4 = st.tabs(["📄 PLANS", "📦 MARCHANDISES", "🛠️ SUIVI", "👥 SALARIÉ"])

    with c1:
        for p in data['plans']:
            with st.expander(f"📁 {p['nom']}"):
                b64 = base64.b64encode(p['content']).decode()
                st.components.v1.html(f'<button onclick="window.open(URL.createObjectURL(new Blob([new Uint8Array(atob(\'{b64}\').split(\'\').map(c=>c.charCodeAt(0)))] , {{type:\'application/pdf\'}})), \'_blank\')" style="width:100%; padding:10px; background:#007bff; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">👁️ VOIR LE PLAN</button>', height=50)

    with c2:
        for m in data['marchandises']:
            with st.expander(f"📦 {m['Fournisseur']} - {m['Désignation']} ({m['Date']})"):
                ca, cb = st.columns(2)
                if m.get('photo_bl'): ca.image(m['photo_bl'], caption="BL")
                if m.get('photo_cam'): cb.image(m['photo_cam'], caption="Camion")

    with c3:
        sel = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)
        k_map = {"Électricité": "elec", "Plomberie": "plomb", "Marbre": "marbre", "Céramique": "ceram"}
        for entry in data[k_map[sel]]:
            label = entry.get('Produit') or entry.get('Nom') or entry.get('Type')
            with st.expander(f"🛠️ {label} ({entry.get('Date')})"):
                if entry.get('photo'): st.image(entry['photo'], width=400)
                st.write(f"**Lieu/Détail :** {entry.get('Lieu') or entry.get('Détail', '')}")

    with c4:
        for s in data['salaries']:
            with st.expander(f"📊 Fichier : {s['nom']}"):
                if s['nom'].lower().endswith('.xlsx') or s['nom'].lower().endswith('.xls'):
                    consulter_excel(s['content'], s['nom'])
                else:
                    b64 = base64.b64encode(s['content']).decode()
                    st.components.v1.html(f'<button onclick="window.open(URL.createObjectURL(new Blob([new Uint8Array(atob(\'{b64}\').split(\'\').map(c=>c.charCodeAt(0)))] , {{type:\'application/pdf\'}})), \'_blank\')" style="width:100%; padding:10px; background:#007bff; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">👁️ VOIR LE PDF</button>', height=50)
