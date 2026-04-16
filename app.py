import streamlit as st
import pandas as pd
import os
import pickle
import datetime
from fpdf import FPDF

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

st.set_page_config(page_title="Les Orchidees Manesmane", layout="wide")

DEFAUT_FRS = ["INTERCABLE","SOFA","PROMELEC","MG LIGHTING","KADIR DISTRIBUTION","SARABO","SOQOP","FROIDEL","NOVACIM","RE SERVICE","ATLAS MULTIMATERIEL","SBBC","LAFARGE","SAFI BAINS","INNOVA WOOD","SINASTONE","MEDIAL","EXPLOMAR","RIVA","INTERSIG","AQUAPLANET","BEKO MAGHREB","ISOLBOX","PLATINOVA","TAMAGROT","AOC","SOCODAM DAVUM","HYDRAU MAC","TRACTRAFFIC","GOOD YEAR BAB DOKALA","MULTICERAME","MALL ZALLIJ","SUPER CERAME","PETROMIN OILS","ALSINA","PERI","Autre"]
DEFAUT_ELEC = ["SPOT","SPOT DOUBLE","BLOC DE SECOURS","DISJ","APPLIQUE","LED","SUPPORT SURMOULE","SUPPORT 3 MODULES","SUPPORT 4 MODULES","SUPPORT 6 MODULES","PRISE 2P+T a clapet IP44","Obturateur","PRISE 2P+T","Prise TV SAT","Interr SVV","Interr V&V","Pousse a basc","Inver volets roul","Video phonique"]
DEFAUT_PLOMB = ["TOILETTE","VASQUE 60 CM","VASQUE 80 CM","BIDETS","DOUCHETTE","POMPE DE DOUCHE","MIT DCH","MIT LVB","MIT BIDET","CHAUFFE EAU","EVIER","MIT EVIER"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]

SHEET_TAB_MAP = {
    "Tranche 3": {"marchandises":"T3 Marchandises","elec":"T3 Elec","plomb":"T3 Plomb","marbre":"T3 Marbre","ceram":"T3 Ceram"},
    "Tranche 4": {"marchandises":"T4 Marchandises","elec":"T4 Elec","plomb":"T4 Plomb","marbre":"T4 Marbre","ceram":"T4 Ceram"},
    "Tranche 5": {"marchandises":"T5 Marchandises","elec":"T5 Elec","plomb":"T5 Plomb","marbre":"T5 Marbre","ceram":"T5 Ceram"},
}

HEADERS = {
    "marchandises": ["Date","Fournisseur","Designation"],
    "elec":         ["Date","Produit","Qté","Lieu"],
    "plomb":        ["Date","Produit","Qté","Lieu"],
    "marbre":       ["Date","Nom","Type","Fournisseur","Reference","Lieu","Surface"],
    "ceram":        ["Date","Type","Immeuble"],
}

# ============================================================
# FONCTIONS GOOGLE SHEETS
# ============================================================

@st.cache_resource(show_spinner=False)
def get_gsheet_client():
    if not GSPREAD_AVAILABLE:
        return None
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None

def get_spreadsheet(client):
    try:
        return client.open_by_key(st.secrets["google_sheet"]["spreadsheet_id"])
    except Exception:
        return None

def get_or_create_worksheet(spreadsheet, tab_name, headers):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers)+1)
        ws.append_row(headers)
    return ws

def row_vers_dict(section, entry):
    mapping = {
        "marchandises": [("Date","Date"),("Fournisseur","Fournisseur"),("Designation","Designation")],
        "elec":         [("Date","Date"),("Produit","Produit"),("Qté","Qte"),("Lieu","Lieu")],
        "plomb":        [("Date","Date"),("Produit","Produit"),("Qté","Qte"),("Lieu","Lieu")],
        "marbre":       [("Date","Date"),("Nom","Nom"),("Type","Type"),("Fournisseur","Fournisseur"),("Reference","Reference"),("Lieu","Lieu"),("Surface","Surface")],
        "ceram":        [("Date","Date"),("Type","Type"),("Immeuble","Immeuble")],
    }
    return {sk: str(entry.get(lk,"")) for sk,lk in mapping[section]}

