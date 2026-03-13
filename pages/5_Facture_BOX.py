import streamlit as st
import pandas as pd
import datetime
import os
from fpdf import FPDF
import io
import zipfile

st.title("📄 Générateur de Factures (Design Personnalisé)")

# --- BARRE LATÉRALE : PARAMÈTRES DE DESIGN ---
st.sidebar.header("🎨 Personnalisation (La Forme)")
logo_file = st.sidebar.file_uploader("Logo de l'entreprise (PNG/JPG)", type=["png", "jpg", "jpeg"])
couleur_principale = st.sidebar.color_picker("Couleur principale (Titres/En-têtes)", "#1E3A8A")
couleur_texte = st.sidebar.color_picker("Couleur du texte", "#000000")

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

color_rgb_main = hex_to_rgb(couleur_principale)
color_rgb_text = hex_to_rgb(couleur_texte)

# --- FONCTION DE GÉNÉRATION DU PDF ---
def generer_pdf_facture(donnees, logo_path=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Couleurs par défaut
    pdf.set_text_color(*color_rgb_text)
    
    # 1. EN-TÊTE (Logo + Infos Yassir)
    if logo_path:
        # On place le logo en haut à gauche
        pdf.image(logo_path, x=10, y=10, w=30)
    else:
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(*color_rgb_main)
        pdf.cell(100, 10, "YASSIR MAROC", ln=True)
        pdf.set_text_color(*color_rgb_text)

    # Info Yassir
    pdf.set_xy(10, 30)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(100, 5, "YASSIR MAROC\nVILLA 269 LOTISSEMENT MANDARONA\nSIDI MAAROUF CASABLANCA - Maroc\nICE: 002148105000084")
    
    # Info Client (À droite)
    pdf.set_xy(110, 30)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 5, "CLIENT :", ln=True)
    pdf.set_xy(110, 35)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(90, 5, f"{donnees['client']}\n{donnees['ville']}")

    pdf.ln(10)
    
    # 2. TITRE DE LA FACTURE ET DATES
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(*color_rgb_main)
    # Réf de facture générée
    num_facture = f"{donnees['reference']}/{datetime.datetime.now().strftime('%m%y')}"
    pdf.cell(0, 10, f"FACTURE N° : {num_facture}", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(*color_rgb_text)
    pdf.cell(0, 5, f"Date de facture : {donnees['date_facture']}", ln=True, align="C")
    pdf.ln(10)
    
    # 3. TABLEAU DES LIGNES (Le Fond)
    pdf.set_fill_color(*color_rgb_main)
    pdf.set_text_color(255, 255, 255) # Texte en blanc pour l'en-tête du tableau
    pdf.set_font("Arial", "B", 11)
    
    # En-tête du tableau
    pdf.cell(140, 10, " DÉSIGNATION", border=1, fill=True)
    pdf.cell(50, 10, " TOTAL HT", border=1, fill=True, align="C", ln=True)
    
    # Lignes du tableau
    pdf.set_fill_color(240, 240, 240) # Fond gris clair
    pdf.set_text_color(*color_rgb_text)
    pdf.set_font("Arial", "", 10)
    
    designation = f"Cession BOX NEW LOGO YASSIR\nRéf N°: {donnees['reference']}"
    
    # Utilisation de multi_cell pour la désignation (pour gérer les retours à la ligne)
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.multi_cell(140, 10, designation, border=1)
    
    # Repositionnement pour la cellule de prix
    pdf.set_xy(x + 140, y)
    pdf.cell(50, 20, f"{donnees['prix_ht']:.2f} DH", border=1, align="C", ln=True)
    
    pdf.ln(10)
    
    # 4. RÉCAPITULATIF DES TOTAUX (Aligné à droite comme sur le modèle)
    pdf.set_font("Arial", "B", 10)
    pdf.set_x(110)
    pdf.cell(40, 8, "Total HT", border=1)
    pdf.cell(40, 8, f"{donnees['prix_ht']:.2f} DH", border=1, align="R", ln=True)
    
    pdf.set_x(110)
    pdf.cell(40, 8, "TVA (20%)", border=1)
    pdf.cell(40, 8, f"{donnees['tva']:.2f} DH", border=1, align="R", ln=True)
    
    pdf.set_x(110)
    pdf.set_fill_color(*color_rgb_main)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 10, "Total à payer TTC", border=1, fill=True)
    pdf.cell(40, 10, f"{donnees['prix_ttc']:.2f} DH", border=1, align="R", fill=True, ln=True)
    
    pdf.set_text_color(*color_rgb_text)
    pdf.ln(15)
    
    # 5. BAS DE PAGE (Mentions)
    pdf.set_font("Arial", "I", 9)
    montant_lettres = "Arrêté la présente facture à la somme de : " # + logique pour écrire en lettres si besoin
    pdf.cell(0, 5, montant_lettres, ln=True)
    pdf.cell(0, 5, f"{donnees['prix_ttc']:.2f} Dirhams TTC.", ln=True)
    
    # Pied de page fixe
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 4, "Tout incident de règlement peut entraîner l'envoi d'une mise en demeure.", ln=True, align="C")
    pdf.cell(0, 4, "YASSIR MAROC SARL au capital de 2,000,000 DH - ICE 002148105000084", ln=True, align="C")
    
    # Retourne le PDF sous forme de bytes
    return pdf.output(dest="S").encode("latin-1")


