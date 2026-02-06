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
YASSIR_RGB = (111, 66, 193)  # Équivalent RGB pour FPDF
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Générateur de Factures", page_icon="📄", layout="wide")

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
        padding: 15px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def safe_text(text):
    """Nettoie le texte pour éviter les erreurs d'encodage"""
    if text is None: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def clean_filename(name):
    """Nettoie le nom du fichier pour le ZIP"""
    return "".join([c for c in str(name) if c.isalnum() or c in (' ', '-', '_')]).strip()

# --- CLASSE PDF (Design Yassir) ---
class PDFTemplate(FPDF):
    def header(self):
        # Logo ou Texte Yassir
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

def generate_invoice_pdf(c_data, totals):
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
    pdf.cell(90, 6, f"N: {safe_text(c_data['ref'])}", 0, 1, 'R')
    
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
    
    pdf.set_xy(16, sy+4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(c_data['name']), 0, 1, 'L')
    
    pdf.set_xy(16, sy+10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    pdf.cell(80, 5, safe_text(c_data['address'][:45]), 0, 1, 'L')
    pdf.set_xy(16, sy+15)
    pdf.cell(80, 5, f"ICE: {safe_text(c_data['ice'])}", 0, 1, 'L')
    
    # Tableau Headers
    pdf.set_y(100)
    pdf.set_fill_color(*YASSIR_RGB)
    pdf.set_draw_color(*YASSIR_RGB)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [60, 40, 40, 50]
    hd = ['Periode', 'Ventes TTC (Food)', 'Taux Comm.', 'Commission HT']
    for i,h in enumerate(hd): 
        pdf.cell(cols[i], 10, safe_text(h), 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    # Tableau Data
    pdf.cell(cols[0], 10, safe_text(c_data['period']), 1, 0, 'C')
    pdf.cell(cols[1], 10, f"{totals['sales']:,.2f}", 1, 0, 'C')
    pdf.cell(cols[2], 10, f"{c_data['rate']}%", 1, 0, 'C')
    pdf.cell(cols[3], 10, f"{totals['comm_ht']:,.2f}", 1, 1, 'C')
    
    # Totaux
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

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- INTERFACE UTILISATEUR ---
st.title("📄 Édition des Factures (Excel)")
st.markdown("Importez votre fichier **Excel (.xlsx)** pour générer les factures.")

# 1. UPLOAD DU FICHIER
uploaded_file = st.file_uploader("📂 Charger le fichier Excel", type=['xlsx'])

# 2. CONFIGURATION LATÉRALE
st.sidebar.markdown("### ⚙️ Configuration")
c_period = st.sidebar.text_input("Période", "FEVRIER 2026")
c_rate = st.sidebar.number_input("Taux de Commission %", value=15.0, step=0.5)
c_prefix = st.sidebar.text_input("Préfixe Facture", "F-2026")

df = None

if uploaded_file:
    try:
        # Lecture du fichier Excel
        df = pd.read_excel(uploaded_file)
        
        # Vérification des colonnes essentielles
        # On cherche une colonne qui ressemble à "Total Food" et "Restaurant Name"
        col_sales = next((c for c in df.columns if "total" in c.lower() and "food" in c.lower()), None)
        col_name = next((c for c in df.columns if "restaurant" in c.lower() or "name" in c.lower()), None)

        if col_sales:
            # Nettoyage des données (enlève les "MAD", espaces, etc.)
            clean_sales = df[col_sales].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['calc_sales'] = pd.to_numeric(clean_sales, errors='coerce').fillna(0)
            
            # KPI GLOBAUX
            total_sales = df['calc_sales'].sum()
            total_comm = total_sales * (c_rate/100)
            
            st.markdown("---")
            k1, k2, k3 = st.columns(3)
            k1.metric("Ventes Totales", f"{total_sales:,.2f} DH")
            k2.metric("Commission HT", f"{total_comm:,.2f} DH")
            k3.metric("Fichiers détectés", f"{len(df)} lignes")
            
            # 3. GÉNÉRATION ZIP
            st.subheader("📦 Téléchargement des Factures")
            
            if st.button("🚀 GÉNÉRER LES FACTURES (ZIP)"):
                with st.spinner("Génération en cours..."):
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        
                        # Si on a une colonne nom de restaurant, on groupe par restaurant
                        if col_name:
                            grouped = df.groupby(col_name)
                            count = 0
                            for name, group in grouped:
                                # Calculs par restaurant
                                g_sales = group['calc_sales'].sum()
                                g_comm = g_sales * (c_rate/100)
                                g_tva = g_comm * 0.20
                                g_ttc = g_comm + g_tva
                                g_net = g_sales - g_ttc
                                
                                totals = {'sales': g_sales, 'comm_ht': g_comm, 'tva': g_tva, 'inv_ttc': g_ttc, 'net_pay': g_net}
                                
                                # Données Facture
                                safe_name = clean_filename(name)
                                c_data = {
                                    'name': str(name), 
                                    'address': "Adresse Partenaire", # À adapter si colonne dispo
                                    'city': "Casablanca",
                                    'ice': "00000000", 
                                    'period': c_period, 
                                    'ref': f"{c_prefix}-{str(count+1).zfill(3)}", 
                                    'rate': c_rate
                                }
                                
                                # Création PDF
                                try:
                                    pdf_bytes = generate_invoice_pdf(c_data, totals)
                                    zip_file.writestr(f"Facture_{safe_name}.pdf", pdf_bytes)
                                    count += 1
                                except Exception as e:
                                    st.warning(f"Erreur pour {name}: {e}")
                            
                            st.success(f"✅ {count} factures générées avec succès !")
                            
                        else:
                            # Si pas de nom de restaurant, on fait une facture globale
                            st.warning("⚠️ Colonne 'Restaurant Name' non trouvée. Une seule facture globale sera générée.")
                            
                            g_tva = total_comm * 0.20
                            g_ttc = total_comm + g_tva
                            g_net = total_sales - g_ttc
                            totals = {'sales': total_sales, 'comm_ht': total_comm, 'tva': g_tva, 'inv_ttc': g_ttc, 'net_pay': g_net}
                            
                            c_data = {
                                'name': "Client Global", 'address': "-", 'city': "-", 'ice': "-", 
                                'period': c_period, 'ref': f"{c_prefix}-GLOBAL", 'rate': c_rate
                            }
                            pdf_bytes = generate_invoice_pdf(c_data, totals)
                            zip_file.writestr("Facture_Globale.pdf", pdf_bytes)

                    # Bouton de téléchargement
                    b_zip = base64.b64encode(zip_buffer.getvalue()).decode()
                    st.markdown(f'''
                        <a href="data:application/zip;base64,{b_zip}" download="Factures_{datetime.now().strftime('%Y%m%d')}.zip">
                            <button style="background-color:#28a745; color:white; border:none; padding:15px 25px; border-radius:10px; width:100%; font-size:16px; font-weight:bold; cursor:pointer;">
                            📥 TÉLÉCHARGER LE DOSSIER ZIP
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)

        else:
            st.error("❌ Impossible de trouver la colonne des ventes (ex: 'Total Food'). Vérifiez votre fichier Excel.")

    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")

else:
    st.info("👆 Veuillez uploader un fichier Excel pour commencer.")
