import streamlit as st
import pandas as pd
import io
import os

# --- 1. CONFIGURATION VISUELLE & CHARTE ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_LIGHT = "#f3eafa"  # Violet très clair pour les fonds
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

# Injection CSS pour le "Look & Feel" Yassir
st.markdown(f"""
    <style>
    /* Import Police Moderne */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}
    
    /* Titres en Violet */
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    
    /* Boutons Principaux */
    .stButton>button {{
        background-color: {YASSIR_PURPLE};
        color: white;
        border-radius: 12px;
        padding: 12px 28px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 14px 0 rgba(111, 66, 193, 0.39);
        transition: all 0.2s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: #5a32a3;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(111, 66, 193, 0.23);
    }}
    
    /* Cartes de KPI */
    div[data-testid="metric-container"] {{
        background-color: white;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
    }}
    
    /* Container de recherche */
    .search-box {{
        background-color: {YASSIR_LIGHT};
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid {YASSIR_PURPLE};
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. EN-TÊTE ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100)
    else:
        st.title("🟣")
with col_title:
    st.title("Préparation & Filtrage Avancé")
    st.markdown("Transformez vos exports bruts en données exploitables pour la facturation.")

# --- 3. UPLOAD ---
st.write("") # Spacer
uploaded_file = st.file_uploader("📂 Déposez votre fichier `Admin Earnings` ici (CSV)", type=['csv'])

if uploaded_file:
    try:
        # Lecture
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # --- 4. SÉLECTION RESTAURANTS (Moteur de Recherche Intelligent) ---
        if 'restaurant name' in df.columns:
            all_partners = sorted(df['restaurant name'].dropna().unique().tolist())
            
            st.markdown(f'<div class="search-box">', unsafe_allow_html=True)
            st.subheader("🔍 Sélection des Partenaires")
            
            c_search, c_action = st.columns([3, 1])
            with c_search:
                search_query = st.text_input("Tapez une marque pour filtrer (ex: KFC, Tacos...)", placeholder="Recherche rapide...")
            
            # Logique d'ajout intelligent
            matches = [p for p in all_partners if search_query.lower() in p.lower()] if search_query else []
            
            with c_action:
                st.write("") # Alignement
                st.write("") 
                if search_query:
                    if st.button(f"➕ Ajouter les ({len(matches)})", use_container_width=True):
                        if 'selected_partners_state' not in st.session_state: st.session_state['selected_partners_state'] = []
                        current = set(st.session_state['selected_partners_state'])
                        st.session_state['selected_partners_state'] = list(current.union(set(matches)))
                        st.rerun()
                else:
                    if st.button("🗑️ Réinitialiser", type="secondary", use_container_width=True):
                        st.session_state['selected_partners_state'] = []
                        st.rerun()
            
            # Widget Multiselect
            if 'selected_partners_state' not in st.session_state: st.session_state['selected_partners_state'] = []
            
            selected_partners = st.multiselect(
                "Liste des magasins sélectionnés :",
                options=all_partners,
                default=st.session_state['selected_partners_state'],
                key="widget_partners",
                on_change=lambda: st.session_state.update({'selected_partners_state': st.session_state.widget_partners})
            )
            st.markdown('</div>', unsafe_allow_html=True)

            if selected_partners:
                # Filtrage initial par Restaurant
                df_filtered = df[df['restaurant name'].isin(selected_partners)].copy()
                
                # --- 5. FILTRAGE AVANCÉ (Multi-Colonnes) ---
                st.markdown("---")
                st.subheader("🌪️ Filtres Avancés")
                
                with st.expander("Afficher les options de filtrage détaillées", expanded=True):
                    f1, f2, f3 = st.columns(3)
                    
                    # Filtre A: Statut (si dispo)
                    cols_lower = [c.lower() for c in df.columns]
                    
                    # Détection auto des colonnes clés
                    col_status_name = next((c for c in df.columns if c.lower() == 'status'), None)
                    col_city_name = next((c for c in df.columns if 'city' in c.lower()), None)
                    col_payment_name = next((c for c in df.columns if 'payment' in c.lower()), None)
                    
                    # Widget 1 : Statut
                    if col_status_name:
                        statuses = sorted(df_filtered[col_status_name].astype(str).unique().tolist())
                        selected_statuses = f1.multiselect("Filtrer par Statut", statuses, default=statuses)
                        if selected_statuses:
                            df_filtered = df_filtered[df_filtered[col_status_name].isin(selected_statuses)]
                    
                    # Widget 2 : Ville (si dispo)
                    if col_city_name:
                        cities = sorted(df_filtered[col_city_name].astype(str).unique().tolist())
                        selected_cities = f2.multiselect("Filtrer par Ville", cities)
                        if selected_cities:
                            df_filtered = df_filtered[df_filtered[col_city_name].isin(selected_cities)]
                            
                    # Widget 3 : Type de paiement (si dispo)
                    if col_payment_name:
                         payments = sorted(df_filtered[col_payment_name].astype(str).unique().tolist())
                         selected_payments = f3.multiselect("Moyen de Paiement", payments)
                         if selected_payments:
                             df_filtered = df_filtered[df_filtered[col_payment_name].isin(selected_payments)]

                # --- 6. KPI & APERÇU ---
                st.markdown("---")
                
                # Nettoyage et Calcul Montant
                col_amt_name = next((c for c in df.columns if 'total' in c.lower() or 'item total' in c.lower()), None)
                total_revenue = 0.0
                
                if col_amt_name:
                    try:
                        clean_vals = df_filtered[col_amt_name].astype(str).str.replace('MAD','').str.replace(' ','').str.replace(',','.')
                        df_filtered['clean_amount_calc'] = pd.to_numeric(clean_vals, errors='coerce').fillna(0)
                        total_revenue = df_filtered['clean_amount_calc'].sum()
                    except:
                        pass

                # Affichage KPI (Cartes)
                k1, k2, k3 = st.columns(3)
                k1.metric("Magasins Actifs", f"{df_filtered['restaurant name'].nunique()}")
                k2.metric("Volume Commandes", f"{len(df_filtered)}")
                k3.metric("Chiffre d'Affaires (Est.)", f"{total_revenue:,.2f} MAD")

                # Mapping Final pour Export
                df_export = pd.DataFrame()
                # On essaie de mapper intelligemment
                map_date = next((c for c in df.columns if 'day' in c.lower() or 'date' in c.lower()), df.columns[0])
                map_id = next((c for c in df.columns if 'id' in c.lower() and 'order' in c.lower()), df.columns[1])
                
                df_export['Date'] = df_filtered[map_date]
                df_export['ID Commande'] = df_filtered[map_id]
                if col_amt_name: df_export['Montant'] = df_filtered[col_amt_name]
                if col_status_name: df_export['Statut'] = df_filtered[col_status_name]
                df_export['Restaurant Source'] = df_filtered['restaurant name'] # Important pour multi-comptes

                # Aperçu Tableau
                st.markdown("### 📋 Données Prêtes")
                st.dataframe(df_export.head(50), use_container_width=True, height=300)

                # --- 7. TÉLÉCHARGEMENT ---
                st.markdown("### 📥 Exporter")
                
                csv_buffer = df_export.to_csv(index=False).encode('utf-8')
                
                # Nommage intelligent
                if len(selected_partners) == 1:
                    fname = f"Detail_{selected_partners[0].replace(' ','_')}.csv"
                elif search_query:
                    fname = f"Detail_Groupe_{search_query}.csv"
                else:
                    fname = "Detail_Multi_Magasins.csv"

                c_dl, _ = st.columns([1, 2])
                c_dl.download_button(
                    label="Télécharger le fichier CSV nettoyé",
                    data=csv_buffer,
                    file_name=fname,
                    mime="text/csv",
                    use_container_width=True
                )
            
            else:
                st.info("👈 Commencez par sélectionner un ou plusieurs restaurants via la recherche.")

        else:
            st.error("Colonne 'restaurant name' introuvable dans le CSV.")

    except Exception as e:
        st.error(f"Erreur lors du traitement : {e}")
