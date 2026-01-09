import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os

# --- CONFIG ---
YASSIR_PURPLE = "#6f42c1"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Génération Factures", page_icon="📄", layout="wide")

# --- STYLE CSS UNIFIÉ ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}
    
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    
    /* SIDEBAR BLANCHE FORCEE */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        border-right: 2px solid {YASSIR_PURPLE};
    }}
    
    .stButton>button {{
        background-color: {YASSIR_PURPLE}; color: white; border-radius: 12px;
        padding: 12px 24px; font-weight: 600; border: none; width: 100%; transition: 0.3s;
        box-shadow: 0 4px 10px rgba(111, 66, 193, 0.2);
    }}
    .stButton>button:hover {{ background-color: #5a32a3; transform: translateY(-2px); }}
    
    div[data-testid="metric-container"] {{
        background-color: white; 
        border-left: 5px solid {YASSIR_PURPLE};
        border-radius: 8px;
        padding: 15px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOGO MENU ---
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=160)
    st.sidebar.markdown("---")

# --- MOTEUR PDF ---
def hex_to_rgb(hex_code): return tuple(int(hex_code.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

class PDFTemplate(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH): self.image(LOGO_PATH, 10, 8, 30)
        else:
            self.set_font('Arial', 'B', 24); r,g,b = hex_to_rgb(YASSIR_PURPLE); self.set_text_color(r,g,b); self.cell(50, 15, 'Yassir', 0, 0, 'L')
        self.set_xy(10, 28); self.set_font('Arial', 'B', 9); self.set_text_color(0); self.cell(0, 4, 'YASSIR MAROC', 0, 1, 'L')
        self.set_font('Arial', '', 8); self.set_text_color(80); self.cell(0, 4, 'VILLA 269 LOTISSEMENT MANDARONA', 0, 1, 'L')
        self.cell(0, 4, 'SIDI MAAROUF CASABLANCA - Maroc', 0, 1, 'L'); self.cell(0, 4, 'ICE: 002148105000084', 0, 1, 'L'); self.ln(5)

    def footer(self):
        self.set_y(-22); self.set_font('Arial', '', 7); self.set_text_color(120)
        self.multi_cell(0, 3, "YASSIR MAROC SARL au capital de 2,000,000 DH\nVILLA 269 LOTISSEMENT MANDARONA SIDI MAAROUF CASABLANCA - Maroc\nICE N°002148105000084 - RC 413733 - IF 26164744", 0, 'C')
        self.set_y(-12); r,g,b = hex_to_rgb(YASSIR_PURPLE); self.set_text_color(r,g,b); self.set_font('Arial', 'B', 8); self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

def generate_invoice_pdf(c_data, totals):
    pdf = PDFTemplate(); pdf.alias_nb_pages(); pdf.add_page(); r,g,b = hex_to_rgb(YASSIR_PURPLE)
    pdf.set_xy(110, 50); pdf.set_font('Arial', 'B', 14); pdf.set_text_color(r,g,b); pdf.cell(90, 8, "FACTURE COMMISSION", 0, 1, 'R')
    pdf.set_x(110); pdf.set_font('Arial', 'B', 10); pdf.set_text_color(0); pdf.cell(90, 6, f"N°: {c_data['ref']}", 0, 1, 'R')
    pdf.set_x(110); pdf.set_font('Arial', '', 10); pdf.cell(90, 6, f"Date: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    sy = 50; pdf.set_fill_color(248, 248, 248); pdf.set_draw_color(220, 220, 220); pdf.rect(10, sy, 90, 35, 'FD')
    pdf.set_fill_color(r,g,b); pdf.rect(10, sy, 3, 35, 'F')
    pdf.set_xy(16, sy+4); pdf.set_font('Arial', 'B', 10); pdf.set_text_color(0); pdf.cell(80, 5, f"{c_data['name']}", 0, 1, 'L')
    pdf.set_xy(16, sy+10); pdf.set_font('Arial', '', 9); pdf.set_text_color(60); pdf.cell(80, 5, f"{c_data['address'][:45]}", 0, 1, 'L')
    pdf.set_xy(16, sy+15); pdf.cell(80, 5, f"{c_data['city']}", 0, 1, 'L')
    pdf.set_xy(16, sy+20); pdf.cell(80, 5, f"ICE: {c_data['ice']}", 0, 1, 'L')
    if c_data['rc']: pdf.set_xy(16, sy+25); pdf.cell(80, 5, f"RC: {c_data['rc']}", 0, 1, 'L')
    pdf.set_y(100); pdf.set_fill_color(r,g,b); pdf.set_draw_color(r,g,b); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 9)
    cols = [60, 40, 40, 50]; hd = ['Période', 'Ventes TTC (Food)', 'Taux Comm.', 'Commission HT']
    for i,h in enumerate(hd): pdf.cell(cols[i], 10, h, 1, 0, 'C', 1)
    pdf.ln(); pdf.set_draw_color(200); pdf.set_text_color(0); pdf.set_font('Arial', '', 9)
    pdf.cell(cols[0], 10, f"{c_data['period']}", 1, 0, 'C'); pdf.cell(cols[1], 10, f"{totals['sales']:,.2f}", 1, 0, 'C')
    pdf.cell(cols[2], 10, f"{c_data['rate']}%", 1, 0, 'C'); pdf.cell(cols[3], 10, f"{totals['comm_ht']:,.2f}", 1, 1, 'C')
    pdf.ln(8); xt = 110
    def aline(l, v, b=False, bg=False):
        pdf.set_x(xt); pdf.set_font('Arial', 'B' if b else '', 9); pdf.set_text_color(0)
        if bg: pdf.set_fill_color(r,g,b); pdf.set_text_color(255); pdf.cell(50, 9, l, 0, 0, 'L', 1); pdf.cell(40, 9, f"{v:,.2f} DH", 0, 1, 'R', 1)
        else: pdf.cell(50, 7, l, 1, 0, 'L'); pdf.cell(40, 7, f"{v:,.2f}", 1, 1, 'R')
    aline("Total Commission HT", totals['comm_ht']); aline("TVA 20%", totals['tva']); aline("Total Facture TTC", totals['inv_ttc'], True)
    pdf.ln(2); aline("NET À PAYER PARTENAIRE", totals['net_pay'], True, True)
    pdf.set_y(165); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100)
    pdf.cell(0, 5, f"Arrêté la présente facture à la somme de : {totals['inv_ttc']:,.2f} Dirhams (TTC)", 0, 1, 'L')
    pdf.cell(0, 5, "Mode de règlement : Virement bancaire sous 30 jours", 0, 1, 'L')
    return pdf.output(dest='S').encode('latin-1')

def generate_detail_pdf(c_data, df):
    pdf = PDFTemplate(); pdf.alias_nb_pages(); pdf.add_page(); r,g,b = hex_to_rgb(YASSIR_PURPLE)
    pdf.set_y(50); pdf.set_font('Arial', 'B', 14); pdf.set_text_color(r,g,b); pdf.cell(0, 10, f"DÉTAIL COMMANDES - {c_data['period']}", 0, 1, 'C'); pdf.ln(5)
    pdf.set_fill_color(240); pdf.set_draw_color(200); pdf.set_font('Arial', 'B', 8); pdf.set_text_color(0)
    cw = [40, 60, 40, 50]; cn = ['Date', 'ID', 'Montant', 'Statut']; xs = (210-sum(cw))/2; pdf.set_x(xs)
    for i,c in enumerate(cn): pdf.cell(cw[i], 8, c, 1, 0, 'C', 1)
    pdf.ln(); pdf.set_font('Arial', '', 8)
    for _,row in df.iterrows():
        try: m_val = float(str(row.get('Total Food', '0')).replace('MAD','').replace(' ','').replace(',','.')); m_str = f"{m_val:,.2f}"
        except: m_str = "0.00"
        pdf.set_x(xs); pdf.cell(cw[0], 6, str(row.get('order day','-'))[:10], 1, 0, 'C'); pdf.cell(cw[1], 6, str(row.get('order id','-')), 1, 0, 'C')
        pdf.cell(cw[2], 6, m_str, 1, 0, 'R'); pdf.cell(cw[3], 6, str(row.get('status','-')), 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("📄 Édition des Factures")
uploaded_file = st.file_uploader("📂 Fichier 'Detail_....csv'", type=['csv'])

def_name = "Nom Partenaire"; df = None
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        if 'restaurant name' in df.columns: def_name = df['restaurant name'].dropna().iloc[0]
    except: pass

st.sidebar.markdown("### ⚙️ Infos Partenaire")
c_name = st.sidebar.text_input("Nom", value=def_name)
c_addr = st.sidebar.text_input("Adresse", "Adresse du restaurant...")
c_city = st.sidebar.text_input("Ville", "CASABLANCA")
c_ice = st.sidebar.text_input("ICE", "Ex: 00123...")
c_rc = st.sidebar.text_input("RC", "")
st.sidebar.markdown("---")
st.sidebar.markdown("### 💰 Conditions")
c_period = st.sidebar.text_input("Période", "NOVEMBRE 2025")
c_ref = st.sidebar.text_input("N° Facture", f"F-{datetime.now().strftime('%Y%m')}-001")
c_rate = st.sidebar.number_input("Taux %", value=15.0, step=0.5)

if df is not None:
    if 'Total Food' in df.columns:
        clean_sales = df['Total Food'].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df['calc'] = pd.to_numeric(clean_sales, errors='coerce').fillna(0)
        sales = df['calc'].sum(); comm = sales * (c_rate/100); tva = comm*0.20; ttc = comm+tva; net = sales-ttc
        
        totals = {'sales': sales, 'comm_ht': comm, 'tva': tva, 'inv_ttc': ttc, 'net_pay': net}
        c_data = {'name': c_name, 'address': c_addr, 'city': c_city, 'ice': c_ice, 'rc': c_rc, 'period': c_period, 'ref': c_ref, 'rate': c_rate}

        st.markdown("---")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ventes (Food)", f"{sales:,.2f} DH"); k2.metric("Comm HT", f"{comm:,.2f} DH"); k3.metric("TTC Yassir", f"{ttc:,.2f} DH"); k4.metric("Net", f"{net:,.2f} DH", delta="Final")

        st.markdown("### 🖨️ Téléchargements")
        c1, c2 = st.columns(2)
        b1 = base64.b64encode(generate_invoice_pdf(c_data, totals)).decode()
        c1.markdown(f'<a href="data:application/pdf;base64,{b1}" download="Facture_{c_ref}.pdf"><button>📥 TÉLÉCHARGER FACTURE</button></a>', unsafe_allow_html=True)
        b2 = base64.b64encode(generate_detail_pdf(c_data, df)).decode()
        c2.markdown(f'<a href="data:application/pdf;base64,{b2}" download="Detail.pdf"><button style="background-color:grey;">📑 TÉLÉCHARGER DÉTAIL</button></a>', unsafe_allow_html=True)
    else: st.error("❌ Colonne 'Total Food' manquante.")