def dict_vers_local(section, rec):
    mapping = {
        "marchandises": [("Date","Date"),("Fournisseur","Fournisseur"),("Designation","Designation")],
        "elec":         [("Date","Date"),("Produit","Produit"),("Qte","Qté"),("Lieu","Lieu")],
        "plomb":        [("Date","Date"),("Produit","Produit"),("Qte","Qté"),("Lieu","Lieu")],
        "marbre":       [("Date","Date"),("Nom","Nom"),("Type","Type"),("Fournisseur","Fournisseur"),("Reference","Reference"),("Lieu","Lieu"),("Surface","Surface")],
        "ceram":        [("Date","Date"),("Type","Type"),("Immeuble","Immeuble")],
    }
    return {lk: rec.get(sk,"") for lk,sk in mapping[section]}

def synchro_vers_sheets(tranche, section, entry):
    client = get_gsheet_client()
    if not client: return False
    spreadsheet = get_spreadsheet(client)
    if not spreadsheet: return False
    headers = HEADERS[section]
    try:
        ws  = get_or_create_worksheet(spreadsheet, SHEET_TAB_MAP[tranche][section], headers)
        d   = row_vers_dict(section, entry)
        ws.append_row([d.get(h,"") for h in headers], value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.warning(f"Sync Sheets echouee : {e}")
        return False

def supprimer_ligne_sheet(tranche, section, entry):
    client = get_gsheet_client()
    if not client: return False
    spreadsheet = get_spreadsheet(client)
    if not spreadsheet: return False
    headers = HEADERS[section]
    try:
        ws = get_or_create_worksheet(spreadsheet, SHEET_TAB_MAP[tranche][section], headers)
        d  = row_vers_dict(section, entry)
        target = [d.get(h,"") for h in headers]
        for idx, row in enumerate(ws.get_all_values()):
            if row == target:
                ws.delete_rows(idx+1)
                return True
    except Exception as e:
        st.warning(f"Suppression Sheets echouee : {e}")
    return False

def exporter_tout_vers_sheets():
    client = get_gsheet_client()
    if not client: st.error("Connexion impossible."); return
    spreadsheet = get_spreadsheet(client)
    if not spreadsheet: st.error("Sheet introuvable."); return
    total = 0
    for tranche in ["Tranche 3","Tranche 4","Tranche 5"]:
        for section, headers in HEADERS.items():
            ws = get_or_create_worksheet(spreadsheet, SHEET_TAB_MAP[tranche][section], headers)
            ws.clear(); ws.append_row(headers)
            for entry in st.session_state.db[tranche].get(section,[]):
                d = row_vers_dict(section, entry)
                ws.append_row([d.get(h,"") for h in headers], value_input_option="USER_ENTERED")
                total += 1
    st.success(f"Export complet : {total} lignes envoyees.")

def importer_depuis_sheets():
    client = get_gsheet_client()
    if not client: st.error("Connexion impossible."); return
    spreadsheet = get_spreadsheet(client)
    if not spreadsheet: st.error("Sheet introuvable."); return
    total = 0
    for tranche in ["Tranche 3","Tranche 4","Tranche 5"]:
        for section in HEADERS:
            try:
                ws = spreadsheet.worksheet(SHEET_TAB_MAP[tranche][section])
            except Exception:
                continue
            local_list = st.session_state.db[tranche].get(section,[])
            def cle(e): return (e.get("Date",""), e.get("Fournisseur",e.get("Produit",e.get("Nom",e.get("Type","")))))
            existing = {cle(e) for e in local_list}
            for rec in ws.get_all_records():
                entry = dict_vers_local(section, rec)
                if cle(entry) not in existing:
                    local_list.append(entry); existing.add(cle(entry)); total += 1
            st.session_state.db[tranche][section] = local_list
    sauvegarder_donnees()
    st.success(f"Import termine : {total} entrees fusionnees.")

def charger_depuis_sheets_au_demarrage():
    client = get_gsheet_client()
    if not client: return
    spreadsheet = get_spreadsheet(client)
    if not spreadsheet: return
    for tranche in ["Tranche 3","Tranche 4","Tranche 5"]:
        for section in HEADERS:
            try:
                ws = spreadsheet.worksheet(SHEET_TAB_MAP[tranche][section])
                records = ws.get_all_records()
                st.session_state.db[tranche][section] = [dict_vers_local(section,r) for r in records]
            except Exception:
                continue
    sauvegarder_donnees()

# ============================================================
# SAUVEGARDE LOCALE
# ============================================================

DB_FILE = "data_chantier_v2.pkl"

def charger_donnees():
    vide = {
        "Tranche 3":{"marchandises":[],"elec":[],"plomb":[],"marbre":[],"ceram":[]},
        "Tranche 4":{"marchandises":[],"elec":[],"plomb":[],"marbre":[],"ceram":[]},
        "Tranche 5":{"marchandises":[],"elec":[],"plomb":[],"marbre":[],"ceram":[]},
        "config":{"fournisseurs":DEFAUT_FRS.copy(),"produits_elec":DEFAUT_ELEC.copy(),"produits_plomb":DEFAUT_PLOMB.copy()}
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE,"rb") as f:
                data = pickle.load(f)
                for t in ["Tranche 3","Tranche 4","Tranche 5"]:
                    if t not in data: data[t] = vide[t]
                if "config" not in data: data["config"] = vide["config"]
                return data
        except: return vide
    return vide

def sauvegarder_donnees():
    with open(DB_FILE,"wb") as f:
        pickle.dump(st.session_state.db, f)

# ============================================================
# DEMARRAGE
# ============================================================

if "db" not in st.session_state:
    st.session_state.db = charger_donnees()

if "sheets_loaded" not in st.session_state:
    charger_depuis_sheets_au_demarrage()
    st.session_state.sheets_loaded = True

cfg = st.session_state.db["config"]

# ============================================================
# GENERATEUR PDF — avec colonne TOTAL pour elec/plomb/marbre
# ============================================================

def creer_pdf_section(titre, data_list, type_rapport):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",14)
    pdf.cell(0, 10, f"RAPPORT : {titre}", ln=True, align="C")
    pdf.set_font("Arial","I",9)
    pdf.cell(0, 6, f"Edite le {datetime.date.today().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(4)

    data_list = [r for r in data_list if r.get("Date","") or r.get("Fournisseur","") or r.get("Produit","") or r.get("Type","")]

    if not data_list:
        pdf.set_font("Arial","I",10)
        pdf.cell(0,10,"Aucune donnee enregistree.", ln=True)
        return pdf.output(dest="S").encode("latin-1")

    pdf.set_font("Arial","B",8)
    pdf.set_fill_color(210, 220, 235)

    if type_rapport == "marchandises":
        cols = ["DATE","FOURNISSEUR","DESIGNATION"]
        w    = [30, 55, 105]
        for i,c in enumerate(cols): pdf.cell(w[i],10,c,1,0,"C",True)
        pdf.ln()
        pdf.set_font("Arial","",8)
        for r in data_list:
            pdf.cell(30,8,str(r.get("Date","-")),1)
            pdf.cell(55,8,str(r.get("Fournisseur","-"))[:30],1)
            pdf.cell(105,8,str(r.get("Designation","-"))[:65],1,1)

    elif type_rapport == "marbre":
        cols = ["DATE","INTERV.","TYPE","LIEU","M2"]
        w    = [22,28,48,60,22]
        for i,c in enumerate(cols): pdf.cell(w[i],10,c,1,0,"C",True)
        pdf.ln()
        pdf.set_font("Arial","",7)
        total_m2 = 0
        for r in data_list:
            surf = 0
            try: surf = float(r.get("Surface",0))
            except: pass
            total_m2 += surf
            pdf.cell(22,8,str(r.get("Date","-")),1)
            pdf.cell(28,8,str(r.get("Nom","-")),1)
            pdf.cell(48,8,str(r.get("Type","-"))[:32],1)
            pdf.cell(60,8,str(r.get("Lieu","-"))[:42],1)
            pdf.cell(22,8,f"{surf} m2",1,1)
        pdf.set_font("Arial","B",8)
        pdf.set_fill_color(230,230,230)
        pdf.cell(158,8,"TOTAL",1,0,"R",True)
        pdf.cell(22,8,f"{total_m2:.2f} m2",1,1,"C",True)

    elif type_rapport in ("elec","plomb"):
        cols = ["DATE","PRODUIT","QTE","LIEU"]
        w    = [25,65,20,80]
        for i,c in enumerate(cols): pdf.cell(w[i],10,c,1,0,"C",True)
        pdf.ln()
        pdf.set_font("Arial","",8)
        total_qte = 0
        for r in data_list:
            qte = 0
            try: qte = int(float(str(r.get("Qte","0") or "0")))
            except: pass
            total_qte += qte
            pdf.cell(25,8,str(r.get("Date","-")),1)
            pdf.cell(65,8,str(r.get("Produit","-"))[:38],1)
            pdf.cell(20,8,str(qte),1)
            pdf.cell(80,8,str(r.get("Lieu","-"))[:48],1,1)
        pdf.set_font("Arial","B",8)
        pdf.set_fill_color(230,230,230)
        pdf.cell(170,8,"TOTAL",1,0,"R",True)
        pdf.cell(20,8,str(total_qte),1,1,"C",True)

    elif type_rapport == "ceram":
        cols = ["DATE","ZONE","IMMEUBLE"]
        w    = [25,65,100]
        for i,c in enumerate(cols): pdf.cell(w[i],10,c,1,0,"C",True)
        pdf.ln()
        pdf.set_font("Arial","",8)
        for r in data_list:
            pdf.cell(25,8,str(r.get("Date","-")),1)
            pdf.cell(65,8,str(r.get("Type","-"))[:38],1)
            pdf.cell(100,8,str(r.get("Immeuble","-"))[:58],1,1)

    return pdf.output(dest="S").encode("latin-1")

# ============================================================
# INTERFACE
# ============================================================

st.title("LES ORCHIDEES MANESMANE")

mode    = st.sidebar.radio("MENU",["SAISIE","CONSULTATION","CATALOGUE","GOOGLE SHEETS"])
tranche = st.sidebar.selectbox("TRANCHE",["Tranche 3","Tranche 4","Tranche 5"])
data    = st.session_state.db[tranche]

gs_client = get_gsheet_client()
if gs_client:
    st.sidebar.success("Google Sheets : Connecte")
else:
    st.sidebar.warning("Google Sheets : Non configure")

# ===== SAISIE =====
if mode == "SAISIE":
    tabs = st.tabs(["MARCHANDISES","SUIVI CHANTIER"])

    with tabs[0]:
        f    = st.selectbox("Fournisseur", cfg["fournisseurs"])
        d    = st.text_area("Designation complete")
        p_bl = st.file_uploader("Photo du Bon de Livraison", type=["jpg","png","jpeg"])
        if st.button("Valider Reception"):
            nouvelle = {"Fournisseur":f,"Designation":d,"Date":datetime.date.today().strftime("%d/%m/%Y"),"photo_bl":p_bl.getvalue() if p_bl else None}
            data["marchandises"].append(nouvelle)
            sauvegarder_donnees()
            synchro_vers_sheets(tranche,"marchandises",nouvelle)
            st.success("Enregistre !")

    with tabs[1]:
        spec = st.radio("Metier",["Electricite","Plomberie","Marbre","Ceramique"],horizontal=True)

        if spec == "Marbre":
            interv = st.selectbox("Intervenant",["FETTAH","Simo"])
            type_m = st.selectbox("Type Marbre",["Gris Bold","White Sand","Blanc Carrara"])

            if type_m == "White Sand":
                imm  = st.text_input("Immeuble")
                empl = st.selectbox("Emplacement",["Magasin","Entree"])
                p_m  = st.file_uploader("Photo de la pose")
                if st.button("Enregistrer Marbre"):
                    nouvelle = {"Nom":interv,"Type":type_m,"Fournisseur":"","Reference":"","Lieu":f"Imm {imm} - {empl}","Surface":0,"Date":datetime.date.today().strftime("%d/%m"),"photo":p_m.getvalue() if p_m else None}
                    data["marbre"].append(nouvelle); sauvegarder_donnees()
                    synchro_vers_sheets(tranche,"marbre",nouvelle); st.success("Marbre Valide")

            elif type_m == "Blanc Carrara":
                sous = st.selectbox("Element",["Dallage","Seuil","Niche","Les douches"])
                fourn,ref_v,surf,appt = "","",0.0,""
                if sous == "Dallage":
                    appt  = st.text_input("N Appartement")
                    c1,c2 = st.columns(2)
                    fourn = c1.selectbox("Fournisseur Marbre",["Graziani","Caro Colombi","Lorenzoni","MARMI BIANCO"])
                    ref_v = c2.text_input("Reference Lot/Bloc")
                    surf  = st.number_input("Surface m2", min_value=0.0)
                imm   = st.text_input("Immeuble")
                etage = st.selectbox("Etage",["RDC","1er","2eme","3eme","4eme","5eme"])
                p_m   = st.file_uploader("Photo de la pose")
                if st.button("Enregistrer Marbre"):
                    lieu = f"Imm {imm} - {etage}" + (f" - Appt {appt}" if appt else "")
                    nouvelle = {"Nom":interv,"Type":f"Blanc Carrara ({sous})","Fournisseur":fourn,"Reference":ref_v,"Lieu":lieu,"Surface":surf,"Date":datetime.date.today().strftime("%d/%m"),"photo":p_m.getvalue() if p_m else None}
                    data["marbre"].append(nouvelle); sauvegarder_donnees()
                    synchro_vers_sheets(tranche,"marbre",nouvelle); st.success("Marbre Valide")

            else:  # Gris Bold
                imm   = st.text_input("Immeuble")
                etage = st.selectbox("Etage",["RDC","1er","2eme","3eme","4eme","5eme"])
                p_m   = st.file_uploader("Photo de la pose")
                if st.button("Enregistrer Marbre"):
                    nouvelle = {"Nom":interv,"Type":type_m,"Fournisseur":"","Reference":"","Lieu":f"Imm {imm} - {etage}","Surface":0,"Date":datetime.date.today().strftime("%d/%m"),"photo":p_m.getvalue() if p_m else None}
                    data["marbre"].append(nouvelle); sauvegarder_donnees()
                    synchro_vers_sheets(tranche,"marbre",nouvelle); st.success("Marbre Valide")

        elif spec == "Ceramique":
            z  = st.selectbox("Zone",["SDB","Cuisine","Chambre","Terrasse Immeuble","Terrasse"])
            im = st.text_input("Immeuble")
            if z != "Terrasse Immeuble":
                et = st.selectbox("Etage",["RDC","1","2","3","4","5"])
                lieu_c = f"Imm {im} - {et}"
            else:
                lieu_c = f"Imm {im}"
            p_c = st.file_uploader("Photo")
            if st.button("Enregistrer Ceramique"):
                nouvelle = {"Type":z,"Immeuble":lieu_c,"Date":datetime.date.today().strftime("%d/%m"),"photo":p_c.getvalue() if p_c else None}
                data["ceram"].append(nouvelle); sauvegarder_donnees()
                synchro_vers_sheets(tranche,"ceram",nouvelle); st.success("Ceramique Validee")

        else:  # Elec / Plomb
            prods = cfg["produits_elec"] if spec == "Electricite" else cfg["produits_plomb"]
            p_sel = st.selectbox("Produit", prods)
            q     = st.number_input("Quantite", min_value=1)
            loc   = st.text_input("Localisation ex: Imm 2 - Appt 4")
            p_s   = st.file_uploader("Photo")
            if st.button(f"Valider {spec}"):
                key = "elec" if spec == "Electricite" else "plomb"
                nouvelle = {"Produit":p_sel,"Qte":q,"Lieu":loc,"Date":datetime.date.today().strftime("%d/%m"),"photo":p_s.getvalue() if p_s else None}
                data[key].append(nouvelle); sauvegarder_donnees()
                synchro_vers_sheets(tranche,key,nouvelle); st.success("Enregistre !")

# ===== CONSULTATION =====
elif mode == "CONSULTATION":
    data = st.session_state.db[tranche]
    cat  = st.radio("Section",["Marchandises","Suivi Chantier"],horizontal=True)

    if cat == "Marchandises":
        st.download_button("Rapport PDF Marchandises", data=creer_pdf_section("MARCHANDISES",data["marchandises"],"marchandises"), file_name="Marchandises.pdf")
        if not data["marchandises"]:
            st.info("Aucune marchandise pour cette tranche.")
        for i, m in enumerate(reversed(data["marchandises"])):
            st.markdown("---")
            st.markdown(f"**{m.get('Fournisseur', '-')}** — {m.get('Date', '-')}")
            st.write(m.get("Designation", ""))
            if m.get("photo_bl"):
                st.image(m["photo_bl"], width=300)
            if st.button("Supprimer", key=f"del_m_{i}"):
                e = data["marchandises"][-(i+1)]
                supprimer_ligne_sheet(tranche, "marchandises", e)
                data["marchandises"].pop(-(i+1))
                sauvegarder_donnees()
                st.rerun()

    else:
        filtre = st.selectbox("Filtrer Metier",["Marbre","Ceramique","Electricite","Plomberie"])
        k = {"Marbre":"marbre","Ceramique":"ceram","Electricite":"elec","Plomberie":"plomb"}[filtre]
        pk = {"Marbre":"marbre","Ceramique":"ceram","Electricite":"elec","Plomberie":"plomb"}[filtre]
        st.download_button(f"Rapport PDF {filtre}", data=creer_pdf_section(filtre.upper(),data[k],pk), file_name=f"{filtre}.pdf")
        if not data[k]:
            st.info(f"Aucune donnee {filtre} pour cette tranche.")
        for i, entry in enumerate(reversed(data[k])):
            st.markdown("---")
            st.markdown(f"**{entry.get('Type', entry.get('Produit', '-'))}** — {entry.get('Date', '-')}")
            c1, c2 = st.columns(2)
            with c1:
                if entry.get("Lieu"):      st.write(f"Lieu: {entry['Lieu']}")
                if entry.get("Immeuble"):  st.write(f"Immeuble: {entry['Immeuble']}")
                qte_val = entry.get("Qte", "")
                if qte_val:                st.write(f"Quantite: {qte_val}")
                if entry.get("Surface"):   st.write(f"Surface: {entry['Surface']} m2")
                if entry.get("Nom"):       st.write(f"Intervenant: {entry['Nom']}")
            with c2:
                if entry.get("photo"):     st.image(entry["photo"], width=250)
            if st.button("Supprimer", key=f"del_{k}_{i}"):
                e = data[k][-(i+1)]
                supprimer_ligne_sheet(tranche, k, e)
                data[k].pop(-(i+1))
                sauvegarder_donnees()
                st.rerun()

# ===== CATALOGUE =====
elif mode == "CATALOGUE":
    st.header("Configuration")
    c1,c2,c3 = st.tabs(["Fournisseurs","Elec","Plomb"])
    with c1:
        nf = st.text_input("Nouveau Fournisseur")
        if st.button("Ajouter FRS") and nf: cfg["fournisseurs"].append(nf); sauvegarder_donnees(); st.success("Ajoute")
        st.write(cfg["fournisseurs"])
    with c2:
        ne = st.text_input("Nouveau Produit Elec")
        if st.button("Ajouter Elec") and ne: cfg["produits_elec"].append(ne); sauvegarder_donnees(); st.success("Ajoute")
        st.write(cfg["produits_elec"])
    with c3:
        np2 = st.text_input("Nouveau Produit Plomb")
        if st.button("Ajouter Plomb") and np2: cfg["produits_plomb"].append(np2); sauvegarder_donnees(); st.success("Ajoute")
        st.write(cfg["produits_plomb"])

# ===== GOOGLE SHEETS =====
elif mode == "GOOGLE SHEETS":
    st.header("Synchronisation Google Sheets")
    if not GSPREAD_AVAILABLE: st.error("gspread et google-auth non installes."); st.stop()
    if gs_client:
        st.success("Connecte au compte de service Google.")
        sp = get_spreadsheet(gs_client)
        if sp: st.info(f"Google Sheet ouvert : {sp.title}")
        else:  st.error("Sheet introuvable. Verifiez spreadsheet_id dans les secrets.")
    else:
        st.error("Non connecte. Configurez vos secrets Streamlit.")
    st.divider()
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Export complet vers Google Sheets**")
        st.caption("Ecrase le Sheet avec toutes les donnees locales.")
        if st.button("Lancer export complet", type="primary"):
            with st.spinner("Export..."): exporter_tout_vers_sheets()
    with c2:
        st.markdown("**Import Google Sheets vers Local**")
        st.caption("Fusionne les donnees du Sheet sans doublon.")
        if st.button("Lancer import / fusion"):
            with st.spinner("Import..."): importer_depuis_sheets()
    st.divider()
    st.subheader("Structure des onglets")
    onglets = [{"Onglet":tab,"Tranche":tr,"Section":sec.capitalize(),"Colonnes":", ".join(HEADERS[sec])} for tr,secs in SHEET_TAB_MAP.items() for sec,tab in secs.items()]
    st.dataframe(pd.DataFrame(onglets), use_container_width=True, hide_index=True)