# --- CORPS DE L'APPLICATION ---
uploaded_file = st.file_uploader("Chargez le fichier de Suivi des ventes (CSV ou Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    df = df.dropna(subset=['Référence', 'Nom du Livreur'])
    
    # Création des options de sélection
    df['Label_Selection'] = df['Référence'].astype(str) + " - " + df['Nom du Livreur'].astype(str)
    toutes_les_options = df['Label_Selection'].tolist()

    st.write("### 📦 Sélection des factures à générer")
    
    # Toggle pour tout sélectionner
    tout_selectionner = st.checkbox("Tout sélectionner (Génération en masse)")
    
    if tout_selectionner:
        selections = toutes_les_options
        st.info(f"{len(selections)} factures seront générées.")
    else:
        selections = st.multiselect("Choisissez une ou plusieurs livraisons :", toutes_les_options)

    if selections:
        if st.button("🚀 Générer les factures", use_container_width=True):
            
            # Si un logo est uploadé, on le sauvegarde temporairement pour FPDF
            logo_path = None
            if logo_file:
                logo_path = "temp_logo.png"
                with open(logo_path, "wb") as f:
                    f.write(logo_file.getbuffer())

            # Préparer un ZIP si on génère en masse, ou un seul fichier
            if len(selections) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for sel in selections:
                        ligne = df[df['Label_Selection'] == sel].iloc[0]
                        
                        try:
                            prix_ttc = float(ligne['Prix de Vente TTC'])
                        except:
                            prix_ttc = 300.0
                        
                        donnees = {
                            "client": ligne['Nom du Livreur'],
                            "ville": ligne.get('Ville', ''),
                            "reference": ligne['Référence'],
                            "date_facture": datetime.datetime.now().strftime("%d/%m/%Y"),
                            "prix_ttc": prix_ttc,
                            "prix_ht": prix_ttc / 1.20,
                            "tva": prix_ttc - (prix_ttc / 1.20)
                        }
                        
                        pdf_bytes = generer_pdf_facture(donnees, logo_path)
                        nom_fichier = f"Facture_{donnees['reference']}_{donnees['client']}.pdf"
                        zip_file.writestr(nom_fichier, pdf_bytes)
                
                st.success("✅ Factures générées avec succès !")
                st.download_button(
                    label="📥 Télécharger toutes les factures (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="Factures_Yassir.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            
            else:
                # Génération d'un seul fichier
                ligne = df[df['Label_Selection'] == selections[0]].iloc[0]
                try:
                    prix_ttc = float(ligne['Prix de Vente TTC'])
                except:
                    prix_ttc = 300.0
                
                donnees = {
                    "client": ligne['Nom du Livreur'],
                    "ville": ligne.get('Ville', ''),
                    "reference": ligne['Référence'],
                    "date_facture": datetime.datetime.now().strftime("%d/%m/%Y"),
                    "prix_ttc": prix_ttc,
                    "prix_ht": prix_ttc / 1.20,
                    "tva": prix_ttc - (prix_ttc / 1.20)
                }
                
                pdf_bytes = generer_pdf_facture(donnees, logo_path)
                nom_fichier = f"Facture_{donnees['reference']}.pdf"
                
                st.success("✅ Facture générée avec succès !")
                st.download_button(
                    label=f"📥 Télécharger {nom_fichier}",
                    data=pdf_bytes,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    use_container_width=True
                )

            # Nettoyage du logo temporaire
            if logo_path and os.path.exists(logo_path):
                os.remove(logo_path)
