import streamlit as st
import pandas as pd
import io

# Configuration de la page
st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

st.title("🛠️ Préparation des Données (Smart Select)")
st.markdown("Utilisez la **recherche intelligente** pour sélectionner rapidement des groupes de magasins (ex: tapez 'KFC' pour tous les sélectionner).")

# 1. UPLOAD
uploaded_file = st.file_uploader("📂 Importez le fichier brut (admin-earnings-orders-export...)", type=['csv'])

if uploaded_file:
    try:
        # Lecture flexible du CSV
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        st.success(f"✅ Fichier chargé : {len(df)} lignes détectées.")
        
        # 2. SELECTION INTELLIGENTE
        if 'restaurant name' in df.columns:
            # Récupération de la liste unique triée
            all_partners = sorted(df['restaurant name'].dropna().unique().tolist())
            
            # --- ZONE DE RECHERCHE RAPIDE ---
            st.markdown("### 🔍 Sélection Rapide")
            c_search, c_btn_add, c_btn_clear = st.columns([2, 1, 1])
            
            # A. Barre de recherche
            search_query = c_search.text_input("Tapez une marque (ex: KFC, Tacos, Rabat...)", placeholder="Rechercher...")
            
            # B. Calcul des correspondances
            matches = []
            if search_query:
                matches = [p for p in all_partners if search_query.lower() in p.lower()]
            
            # C. Initialisation Session State (Mémoire)
            if 'selected_partners_state' not in st.session_state:
                st.session_state['selected_partners_state'] = []

            # D. Boutons d'action
            with c_btn_add:
                st.write("") # Spacer pour aligner le bouton
                if search_query:
                    # Bouton dynamique : "Ajouter les 12 KFC"
                    if st.button(f"➕ Ajouter les ({len(matches)})", use_container_width=True):
                        # On ajoute les nouveaux sans doublons
                        current = set(st.session_state['selected_partners_state'])
                        new_items = set(matches)
                        st.session_state['selected_partners_state'] = list(current.union(new_items))
                        st.rerun() # Rafraîchir pour afficher la sélection
                else:
                    # Bouton désactivé si pas de recherche
                    st.button("➕ Ajouter", disabled=True, use_container_width=True)

            with c_btn_clear:
                st.write("") # Spacer
                if st.button("🗑️ Tout Vider", use_container_width=True):
                    st.session_state['selected_partners_state'] = []
                    st.rerun()

            # --- WIDGET MULTI-SELECT PRINCIPAL ---
            # Il est piloté par le session_state
            selected_partners = st.multiselect(
                "Vos magasins sélectionnés :", 
                options=all_partners,
                default=st.session_state['selected_partners_state'],
                key="multiselect_widget", # Clé interne
                on_change=lambda: st.session_state.update({'selected_partners_state': st.session_state.multiselect_widget}) # Synchro inverse (si l'utilisateur en retire un manuellement)
            )
            
            # --- TRAITEMENT ---
            if selected_partners:
                st.markdown("---")
                # Filtrage
                df_filtered = df[df['restaurant name'].isin(selected_partners)].copy()
                
                st.info(f"✅ **{len(selected_partners)} magasins** sélectionnés | **{len(df_filtered)} commandes** prêtes à l'export.")
                
                # 3. MAPPING
                df_clean = pd.DataFrame()
                cols = df.columns.str.lower()
                
                # Mapping intelligent (Date)
                if 'order day' in cols: df_clean['Date'] = df_filtered['order day']
                elif 'date' in cols: df_clean['Date'] = df_filtered['date']
                
                # Mapping (ID)
                if 'order id' in cols: df_clean['ID Commande'] = df_filtered['order id']
                elif 'order_id' in cols: df_clean['ID Commande'] = df_filtered['order_id']
                
                # Mapping (Montant)
                if 'item total' in cols: df_clean['Montant'] = df_filtered['item total']
                elif 'total' in cols: df_clean['Montant'] = df_filtered['total']
                
                # Mapping (Statut)
                if 'status' in cols: df_clean['Statut'] = df_filtered['status']
                
                # Colonne Restaurant Source (Utile pour le multi-comptes)
                df_clean['Restaurant Source'] = df_filtered['restaurant name']
                
                # Aperçu
                with st.expander("👁️ Voir un aperçu des données"):
                    st.dataframe(df_clean.head())
                
                # Calcul CA Total
                try:
                    clean_sum = df_clean['Montant'].astype(str).str.replace('MAD','').str.replace(' ','').astype(float).sum()
                    st.metric("💰 Chiffre d'Affaires Total (Sélection)", f"{clean_sum:,.2f} MAD")
                except:
                    pass
                
                # 4. TELECHARGEMENT
                csv_buffer = df_clean.to_csv(index=False).encode('utf-8')
                
                # Nom de fichier dynamique
                if len(selected_partners) == 1:
                    fname = f"Detail_{selected_partners[0].replace(' ','_')}.csv"
                elif len(matches) > 0 and len(matches) == len(selected_partners):
                     # Si on a sélectionné exactement tout ce qui correspond à la recherche (ex: "KFC")
                     fname = f"Detail_Groupe_{search_query}.csv"
                else:
                    fname = "Detail_Multi_Magasins.csv"
                
                st.download_button(
                    label="📥 Télécharger le fichier consolidé (CSV)",
                    data=csv_buffer,
                    file_name=fname,
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.info("👈 Utilisez la barre de recherche ou la liste pour commencer.")
            
        else:
            st.error("Erreur: La colonne 'restaurant name' est introuvable.")

    except Exception as e:
        st.error(f"Erreur : {e}")
