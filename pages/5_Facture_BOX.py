import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os
import zipfile
import io

# --- CONFIG ---
YASSIR_PURPLE = "#6f42c1"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Génération Factures Boxes", page_icon="📦", layout="wide")

# --- STYLE CSS (GLOBAL) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    
    /* SIDEBAR BLANCHE */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        border-right: 2px solid {YASSIR_PURPLE};
    }}
    
    /* KPI CARDS */
    div[data-testid="metric-container"] {{
        background-color: white; 
        border-left: 5px solid {YASSIR_PURPLE};
        border-radius: 8px;
        padding: 15px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=160)
    st.sidebar.markdown("---")

st.sidebar.markdown("### ✍️ Cachet & Signature")
signature_file = st.sidebar.file_uploader("Importer une signature (PNG/JPG)", type=["png", "jpg", "jpeg"])

# --- MOTEUR PDF ---
def hex_to_rgb(hex_code): 
    return tuple(int(hex_code.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

def safe_text(text):
    if text is None: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def clean_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in (' ', '-', '_')]).strip()

class PDFTemplate(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH): 
            self.image(LOGO_PATH, 10, 8, 30)
        else:
            self.set_font('Arial', 'B', 24)
            r,g,b = hex_to_rgb(YASSIR_PURPLE)
            self.set_text_color(r,g,b)
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
        self.multi_cell(0, 3, "Tout incident de reglement des echeances peut entrainer l'envoi d'une mise en demeure.\nYASSIR MAROC SARL au capital de 2,000,000 DH\nVILLA 269 LOTISSEMENT MANDARONA SIDI MAAROUF CASABLANCA - Maroc\nICE N002148105000084 - RC 413733 - IF 26164744", 0, 'C')
        
        self.set_y(-12)
        r,g,b = hex_to_rgb(YASSIR_PURPLE)
        self.set_text_color(r,g,b)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

def generate_box_invoice_pdf(c_data, signature_path=None):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    r,g,b = hex_to_rgb(YASSIR_PURPLE)
    
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r,g,b)
    pdf.cell(90, 8, "FACTURE DE CESSION", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N: {safe_text(c_data['num_facture'])}", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {safe_text(c_data['date_facture'])}", 0, 1, 'R')
    
    sy = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, sy, 90, 25, 'FD')
    pdf.set_fill_color(r,g,b)
    pdf.rect(10, sy, 3, 25, 'F')
    
    pdf.set_xy(16, sy+6)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(c_data['client'].upper()), 0, 1, 'L')
    
    pdf.set_xy(16, sy+12)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    pdf.cell(80, 5, f"Ville: {safe_text(c_data['ville'])}", 0, 1, 'L')
    
    pdf.set_y(90)
    pdf.set_fill_color(r,g,b)
    pdf.set_draw_color(r,g,b)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [140, 50]
    hd = ['DÉSIGNATION', 'TOTAL HT']
    pdf.cell(cols[0], 10, safe_text(hd[0]), 1, 0, 'L', 1)
    pdf.cell(cols[1], 10, safe_text(hd[1]), 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    x = pdf.get_x()
    y = pdf.get_y()
    designation = f"Cession BOX NEW LOGO YASSIR\nRef N: {c_data['reference']}"
    pdf.multi_cell(cols[0], 10, safe_text(designation), 1)
    
    pdf.set_xy(x + cols[0], y)
    pdf.cell(cols[1], 20, f"{c_data['prix_ht']:.2f}", 1, 1, 'C')
    
    pdf.ln(8)
    xt = 100
    
    def aline(l, v, b=False, bg=False):
        pdf.set_x(xt)
        pdf.set_font('Arial', 'B' if b else '', 9)
        pdf.set_text_color(0)
        if bg: 
            pdf.set_fill_color(r,g,b)
            pdf.set_text_color(255)
            pdf.cell(50, 9, safe_text(l), 0, 0, 'L', 1)
            pdf.cell(40, 9, f"{v:,.2f} DH", 0, 1, 'R', 1)
        else: 
            pdf.cell(50, 7, safe_text(l), 1, 0, 'L')
            pdf.cell(40, 7, f"{v:,.2f}", 1, 1, 'R')
            
    aline("Total HT", c_data['prix_ht'])
    aline("TVA 20%", c_data['tva'])
    aline("Total à payer TTC", c_data['prix_ttc'], True, True)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    pdf.cell(0, 5, f"Arrete la presente facture a la somme de : {c_data['prix_ttc']:.2f} Dirhams (TTC)", 0, 1, 'L')
    
    if signature_path and os.path.exists(signature_path):
        y_signature = pdf.get_y() + 5
        pdf.image(signature_path, x=140, y=y_signature, w=40)
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- UI ---
st.title("📄 Générateur de Factures Boxes")
st.markdown("Importez le fichier **Suivi des ventes** pour éditer vos factures au nouveau format Yassir.")

uploaded_file = st.file_uploader("📂 Fichier Excel/CSV de suivi", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file)
            
        df = df.dropna(subset=['Référence', 'Nom du Livreur'])
        df['Label_Selection'] = df['Référence'].astype(str) + " - " + df['Nom du Livreur'].astype(str)
        toutes_les_options = df['Label_Selection'].tolist()
        
        st.write("### 📦 Sélection des factures")
        tout_selectionner = st.checkbox("Tout sélectionner (Génération en masse)")
        
        if tout_selectionner:
            selections = toutes_les_options
        else:
            selections = st.multiselect("Choisissez une ou plusieurs livraisons :", toutes_les_options)

        if selections:
            # OPTIMISATION : On filtre le dataframe une seule fois !
            df_selectionne = df[df['Label_Selection'].isin(selections)]
            total_ttc_global = pd.to_numeric(df_selectionne['Prix de Vente TTC'], errors='coerce').fillna(300.0).sum()
            
            st.markdown("---")
            k1, k2 = st.columns(2)
            k1.metric("Factures sélectionnées", f"{len(selections)}")
            k2.metric("Montant TTC Global", f"{total_ttc_global:,.2f} DH")

            st.markdown("### 🖨️ Téléchargements")
            
            signature_path = None
            if signature_file:
                signature_path = "temp_signature.png"
                with open(signature_path, "wb") as f:
                    f.write(signature_file.getbuffer())

            # --- GÉNÉRATION EN MASSE (OPTIMISÉE) ---
            if len(selections) > 1:
                if st.button("🚀 GÉNÉRER LE ZIP DES FACTURES", use_container_width=True):
                    
                    # Interface de progression
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    total_fichiers = len(df_selectionne)
                    
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        
                        # Itération optimisée (on utilise iterrows au lieu de chercher la ligne à chaque fois)
                        for index, (i, ligne) in enumerate(df_selectionne.iterrows()):
                            
                            # Mise à jour de l'UI
                            progress_text.text(f"⏳ Génération {index + 1}/{total_fichiers} : Facture {ligne['Référence']}...")
                            
                            try:
                                prix_ttc = float(ligne['Prix de Vente TTC'])
                            except:
                                prix_ttc = 300.0
                            
                            c_data = {
                                "client": ligne['Nom du Livreur'],
                                "ville": ligne.get('Ville', ''),
                                "reference": ligne['Référence'],
                                "num_facture": f"{ligne['Référence']}/{datetime.now().strftime('%m%y')}",
                                "date_facture": datetime.now().strftime("%d/%m/%Y"),
                                "prix_ttc": prix_ttc,
                                "prix_ht": prix_ttc / 1.20,
                                "tva": prix_ttc - (prix_ttc / 1.20)
                            }
                            
                            try:
                                pdf_bytes = generate_box_invoice_pdf(c_data, signature_path)
                                nom_fichier = f"Facture_{clean_filename(c_data['reference'])}_{clean_filename(c_data['client'])}.pdf"
                                zip_file.writestr(nom_fichier, pdf_bytes)
                            except Exception as e:
                                st.warning(f"Erreur sur {ligne['Référence']}: {e}")
                                
                            # Mettre à jour la barre de progression
                            progress_bar.progress((index + 1) / total_fichiers)
                    
                    progress_text.empty() # Efface le texte de chargement
                    b_zip = base64.b64encode(zip_buffer.getvalue()).decode()
                    filename_zip = f"Batch_Factures_Boxes_{datetime.now().strftime('%Y%m%d')}.zip"
                    
                    st.success("✅ Fichiers prêts !")
                    st.markdown(f'''
                        <a href="data:application/zip;base64,{b_zip}" download="{filename_zip}">
                            <button style="background-color:#28a745; color:white; border:none; padding:15px 25px; border-radius:10px; width:100%; font-size:16px; font-weight:bold; cursor:pointer;">
                            📦 TÉLÉCHARGER LE DOSSIER ZIP COMPLET
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)

            # --- GÉNÉRATION UNITAIRE ---
            elif len(selections) == 1:
                ligne = df_selectionne.iloc[0]
                try:
                    prix_ttc = float(ligne['Prix de Vente TTC'])
                except:
                    prix_ttc = 300.0
                
                c_data = {
                    "client": ligne['Nom du Livreur'],
                    "ville": ligne.get('Ville', ''),
                    "reference": ligne['Référence'],
                    "num_facture": f"{ligne['Référence']}/{datetime.now().strftime('%m%y')}",
                    "date_facture": datetime.now().strftime("%d/%m/%Y"),
                    "prix_ttc": prix_ttc,
                    "prix_ht": prix_ttc / 1.20,
                    "tva": prix_ttc - (prix_ttc / 1.20)
                }
                
                try:
                    with st.spinner("Génération de la facture..."):
                        pdf_bytes = generate_box_invoice_pdf(c_data, signature_path)
                        b_pdf = base64.b64encode(pdf_bytes).decode()
                        nom_fichier = f"Facture_{clean_filename(c_data['reference'])}.pdf"
                    
                    st.markdown(f'''
                        <a href="data:application/pdf;base64,{b_pdf}" download="{nom_fichier}">
                            <button style="background-color:{YASSIR_PURPLE}; color:white; border:none; padding:15px 25px; border-radius:10px; width:100%; font-size:16px; font-weight:bold; cursor:pointer;">
                            📥 TÉLÉCHARGER LA FACTURE
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erreur PDF: {e}")

            if signature_path and os.path.exists(signature_path):
                os.remove(signature_path)

    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
else:
    st.info("Attente du fichier...")
