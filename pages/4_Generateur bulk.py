import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime
import os
import zipfile
import io

# --- CONFIGURATION ---
YASSIR_PURPLE = "#6f42c1"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Génération Factures Partenaires", page_icon="📄", layout="wide")

# --- STYLE CSS (GLOBAL) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    section[data-testid="stSidebar"] {{ background-color: #FFFFFF !important; border-right: 2px solid {YASSIR_PURPLE}; }}
    div[data-testid="metric-container"] {{
        background-color: white; 
        border-left: 5px solid {YASSIR_PURPLE};
        border-radius: 8px;
        padding: 15px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=160)
    st.sidebar.markdown("---")

st.sidebar.markdown("### ✍️ Cachet & Signature")
signature_file = st.sidebar.file_uploader("Importer une signature (PNG/JPG)", type=["png", "jpg", "jpeg"])

# --- MOTEUR PDF ---
def hex_to_rgb(hex_code): 
    return tuple(int(hex_code.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

def safe_text(text):
    if pd.isna(text): return ""
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
        self.multi_cell(0, 3, "Tout incident de règlement des échéances peut entraîner l'envoi d'une mise en demeure.\nYASSIR MAROC SARL au capital de 2,000,000 DH\nVILLA 269 LOTISSEMENT MANDARONA SIDI MAAROUF CASABLANCA - Maroc\nICE N002148105000084 - RC 413733 - IF 26164744", 0, 'C')
        self.set_y(-12)
        r,g,b = hex_to_rgb(YASSIR_PURPLE)
        self.set_text_color(r,g,b)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

def generate_invoice_pdf(c_data, signature_path=None):
    pdf = PDFTemplate()
    pdf.alias_nb_pages()
    pdf.add_page()
    r,g,b = hex_to_rgb(YASSIR_PURPLE)
    
    # En-tête Facture
    pdf.set_xy(110, 50)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r,g,b)
    pdf.cell(90, 8, "FACTURE COMMISSION", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(90, 6, f"N°: {safe_text(c_data['num_facture'])}", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 6, f"Date: {safe_text(c_data['date_facture'])}", 0, 1, 'R')
    
    # Bloc Client
    sy = 50
    pdf.set_fill_color(248, 248, 248)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, sy, 90, 35, 'FD')
    pdf.set_fill_color(r,g,b)
    pdf.rect(10, sy, 3, 35, 'F')
    
    pdf.set_xy(16, sy+4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(80, 5, safe_text(c_data['client']), 0, 1, 'L')
    
    pdf.set_xy(16, sy+10)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(60)
    pdf.cell(80, 5, safe_text(c_data['adresse'][:45]), 0, 1, 'L')
    
    pdf.set_xy(16, sy+20)
    pdf.cell(80, 5, f"ICE: {safe_text(c_data['ice'])}", 0, 1, 'L')
    
    # Tableau
    pdf.set_y(100)
    pdf.set_fill_color(r,g,b)
    pdf.set_draw_color(r,g,b)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [50, 45, 45, 50]
    hd = ['Période', 'Ventes TTC (Food)', 'Taux Comm.', 'Commission HT']
    for i,h in enumerate(hd): 
        pdf.cell(cols[i], 10, safe_text(h), 1, 0, 'C', 1)
    
    pdf.ln()
    pdf.set_draw_color(200)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    
    pdf.cell(cols[0], 10, safe_text(c_data['periode']), 1, 0, 'C')
    pdf.cell(cols[1], 10, f"{c_data['ventes']:,.2f} DH", 1, 0, 'C')
    pdf.cell(cols[2], 10, f"{c_data['taux']}%", 1, 0, 'C')
    pdf.cell(cols[3], 10, f"{c_data['ht']:,.2f} DH", 1, 1, 'C')
    
    pdf.ln(8)
    xt = 110
    
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
            pdf.cell(40, 7, f"{v:,.2f} DH", 1, 1, 'R')
            
    aline("Total Commission HT", c_data['ht'])
    aline("TVA 20%", c_data['tva'])
    aline("Total à payer TTC", c_data['ttc'], True, True)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100)
    pdf.cell(0, 5, f"Arrêté la présente facture à la somme de : {c_data['ttc']:,.2f} Dirhams (TTC)", 0, 1, 'L')
    
    if signature_path and os.path.exists(signature_path):
        y_signature = pdf.get_y() + 5
        pdf.image(signature_path, x=140, y=y_signature, w=40)
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- LECTURE ROBUSTE ET INTELLIGENTE DU FICHIER ---
def load_and_clean_data(file):
    try:
        # Lire avec header=None pour trouver la ligne contenant les titres (ex: Restaurant name)
        if file.name.endswith('.csv'):
            raw_df = pd.read_csv(file, sep=None, engine='python', header=None)
        else:
            raw_df = pd.read_excel(file, header=None)

        # Recherche de la ligne d'en-tête
        header_row_index = -1
        for i, row in raw_df.iterrows():
            if row.astype(str).str.contains('Restaurant name', case=False, na=False).any():
                header_row_index = i
                break
                
        if header_row_index == -1:
            st.error("Impossible de trouver la colonne 'Restaurant name'. Vérifiez le fichier.")
            return None

        # Re-lire le fichier en sautant les lignes inutiles au-dessus du tableau
        file.seek(0)
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python', skiprows=header_row_index)
        else:
            df = pd.read_excel(file, skiprows=header_row_index)

        # Nettoyage des noms de colonnes (enlever les espaces inutiles)
        df.columns = df.columns.str.strip()

        # CONVERSION NUMÉRIQUE SÉCURISÉE (Évite l'erreur float64)
        colonnes_numeriques = ['Item total', 'Commission YASSIR', 'HT', 'TVA', 'TTC']
        for col in colonnes_numeriques:
            if col in df.columns:
                # Remplace les erreurs (ex: lettres dans une colonne de prix) par 0.0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # Gérer le taux de commission (si c'est 0.15 on le met à 15%)
        if 'Taux de commission' in df.columns:
            df['Taux de commission'] = pd.to_numeric(df['Taux de commission'], errors='coerce').fillna(0.0)
            df['Taux de commission'] = df['Taux de commission'].apply(lambda x: x * 100 if x < 1 else x)

        # Enlever les lignes vides
        df = df.dropna(subset=['Restaurant name'])
        return df
    
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
        return None

# --- INTERFACE UTILISATEUR ---
st.title("📄 Générateur Factures Partenaires (Commissions)")
st.markdown("Importez le fichier de **Suivi des partenaires** (Excel ou CSV).")

uploaded_file = st.file_uploader("📂 Fichier Suivi des partenaires", type=["csv", "xlsx"])

if uploaded_file:
    df = load_and_clean_data(uploaded_file)
    
    if df is not None:
        # Créer des labels lisibles pour la sélection
        df['Label_Partenaire'] = df['Restaurant name'].astype(str) + " (" + df['Facture N°'].astype(str) + ")"
        toutes_les_options = df['Label_Partenaire'].tolist()
        
        st.write("### 📦 Sélection des factures")
        tout_selectionner = st.checkbox("Tout sélectionner (Génération en masse)")
        
        if tout_selectionner:
            selections = toutes_les_options
        else:
            selections = st.multiselect("Choisissez un ou plusieurs partenaires :", toutes_les_options)

        if selections:
            df_selectionne = df[df['Label_Partenaire'].isin(selections)]
            
            # Détection dynamique de la colonne HT/TTC
            col_ht = 'HT' if 'HT' in df_selectionne.columns else 'Commission YASSIR'
            
            if 'TTC' in df_selectionne.columns:
                total_ttc_global = df_selectionne['TTC'].sum()
            else:
                total_ttc_global = df_selectionne[col_ht].sum() * 1.2
            
            st.markdown("---")
            k1, k2 = st.columns(2)
            k1.metric("Factures sélectionnées", f"{len(df_selectionne)}")
            k2.metric("Montant TTC Global", f"{total_ttc_global:,.2f} DH")

            st.markdown("### 🖨️ Téléchargements")
            
            signature_path = None
            if signature_file:
                signature_path = "temp_signature.png"
                with open(signature_path, "wb") as f:
                    f.write(signature_file.getbuffer())

            # --- GÉNÉRATION EN MASSE (ZIP) ---
            if len(df_selectionne) > 1:
                if st.button("🚀 GÉNÉRER LE ZIP DES FACTURES", use_container_width=True):
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    total_fichiers = len(df_selectionne)
                    
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for index, (i, ligne) in enumerate(df_selectionne.iterrows()):
                            nom_partenaire = str(ligne.get('Restaurant name', f'Partenaire_{index}'))
                            num_facture = str(ligne.get('Facture N°', f"F-{datetime.now().strftime('%Y%m')}-{index}"))
                            
                            progress_text.text(f"⏳ Génération {index + 1}/{total_fichiers} : {nom_partenaire}...")
                            
                            date_facture = str(ligne.get('Date de Facture', datetime.now().strftime("%d/%m/%Y")))
                            ht = float(ligne.get(col_ht, 0.0))
                            ttc = float(ligne.get('TTC', ht * 1.20))
                            tva = float(ligne.get('TVA', ttc - ht))
                            
                            c_data = {
                                "client": str(ligne.get('Raison sociale', nom_partenaire)), # Raison sociale en priorité
                                "adresse": str(ligne.get('Adresse', '')),
                                "ice": str(ligne.get('ICE', '')),
                                "num_facture": num_facture,
                                "date_facture": date_facture[:10],
                                "periode": str(ligne.get('Période', '')),
                                "ventes": float(ligne.get('Item total', 0.0)),
                                "taux": float(ligne.get('Taux de commission', 15.0)),
                                "ht": ht,
                                "tva": tva,
                                "ttc": ttc
                            }
                            
                            try:
                                pdf_bytes = generate_invoice_pdf(c_data, signature_path)
                                nom_fichier = f"Facture_{clean_filename(num_facture)}_{clean_filename(nom_partenaire)}.pdf"
                                zip_file.writestr(nom_fichier, pdf_bytes)
                            except Exception as e:
                                st.warning(f"Erreur sur {nom_partenaire}: {e}")
                                
                            progress_bar.progress((index + 1) / total_fichiers)
                    
                    progress_text.empty()
                    b_zip = base64.b64encode(zip_buffer.getvalue()).decode()
                    filename_zip = f"Factures_Commissions_{datetime.now().strftime('%Y%m%d')}.zip"
                    
                    st.success("✅ Dossier généré avec succès !")
                    st.markdown(f'''
                        <a href="data:application/zip;base64,{b_zip}" download="{filename_zip}">
                            <button style="background-color:#28a745; color:white; border:none; padding:15px 25px; border-radius:10px; width:100%; font-size:16px; font-weight:bold; cursor:pointer;">
                            📦 TÉLÉCHARGER LE DOSSIER ZIP COMPLET
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)

            # --- GÉNÉRATION UNITAIRE ---
            elif len(df_selectionne) == 1:
                ligne = df_selectionne.iloc[0]
                nom_partenaire = str(ligne.get('Restaurant name', 'Partenaire'))
                num_facture = str(ligne.get('Facture N°', f"F-{datetime.now().strftime('%Y%m')}-01"))
                date_facture = str(ligne.get('Date de Facture', datetime.now().strftime("%d/%m/%Y")))
                ht = float(ligne.get(col_ht, 0.0))
                ttc = float(ligne.get('TTC', ht * 1.20))
                tva = float(ligne.get('TVA', ttc - ht))
                
                c_data = {
                    "client": str(ligne.get('Raison sociale', nom_partenaire)),
                    "adresse": str(ligne.get('Adresse', '')),
                    "ice": str(ligne.get('ICE', '')),
                    "num_facture": num_facture,
                    "date_facture": date_facture[:10],
                    "periode": str(ligne.get('Période', '')),
                    "ventes": float(ligne.get('Item total', 0.0)),
                    "taux": float(ligne.get('Taux de commission', 15.0)),
                    "ht": ht,
                    "tva": tva,
                    "ttc": ttc
                }
                
                try:
                    with st.spinner("Génération de la facture..."):
                        pdf_bytes = generate_invoice_pdf(c_data, signature_path)
                        b_pdf = base64.b64encode(pdf_bytes).decode()
                        nom_fichier = f"Facture_{clean_filename(num_facture)}.pdf"
                    
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

else:
    st.info("Attente du fichier...")
