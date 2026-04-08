import streamlit as st
import pandas as pd
import os
import pickle
import io
import datetime
import json
from fpdf import FPDF

# --- GOOGLE SHEETS INTEGRATION ---
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(page_title="Les Orchidées Manesmane", layout="wide")

# --- LISTES PAR DÉFAUT ---
DEFAUT_FRS = ["INTERCABLE", "SOFA", "PROMELEC", "MG LIGHTING", "KADIR DISTRIBUTION", "SARABO", "SOQOP", "FROIDEL", "NOVACIM", "RE SERVICE", "ATLAS MULTIMATERIEL", "SBBC", "LAFARGE", "SAFI BAINS", "INNOVA WOOD", "SINASTONE", "MEDIAL", "EXPLOMAR", "RIVA", "INTERSIG", "AQUAPLANET", "BEKO MAGHREB", "ISOLBOX", "PLATINOVA", "TAMAGROT", "AOC", "SOCODAM DAVUM", "HYDRAU MAC", "TRACTRAFFIC", "GOOD YEAR BAB DOKALA", "MULTICERAME", "MALL ZALLIJ", "SUPER CERAME", "PETROMIN OILS", "ALSINA", "PERI", "Autre"]
DEFAUT_ELEC = ["SPOT", "SPOT DOUBLE", "BLOC DE SECOURS", "DISJ", "APPLIQUE", "LED", "SUPPORT SURMOULE", "SUPPORT 3 MODULES", "SUPPORT 4 MODULES", "SUPPORT 6 MODULES", "PRISE 2P+T à clapet IP44", "Obturateur", "PRISE 2P+T", "Prise TV SAT", "Interr SVV", "Interr V&V", "Pousse à basc", "Inver volets roul", "Video phonique"]
DEFAUT_PLOMB = ["TOILETTE", "VASQUE 60 CM", "VASQUE 80 CM", "BIDETS", "DOUCHETTE", "POMPE DE DOUCHE", "MIT DCH", "MIT LVB", "MIT BIDET", "CHAUFFE EAU", "EVIER", "MIT EVIER"]

# --- SYSTÈME DE SAUVEGARDE (Local) ---
DB_FILE = "data_chantier_v2.pkl"

def charger_donnees():
    structure_vide = {
        "Tranche 3": {"marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": []},
        "Tranche 4": {"marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": []},
        "Tranche 5": {"marchandises": [], "elec": [], "plomb": [], "marbre": [], "ceram": []},
        "config": {"fournisseurs": DEFAUT_FRS.copy(), "produits_elec": DEFAUT_ELEC.copy(), "produits_plomb": DEFAUT_PLOMB.copy()}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                data = pickle.load(f)
                for t in ["Tranche 3", "Tranche 4", "Tranche 5"]:
                    if t not in data: data[t] = structure_vide[t]
                if "config" not in data: data["config"] = structure_vide["config"]
                return data
        except:
            return structure_vide
    return structure_vide

def sauvegarder_donnees():
    with open(DB_FILE, "wb") as f:
        pickle.dump(st.session_state.db, f)

if 'db' not in st.session_state:
    st.session_state.db = charger_donnees()

cfg = st.session_state.db["config"]

# =====================================================================
# --- GOOGLE SHEETS : CONNEXION & SYNCHRONISATION ---
# =====================================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Noms des onglets dans le Google Sheet (un par tranche + section)
# Structure : "T3 Marchandises", "T3 Elec", "T3 Plomb", "T3 Marbre", "T3 Ceram", etc.
SHEET_TAB_MAP = {
    "Tranche 3": {"marchandises": "T3 Marchandises", "elec": "T3 Elec", "plomb": "T3 Plomb", "marbre": "T3 Marbre", "ceram": "T3 Ceram"},
    "Tranche 4": {"marchandises": "T4 Marchandises", "elec": "T4 Elec", "plomb": "T4 Plomb", "marbre": "T4 Marbre", "ceram": "T4 Ceram"},
    "Tranche 5": {"marchandises": "T5 Marchandises", "elec": "T5 Elec", "plomb": "T5 Plomb", "marbre": "T5 Marbre", "ceram": "T5 Ceram"},
}

# En-têtes par type de données
HEADERS = {
    "marchandises": ["Date", "Fournisseur", "Désignation"],
    "elec":         ["Date", "Produit", "Qté", "Lieu"],
    "plomb":        ["Date", "Produit", "Qté", "Lieu"],
    "marbre":       ["Date", "Nom", "Type", "Fournisseur", "Référence", "Lieu", "Surface", "Finition"],
    "ceram":        ["Date", "Type", "Lieu"],
}

@st.cache_resource(show_spinner=False)
def get_gsheet_client():
    """
    Initialise le client gspread depuis les secrets Streamlit.
    Dans Streamlit Cloud, configurez un secret nommé 'gcp_service_account'
    contenant le JSON complet du compte de service.
    """
    if not GSPREAD_AVAILABLE:
        return None
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

def get_spreadsheet(client):
    """Ouvre le Google Sheet via son nom ou son URL stocké dans les secrets."""
    try:
        sheet_id = st.secrets["google_sheet"]["spreadsheet_id"]
        return client.open_by_key(sheet_id)
    except Exception:
        return None

def get_or_create_worksheet(spreadsheet, tab_name, headers):
    """Retourne l'onglet existant ou le crée avec les en-têtes."""
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers) + 1)
        ws.append_row(headers)
    return ws

