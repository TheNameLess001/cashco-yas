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

def extract_end_date(period_str):
    """
    Gère le format '01/04 au 15/04'.
    Récupère la date de fin et ajoute l'année en cours si manquante.
    """
    text = str(period_str).strip().lower()
    
    # 1. On sépare sur " au ", " - " ou " to "
    # On remplace tout par un séparateur unique
    text = text.replace(' au ', '|').replace(' - ', '|').replace(' to ', '|')
    
    if '|' in text:
        # On prend la partie droite (fin de période)
        end_part = text.split('|')[-1].strip()
    else:
        # Si pas de séparateur, on prend tout le texte (date unique ?)
        end_part = text

    # 2. Nettoyage (enlève espaces)
    end_part = end_part.replace(' ', '')

    # 3. Vérification du format JJ/MM (5 caractères, ex: 15/04)
    if len(end_part) == 5 and end_part[2] == '/':
        current_year = datetime.now().year
        return f"{end_part}/{current_year}"
    
    # 4. Vérification si format déjà complet (JJ/MM/AAAA)
    if len(end_part) >= 8 and '/' in end_part:
        return end_part

    # Fallback : date du jour
    return datetime.now().strftime('%d/%m/%Y')

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

def generate_invoice_pdf(row_data, totals, invoice_date):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # TITRE
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*YASSIR_RGB)
    pdf.cell(90, 8, "FACTURE", 0, 1, 'R')
    
    # Info Facture
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N: {safe_text(row_data['ref'])}", 0, 1, 'R')
    
    # DATE FACTURE (Date Fin Période)
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {safe_text(invoice_date)}", 0, 1, 'R')
    
    # --- BLOC DESTINATAIRE ---
    sy = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, sy, 90, 35, 'FD')
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.rect(10, sy, 3, 35, 'F')
    
    # Nom
    client_name = row_data.get('Raison sociale') if pd.notna(row_data.get('Raison sociale')) else row_data.get('Restaurant name')
    pdf.set_xy(16, sy+4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(client_name), 0, 1, 'L')
    
    # Adresse
    pdf.set_xy(16, sy+10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    adresse_text = safe_text(row_data.get('Adresse', 'Casablanca'))
    pdf.multi_cell(80, 4, adresse_text, 0, 'L')
    
    # ICE
    raw_ice = row_data.get('ICE')
    if pd.notna(raw_ice):
        ice_str = str(raw_ice).strip()
        if ice_str and ice_str not in ['0', '-', 'nan', 'None', '']:
            current_y = pdf.get_y()
            pdf.set_xy(16, current_y + 1)
            pdf.cell(80, 5, f"ICE: {safe_text(ice_str)}", 0, 1, 'L')
            
    # --- TABLEAU ---
    pdf.set_y(100)
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.set_draw_color(*YASSIR_RGB)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [60, 40, 40, 50]
    hd = ['Periode', 'Ventes TTC', 'Taux Comm.', 'Commission HT']
    for i,h in enumerate(hd): 
        pdf.cell(cols[i], 10, safe_text(h), 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    # Data
    period_val = str(row_data.get('Période', ''))
    raw_rate = row_data.get('Taux de commission', '0')
    try:
        if pd.isna(raw_rate):
            rate_val = "0"
        else:
            rate_float = float(str(raw_rate).replace('%', ''))
            if rate_float < 1: rate_float *= 100
            rate_val = f"{rate_float:g}"
    except:
        rate_val = "0"
    
    pdf.cell(cols[0], 10, safe_text(period_val), 1, 0, 'C')
    pdf.cell(cols[1], 10, f"{totals['sales']:,.2f}", 1, 0, 'C')
    pdf.cell(cols[2], 10, f"{rate_val}%", 1, 0, 'C')
    pdf.cell(cols[3], 10, f"{totals['comm_ht']:,.2f}", 1, 1, 'C')
    
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
        
    aline("Total Commission HT", totals['comm_ht'])
    aline("TVA 20%", totals['tva'])
    aline("Total Facture TTC", totals['inv_ttc'], True)
    pdf.ln(2)
    aline("NET A PAYER PARTENAIRE", totals['net_pay'], True, True)
    
    # ARRETÉ DE COMPTE EN LETTRES
    pdf.set_y(165)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    
    try:
        amount_to_word = totals['net_pay']
        text_amount = num2words(amount_to_word, lang='fr', to='currency', currency='DH').upper()
        text_amount = text_amount.replace('EURO', 'DIRHAM').replace('EUROS', 'DIRHAMS')
    except:
        text_amount = f"{totals['net_pay']:,.2f} DIRHAMS"

    pdf.multi_cell(0, 5, f"Arrete la presente facture a la somme de : {safe_text(text_amount)} (NET A PAYER PARTENAIRE)", 0, 'L')
    
    rib = str(row_data.get('RIB', ''))
    if len(rib) > 5 and 'nan' not in rib.lower():
        pdf.ln(2)
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, f"RIB Paiement : {rib}", 0, 1, 'L')

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- INTERFACE ---
st.title("📄 Édition Factures & Mise à jour Excel")
st.info("Période '01/04 au 15/04' -> Date Facture '15/04/202X'")

uploaded_file = st.file_uploader("📂 Charger le fichier Excel (xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        # Lecture HEADER LIGNE 11
        df = pd.read_excel(uploaded_file, header=10)
        df.columns = df.columns.str.strip()
        
        required_cols = ['Restaurant name', 'Commission YASSIR', 'Item total', 'Facture N°', 'Période']
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
                    progress_text = "Traitement en cours..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        
                        count = 0
                        for index, row in df_to_process.iterrows():
                            try:
                                # 1. CALCULS
                                sales = clean_currency(row.get('Item total', 0))
                                comm_ht = clean_currency(row.get('Commission YASSIR', 0))
                                
                                tva = comm_ht * 0.20
                                ttc = comm_ht + tva
                                net_pay_initial = sales - ttc
                                net_pay_final = net_pay_initial + tva # Net + TVA
                                
                                totals = {
                                    'sales': sales, 
                                    'comm_ht': comm_ht, 
                                    'tva': tva, 
                                    'inv_ttc': ttc, 
                                    'net_pay': net_pay_final
                                }
                                
                                # 2. DATE FACTURE
                                period_str = row.get('Période', '')
                                invoice_date = extract_end_date(period_str)
                                
                                # 3. REFERENCE
                                current_seq = start_idx + count
                                current_ref = f"{current_seq}-{date_suffix}YAS"
                                
                                df.at[index, 'Facture N°'] = current_ref
                                row['ref'] = current_ref
                                
                                # 4. PDF
                                pdf_bytes = generate_invoice_pdf(row, totals, invoice_date)
                                safe_name = clean_filename(row.get('Restaurant name', f'Client_{index}'))
                                filename = f"{current_ref}_{safe_name}.pdf"
                                
                                zip_file.writestr(filename, pdf_bytes)
                                count += 1
                                my_bar.progress(int((count / len(df_to_process)) * 100))
                                
                            except Exception as e:
                                st.error(f"Erreur ligne {index}: {e}")

                    my_bar.empty()
                    st.success(f"🎉 Terminé ! {count} factures générées.")
                    
                    st.markdown("---")
                    col_zip, col_xls = st.columns(2)
                    
                    # ZIP
                    b_zip = base64.b64encode(zip_buffer.getvalue()).decode()
                    file_name_zip = f"Factures_{datetime.now().strftime('%Y%m%d')}.zip"
                    col_zip.markdown(f'''
                        <a href="data:application/zip;base64,{b_zip}" download="{file_name_zip}">
                            <button style="background-color:{YASSIR_PURPLE}; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold; cursor:pointer;">
                            📦 TÉLÉCHARGER ZIP
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                    
                    # EXCEL
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Suivi_Facturation')
                        
                    b_xls = base64.b64encode(excel_buffer.getvalue()).decode()
                    file_name_xls = f"Suivi_Mis_a_Jour_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    col_xls.markdown(f'''
                        <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b_xls}" download="{file_name_xls}">
                            <button style="background-color:#28a745; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold; cursor:pointer;">
                            📊 TÉLÉCHARGER EXCEL
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur critique: {e}")
