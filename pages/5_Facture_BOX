import streamlit as st
import pandas as pd
import datetime
# import openpyxl # Décommentez si votre modèle est un Excel

st.title("📄 Générateur de Factures")

# 1. Chargement du fichier de suivi
uploaded_file = st.file_uploader("Chargez le fichier de Suivi des ventes (CSV ou Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Lecture du fichier selon l'extension
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    st.success("Fichier de suivi chargé avec succès !")
    
    # Nettoyer les colonnes vides si nécessaire
    df = df.dropna(subset=['Référence', 'Nom du Livreur'])

    # 2. Sélection de la livraison pour générer la facture
    # On crée une liste lisible pour le menu déroulant
    options = df['Référence'].astype(str) + " - " + df['Nom du Livreur'].astype(str)
    selection = st.selectbox("Sélectionnez la livraison à facturer :", options)

    if selection:
        # Extraire la ligne correspondante
        ref_selectionnee = selection.split(" - ")[0]
        ligne = df[df['Référence'] == ref_selectionnee].iloc[0]

        # 3. Récupération et calcul des données de la facture
        client = ligne['Nom du Livreur']
        date_sortie = ligne['Date de Sortie']
        reference = ligne['Référence']
        ville = ligne['Ville']
        
        # Gestion des prix (TTC, HT, TVA)
        try:
            prix_ttc = float(ligne['Prix de Vente TTC'])
        except:
            prix_ttc = 300.0 # Valeur par défaut si erreur
            
        prix_ht = prix_ttc / 1.20
        tva = prix_ttc - prix_ht
        
        # Formatage de la date d'aujourd'hui pour la facture
        date_facture = datetime.datetime.now().strftime("%d/%m/%Y")

        st.write("### Aperçu des données à injecter")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Client :** {client}")
            st.write(f"**Référence Box :** {reference}")
            st.write(f"**Date de sortie :** {date_sortie}")
            st.write(f"**Date de facture :** {date_facture}")
        with col2:
            st.write(f"**Total HT :** {prix_ht:.2f} DH")
            st.write(f"**TVA (20%) :** {tva:.2f} DH")
            st.write(f"**Total TTC :** {prix_ttc:.2f} DH")

        # 4. Bouton de génération
        if st.button("Générer la Facture"):
            with st.spinner('Génération en cours...'):
                
                # ==========================================
                # INSÉREZ ICI LA LOGIQUE DE VOTRE MODÈLE
                # ==========================================
                
                # Exemple si vous utilisez un template Excel (openpyxl) :
                # wb = openpyxl.load_workbook("modele_facture.xlsx")
                # sheet = wb.active
                # sheet['A10'] = client
                # sheet['C20'] = prix_ht
                # sheet['C21'] = tva
                # sheet['C22'] = prix_ttc
                # nom_fichier = f"Facture_{reference}_{client}.xlsx"
                # wb.save(nom_fichier)
                
                # Exemple factice pour l'interface :
                st.success(f"La facture pour {client} a été générée avec succès ! 🎉")
                
                # (Optionnel) Proposer le téléchargement du fichier généré
                # with open(nom_fichier, "rb") as file:
                #     st.download_button(label="📥 Télécharger la facture", data=file, file_name=nom_fichier)