def synchro_vers_sheets(tranche, section, nouvelle_ligne):
    """
    Ajoute une seule ligne dans l'onglet Google Sheet correspondant.
    C'est la méthode rapide appelée à chaque saisie.
    """
    client = get_gsheet_client()
    if client is None:
        return False
    spreadsheet = get_spreadsheet(client)
    if spreadsheet is None:
        return False

    tab_name = SHEET_TAB_MAP[tranche][section]
    headers  = HEADERS[section]

    try:
        ws = get_or_create_worksheet(spreadsheet, tab_name, headers)
        # Construire la ligne dans l'ordre des en-têtes (ignorer les photos)
        row = [str(nouvelle_ligne.get(col, "")) for col in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.warning(f"⚠️ Sync Google Sheets échouée : {e}")
        return False

def exporter_tout_vers_sheets():
    """
    Exporte TOUTES les données locales vers Google Sheets (écrase le contenu).
    À utiliser pour une resynchronisation complète.
    """
    client = get_gsheet_client()
    if client is None:
        st.error("❌ Impossible de se connecter à Google Sheets. Vérifiez vos secrets.")
        return
    spreadsheet = get_spreadsheet(client)
    if spreadsheet is None:
        st.error("❌ Google Sheet introuvable. Vérifiez le 'spreadsheet_id' dans les secrets.")
        return

    total = 0
    for tranche in ["Tranche 3", "Tranche 4", "Tranche 5"]:
        for section, headers in HEADERS.items():
            tab_name = SHEET_TAB_MAP[tranche][section]
            ws = get_or_create_worksheet(spreadsheet, tab_name, headers)
            # Effacer et réécrire
            ws.clear()
            ws.append_row(headers)
            rows = st.session_state.db[tranche].get(section, [])
            for entry in rows:
                row = [str(entry.get(col, "")) for col in headers]
                ws.append_row(row, value_input_option="USER_ENTERED")
                total += 1
    st.success(f"✅ Export complet : {total} lignes envoyées vers Google Sheets.")

def importer_depuis_sheets():
    """
    Importe les données depuis Google Sheets et FUSIONNE avec les données locales
    (dédoublonnage sur Date + champ principal).
    """
    client = get_gsheet_client()
    if client is None:
        st.error("❌ Impossible de se connecter à Google Sheets.")
        return
    spreadsheet = get_spreadsheet(client)
    if spreadsheet is None:
        st.error("❌ Google Sheet introuvable.")
        return

    total_importe = 0
    for tranche in ["Tranche 3", "Tranche 4", "Tranche 5"]:
        for section, headers in HEADERS.items():
            tab_name = SHEET_TAB_MAP[tranche][section]
            try:
                ws = spreadsheet.worksheet(tab_name)
            except gspread.WorksheetNotFound:
                continue

            records = ws.get_all_records()  # liste de dicts avec les en-têtes comme clés
            local_list = st.session_state.db[tranche].get(section, [])

            # Créer un set de clés existantes pour dédoublonnage
            def cle(entry):
                return (entry.get("Date", ""), entry.get("Fournisseur", entry.get("Produit", entry.get("Nom", entry.get("Type", "")))))

            existing_keys = {cle(e) for e in local_list}

            for rec in records:
                if cle(rec) not in existing_keys:
                    local_list.append(rec)
                    existing_keys.add(cle(rec))
                    total_importe += 1

            st.session_state.db[tranche][section] = local_list

    sauvegarder_donnees()
    st.success(f"✅ Import terminé : {total_importe} nouvelles entrées fusionnées.")

# --- GÉNÉRATEUR PDF ---
def creer_pdf_section(titre, data_list, type_rapport):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"RAPPORT : {titre}", ln=True, align='C')
    pdf.ln(5)

    if not data_list:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "Aucune donnee enregistree.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(230, 230, 230)

    if type_rapport == "marchandises":
        cols = ["DATE", "FOURNISSEUR", "DESIGNATION"]
        w = [30, 50, 110]
        for i, c in enumerate(cols): pdf.cell(w[i], 10, c, 1, 0, 'C', True)
        pdf.ln()
        pdf.set_font('Arial', '', 8)
        for r in data_list:
            pdf.cell(30, 8, str(r.get('Date', '-')), 1)
            pdf.cell(50, 8, str(r.get('Fournisseur', '-'))[:25], 1)
            pdf.cell(110, 8, str(r.get('Désignation', '-'))[:65], 1, 1)

    elif type_rapport == "marbre":
        cols = ["DATE", "INTERV.", "TYPE", "LIEU", "M2"]
        w = [25, 30, 50, 60, 25]
        for i, c in enumerate(cols): pdf.cell(w[i], 10, c, 1, 0, 'C', True)
        pdf.ln()
        pdf.set_font('Arial', '', 7)
        for r in data_list:
            pdf.cell(25, 8, str(r.get('Date', '-')), 1)
            pdf.cell(30, 8, str(r.get('Nom', '-')), 1)
            pdf.cell(50, 8, str(r.get('Type', '-'))[:35], 1)
            pdf.cell(60, 8, str(r.get('Lieu', '-'))[:45], 1)
            pdf.cell(25, 8, f"{r.get('Surface', '0')} m2", 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("🏗️ LES ORCHIDÉES MANESMANE")

# --- SIDEBAR ---
mode    = st.sidebar.radio("MENU", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE", "☁️ GOOGLE SHEETS"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data    = st.session_state.db[tranche]

# Indicateur de connexion Google Sheets dans la sidebar
gs_client = get_gsheet_client()
if gs_client:
    st.sidebar.success("☁️ Google Sheets : Connecté")
else:
    st.sidebar.warning("☁️ Google Sheets : Non configuré")

# ================= MODE SAISIE =================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📦 MARCHANDISES", "🛠️ SUIVI CHANTIER"])

    with tabs[0]:
        f   = st.selectbox("Fournisseur", cfg["fournisseurs"])
        d   = st.text_area("Désignation complète")
        p_bl = st.file_uploader("Photo du Bon de Livraison", type=['jpg','png','jpeg'])
        if st.button("Valider Réception"):
            nouvelle = {
                "Fournisseur": f, "Désignation": d,
                "Date": datetime.date.today().strftime("%d/%m/%Y"),
                "photo_bl": p_bl.getvalue() if p_bl else None
            }
            data['marchandises'].append(nouvelle)
            sauvegarder_donnees()
            synchro_vers_sheets(tranche, "marchandises", nouvelle)
            st.success("Enregistré !")

    with tabs[1]:
        spec = st.radio("Métier", ["Électricité", "Plomberie", "Marbre", "Céramique"], horizontal=True)

        if spec == "Marbre":
            interv = st.selectbox("Intervenant", ["FETTAH", "Simo"])
            type_m = st.selectbox("Type Marbre", ["Gris Bold", "White Sand", "Blanc Carrara"])

            fourn, ref_v, surf, fini, sous_type_bc, appt = None, None, 0.0, None, None, ""

            if type_m == "Blanc Carrara":
                sous_type_bc = st.selectbox("Élément Blanc Carrara", ["Dallage", "Seuil", "Niche", "Les douches"])
                if sous_type_bc == "Dallage":
                    appt = st.text_input("N° Appartement")
                    c1, c2 = st.columns(2)
                    fourn  = c1.selectbox("Fournisseur Marbre", ["Graziani", "Caro Colombi", "Lorenzoni", "MARMI BIANCO"])
                    ref_v  = c2.text_input("Référence (Lot/Bloc)")
                    surf   = st.number_input("Surface (m²)", min_value=0.0)
                    fini   = st.selectbox("Finition", ["Poli", "Adouci", "Brut"])

            imm   = st.text_input("Immeuble")
            etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "5ème"])
            p_m   = st.file_uploader("Photo de la pose")

            if st.button("Enregistrer Marbre"):
                lieu_final = f"Imm {imm} - {etage}" + (f" - Appt {appt}" if appt else "")
                type_final = f"Blanc Carrara ({sous_type_bc})" if sous_type_bc else type_m
                nouvelle = {
                    "Nom": interv, "Type": type_final, "Fournisseur": fourn,
                    "Référence": ref_v, "Lieu": lieu_final, "Surface": surf,
                    "Finition": fini, "Date": datetime.date.today().strftime("%d/%m"),
                    "photo": p_m.getvalue() if p_m else None
                }
                data['marbre'].append(nouvelle)
                sauvegarder_donnees()
                synchro_vers_sheets(tranche, "marbre", nouvelle)
                st.success("Saisie Marbre Validée")

        elif spec == "Céramique":
            z   = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse", "Salon"])
            im  = st.text_input("Immeuble")
            et  = st.selectbox("Etage", ["RDC","1","2","3","4","5"])
            p_c = st.file_uploader("Photo")
            if st.button("Enregistrer Céramique"):
                nouvelle = {
                    "Type": z, "Lieu": f"Imm {im} - {et}",
                    "Date": datetime.date.today().strftime("%d/%m"),
                    "photo": p_c.getvalue() if p_c else None
                }
                data['ceram'].append(nouvelle)
                sauvegarder_donnees()
                synchro_vers_sheets(tranche, "ceram", nouvelle)
                st.success("Céramique Validée")

        else:  # Elec / Plomb
            prods = cfg["produits_elec"] if spec == "Électricité" else cfg["produits_plomb"]
            p_sel = st.selectbox("Produit", prods)
            q     = st.number_input("Quantité", min_value=1)
            loc   = st.text_input("Localisation (ex: Imm 2 - Appt 4)")
            p_s   = st.file_uploader("Photo")
            if st.button(f"Valider {spec}"):
                key      = "elec" if spec == "Électricité" else "plomb"
                nouvelle = {
                    "Produit": p_sel, "Qté": q, "Lieu": loc,
                    "Date": datetime.date.today().strftime("%d/%m"),
                    "photo": p_s.getvalue() if p_s else None
                }
                data[key].append(nouvelle)
                sauvegarder_donnees()
                synchro_vers_sheets(tranche, key, nouvelle)
                st.success("Enregistré !")

