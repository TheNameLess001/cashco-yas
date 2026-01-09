import streamlit as st
import pandas as pd
import io
import os

# --- 1. CONFIGURATION VISUELLE & CHARTE ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_LIGHT = "#f3eafa"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    .stButton>button {{
        background-color: {YASSIR_PURPLE}; color: white; border-radius: 12px;
        padding: 12px 28px; font-weight: 600; border: none;
        box-shadow: 0 4px 14px 0 rgba(111, 66, 193, 0.39); transition: all 0.2s ease-in-out;
    }}
    .stButton>button:hover {{ background-color: #5a32a3; transform: translateY(-2px); }}
    div[data-testid="metric-container"] {{
        background-color: white; border: 1px solid #e0e0e0;
        padding: 20px; border-radius: 15px; text-align: center;
    }}
    .search-box {{
        background-color: {YASSIR_LIGHT}; padding: 20px;
        border-radius: 15px; margin-bottom: 20px; border: 1px solid {YASSIR_PURPLE};
    }}
    </style>
""", unsafe_allow_html=True)

# --- FONCTION DE CHARGEMENT AVEC CACHE ---
@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    try:
        return pd.read_csv(uploaded_file, sep=None, engine='python')
    except Exception as e:
        st.error(f"Erreur de lecture: {e}")
        return None

# --- 2. EN-TÊTE ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100)
    else:
        st.title("🟣")
with col_title:
    st.title("Préparation & Filtrage")
    st.markdown("Extraction des colonnes : `order day`, `order id`, `restaurant name`, `status`, `commission`, `Total Food`.")

# --- 3. UPLOAD ---
st.write("") 
uploaded_file = st.file_uploader("📂 Déposez votre fichier `Admin Earnings` ici (CSV)", type=['csv'])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None:
        # --- 4. SÉLECTION RESTAURANTS ---
        if 'restaurant name' in df.columns:
            all_partners = sorted(df['restaurant name'].dropna().unique().tolist())
            
            st.markdown(f'<div class="search-box">', unsafe_allow_html=True)
            st.subheader("🔍 Sélection des Partenaires")
            
            c_search, c_action = st.columns([3, 1])
            with c_search:
                search_query = st.text_input("Tapez une marque pour filtrer (ex: KFC...)", placeholder="Recherche rapide...")
            
            matches = [p for p in all_partners if search_query.lower() in p.lower()] if search_query else []
            
            with c_action:
                st.write("") 
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
                # Filtrage initial
                df_filtered = df[df['restaurant name'].isin(selected_partners)].copy()
                
                # --- 5. FILTRAGE AVANCÉ ---
                st.markdown("---")
                with st.expander("🌪️ Filtres Avancés (Statut, Ville...)", expanded=False):
                    f1, f2 = st.columns(2)
                    
                    # Filtre Statut
                    col_status_guess = next((c for c in df.columns if c.lower() == 'status'), None)
                    if col_status_guess:
                        statuses = sorted(df_filtered[col_status_guess].astype(str).unique().tolist())
                        # Par défaut on sélectionne tout, sinon ça vide le tableau
                        sel_stats = f1.multiselect("Filtrer par Statut", statuses, default=statuses, key="filter_status")
                        if sel_stats: df_filtered = df_filtered[df_filtered[col_status_guess].isin(sel_stats)]

                    # Filtre Ville (si dispo)
                    col_city_guess = next((c for c in df.columns if 'city' in c.lower()), None)
                    if col_city_guess:
                        cities = sorted(df_filtered[col_city_guess].astype(str).unique().tolist())
                        sel_cities = f2.multiselect("Filtrer par Ville", cities, key="filter_city")
                        if sel_cities: df_filtered = df_filtered[df_filtered[col_city_guess].isin(sel_cities)]

                # --- 6. MAPPING DES 6 COLONNES DEMANDÉES ---
                st.markdown("---")
                st.subheader("🔗 Validation des Colonnes (Mapping)")
                st.caption("Associez les colonnes de votre fichier brut aux 6 colonnes de sortie demandées.")
                
                cols = df.columns.tolist()
                
                # Auto-Detection des indices
                idx_day = next((i for i, c in enumerate(cols) if 'day' in c.lower() or 'date' in c.lower()), 0)
                idx_id = next((i for i, c in enumerate(cols) if 'id' in c.lower() and 'order' in c.lower()), 0)
                idx_resto = next((i for i, c in enumerate(cols) if 'restaurant name' in c.lower()), 0)
                idx_stat = next((i for i, c in enumerate(cols) if 'status' in c.lower()), 0)
                idx_comm = next((i for i, c in enumerate(cols) if 'commission' in c.lower()), 0)
                idx_food = next((i for i, c in enumerate(cols) if 'total' in c.lower() or 'item' in c.lower()), 0)

                c1, c2, c3 = st.columns(3)
                col_day_src = c1.selectbox("1. order day", cols, index=idx_day)
                col_id_src = c2.selectbox("2. order id", cols, index=idx_id)
                col_resto_src = c3.selectbox("3. restaurant name", cols, index=idx_resto)
                
                c4, c5, c6 = st.columns(3)
                col_stat_src = c4.selectbox("4. status", cols, index=idx_stat)
                col_comm_src = c5.selectbox("5. restaurant commission", cols, index=idx_comm)
                col_food_src = c6.selectbox("6. Total Food", cols, index=idx_food)

                # --- 7. CRÉATION DU FICHIER FINAL ---
                df_export = pd.DataFrame()
                df_export['order day'] = df_filtered[col_day_src]
                df_export['order id'] = df_filtered[col_id_src]
                df_export['restaurant name'] = df_filtered[col_resto_src]
                df_export['status'] = df_filtered[col_stat_src]
                df_export['restaurant commission'] = df_filtered[col_comm_src]
                df_export['Total Food'] = df_filtered[col_food_src]

                # --- 8. KPI & NETTOYAGE POUR AFFICHAGE ---
                total_food_val = 0.0
                total_comm_val = 0.0

                def clean_money(series):
                    return pd.to_numeric(series.astype(str).str.replace('MAD','').str.replace(' ','').str.replace(',','.'), errors='coerce').fillna(0)

                try:
                    total_food_val = clean_money(df_export['Total Food']).sum()
                    total_comm_val = clean_money(df_export['restaurant commission']).sum()
                except: pass

                st.markdown("### 📊 Résumé de la Sélection")
                k1, k2, k3 = st.columns(3)
                k1.metric("Nombre de Commandes", f"{len(df_export)}")
                k2.metric("Total Food (Est.)", f"{total_food_val:,.2f} MAD")
                k3.metric("Total Commission (Est.)", f"{total_comm_val:,.2f} MAD")

                st.markdown("### 📋 Aperçu des Données (6 Colonnes)")
                st.dataframe(df_export.head(50), use_container_width=True, height=300)

                # --- 9. EXPORT ---
                st.markdown("### 📥 Télécharger")
                
                csv_buffer = df_export.to_csv(index=False).encode('utf-8')
                
                if len(selected_partners) == 1: fname = f"Detail_{selected_partners[0].replace(' ','_')}.csv"
                elif search_query: fname = f"Detail_Groupe_{search_query}.csv"
                else: fname = "Detail_Commandes_Yassir.csv"

                st.download_button(
                    label="Télécharger le CSV prêt (6 colonnes)",
                    data=csv_buffer,
                    file_name=fname,
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
            
            else:
                st.info("👈 Sélectionnez des magasins pour commencer.")
        else:
            st.error("Colonne 'restaurant name' introuvable.")
