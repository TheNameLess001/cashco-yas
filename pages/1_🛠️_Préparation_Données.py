import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURATION & STYLE ---
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
        padding: 10px 24px; font-weight: 600; border: none;
        box-shadow: 0 4px 14px 0 rgba(111, 66, 193, 0.39); transition: all 0.2s ease-in-out;
    }}
    .stButton>button:hover {{ background-color: #5a32a3; transform: translateY(-2px); }}
    .search-box {{
        background-color: {YASSIR_LIGHT}; padding: 20px;
        border-radius: 15px; margin-bottom: 20px; border: 1px solid {YASSIR_PURPLE};
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTION DE LA SESSION (INIT) ---
if 'global_df' not in st.session_state:
    st.session_state['global_df'] = None
if 'file_signature' not in st.session_state:
    st.session_state['file_signature'] = None
if 'selected_partners' not in st.session_state:
    st.session_state['selected_partners'] = []

# --- 3. FONCTION DE CHARGEMENT STABLE ---
def process_file_upload(uploaded_file):
    """Ne charge le fichier que s'il est nouveau."""
    if uploaded_file is None:
        return

    # Création d'une signature unique (Nom + Taille)
    file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # Si c'est un nouveau fichier, on charge tout
    if st.session_state['file_signature'] != file_sig:
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
            # Nettoyage des noms de colonnes
            df.columns = df.columns.str.strip()
            
            # Stockage en session
            st.session_state['global_df'] = df
            st.session_state['file_signature'] = file_sig
            st.session_state['selected_partners'] = [] # Reset sélection sur nouveau fichier
            
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

# --- 4. EN-TÊTE ---
c_logo, c_titre = st.columns([1, 5])
with c_logo:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=100)
    else: st.title("🟣")
with c_titre:
    st.title("Préparation & Filtrage")

# --- 5. UPLOAD ---
uploaded_file = st.file_uploader("📂 Fichier Admin Earnings (CSV)", type=['csv'])
process_file_upload(uploaded_file)

# --- 6. LOGIQUE PRINCIPALE (Sur données en cache) ---
if st.session_state['global_df'] is not None:
    df = st.session_state['global_df']
    
    # Recherche colonne Restaurant
    col_resto = next((c for c in df.columns if 'restaurant name' in c.lower()), None)
    
    if col_resto:
        all_partners = sorted(df[col_resto].dropna().unique().tolist())
        
        # --- A. ZONE DE RECHERCHE PARTENAIRES ---
        st.markdown(f'<div class="search-box">', unsafe_allow_html=True)
        st.subheader("🔍 Sélection des Magasins")
        
        c_search, c_add, c_reset = st.columns([3, 1, 1])
        
        # Barre de recherche
        search_txt = c_search.text_input("Tapez une marque (ex: KFC)", key="sb_search")
        matches = [p for p in all_partners if search_txt.lower() in p.lower()] if search_txt else []
        
        # Bouton Ajouter
        with c_add:
            st.write("") 
            st.write("") 
            if search_txt:
                if st.button(f"➕ Ajouter ({len(matches)})", use_container_width=True):
                    # Mise à jour directe de la session
                    current = set(st.session_state['selected_partners'])
                    st.session_state['selected_partners'] = list(current.union(set(matches)))
                    st.rerun() # Force le rafraîchissement immédiat
            else:
                 st.button("➕ Ajouter", disabled=True, use_container_width=True)

        # Bouton Reset
        with c_reset:
            st.write("")
            st.write("")
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state['selected_partners'] = []
                st.rerun()

        # Widget Multiselect (Relié directement à la session 'selected_partners')
        # L'argument 'key' lie automatiquement ce widget à st.session_state['selected_partners']
        sel_partners = st.multiselect(
            "Liste active :",
            options=all_partners,
            key="selected_partners" 
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- B. FILTRAGE ET AFFICHAGE ---
        if sel_partners:
            # 1. Filtre par Partenaires
            df_filtered = df[df[col_resto].isin(sel_partners)].copy()
            
            st.markdown("---")
            
            # 2. Filtres Avancés (Statut, Ville...)
            # On utilise un formulaire ou expander
            with st.expander("🌪️ Filtres Avancés (Statut, Ville...)", expanded=True):
                f1, f2, f3 = st.columns(3)
                
                # Identification colonnes
                c_stat = next((c for c in df.columns if c.lower() == 'status'), None)
                c_city = next((c for c in df.columns if 'city' in c.lower()), None)
                c_pay = next((c for c in df.columns if 'payment' in c.lower()), None)
                
                # Filtre Statut
                if c_stat:
                    opts_stat = sorted(df_filtered[c_stat].astype(str).unique().tolist())
                    sel_stat = f1.multiselect("Statut", opts_stat, default=opts_stat, key="f_stat")
                    if sel_stat: df_filtered = df_filtered[df_filtered[c_stat].isin(sel_stat)]
                
                # Filtre Ville
                if c_city:
                    opts_city = sorted(df_filtered[c_city].astype(str).unique().tolist())
                    sel_city = f2.multiselect("Ville", opts_city, key="f_city")
                    if sel_city: df_filtered = df_filtered[df_filtered[c_city].isin(sel_city)]

                # Filtre Paiement
                if c_pay:
                    opts_pay = sorted(df_filtered[c_pay].astype(str).unique().tolist())
                    sel_pay = f3.multiselect("Paiement", opts_pay, key="f_pay")
                    if sel_pay: df_filtered = df_filtered[df_filtered[c_pay].isin(sel_pay)]

            # 3. MAPPING (6 Colonnes)
            st.markdown("---")
            st.subheader("🔗 Validation Colonnes")
            
            cols = df.columns.tolist()
            # Auto-Detection
            idx_d = next((i for i, c in enumerate(cols) if 'day' in c.lower() or 'date' in c.lower()), 0)
            idx_i = next((i for i, c in enumerate(cols) if 'id' in c.lower() and 'order' in c.lower()), 0)
            idx_r = next((i for i, c in enumerate(cols) if 'restaurant name' in c.lower()), 0)
            idx_s = next((i for i, c in enumerate(cols) if 'status' in c.lower()), 0)
            idx_c = next((i for i, c in enumerate(cols) if 'commission' in c.lower()), 0)
            idx_f = next((i for i, c in enumerate(cols) if 'total' in c.lower() or 'item' in c.lower()), 0)

            m1, m2, m3 = st.columns(3)
            src_day = m1.selectbox("1. order day", cols, index=idx_d)
            src_id = m2.selectbox("2. order id", cols, index=idx_i)
            src_res = m3.selectbox("3. restaurant name", cols, index=idx_r)
            
            m4, m5, m6 = st.columns(3)
            src_stat = m4.selectbox("4. status", cols, index=idx_s)
            src_comm = m5.selectbox("5. commission", cols, index=idx_c)
            src_food = m6.selectbox("6. Total Food", cols, index=idx_f)

            # Construction Finale
            df_export = pd.DataFrame({
                'order day': df_filtered[src_day],
                'order id': df_filtered[src_id],
                'restaurant name': df_filtered[src_res],
                'status': df_filtered[src_stat],
                'restaurant commission': df_filtered[src_comm],
                'Total Food': df_filtered[src_food]
            })

            # 4. KPI & EXPORT
            st.markdown("### 📊 Résumé")
            
            def clean_money(s): return pd.to_numeric(s.astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            tf = clean_money(df_export['Total Food']).sum()
            tc = clean_money(df_export['restaurant commission']).sum()
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Commandes", len(df_export))
            k2.metric("Total Food (Est.)", f"{tf:,.2f}")
            k3.metric("Total Comm. (Est.)", f"{tc:,.2f}")

            st.dataframe(df_export.head(50), use_container_width=True, height=250)
            
            # Bouton Export
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            
            # Nom fichier intelligent
            if len(sel_partners) == 1:
                f_name = f"Detail_{sel_partners[0].strip().replace(' ','_')}.csv"
            elif search_txt:
                f_name = f"Detail_Groupe_{search_txt}.csv"
            else:
                f_name = "Detail_Multi_Magasins.csv"

            st.download_button(
                "📥 Télécharger CSV (6 Colonnes)", 
                csv_data, f_name, "text/csv", 
                type="primary", use_container_width=True
            )
            
        else:
            st.info("👈 Veuillez sélectionner au moins un magasin pour voir les données.")
            
    else:
        st.error("Colonne 'restaurant name' introuvable dans le fichier.")
