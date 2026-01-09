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

# --- MOTEUR PDF ---
def hex_to_rgb(hex_code):
    return tuple(int(hex_code.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

class PDFTemplate(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 30)
        else:
            self.set_font('Arial', 'B', 24)
            r, g, b = hex_to_rgb(YASSIR_PURPLE)
            self.set_text_color(r, g, b)
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
        self.set_y(-20)
        self.set_font('Arial', '', 7)
        self.set_text_color(120)
        self.multi_cell(0, 3, "YASSIR MAROC SARL au capital de 2,000,000 DH\nVILLA 269 LOTISSEMENT MANDARONA SIDI MAAROUF CASABLANCA - Maroc\nICE N°002148105000084 - RC 413733 - IF 26164744", 0, 'C')
        self.set_y(-10)
        r, g, b = hex_to_rgb(YASSIR_PURPLE)
        self.set_text_color(r, g, b)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

# --- FONCTIONS GENERATION PDF (Facture & Détail) ---
# ... (Copiez ici les fonctions generate_invoice_pdf et generate_detail_pdf du code précédent) ...
# Pour gagner de la place ici, je réutilise la logique exacte que nous avons validée.
# Assurez-vous d'inclure les fonctions complètes dans votre fichier final.

def generate_invoice_pdf(client_data, totals):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    r, g, b = hex_to_rgb(YASSIR_PURPLE)

    # 1. EN-TÊTE
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r, g, b)
    pdf.cell(90, 8, "FACTURE COMMISSION", 0, 1, 'R')
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N°: {client_data['ref']}", 0, 1, 'R')
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')

    # 2. CLIENT
    start_y = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(230, 230, 230)
    pdf.rect(10, start_y, 90, 35, 'FD')
    pdf.set_fill_color(r, g, b)
    pdf.rect(10, start_y, 2, 35, 'F')
    
    pdf.set_xy(15, start_y + 3)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, f"{client_data['name']}", 0, 1, 'L')
    pdf.set_xy(15, start_y + 9)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(50)
    pdf.cell(80, 5, f"{client_data['address']}", 0, 1, 'L')
    pdf.set_xy(15, start_y + 14)
    pdf.cell(80, 5, f"{client_data['city']}", 0, 1, 'L')
    pdf.set_xy(15, start_y + 19)
    pdf.cell(80, 5, f"ICE: {client_data['ice']}", 0, 1, 'L')
    if client_data['rc']:
        pdf.set_xy(15, start_y + 24)
        pdf.cell(80, 5, f"RC: {client_data['rc']}", 0, 1, 'L')

    # 3. TABLEAU
    pdf.set_y(100)
    pdf.set_fill_color(r, g, b)
    pdf.set_draw_color(r, g, b)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    cols = [60, 40, 40, 50]
    headers = ['Période', 'Ventes TTC', 'Taux Comm.', 'Commission HT']
    for i, h in enumerate(headers):
        pdf.cell(cols[i], 10, h, 1, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_draw_color(200, 200, 200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    h_row = 10
    pdf.cell(cols[0], h_row, f"{client_data['period']}", 1, 0, 'C')
    pdf.cell(cols[1], h_row, f"{totals['sales']:,.2f}", 1, 0, 'C')
    pdf.cell(cols[2], h_row, f"{client_data['rate']}%", 1, 0, 'C')
    pdf.cell(cols[3], h_row, f"{totals['comm_ht']:,.2f}", 1, 1, 'C')

    # 4. TOTAUX
    pdf.ln(5)
    x_totals = 110
    def print_total(label, value, bold=False, bg=False):
        pdf.set_x(x_totals)
        pdf.set_font('Arial', 'B' if bold else '', 9)
        pdf.set_text_color(0)
        pdf.set_draw_color(200)
        if bg:
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255)
            pdf.cell(50, 8, label, 0, 0, 'L', 1)
            pdf.cell(40, 8, f"{value:,.2f} DH", 0, 1, 'R', 1)
        else:
            pdf.cell(50, 7, label, 1, 0, 'L')
            pdf.cell(40, 7, f"{value:,.2f}", 1, 1, 'R')

    print_total("Total Commission HT", totals['comm_ht'])
    print_total("TVA 20%", totals['tva'])
    print_total("Total Facture TTC", totals['invoice_ttc'], bold=True)
    pdf.ln(2)
    print_total("NET À PAYER", totals['net_pay'], bold=True, bg=True)

    # Info légale
    pdf.set_y(160)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    pdf.cell(0, 5, f"Arrêté la présente facture à la somme de : {totals['net_pay']:,.2f} Dirhams", 0, 1, 'L')
    pdf.cell(0, 5, "Mode de règlement : Virement bancaire sous 30 jours", 0, 1, 'L')
    return pdf.output(dest='S').encode('latin-1')

def generate_detail_pdf(client_data, df_detail, mapping):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    r, g, b = hex_to_rgb(YASSIR_PURPLE)

    pdf.set_y(55)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 10, f"DÉTAIL DES COMMANDES - {client_data['period']}", 0, 1, 'C')
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_draw_color(200)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(0)
    cols = ['Date', 'ID Commande', 'Montant TTC', 'Statut']
    w = [40, 60, 40, 50]
    x_start = (210 - sum(w)) / 2
    pdf.set_x(x_start)
    for i, c in enumerate(cols):
        pdf.cell(w[i], 8, c, 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    pdf.set_draw_color(220)
    for _, row in df_detail.iterrows():
        date_val = str(row[mapping['date']])[:10]
        id_val = str(row[mapping['id']])
        try:
            raw_amt = str(row[mapping['amount']]).replace(',','.').replace('MAD','').strip()
            amt_val = float(raw_amt)
            amt_str = f"{amt_val:,.2f}"
        except:
            amt_str = "0.00"
        stat_val = str(row[mapping['status']]) if mapping['status'] != 'Aucun' else '-'
        
        pdf.set_x(x_start)
        pdf.cell(w[0], 6, date_val, 1, 0, 'C')
        pdf.cell(w[1], 6, id_val, 1, 0, 'C')
        pdf.cell(w[2], 6, amt_str, 1, 0, 'R')
        pdf.cell(w[3], 6, stat_val, 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("📄 Génération Factures")
st.markdown("Importez ici le fichier nettoyé (`Detail_Commandes...csv`) obtenu à l'étape précédente.")

# Sidebar Infos
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=150)
st.sidebar.markdown("## ⚙️ Paramètres Client")
c_name = st.sidebar.text_input("Raison Sociale", "BLUE TACOS")
c_addr = st.sidebar.text_input("Adresse", "BD MOHAMMED VI")
c_city = st.sidebar.text_input("Ville", "CASABLANCA")
c_ice = st.sidebar.text_input("ICE", "003...")
c_rc = st.sidebar.text_input("RC", "")
st.sidebar.markdown("---")
st.sidebar.markdown("## 📅 Facturation")
c_period = st.sidebar.text_input("Période", "NOVEMBRE 2025")
c_ref = st.sidebar.text_input("N° Facture", f"F-{datetime.now().strftime('%Y%m')}-001")
c_rate = st.sidebar.number_input("Taux Commission (%)", value=14.0, step=0.5)

# Main Logic
uploaded_file = st.file_uploader("📂 Fichier Détail (CSV Nettoyé)", type=['csv'])

if uploaded_file:
    try:
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')

        st.success(f"Données chargées : {len(df)} commandes.")
        
        # Auto-Mapping si possible
        cols = df.columns.tolist()
        # On essaie de deviner les colonnes si elles viennent de l'étape 1
        idx_date = cols.index("Date") if "Date" in cols else 0
        idx_id = cols.index("ID Commande") if "ID Commande" in cols else 1
        idx_amt = cols.index("Montant") if "Montant" in cols else 2
        idx_stat = cols.index("Statut") if "Statut" in cols else 3

        st.subheader("🔗 Validation des Colonnes")
        c1, c2, c3, c4 = st.columns(4)
        col_date = c1.selectbox("Date", cols, index=idx_date)
        col_id = c2.selectbox("ID Commande", cols, index=idx_id)
        col_amt = c3.selectbox("Montant", cols, index=idx_amt)
        col_stat = c4.selectbox("Statut", ["Aucun"] + cols, index=idx_stat+1)

        # Calculs
        try:
            clean_s = df[col_amt].astype(str).str.replace('MAD','').str.replace(' ','').str.replace(',','.')
            df['clean_amount'] = pd.to_numeric(clean_s, errors='coerce').fillna(0)
        except:
            df['clean_amount'] = 0

        total_sales = df['clean_amount'].sum()
        comm_ht = total_sales * (c_rate / 100)
        tva = comm_ht * 0.20
        invoice_ttc = comm_ht + tva
        net_pay = total_sales - invoice_ttc
        
        totals = {'sales': total_sales, 'comm_ht': comm_ht, 'tva': tva, 'invoice_ttc': invoice_ttc, 'net_pay': net_pay}
        client_data = {'name': c_name, 'address': c_addr, 'city': c_city, 'ice': c_ice, 'rc': c_rc, 'period': c_period, 'ref': c_ref, 'rate': c_rate}
        mapping = {'date': col_date, 'id': col_id, 'amount': col_amt, 'status': col_stat}

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ventes", f"{total_sales:,.2f}")
        m2.metric("Com. HT", f"{comm_ht:,.2f}")
        m3.metric("Facture", f"{invoice_ttc:,.2f}")
        m4.metric("Net", f"{net_pay:,.2f}")

        st.markdown("### 📥 Télécharger les Documents")
        b1, b2 = st.columns(2)
        
        pdf1 = generate_invoice_pdf(client_data, totals)
        b64_1 = base64.b64encode(pdf1).decode()
        b1.markdown(f'<a href="data:application/pdf;base64,{b64_1}" download="Facture_{c_ref}.pdf"><button style="background-color:{YASSIR_PURPLE};color:white;border:none;padding:15px;border-radius:10px;width:100%;font-weight:bold;cursor:pointer;">📄 FACTURE</button></a>', unsafe_allow_html=True)
        
        pdf2 = generate_detail_pdf(client_data, df, mapping)
        b64_2 = base64.b64encode(pdf2).decode()
        b2.markdown(f'<a href="data:application/pdf;base64,{b64_2}" download="Detail_{c_period}.pdf"><button style="background-color:#6c757d;color:white;border:none;padding:15px;border-radius:10px;width:100%;font-weight:bold;cursor:pointer;">📑 DÉTAIL</button></a>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur : {e}")
