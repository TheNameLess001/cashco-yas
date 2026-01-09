import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os

# --- 1. CONFIGURATION & STYLE ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_GRAY = "#F8F9FA"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Génération Factures", page_icon="📄", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    .stButton>button {{
        background-color: {YASSIR_PURPLE}; color: white; border-radius: 12px;
        padding: 12px 24px; font-weight: 600; border: none; width: 100%;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ background-color: #5a32a3; transform: translateY(-2px); }}
    
    /* KPI Cards */
    div[data-testid="metric-container"] {{
        background-color: white; border-left: 5px solid {YASSIR_PURPLE};
        padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTEUR PDF (DESIGN YASSIR) ---
def hex_to_rgb(hex_code):
    return tuple(int(hex_code.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

class PDFTemplate(FPDF):
    def header(self):
        # Logo & Titre
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 30)
        else:
            self.set_font('Arial', 'B', 24)
            r, g, b = hex_to_rgb(YASSIR_PURPLE)
            self.set_text_color(r, g, b)
            self.cell(50, 15, 'Yassir', 0, 0, 'L')
        
        # Info Yassir (Émetteur)
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
        self.multi_cell(0, 3, "YASSIR MAROC SARL au capital de 2,000,000 DH\nVILLA 269 LOTISSEMENT MANDARONA SIDI MAAROUF CASABLANCA - Maroc\nICE N°002148105000084 - RC 413733 - IF 26164744", 0, 'C')
        
        # Pagination
        self.set_y(-12)
        r, g, b = hex_to_rgb(YASSIR_PURPLE)
        self.set_text_color(r, g, b)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

# --- 3. FONCTIONS GÉNÉRATION ---
def generate_invoice_pdf(c_data, totals):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    r, g, b = hex_to_rgb(YASSIR_PURPLE)

    # A. Bloc Droite (Infos Facture)
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r, g, b)
    pdf.cell(90, 8, "FACTURE COMMISSION", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N°: {c_data['ref']}", 0, 1, 'R')
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')

    # B. Bloc Gauche (Client)
    start_y = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, start_y, 90, 35, 'FD') # Cadre gris
    pdf.set_fill_color(r, g, b)
    pdf.rect(10, start_y, 3, 35, 'F')   # Barre violette
    
    pdf.set_xy(16, start_y + 4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, f"{c_data['name']}", 0, 1, 'L')
    
    pdf.set_xy(16, start_y + 10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    pdf.cell(80, 5, f"{c_data['address']}", 0, 1, 'L')
    pdf.set_xy(16, start_y + 15)
    pdf.cell(80, 5, f"{c_data['city']}", 0, 1, 'L')
    pdf.set_xy(16, start_y + 20)
    pdf.cell(80, 5, f"ICE: {c_data['ice']}", 0, 1, 'L')
    if c_data['rc']:
        pdf.set_xy(16, start_y + 25)
        pdf.cell(80, 5, f"RC: {c_data['rc']}", 0, 1, 'L')

    # C. Tableau
    pdf.set_y(100)
    pdf.set_fill_color(r, g, b)
    pdf.set_draw_color(r, g, b)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [60, 40, 40, 50] # Largeurs colonnes
    headers = ['Période', 'Ventes TTC (Food)', 'Taux Comm.', 'Commission HT']
    
    for i, h in enumerate(headers):
        pdf.cell(cols[i], 10, h, 1, 0, 'C', 1)
    pdf.ln()
    
    # Données
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    pdf.cell(cols[0], 10, f"{c_data['period']}", 1, 0, 'C')
    pdf.cell(cols[1], 10, f"{totals['sales']:,.2f}", 1, 0, 'C')
    pdf.cell(cols[2], 10, f"{c_data['rate']}%", 1, 0, 'C')
    pdf.cell(cols[3], 10, f"{totals['comm_ht']:,.2f}", 1, 1, 'C')

    # D. Totaux
    pdf.ln(8)
    x_tot = 110
    
    def add_line(label, val, bold=False, bg=False):
        pdf.set_x(x_tot)
        pdf.set_font('Arial', 'B' if bold else '', 9)
        pdf.set_text_color(0)
        
        if bg:
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255)
            pdf.cell(50, 9, label, 0, 0, 'L', 1)
            pdf.cell(40, 9, f"{val:,.2f} DH", 0, 1, 'R', 1)
        else:
            pdf.cell(50, 7, label, 1, 0, 'L')
            pdf.cell(40, 7, f"{val:,.2f}", 1, 1, 'R')

    add_line("Total Commission HT", totals['comm_ht'])
    add_line("TVA 20%", totals['tva'])
    add_line("Total Facture TTC", totals['inv_ttc'], bold=True)
    pdf.ln(2)
    # Le Net à payer pour le partenaire = Ventes - Com TTC
    add_line("NET À PAYER PARTENAIRE", totals['net_pay'], bold=True, bg=True)

    # E. Info Légale
    pdf.set_y(165)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    pdf.cell(0, 5, f"Arrêté la présente facture à la somme de : {totals['inv_ttc']:,.2f} Dirhams (TTC)", 0, 1, 'L')
    pdf.cell(0, 5, "Mode de règlement : Virement bancaire sous 30 jours", 0, 1, 'L')

    return pdf.output(dest='S').encode('latin-1')

def generate_detail_pdf(c_data, df):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    r, g, b = hex_to_rgb(YASSIR_PURPLE)

    pdf.set_y(50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 10, f"DÉTAIL DES COMMANDES - {c_data['period']}", 0, 1, 'C')
    pdf.ln(5)

    # Table Header
    pdf.set_fill_color(240)
    pdf.set_draw_color(200)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(0)
    
    cols_w = [40, 60, 40, 50] # Largeurs
    cols_n = ['Date', 'ID Commande', 'Montant Food', 'Statut'] # Noms
    
    x_start = (210 - sum(cols_w)) / 2
    pdf.set_x(x_start)
    
    for i, c in enumerate(cols_n):
        pdf.cell(cols_w[i], 8, c, 1, 0, 'C', 1)
    pdf.ln()

    # Table Body
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        # Parsing sécurisé (le fichier d'entrée a des noms standardisés maintenant)
        d_val = str(row.get('order day', '-'))[:10]
        i_val = str(row.get('order id', '-'))
        
        # Nettoyage montant
        raw_m = str(row.get('Total Food', '0')).replace('MAD','').replace(' ','').replace(',','.')
        try:
            m_val = float(raw_m)
            m_str = f"{m_val:,.2f}"
        except:
            m_str = "0.00"
            
        s_val = str(row.get('status', '-'))

        pdf.set_x(x_start)
        pdf.cell(cols_w[0], 6, d_val, 1, 0, 'C')
        pdf.cell(cols_w[1], 6, i_val, 1, 0, 'C')
        pdf.cell(cols_w[2], 6, m_str, 1, 0, 'R')
        pdf.cell(cols_w[3], 6, s_val, 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
# Sidebar
if os.path.exists(LOGO_PATH): st.sidebar.image(LOGO_PATH, width=140)
st.sidebar.markdown("### ⚙️ Paramètres Facture")

c_name = st.sidebar.text_input("Raison Sociale", "BLUE TACOS")
c_addr = st.sidebar.text_input("Adresse", "BD MOHAMMED VI")
c_city = st.sidebar.text_input("Ville", "CASABLANCA")
c_ice = st.sidebar.text_input("ICE", "003...")
c_rc = st.sidebar.text_input("RC", "")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💰 Conditions")
c_period = st.sidebar.text_input("Période", "NOVEMBRE 2025")
c_ref = st.sidebar.text_input("N° Facture", f"F-{datetime.now().strftime('%Y%m')}-001")
c_rate = st.sidebar.number_input("Taux Commission (%)", value=15.0, step=0.5, help="Le taux sera appliqué sur le Total Food.")

# Main
st.title("📄 Édition des Factures")
st.markdown("Importez le fichier **nettoyé** (étape 1) pour générer les documents officiels.")

uploaded_file = st.file_uploader("📂 Fichier 'Detail_....csv' (5 colonnes)", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # Vérification minimale des colonnes
        req_col = 'Total Food'
        if req_col not in df.columns:
            st.error(f"❌ Colonne '{req_col}' manquante. Vérifiez que vous utilisez bien le fichier généré à l'étape 1.")
        else:
            st.success(f"✅ Données chargées : {len(df)} commandes.")
            
            # --- CALCULS ---
            # Nettoyage
            clean_sales = df[req_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['calc_amount'] = pd.to_numeric(clean_sales, errors='coerce').fillna(0)
            
            total_sales = df['calc_amount'].sum()
            comm_ht = total_sales * (c_rate / 100)
            tva = comm_ht * 0.20
            inv_ttc = comm_ht + tva
            net_pay = total_sales - inv_ttc
            
            totals = {
                'sales': total_sales,
                'comm_ht': comm_ht,
                'tva': tva,
                'inv_ttc': inv_ttc,
                'net_pay': net_pay
            }
            client_data = {
                'name': c_name, 'address': c_addr, 'city': c_city,
                'ice': c_ice, 'rc': c_rc, 'period': c_period,
                'ref': c_ref, 'rate': c_rate
            }

            # --- AFFICHAGE KPI ---
            st.markdown("---")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Ventes (Total Food)", f"{total_sales:,.2f} MAD")
            k2.metric(f"Commission ({c_rate}%)", f"{comm_ht:,.2f} MAD")
            k3.metric("Facture Yassir (TTC)", f"{inv_ttc:,.2f} MAD")
            k4.metric("Net à Payer Partenaire", f"{net_pay:,.2f} MAD", delta="Final")

            # --- EXPORT PDF ---
            st.markdown("### 🖨️ Téléchargements")
            
            c_pdf1, c_pdf2 = st.columns(2)
            
            # 1. Facture
            pdf_bytes = generate_invoice_pdf(client_data, totals)
            b64_pdf = base64.b64encode(pdf_bytes).decode()
            c_pdf1.markdown(
                f'<a href="data:application/pdf;base64,{b64_pdf}" download="Facture_{c_ref}.pdf">'
                f'<button style="background-color:{YASSIR_PURPLE};color:white;border:none;padding:15px;border-radius:10px;width:100%;font-weight:bold;cursor:pointer;">'
                f'📥 TÉLÉCHARGER LA FACTURE</button></a>', 
                unsafe_allow_html=True
            )
            
            # 2. Détail
            det_bytes = generate_detail_pdf(client_data, df)
            b64_det = base64.b64encode(det_bytes).decode()
            c_pdf2.markdown(
                f'<a href="data:application/pdf;base64,{b64_det}" download="Detail_{c_period}.pdf">'
                f'<button style="background-color:#6c757d;color:white;border:none;padding:15px;border-radius:10px;width:100%;font-weight:bold;cursor:pointer;">'
                f'📑 TÉLÉCHARGER LE DÉTAIL</button></a>', 
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"Erreur de traitement : {e}")
else:
    st.info("👋 En attente du fichier CSV...")
