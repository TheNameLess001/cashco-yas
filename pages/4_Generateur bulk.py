import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- CONFIGURATION DU THÈME (Extrait de ton code) ---
YASSIR_PURPLE = (111, 66, 193)  # Conversion de #6f42c1 en RGB
LOGO_PATH = "logo.png"  # Assure-toi que le fichier est dans le même dossier

class InvoiceGenerator(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 30)
        else:
            self.set_font('Arial', 'B', 24)
            self.set_text_color(*YASSIR_PURPLE)
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
        self.set_text_color(*YASSIR_PURPLE)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

def safe_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def create_pdf(data, totals, filename):
    pdf = InvoiceGenerator()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre Facture
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*YASSIR_PURPLE)
    pdf.cell(90, 8, "FACTURE COMMISSION", 0, 1, 'R')
    
    # Infos Facture
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N: {data['ref']}", 0, 1, 'R')
    pdf.cell(90, 6, f"Date: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
    
    # Bloc Client (Rectangle gris avec bordure violette)
    pdf.set_fill_color(248, 248, 248)
    pdf.rect(10, 50, 90, 35, 'FD')
    pdf.set_fill_color(*YASSIR_PURPLE)
    pdf.rect(10, 50, 3, 35, 'F')
    
    pdf.set_xy(16, 54)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(data['name']), 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    pdf.cell(80, 5, safe_text(data['address']), 0, 1, 'L')
    pdf.cell(80, 5, f"ICE: {data['ice']}", 0, 1, 'L')

    # Tableau
    pdf.set_y(100)
    pdf.set_fill_color(*YASSIR_PURPLE)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    headers = ['Periode', 'Ventes TTC', 'Taux', 'Comm. HT']
    widths = [60, 40, 40, 50]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 10, h, 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.cell(widths[0], 10, data['period'], 1, 0, 'C')
    pdf.cell(widths[1], 10, f"{totals['sales']:,.2f}", 1, 0, 'C')
    pdf.cell(widths[2], 10, f"{data['rate']}%", 1, 0, 'C')
    pdf.cell(widths[3], 10, f"{totals['comm_ht']:,.2f}", 1, 1, 'C')

    # Totaux
    pdf.ln(10)
    pdf.set_x(110)
    pdf.cell(50, 7, "Total Commission HT", 1)
    pdf.cell(40, 7, f"{totals['comm_ht']:,.2f}", 1, 1, 'R')
    pdf.set_x(110)
    pdf.cell(50, 7, "TVA 20%", 1)
    pdf.cell(40, 7, f"{totals['tva']:,.2f}", 1, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_fill_color(*YASSIR_PURPLE)
    pdf.set_text_color(255)
    pdf.cell(50, 9, "NET A PAYER", 0, 0, 'L', 1)
    pdf.cell(40, 9, f"{totals['net_pay']:,.2f} DH", 0, 1, 'R', 1)

    pdf.output(filename)
    print(f"✅ Facture générée : {filename}")

# --- LOGIQUE DE TRAITEMENT ---
def process_suivi(file_path, rate=15.0):
    if not os.path.exists(file_path):
        print(f"❌ Erreur : Le fichier {file_path} est introuvable.")
        return

    # Chargement et nettoyage
    df = pd.read_csv(file_path)
    # Nettoyage de la colonne 'Total Food' (enlève 'MAD', les espaces, etc.)
    df['calc'] = pd.to_numeric(df['Total Food'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    # Paramètres par défaut
    period = "FEVRIER 2026"
    
    # On itère par restaurant pour générer des factures individuelles
    for name, group in df.groupby('restaurant name'):
        sales = group['calc'].sum()
        comm_ht = sales * (rate / 100)
        tva = comm_ht * 0.20
        ttc = comm_ht + tva
        net_pay = sales - ttc
        
        totals = {'sales': sales, 'comm_ht': comm_ht, 'tva': tva, 'net_pay': net_pay}
        data = {
            'name': name,
            'address': "Casablanca, Maroc", # À personnaliser ou extraire si dispo
            'ice': "0000000000", 
            'period': period,
            'rate': rate,
            'ref': f"INV-{datetime.now().strftime('%Y%m')}-{name[:3].upper()}"
        }
        
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).strip()
        create_pdf(data, totals, f"Facture_{clean_name}.pdf")

if __name__ == "__main__":
    # Lance le traitement sur le fichier 'suivi.csv'
    process_suivi("suivi.csv")
