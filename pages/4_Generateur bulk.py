import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os
import zipfile
import io
import tempfile
from num2words import num2words 
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION DU THÈME ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_RGB = (111, 66, 193)
LOGO_PATH = "logo.png"
CACHET_PATH = "cachet.png" # NOUVEAU : Chemin par défaut du cachet

st.set_page_config(page_title="Générateur Factures Yassir", page_icon="📄", layout="wide")

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    div[data-testid="metric-container"] {{
        background-color: white; 
        border-left: 5px solid {YASSIR_PURPLE};
        border-radius: 8px; 
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def safe_text(text):
    if text is None or pd.isna(text): return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def clean_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in (' ', '-', '_')]).strip()

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    s = str(value).replace('DH', '').replace('MAD', '').replace(' ', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def parse_rate(val):
    try:
        if pd.isna(val): return 0.0
        s_rate = str(val).replace('%', '').replace(',', '.').strip()
        v = float(s_rate)
        return v / 100.0 if v > 1.0 else v
    except:
        return 0.0

def format_date_virement(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "":
        return datetime.now().strftime('%d/%m/%Y')
    try:
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return date_val.strftime('%d/%m/%Y')
        d_str = str(date_val).strip()
        if " " in d_str: d_str = d_str.split(" ")[0]
        dt = pd.to_datetime(d_str, dayfirst=True, errors='coerce')
        if not pd.isna(dt): return dt.strftime('%d/%m/%Y')
        return d_str
    except:
        return str(date_val)

# --- CLASSE PDF ---
class PDFTemplate(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH): 
            self.image(LOGO_PATH, 10, 8, 30)
        else:
            self.set_font('Arial', 'B', 24)
            self.set_text_color(*YASSIR_RGB)
            self.cell(50, 15, 'Yassir', 0, 0, 'L')
            
        self.set_xy(10, 28)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0)
        self.cell(0, 4, 'YASSIR MAROC', 0, 1, 'L')
        self.set_font('Arial', '', 8)
        self.set_text_color(80)
        self.cell(0, 4, 'VILLA 269 LOTISSEMENT MANDARONA', 0, 1, 'L')
        self.cell(0, 4, 'SIDI MAAROUF CASABLANCA - Maroc', 0, 1, 'L')
        self.cell(0, 4, 'ICE: 002148105000084', 0, 1, 'L')
        self.ln(5)

    def footer(self):
        self.set_y(-22)
        self.set_font('Arial', '', 7)
        self.set_text_color(120)
        self.multi_cell(0, 3, "YASSIR MAROC SARL au capital de 2,000,000 DH\nICE N002148105000084 - RC 413733 - IF 26164744", 0, 'C')
        self.set_y(-12)
        self.set_text_color(*YASSIR_RGB)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

def generate_invoice_pdf(row_data, invoice_type, invoice_ref, signature_path=None):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # TITRE SELON LE TYPE
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*YASSIR_RGB)
    
    doc_title = "FACTURE"
    if invoice_type == 'commission': doc_title = "FACTURE COMMISSION"
    elif invoice_type == 'debours': doc_title = "NOTE DE DÉBOURS"
        
    pdf.cell(90, 8, doc_title, 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N: {safe_text(invoice_ref)}", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {safe_text(row_data['Invoice Date Formatted'])}", 0, 1, 'R')
    
    # --- BLOC DESTINATAIRE ---
    sy = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, sy, 90, 35, 'FD')
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.rect(10, sy, 3, 35, 'F')
    
    client_name = row_data.get('Raison sociale') if pd.notna(row_data.get('Raison sociale')) else row_data.get('Restaurant name')
    pdf.set_xy(16, sy+4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(client_name), 0, 1, 'L')
    
    pdf.set_xy(16, sy+10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    adresse_text = safe_text(row_data.get('Adresse', 'Casablanca'))
    pdf.multi_cell(80, 4, adresse_text, 0, 'L')
    
    raw_ice = row_data.get('ICE')
    if pd.notna(raw_ice):
        ice_str = str(raw_ice).strip()
        if ice_str and ice_str not in ['0', '-', 'nan', 'None', '']:
            pdf.set_xy(16, pdf.get_y() + 1)
            pdf.cell(80, 5, f"ICE: {safe_text(ice_str)}", 0, 1, 'L')
            
    # --- TABLEAU ---
    pdf.set_y(100)
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.set_draw_color(*YASSIR_RGB)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [60, 40, 40, 50]
    
    if invoice_type == 'commission':
        hd = ['Periode', 'Base Calcul (HT)', 'Taux Comm.', 'Commission HT']
        val_col1 = row_data['sales_ht']
        val_col3 = row_data['comm_ht']
    elif invoice_type == 'debours':
        hd = ['Periode', 'Ventes (TTC)', 'Taux Comm.', 'Commission (TTC)']
        val_col1 = row_data['sales_ttc']
        val_col3 = row_data['inv_ttc']
    else: # grouped
        hd = ['Periode', 'Note Debours', 'Taux Comm.', 'Commission HT']
        val_col1 = row_data['sales_ttc']
        val_col3 = row_data['comm_ht']
        
    for i,h in enumerate(hd): 
        pdf.cell(cols[i], 10, safe_text(h), 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    pdf.cell(cols[0], 10, safe_text(str(row_data.get('Période', ''))), 1, 0, 'C')
    pdf.cell(cols[1], 10, f"{val_col1:,.2f}", 1, 0, 'C')
    
    rate_val = row_data['rate_decimal'] * 100 if row_data['rate_decimal'] else 0
    pdf.cell(cols[2], 10, f"{rate_val:g}%", 1, 0, 'C')
    pdf.cell(cols[3], 10, f"{val_col3:,.2f}", 1, 1, 'C')

    # --- TOTAUX ---
    pdf.ln(8)
    xt = 110
    
    def aline(l, v, b=False, bg=False):
        pdf.set_x(xt)
        pdf.set_font('Arial', 'B' if b else '', 9)
        pdf.set_text_color(0)
        if bg: 
            pdf.set_fill_color(*YASSIR_RGB)
            pdf.set_text_color(255)
            pdf.cell(50, 9, safe_text(l), 0, 0, 'L', 1)
            pdf.cell(40, 9, f"{v:,.2f} DH", 0, 1, 'R', 1)
        else: 
            pdf.cell(50, 7, safe_text(l), 1, 0, 'L')
            pdf.cell(40, 7, f"{v:,.2f}", 1, 1, 'R')

    if invoice_type == 'commission':
        aline("Total Commission HT", row_data['comm_ht'])
        aline("TVA 20%", row_data['tva'])
        aline("Total Facture TTC", row_data['inv_ttc'], True, True)
        amount_to_word = row_data['inv_ttc']
        word_label = "Total Facture TTC"
    elif invoice_type == 'debours':
        aline("Total du panier (TTC)", row_data['sales_ttc'])
        aline("Deduction Yassir (TTC)", row_data['inv_ttc']) 
        aline("Total à payer TTC", row_data['net_pay'], True, True)
        amount_to_word = row_data['net_pay']
        word_label = "Total à payer TTC"
    else: 
        aline("Total Commission HT", row_data['comm_ht'])
        aline("TVA 20%", row_data['tva'])
        aline("Total Facture TTC", row_data['inv_ttc'], True)
        aline("Total du panier", row_data['sales_ttc'])
        pdf.ln(2)
        aline("Total à payer TTC", row_data['net_pay'], True, True)
        amount_to_word = row_data['net_pay']
        word_label = "Total à payer TTC"
    
    # --- ARRETÉ DE COMPTE ---
    pdf.set_y(165)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    
    try:
        amount_to_word = round(amount_to_word, 2)
        text_amount = num2words(amount_to_word, lang='fr', to='currency', currency='DH').upper()
        text_amount = text_amount.replace('EURO', 'DIRHAM').replace('EUROS', 'DIRHAMS')
    except:
        text_amount = f"{amount_to_word:,.2f} DIRHAMS"

    pdf.multi_cell(0, 5, f"Arrete le present document a la somme de : {safe_text(text_amount)} ({word_label})", 0, 'L')
    
    rib = str(row_data.get('RIB', ''))
    if len(rib) > 5 and 'nan' not in rib.lower():
        pdf.ln(2)
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, f"RIB Paiement : {rib}", 0, 1, 'L')

    # --- SIGNATURE ---
    if signature_path and os.path.exists(signature_path):
        y_pos = pdf.get_y() + 5
        if y_pos > 250:
            pdf.add_page()
            y_pos = 20
        # x=140 pour décaler un peu à gauche, w=60 pour la taille de l'image
        pdf.image(signature_path, x=140, y=y_pos, w=60)

    return pdf.output(dest='S').encode('latin-1', errors='replace')


# --- FONCTION EXÉCUTÉE EN PARALLÈLE ---
def process_row_task(row_dict, is_separated, signature_path):
    results = []
    safe_name = clean_filename(row_dict.get('Restaurant name', f"Client_{row_dict['Original_Index']}"))
    base_ref = row_dict['Base_Ref']
    
    if is_separated:
        ref_comm = f"{base_ref}-COMMISSION"
        ref_deb = f"{base_ref}-NOTE-DEBOURS"
        
        pdf_comm = generate_invoice_pdf(row_dict, 'commission', ref_comm, signature_path)
        pdf_deb = generate_invoice_pdf(row_dict, 'debours', ref_deb, signature_path)
        
        results.append((f"{ref_comm}_{safe_name}.pdf", pdf_comm))
        results.append((f"{ref_deb}_{safe_name}.pdf", pdf_deb))
        final_excel_ref = f"{ref_comm}  /  {ref_deb}"
    else:
        pdf_grouped = generate_invoice_pdf(row_dict, 'grouped', base_ref, signature_path)
        results.append((f"{base_ref}_{safe_name}.pdf", pdf_grouped))
        final_excel_ref = base_ref
        
    return row_dict['Original_Index'], final_excel_ref, results

# --- INTERFACE ---
st.title("📄 Édition Factures & Mise à jour Excel ⚡(Rapide)")

col_options1, col_options2 = st.columns(2)

with col_options1:
    format_generation = st.radio(
        "👉 Format de génération :",
        ["Regroupé (1 document par ligne)", "Séparé (2 documents : Facture Commission + Note Débours)"],
        horizontal=False
    )

with col_options2:
    st.markdown("✍️ **Cachet et Signature**")
    st.info("💡 Placez un fichier `cachet.png` dans le dossier pour l'utiliser par défaut, ou uploadez-en un ici.")
    signature_file = st.file_uploader("Uploader une image (PNG ou JPG) pour écraser le défaut", type=['png', 'jpg', 'jpeg'])

uploaded_file = st.file_uploader("📂 Charger le fichier Excel (xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=10)
        df.columns = df.columns.str.strip()
        
        required_cols = ['Restaurant name', 'Item total', 'Facture N°', 'Date du virement']
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            st.error(f"❌ Colonnes manquantes : {', '.join(missing)}")
        else:
            df_to_process = df[df['Facture N°'].isna() | (df['Facture N°'].astype(str).str.strip() == '')].copy()
            
            if df_to_process.empty:
                st.warning("⚠️ Toutes les lignes sont déjà traitées.")
            else:
                st.success(f"✅ {len(df_to_process)} lignes prêtes à être traitées.")
                
                c1, c2 = st.columns(2)
                with c1:
                    start_idx = st.number_input("Index départ (ex: 378)", value=378, step=1)
                with c2:
                    default_suffix = datetime.now().strftime('%m-%Y')
                    date_suffix = st.text_input("Suffixe Date Réf.", value=default_suffix)
                
                if st.button("🚀 GÉNÉRER (PDF + EXCEL)"):
                    
                    # Gestion Signature (Priorité Upload > Fichier cachet.png local)
                    signature_path = None
                    if signature_file:
                        try:
                            ext = "." + signature_file.name.split(".")[-1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                                tmp.write(signature_file.getvalue())
                                signature_path = tmp.name
                        except Exception as e:
                            st.warning(f"Impossible de charger la signature uploadée : {e}")
                    elif os.path.exists(CACHET_PATH):
                        signature_path = CACHET_PATH

                    # 1. VECTORISATION PANDAS (Ultra-rapide)
                    df_to_process['sales_ttc'] = df_to_process['Item total'].apply(clean_currency)
                    df_to_process['rate_decimal'] = df_to_process['Taux de commission'].apply(parse_rate)
                    df_to_process['sales_ht'] = df_to_process['sales_ttc'] / 1.2
                    df_to_process['comm_ht'] = df_to_process['sales_ht'] * df_to_process['rate_decimal']
                    df_to_process['tva'] = df_to_process['comm_ht'] * 0.20
                    df_to_process['inv_ttc'] = df_to_process['comm_ht'] + df_to_process['tva']
                    df_to_process['net_pay'] = df_to_process['sales_ttc'] - df_to_process['inv_ttc']
                    df_to_process['Invoice Date Formatted'] = df_to_process['Date du virement'].apply(format_date_virement)
                    
                    is_separated = "Séparé" in format_generation
                    
                    # Préparation des tâches pour le multithreading
                    tasks = []
                    for count, (idx, row) in enumerate(df_to_process.iterrows()):
                        row_dict = row.to_dict()
                        row_dict['Original_Index'] = idx
                        row_dict['Base_Ref'] = f"{start_idx + count}-{date_suffix}YAS"
                        tasks.append(row_dict)
                    
                    zip_buffer = io.BytesIO()
                    progress_text = "Génération des PDF en parallèle..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    # 2. MULTITHREADING + ÉCRITURE ZIP
                    completed_count = 0
                    total_tasks = len(tasks)
                    
                    try:
                        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                            # Utilisation de 8 threads en parallèle
                            with ThreadPoolExecutor(max_workers=8) as executor:
                                futures = {executor.submit(process_row_task, t, is_separated, signature_path): t for t in tasks}
                                
                                for future in as_completed(futures):
                                    idx, final_ref, pdf_files = future.result()
                                    
                                    # Mise à jour de l'Excel
                                    df.at[idx, 'Facture N°'] = final_ref
                                    
                                    # Ajout des PDF dans le zip
                                    for filename, pdf_bytes in pdf_files:
                                        zip_file.writestr(filename, pdf_bytes)
                                    
                                    completed_count += 1
                                    
                                    # Throttle de la progress bar (mise à jour fluide)
                                    percent = int((completed_count / total_tasks) * 100)
                                    if completed_count % max(1, total_tasks // 20) == 0 or completed_count == total_tasks:
                                        my_bar.progress(percent, text=f"{progress_text} ({percent}%)")

                        my_bar.empty()
                        st.success(f"🎉 Génération terminée à la vitesse de l'éclair ! ({completed_count} lignes traitées)")
                        
                        st.markdown("---")
                        col_zip, col_xls = st.columns(2)
                        
                        b_zip = base64.b64encode(zip_buffer.getvalue()).decode()
                        file_name_zip = f"Factures_{datetime.now().strftime('%Y%m%d')}.zip"
                        col_zip.markdown(f'''
                            <a href="data:application/zip;base64,{b_zip}" download="{file_name_zip}">
                                <button style="background-color:{YASSIR_PURPLE}; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold; cursor:pointer;">
                                📦 TÉLÉCHARGER LE ZIP DES PDF
                                </button>
                            </a>
                        ''', unsafe_allow_html=True)
                        
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Suivi_Facturation')
                            
                        b_xls = base64.b64encode(excel_buffer.getvalue()).decode()
                        file_name_xls = f"Suivi_Mis_a_Jour_{datetime.now().strftime('%Y%m%d')}.xlsx"
                        col_xls.markdown(f'''
                            <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b_xls}" download="{file_name_xls}">
                                <button style="background-color:#28a745; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold; cursor:pointer;">
                                📊 TÉLÉCHARGER EXCEL MIS A JOUR
                                </button>
                            </a>
                        ''', unsafe_allow_html=True)

                    finally:
                        # On supprime uniquement si on a créé un fichier temporaire
                        if signature_file and signature_path and os.path.exists(signature_path):
                            try: os.remove(signature_path)
                            except: pass

    except Exception as e:
        st.error(f"Erreur critique: {e}")
