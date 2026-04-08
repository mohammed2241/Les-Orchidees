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

SHEET_TAB_MAP = {
    "Tranche 3": {"marchandises": "T3 Marchandises", "elec": "T3 Elec", "plomb": "T3 Plomb", "marbre": "T3 Marbre", "ceram": "T3 Ceram"},
    "Tranche 4": {"marchandises": "T4 Marchandises", "elec": "T4 Elec", "plomb": "T4 Plomb", "marbre": "T4 Marbre", "ceram": "T4 Ceram"},
    "Tranche 5": {"marchandises": "T5 Marchandises", "elec": "T5 Elec", "plomb": "T5 Plomb", "marbre": "T5 Marbre", "ceram": "T5 Ceram"},
}

HEADERS = {
    "marchandises": ["Date", "Fournisseur", "Désignation"],
    "elec":         ["Date", "Produit", "Qté", "Lieu"],
    "plomb":        ["Date", "Produit", "Qté", "Lieu"],
    "marbre":       ["Date", "Nom", "Type", "Fournisseur", "Référence", "Lieu", "Surface"],
    "ceram":        ["Date", "Type", "Immeuble"],
}

@st.cache_resource(show_spinner=False)
def get_gsheet_client():
    if not GSPREAD_AVAILABLE:
        return None
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception:
        return None

def get_spreadsheet(client):
    try:
        sheet_id = st.secrets["google_sheet"]["spreadsheet_id"]
        return client.open_by_key(sheet_id)
    except Exception:
        return None

def get_or_create_worksheet(spreadsheet, tab_name, headers):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers) + 1)
        ws.append_row(headers)
    return ws

