import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os
import zipfile
import io

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
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def safe_text(text):
    if text is None or pd.isna(text): return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def clean_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in (' ', '-', '_')]).strip()

def clean_currency(value):
    """Convertit une valeur (str ou float) en float propre."""
    if pd.isna(value) or value == '': return 0.0
    s = str(value).replace('DH', '').replace('MAD', '').replace(' ', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

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

def generate_invoice_pdf(row_data, totals):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*YASSIR_RGB)
    pdf.cell(90, 8, "FACTURE COMMISSION", 0, 1, 'R')
    
    # Info Facture
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N: {safe_text(row_data['ref'])}", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    # Bloc Destinataire
    sy = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, sy, 90, 35, 'FD')
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.rect(10, sy, 3, 35, 'F')
    
    # Nom: Raison sociale en priorité, sinon Restaurant Name
    client_name = row_data.get('Raison sociale') if pd.notna(row_data.get('Raison sociale')) else row_data.get('Restaurant name')
    
    pdf.set_xy(16, sy+4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(client_name), 0, 1, 'L')
    
    pdf.set_xy(16, sy+10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    pdf.cell(80, 5, safe_text(row_data.get('Adresse', 'Casablanca')), 0, 1, 'L')
    
    pdf.set_xy(16, sy+15)
    pdf.cell(80, 5, f"ICE: {safe_text(row_data.get('ICE', '-'))}", 0, 1, 'L')
    
    # Tableau Headers
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
    
    # Tableau Data
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
    
    pdf.set_y(165)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    pdf.cell(0, 5, f"Arrete la presente facture a la somme de : {totals['inv_ttc']:,.2f} Dirhams (TTC)", 0, 1, 'L')
    
    rib = str(row_data.get('RIB', ''))
    if len(rib) > 5:
        pdf.ln(5)
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, f"RIB Paiement : {rib}", 0, 1, 'L')

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- INTERFACE ---
st.title("📄 Édition Factures (Automatique)")
st.info("Le système génère uniquement les factures pour les lignes où **'Facture N°'** est vide.")

uploaded_file = st.file_uploader("📂 Charger le fichier Excel (xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        # LECTURE AVEC HEADER=10 (Ligne 11)
        df = pd.read_excel(uploaded_file, header=10)
        df.columns = df.columns.str.strip()
        
        required_cols = ['Restaurant name', 'Commission YASSIR', 'Item total', 'Facture N°']
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            st.error(f"❌ Colonnes manquantes : {', '.join(missing)}")
            st.write("Colonnes détectées :", list(df.columns))
        else:
            # 1. FILTRAGE
            df_to_process = df[df['Facture N°'].isna() | (df['Facture N°'].astype(str).str.strip() == '')].copy()
            
            if df_to_process.empty:
                st.warning("⚠️ Aucune ligne à traiter.")
            else:
                st.success(f"✅ {len(df_to_process)} factures à générer.")
                st.dataframe(df_to_process[['Restaurant name', 'Commission YASSIR']].head())

                st.sidebar.subheader("🔢 Numérotation Spécifique")
                st.sidebar.info("Format : [Index]-[Mois]-[Année]YAS")
                
                # Saisie de l'index de départ (378 par défaut)
                start_idx = st.sidebar.number_input("Index de départ (ex: 378)", value=378, step=1)
                
                # Suffixe date (automatique ou manuel)
                default_date_suffix = datetime.now().strftime('%m-%Y')
                date_suffix = st.sidebar.text_input("Suffixe Date", value=default_date_suffix, help="Par défaut : Mois et Année en cours")

                if st.button("🚀 GÉNÉRER LES FACTURES (ZIP)"):
                    
                    zip_buffer = io.BytesIO()
                    progress_text = "Génération en cours..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        
                        count = 0
                        for index, row in df_to_process.iterrows():
                            try:
                                # Calculs
                                sales = clean_currency(row.get('Item total', 0))
                                comm_ht = clean_currency(row.get('Commission YASSIR', 0))
                                tva = comm_ht * 0.20
                                ttc = comm_ht + tva
                                net_pay = sales - ttc 
                                totals = {'sales': sales, 'comm_ht': comm_ht, 'tva': tva, 'inv_ttc': ttc, 'net_pay': net_pay}
                                
                                # --- FORMAT RÉFÉRENCE ---
                                # Structure : 378-05-2025YAS
                                current_seq = start_idx + count
                                current_ref = f"{current_seq}-{date_suffix}YAS"
                                row['ref'] = current_ref
                                
                                # PDF
                                pdf_bytes = generate_invoice_pdf(row, totals)
                                
                                # Nom fichier
                                safe_name = clean_filename(row.get('Restaurant name', f'Client_{index}'))
                                filename = f"{current_ref}_{safe_name}.pdf"
                                
                                zip_file.writestr(filename, pdf_bytes)
                                count += 1
                                my_bar.progress(int((count / len(df_to_process)) * 100))
                                
                            except Exception as e:
                                st.error(f"Erreur ligne {index}: {e}")

                    my_bar.empty()
                    st.success(f"🎉 Terminé ! {count} factures générées.")
                    
                    b_zip = base64.b64encode(zip_buffer.getvalue()).decode()
                    file_name_zip = f"Factures_Batch_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                    
                    st.markdown(f'''
                        <a href="data:application/zip;base64,{b_zip}" download="{file_name_zip}">
                            <button style="background-color:#28a745; color:white; border:none; padding:15px 25px; border-radius:8px; width:100%; font-size:16px; font-weight:bold; cursor:pointer;">
                            📦 TÉLÉCHARGER TOUTES LES FACTURES (.ZIP)
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur: {e}")
