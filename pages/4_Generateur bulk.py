import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os
import zipfile
import io
import re
from num2words import num2words 

# --- CONFIGURATION DU THÈME ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_RGB = (111, 66, 193)
LOGO_PATH = "logo.png"

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

def format_date_virement(date_val):
    if pd.isna(date_val) or str(date_val).strip() == "":
        return datetime.now().strftime('%d/%m/%Y')
    
    try:
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return date_val.strftime('%d/%m/%Y')
        d_str = str(date_val).strip()
        if " " in d_str:
            d_str = d_str.split(" ")[0]
        dt = pd.to_datetime(d_str, dayfirst=True, errors='coerce')
        if not pd.isna(dt):
            return dt.strftime('%d/%m/%Y')
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

def generate_invoice_pdf(row_data, totals, invoice_date, invoice_type='commission'):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # TITRE SELON LE TYPE
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*YASSIR_RGB)
    
    if invoice_type == 'commission':
        doc_title = "FACTURE COMMISSION"
        doc_suffix = "-C"
    else:
        doc_title = "NOTE DE DÉBOURS"
        doc_suffix = "-D"
        
    pdf.cell(90, 8, doc_title, 0, 1, 'R')
    
    # Info Facture
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N: {safe_text(row_data['ref'])}{doc_suffix}", 0, 1, 'R')
    
    # DATE FACTURE
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    display_date = invoice_date if invoice_date else "-" 
    pdf.cell(90, 6, f"Date: {safe_text(display_date)}", 0, 1, 'R')
    
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
            current_y = pdf.get_y()
            pdf.set_xy(16, current_y + 1)
            pdf.cell(80, 5, f"ICE: {safe_text(ice_str)}", 0, 1, 'L')
            
    # --- TABLEAU (Même design avec 4 colonnes pour les deux documents) ---
    pdf.set_y(100)
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.set_draw_color(*YASSIR_RGB)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [60, 40, 40, 50]
    
    if invoice_type == 'commission':
        hd = ['Periode', 'Base Calcul (HT)', 'Taux Comm.', 'Commission HT']
        val_col1 = totals['sales_ht']
        val_col3 = totals['comm_ht']
    else:
        hd = ['Periode', 'Ventes (TTC)', 'Taux Comm.', 'Commission (TTC)']
        val_col1 = totals['sales_ttc']
        val_col3 = totals['inv_ttc']
        
    for i,h in enumerate(hd): 
        pdf.cell(cols[i], 10, safe_text(h), 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    period_val = str(row_data.get('Période', ''))
    
    raw_rate = row_data.get('Taux de commission', '0')
    try:
        if pd.isna(raw_rate):
            rate_val_disp = "0"
        else:
            rate_float = float(str(raw_rate).replace('%', '').replace(',', '.'))
            if rate_float < 1.0 and rate_float != 0: 
                rate_float *= 100
            rate_val_disp = f"{rate_float:g}"
    except:
        rate_val_disp = "0"
        
    pdf.cell(cols[0], 10, safe_text(period_val), 1, 0, 'C')
    pdf.cell(cols[1], 10, f"{val_col1:,.2f}", 1, 0, 'C')
    pdf.cell(cols[2], 10, f"{rate_val_disp}%", 1, 0, 'C')
    pdf.cell(cols[3], 10, f"{val_col3:,.2f}", 1, 1, 'C')

    # --- TOTAUX (Lignes du bas) ---
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
        aline("Total Commission HT", totals['comm_ht'])
        aline("TVA 20%", totals['tva'])
        aline("Total Facture TTC", totals['inv_ttc'], True, True)
        amount_to_word = totals['inv_ttc']
        word_label = "Total Facture TTC"
    else:
        aline("Total du panier (TTC)", totals['sales_ttc'])
        aline("Deduction Yassir (TTC)", totals['inv_ttc']) 
        aline("Total à payer TTC", totals['net_pay'], True, True)
        amount_to_word = totals['net_pay']
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

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- INTERFACE ---
st.title("📄 Édition Factures & Mise à jour Excel")
st.info("Génère 2 documents identiques en design : Une Facture de Commission Yassir et une Note de Débours.")

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
                st.success(f"✅ {len(df_to_process)} factures prêtes.")
                
                c1, c2 = st.columns(2)
                with c1:
                    start_idx = st.number_input("Index départ (ex: 378)", value=378, step=1)
                with c2:
                    default_suffix = datetime.now().strftime('%m-%Y')
                    date_suffix = st.text_input("Suffixe Date Réf.", value=default_suffix)
                
                if st.button("🚀 GÉNÉRER (PDF + EXCEL)"):
                    
                    zip_buffer = io.BytesIO()
                    progress_text = "Génération des documents en cours..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        
                        count = 0
                        for index, row in df_to_process.iterrows():
                            try:
                                # 1. VENTES TTC & HT
                                sales_ttc = clean_currency(row.get('Item total', 0))
                                sales_ht = sales_ttc / 1.2 
                                
                                raw_rate = row.get('Taux de commission', 0)
                                rate_decimal = 0.0
                                try:
                                    if not pd.isna(raw_rate):
                                        s_rate = str(raw_rate).replace('%', '').replace(',', '.').strip()
                                        val = float(s_rate)
                                        if val > 1.0: 
                                            rate_decimal = val / 100.0
                                        else:
                                            rate_decimal = val
                                except:
                                    rate_decimal = 0.0
                                
                                comm_ht = sales_ht * rate_decimal
                                tva = comm_ht * 0.20
                                ttc = comm_ht + tva
                                net_pay_final = sales_ttc - ttc
                                
                                totals = {
                                    'sales_ttc': sales_ttc,
                                    'sales_ht': sales_ht,
                                    'comm_ht': comm_ht, 
                                    'tva': tva, 
                                    'inv_ttc': ttc, 
                                    'net_pay': net_pay_final
                                }
                                
                                raw_date_virement = row.get('Date du virement', '')
                                invoice_date = format_date_virement(raw_date_virement)
                                
                                current_seq = start_idx + count
                                current_ref = f"{current_seq}-{date_suffix}YAS"
                                
                                df.at[index, 'Facture N°'] = current_ref
                                row['ref'] = current_ref
                                safe_name = clean_filename(row.get('Restaurant name', f'Client_{index}'))
                                
                                # GENERATION PDF 1 : FACTURE COMMISSION
                                pdf_comm = generate_invoice_pdf(row, totals, invoice_date, 'commission')
                                file_comm = f"{current_ref}-C_Facture_Commission_{safe_name}.pdf"
                                zip_file.writestr(file_comm, pdf_comm)

                                # GENERATION PDF 2 : NOTE DE DEBOURS
                                pdf_debours = generate_invoice_pdf(row, totals, invoice_date, 'debours')
                                file_debours = f"{current_ref}-D_Note_Debours_{safe_name}.pdf"
                                zip_file.writestr(file_debours, pdf_debours)
                                
                                count += 1
                                my_bar.progress(int((count / len(df_to_process)) * 100))
                                
                            except Exception as e:
                                st.error(f"Erreur ligne {index}: {e}")

                    my_bar.empty()
                    st.success(f"🎉 Terminé ! {count*2} documents générés dans l'archive zip.")
                    
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

    except Exception as e:
        st.error(f"Erreur critique: {e}")