def synchro_vers_sheets(tranche, section, nouvelle_ligne):
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
        row = [str(nouvelle_ligne.get(col, "")) for col in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.warning(f"⚠️ Sync Google Sheets échouée : {e}")
        return False

def exporter_tout_vers_sheets():
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
            ws.clear()
            ws.append_row(headers)
            rows = st.session_state.db[tranche].get(section, [])
            for entry in rows:
                row = [str(entry.get(col, "")) for col in headers]
                ws.append_row(row, value_input_option="USER_ENTERED")
                total += 1
    st.success(f"✅ Export complet : {total} lignes envoyées vers Google Sheets.")

def supprimer_ligne_sheet(tranche, section, entry):
    """
    Supprime la ligne correspondant à 'entry' dans l'onglet Google Sheets.
    La correspondance se fait sur toutes les colonnes texte (sans les photos).
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
        # Construire la ligne à chercher
        row_to_find = [str(entry.get(col, "")) for col in headers]
        all_rows = ws.get_all_values()  # incluant l'en-tête en ligne 1
        for idx, row in enumerate(all_rows):
            if row == row_to_find:
                ws.delete_rows(idx + 1)  # gspread : lignes indexées à partir de 1
                return True
        return False
    except Exception as e:
        st.warning(f"⚠️ Suppression Google Sheets échouée : {e}")
        return False

def importer_depuis_sheets():
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
            records = ws.get_all_records()
            local_list = st.session_state.db[tranche].get(section, [])

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

mode    = st.sidebar.radio("MENU", ["📝 SAISIE", "🔍 CONSULTATION", "⚙️ CATALOGUE", "☁️ GOOGLE SHEETS"])
tranche = st.sidebar.selectbox("TRANCHE", ["Tranche 3", "Tranche 4", "Tranche 5"])
data    = st.session_state.db[tranche]

gs_client = get_gsheet_client()
if gs_client:
    st.sidebar.success("☁️ Google Sheets : Connecté")
else:
    st.sidebar.warning("☁️ Google Sheets : Non configuré")

# ================= MODE SAISIE =================
if mode == "📝 SAISIE":
    tabs = st.tabs(["📦 MARCHANDISES", "🛠️ SUIVI CHANTIER"])

    with tabs[0]:
        f    = st.selectbox("Fournisseur", cfg["fournisseurs"])
        d    = st.text_area("Désignation complète")
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

            fourn, ref_v, surf, sous_type_bc, appt = None, None, 0.0, None, ""

            # ---- WHITE SAND : étage → Magasin ou Entrée ----
            if type_m == "White Sand":
                imm      = st.text_input("Immeuble")
                emplacement = st.selectbox("Emplacement", ["Magasin", "Entrée"])
                p_m      = st.file_uploader("Photo de la pose")
                if st.button("Enregistrer Marbre"):
                    lieu_final = f"Imm {imm} - {emplacement}"
                    nouvelle = {
                        "Nom": interv, "Type": type_m, "Fournisseur": None,
                        "Référence": None, "Lieu": lieu_final, "Surface": 0,
                        "Date": datetime.date.today().strftime("%d/%m"),
                        "photo": p_m.getvalue() if p_m else None
                    }
                    data['marbre'].append(nouvelle)
                    sauvegarder_donnees()
                    synchro_vers_sheets(tranche, "marbre", nouvelle)
                    st.success("Saisie Marbre Validée")

            # ---- BLANC CARRARA ----
            elif type_m == "Blanc Carrara":
                sous_type_bc = st.selectbox("Élément Blanc Carrara", ["Dallage", "Seuil", "Niche", "Les douches"])

                if sous_type_bc == "Dallage":
                    appt  = st.text_input("N° Appartement")
                    c1, c2 = st.columns(2)
                    fourn = c1.selectbox("Fournisseur Marbre", ["Graziani", "Caro Colombi", "Lorenzoni", "MARMI BIANCO"])
                    ref_v = c2.text_input("Référence (Lot/Bloc)")
                    surf  = st.number_input("Surface (m²)", min_value=0.0)
                    # ✅ Finition supprimée pour Dallage

                imm   = st.text_input("Immeuble")
                etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "5ème"])
                p_m   = st.file_uploader("Photo de la pose")

                if st.button("Enregistrer Marbre"):
                    lieu_final = f"Imm {imm} - {etage}" + (f" - Appt {appt}" if appt else "")
                    type_final = f"Blanc Carrara ({sous_type_bc})"
                    nouvelle = {
                        "Nom": interv, "Type": type_final, "Fournisseur": fourn,
                        "Référence": ref_v, "Lieu": lieu_final, "Surface": surf,
                        "Date": datetime.date.today().strftime("%d/%m"),
                        "photo": p_m.getvalue() if p_m else None
                    }
                    data['marbre'].append(nouvelle)
                    sauvegarder_donnees()
                    synchro_vers_sheets(tranche, "marbre", nouvelle)
                    st.success("Saisie Marbre Validée")

            # ---- GRIS BOLD (inchangé) ----
            else:
                imm   = st.text_input("Immeuble")
                etage = st.selectbox("Étage", ["RDC", "1er", "2ème", "3ème", "4ème", "5ème"])
                p_m   = st.file_uploader("Photo de la pose")
                if st.button("Enregistrer Marbre"):
                    lieu_final = f"Imm {imm} - {etage}"
                    nouvelle = {
                        "Nom": interv, "Type": type_m, "Fournisseur": None,
                        "Référence": None, "Lieu": lieu_final, "Surface": 0,
                        "Date": datetime.date.today().strftime("%d/%m"),
                        "photo": p_m.getvalue() if p_m else None
                    }
                    data['marbre'].append(nouvelle)
                    sauvegarder_donnees()
                    synchro_vers_sheets(tranche, "marbre", nouvelle)
                    st.success("Saisie Marbre Validée")

        # ---- CÉRAMIQUE ----
        elif spec == "Céramique":
            z  = st.selectbox("Zone", ["SDB", "Cuisine", "Chambre", "Terrasse Immeuble", "Salon"])
            im = st.text_input("Immeuble")

            # Étage uniquement pour les zones autres que Terrasse Immeuble
            if z != "Terrasse Immeuble":
                et = st.selectbox("Étage", ["RDC", "1", "2", "3", "4", "5"])
                lieu_ceram = f"Imm {im} - {et}"
            else:
                lieu_ceram = f"Imm {im}"

            p_c = st.file_uploader("Photo")
            if st.button("Enregistrer Céramique"):
                nouvelle = {
                    "Type": z,
                    "Immeuble": lieu_ceram,
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
                    entry_to_del = data['marchandises'][-(i+1)]
                    supprimer_ligne_sheet(tranche, "marchandises", entry_to_del)
                    data['marchandises'].pop(-(i+1))
                    sauvegarder_donnees()
                    st.rerun()
    else:
        m_filter = st.selectbox("Filtrer Métier", ["Marbre", "Céramique", "Électricité", "Plomberie"])
        k = {"Marbre": "marbre", "Céramique": "ceram", "Électricité": "elec", "Plomberie": "plomb"}[m_filter]

        st.download_button(f"📥 Rapport PDF {m_filter}", data=creer_pdf_section(m_filter.upper(), data[k], k), file_name=f"{m_filter}.pdf")

        for i, entry in enumerate(reversed(data[k])):
            titre = f"{entry.get('Type', entry.get('Produit', '-'))} - {entry.get('Date', '-')}"
            with st.expander(titre):
                col1, col2 = st.columns(2)
                with col1:
                    if 'Lieu' in entry:      st.write(f"**Lieu:** {entry['Lieu']}")
                    if 'Immeuble' in entry:  st.write(f"**Immeuble:** {entry['Immeuble']}")
                    if 'Qté' in entry:       st.write(f"**Qté:** {entry['Qté']}")
                    if 'Surface' in entry:   st.write(f"**Surface:** {entry['Surface']} m2")
                with col2:
                    if entry.get('photo'): st.image(entry['photo'], width=250)
                if st.button("🗑️ Supprimer", key=f"del_{k}_{i}"):
                    entry_to_del = data[k][-(i+1)]
                    supprimer_ligne_sheet(tranche, k, entry_to_del)
                    data[k].pop(-(i+1))
                    sauvegarder_donnees()
                    st.rerun()

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

    st.subheader("État de la connexion")
    if gs_client:
        st.success("✅ Connecté au compte de service Google.")
        spreadsheet = get_spreadsheet(gs_client)
        if spreadsheet:
            st.info(f"📊 Google Sheet ouvert : **{spreadsheet.title}**")
        else:
            st.error("❌ Impossible d'ouvrir le Google Sheet. Vérifiez `spreadsheet_id` dans les secrets Streamlit.")
    else:
        st.error("❌ Non connecté. Configurez vos secrets Streamlit.")

    st.divider()

    st.subheader("Actions")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📤 Export complet → Google Sheets**")
        st.caption("Écrase le contenu du Sheet avec toutes les données locales.")
        if st.button("Lancer l'export complet", type="primary"):
            with st.spinner("Export en cours..."):
                exporter_tout_vers_sheets()

    with col2:
        st.markdown("**📥 Import Google Sheets → Local**")
        st.caption("Fusionne les données du Sheet dans l'application (sans doublon).")
        if st.button("Lancer l'import / fusion"):
            with st.spinner("Import en cours..."):
                importer_depuis_sheets()

    st.divider()

    st.subheader("📋 Structure des onglets Google Sheet")
    onglets = []
    for tranche_nom, sections in SHEET_TAB_MAP.items():
        for section, tab in sections.items():
            onglets.append({"Onglet": tab, "Tranche": tranche_nom, "Section": section.capitalize(), "Colonnes": ", ".join(HEADERS[section])})
    st.dataframe(pd.DataFrame(onglets), use_container_width=True, hide_index=True)
