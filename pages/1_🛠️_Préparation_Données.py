import streamlit as st
import pandas as pd
import io

# Configuration de la page
st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

st.title("🛠️ Préparation des Données (Multi-Comptes)")
st.markdown("Filtrez l'export brut `Admin Earnings` pour un ou **plusieurs restaurants** simultanément.")

# 1. UPLOAD
uploaded_file = st.file_uploader("📂 Importez le fichier brut (admin-earnings-orders-export...)", type=['csv'])

if uploaded_file:
    try:
        # Lecture flexible du CSV
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        st.success(f"✅ Fichier chargé : {len(df)} lignes détectées.")
        
        # 2. SELECTION PARTENAIRES (MULTIPLE)
        if 'restaurant name' in df.columns:
            # Récupération de la liste unique triée
            partners = sorted(df['restaurant name'].dropna().unique().tolist())
            
            # WIDGET MULTI-SELECT
            selected_partners = st.multiselect(
                "🏪 Sélectionnez le(s) Restaurant(s) à inclure :", 
                partners,
                help="Vous pouvez sélectionner plusieurs magasins pour créer un fichier consolidé."
            )
            
            if selected_partners:
                # Filtrage : On garde les lignes où le nom est DANS la liste sélectionnée
                df_filtered = df[df['restaurant name'].isin(selected_partners)].copy()
                
                st.info(f"Commandes trouvées pour **{len(selected_partners)} restaurant(s)** : {len(df_filtered)} commandes.")
                
                # 3. MAPPING AUTOMATIQUE DES COLONNES
                df_clean = pd.DataFrame()
                
                # Récupération des colonnes standards
                # On gère les variations de noms possibles
                cols = df.columns.str.lower()
                
                # Date
                if 'order day' in cols:
                    df_clean['Date'] = df_filtered['order day']
                elif 'date' in cols:
                     df_clean['Date'] = df_filtered['date']
                
                # ID
                if 'order id' in cols:
                    df_clean['ID Commande'] = df_filtered['order id']
                elif 'order_id' in cols:
                    df_clean['ID Commande'] = df_filtered['order_id']
                
                # Montant
                if 'item total' in cols:
                    df_clean['Montant'] = df_filtered['item total']
                elif 'total' in cols:
                    df_clean['Montant'] = df_filtered['total']
                
                # Statut
                if 'status' in cols:
                    df_clean['Statut'] = df_filtered['status']
                
                # Optionnel : Ajouter le nom du resto dans le fichier propre pour vérification
                df_clean['Restaurant Source'] = df_filtered['restaurant name']
                
                # Aperçu
                st.markdown("### 📊 Aperçu du fichier consolidé")
                st.dataframe(df_clean.head())
                
                # Calcul Rapide pour vérif
                # Nettoyage rapide pour l'affichage de la métrique seulement
                try:
                    clean_sum = df_clean['Montant'].astype(str).str.replace('MAD','').str.replace(' ','').astype(float).sum()
                    st.metric("Chiffre d'Affaires Total (Consolidé)", f"{clean_sum:,.2f} MAD")
                except:
                    pass
                
                # 4. TELECHARGEMENT
                csv_buffer = df_clean.to_csv(index=False).encode('utf-8')
                
                # Gestion du nom de fichier intelligent
                if len(selected_partners) == 1:
                    filename = f"Detail_Commandes_{selected_partners[0].replace(' ', '_')}.csv"
                else:
                    filename = "Detail_Commandes_Multi_Restos.csv"
                
                st.download_button(
                    label="📥 Télécharger le fichier nettoyé",
                    data=csv_buffer,
                    file_name=filename,
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.warning("👈 Veuillez sélectionner au moins un restaurant dans la liste ci-dessus.")
            
        else:
            st.error("Erreur: La colonne 'restaurant name' est introuvable dans ce fichier.")
            st.write("Colonnes disponibles :", df.columns.tolist())

    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