# ================= MODE CONSULTATION =================
elif mode == "🔍 CONSULTATION":
    cat_consul = st.radio("Section", ["Marchandises", "Suivi Chantier"], horizontal=True)

    if cat_consul == "Marchandises":
        st.download_button("📥 Rapport PDF Marchandises", data=creer_pdf_section("MARCHANDISES", data['marchandises'], "marchandises"), file_name="Marchandises.pdf")
        for i, m in enumerate(reversed(data['marchandises'])):
            with st.expander(f"📦 {m['Fournisseur']} - {m['Date']}"):
                st.write(m['Désignation'])
                if m.get('photo_bl'): st.image(m['photo_bl'], width=300)
                if st.button("🗑️ Supprimer", key=f"del_m_{i}"):
                    data['marchandises'].pop(-(i+1)); sauvegarder_donnees(); st.rerun()
    else:
        m_filter = st.selectbox("Filtrer Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"])
        k = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}[m_filter]

        st.download_button(f"📥 Rapport PDF {m_filter}", data=creer_pdf_section(m_filter.upper(), data[k], k), file_name=f"{m_filter}.pdf")

        for i, entry in enumerate(reversed(data[k])):
            titre = f"{entry.get('Type', entry.get('Produit'))} - {entry['Date']}"
            with st.expander(titre):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Lieu:** {entry['Lieu']}")
                    if 'Qté' in entry:     st.write(f"**Qté:** {entry['Qté']}")
                    if 'Surface' in entry: st.write(f"**Surface:** {entry['Surface']} m2")
                with col2:
                    if entry.get('photo'): st.image(entry['photo'], width=250)
                if st.button("🗑️ Supprimer", key=f"del_{k}_{i}"):
                    data[k].pop(-(i+1)); sauvegarder_donnees(); st.rerun()

