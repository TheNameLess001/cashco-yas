import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

st.title("🛠️ Préparation des Données")
st.markdown("Transformez l'export brut `Admin Earnings` en fichier de détail compatible pour la facturation.")

# 1. UPLOAD
uploaded_file = st.file_uploader("📂 Importez le fichier brut (admin-earnings-orders-export...)", type=['csv'])

if uploaded_file:
    try:
        # Lecture flexible du CSV
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        st.success(f"Fichier chargé : {len(df)} lignes détectées.")
        
        # 2. SELECTION PARTENAIRE
        if 'restaurant name' in df.columns:
            partners = df['restaurant name'].unique().tolist()
            selected_partner = st.selectbox("🏪 Sélectionnez le Partenaire (Restaurant)", partners)
            
            # Filtrage
            df_filtered = df[df['restaurant name'] == selected_partner].copy()
            st.info(f"Commandes trouvées pour **{selected_partner}** : {len(df_filtered)}")
            
            # 3. MAPPING AUTOMATIQUE DES COLONNES
            # On crée un nouveau dataframe propre avec les colonnes attendues par la page Facture
            df_clean = pd.DataFrame()
            
            # Date (on prend 'order day')
            df_clean['Date'] = df_filtered['order day']
            
            # ID Commande (on prend 'order id')
            df_clean['ID Commande'] = df_filtered['order id']
            
            # Montant (on prend 'item total')
            # On s'assure que c'est bien numérique
            df_clean['Montant'] = df_filtered['item total']
            
            # Statut (on prend 'status')
            df_clean['Statut'] = df_filtered['status']
            
            # Aperçu
            st.markdown("### 📊 Aperçu du fichier nettoyé")
            st.dataframe(df_clean.head())
            
            # Calcul Rapide pour vérif
            total_ca = df_clean['Montant'].sum()
            st.metric("Chiffre d'Affaires (brut)", f"{total_ca:,.2f} MAD")
            
            # 4. TELECHARGEMENT
            csv_buffer = df_clean.to_csv(index=False).encode('utf-8')
            
            filename = f"Detail_Commandes_{selected_partner.replace(' ', '_')}.csv"
            
            st.download_button(
                label="📥 Télécharger le fichier prêt pour la Facturation",
                data=csv_buffer,
                file_name=filename,
                mime="text/csv",
                type="primary"
            )
            
        else:
            st.error("Erreur: La colonne 'restaurant name' est introuvable dans ce fichier.")
            st.write("Colonnes disponibles :", df.columns.tolist())

    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