# ================= MODE CATALOGUE =================
elif mode == "⚙️ CATALOGUE":
    st.header("⚙️ Configuration")
    c1, c2, c3 = st.tabs(["Fournisseurs", "Élec", "Plomb"])

    with c1:
        nf = st.text_input("Nouveau Fournisseur")
        if st.button("Ajouter FRS") and nf:
            cfg["fournisseurs"].append(nf); sauvegarder_donnees(); st.success("Ajouté")
        st.write(cfg["fournisseurs"])

    with c2:
        ne = st.text_input("Nouveau Produit Élec")
        if st.button("Ajouter Élec") and ne:
            cfg["produits_elec"].append(ne); sauvegarder_donnees(); st.success("Ajouté")
        st.write(cfg["produits_elec"])

    with c3:
        np_val = st.text_input("Nouveau Produit Plomb")
        if st.button("Ajouter Plomb") and np_val:
            cfg["produits_plomb"].append(np_val); sauvegarder_donnees(); st.success("Ajouté")
        st.write(cfg["produits_plomb"])

# ================= MODE GOOGLE SHEETS =================
elif mode == "☁️ GOOGLE SHEETS":
    st.header("☁️ Synchronisation Google Sheets")

    if not GSPREAD_AVAILABLE:
        st.error("Les librairies `gspread` et `google-auth` ne sont pas installées. Ajoutez-les à `requirements.txt`.")
        st.stop()

    # --- Statut de connexion ---
    st.subheader("État de la connexion")
    if gs_client:
        st.success("✅ Connecté au compte de service Google.")
        spreadsheet = get_spreadsheet(gs_client)
        if spreadsheet:
            st.info(f"📊 Google Sheet ouvert : **{spreadsheet.title}**")
        else:
            st.error("❌ Impossible d'ouvrir le Google Sheet. Vérifiez `spreadsheet_id` dans les secrets Streamlit.")
    else:
        st.error("❌ Non connecté. Configurez vos secrets Streamlit (voir instructions ci-dessous).")

    st.divider()

    # --- Actions de synchronisation ---
    st.subheader("Actions")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📤 Export complet → Google Sheets**")
        st.caption("Écrase le contenu du Sheet avec toutes les données locales. Utile pour initialiser ou resynchroniser.")
        if st.button("Lancer l'export complet", type="primary"):
            with st.spinner("Export en cours..."):
                exporter_tout_vers_sheets()

    with col2:
        st.markdown("**📥 Import Google Sheets → Local**")
        st.caption("Fusionne les données du Sheet dans l'application (sans doublon). Utile si quelqu'un a modifié le Sheet directement.")
        if st.button("Lancer l'import / fusion"):
            with st.spinner("Import en cours..."):
                importer_depuis_sheets()

    st.divider()

    # --- Structure du Sheet ---
    st.subheader("📋 Structure des onglets Google Sheet")
    st.markdown("L'application crée automatiquement les onglets suivants dans votre Google Sheet :")

    onglets = []
    for tranche_nom, sections in SHEET_TAB_MAP.items():
        for section, tab in sections.items():
            onglets.append({"Onglet": tab, "Tranche": tranche_nom, "Section": section.capitalize(), "Colonnes": ", ".join(HEADERS[section])})
    st.dataframe(pd.DataFrame(onglets), use_container_width=True, hide_index=True)

    st.divider()

    # --- Guide de configuration ---
    with st.expander("📖 Guide de configuration des secrets Streamlit", expanded=not gs_client):
        st.markdown("""
### Étape 1 – Préparer le fichier JSON du compte de service

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Sélectionnez votre projet → **APIs & Services → Credentials**
3. Cliquez sur votre compte de service → **Gérer les clés → Ajouter une clé → JSON**
4. Téléchargez le fichier `.json`

---

### Étape 2 – Partager votre Google Sheet

1. Ouvrez votre Google Sheet
2. Copiez l'**email** du compte de service (ex: `mon-service@projet.iam.gserviceaccount.com`)
3. Cliquez **Partager** dans le Sheet → collez cet email → rôle **Éditeur**
4. Copiez l'**ID du Sheet** depuis l'URL :  
   `https://docs.google.com/spreadsheets/d/` **`SPREADSHEET_ID`** `/edit`

---

### Étape 3 – Configurer les secrets sur Streamlit Cloud

Dans **Streamlit Cloud → App settings → Secrets**, collez :

```toml
[google_sheet]
spreadsheet_id = "VOTRE_SPREADSHEET_ID_ICI"

[gcp_service_account]
type = "service_account"
project_id = "votre-projet-id"
private_key_id = "xxxxx"
private_key = "-----BEGIN RSA PRIVATE KEY-----\\nXXXXX\\n-----END RSA PRIVATE KEY-----\\n"
client_email = "votre-compte@projet.iam.gserviceaccount.com"
client_id = "xxxxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/votre-compte%40projet.iam.gserviceaccount.com"
```

> ⚠️ Copiez les valeurs **exactement** depuis le fichier JSON téléchargé. Faites attention aux `\\n` dans `private_key`.

---

### Étape 4 – Vérifier requirements.txt

Assurez-vous que votre `requirements.txt` contient :
```
streamlit
fpdf
gspread
google-auth
pandas
```
""")
