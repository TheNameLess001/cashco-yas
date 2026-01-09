import streamlit as st
import pandas as pd
import io
import os

# --- 1. CONFIGURATION & CHARTE ---
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

# --- 2. GESTION DE L'ÉTAT (SESSION STATE) ---
if 'data' not in st.session_state:
    st.session_state['data'] = None

def load_csv(file):
    try:
        df = pd.read_csv(file, sep=None, engine='python')
        # On normalise les noms de colonnes pour éviter les soucis
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Erreur lecture: {e}")
        return None

# --- 3. EN-TÊTE ---
c_logo, c_titre = st.columns([1, 5])
with c_logo:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=100)
    else: st.title("🟣")
with c_titre:
    st.title("Préparation & Filtrage Stable")

# --- 4. UPLOAD (Avec persistance) ---
uploaded_file = st.file_uploader("📂 Fichier Admin Earnings (CSV)", type=['csv'])

# Si un nouveau fichier arrive, on le charge dans la session
if uploaded_file is not None:
    df_loaded = load_csv(uploaded_file)
    if df_loaded is not None:
        st.session_state['data'] = df_loaded

# --- 5. LOGIQUE PRINCIPALE (Basée sur la session) ---
if st.session_state['data'] is not None:
    df = st.session_state['data']
    
    # Vérif colonne clé
    # On cherche la colonne 'restaurant name' peu importe la casse
    col_resto = next((c for c in df.columns if 'restaurant name' in c.lower()), None)
    
    if col_resto:
        # A. SÉLECTION PARTENAIRES
        all_partners = sorted(df[col_resto].dropna().unique().tolist())
        
        st.markdown(f'<div class="search-box">', unsafe_allow_html=True)
        st.subheader("🔍 Sélection des Partenaires")
        
        c_search, c_add = st.columns([3, 1])
        search_txt = c_search.text_input("Recherche rapide (ex: KFC)", key="search_bar")
        
        # Logique boutons
        matches = [p for p in all_partners if search_txt.lower() in p.lower()] if search_txt else []
        
        with c_add:
            st.write("")
            st.write("")
            if search_txt and st.button(f"➕ Ajouter ({len(matches)})", key="btn_add"):
                if 'selected_partners_state' not in st.session_state: st.session_state['selected_partners_state'] = []
                # Fusion sans doublons
                current = set(st.session_state['selected_partners_state'])
                st.session_state['selected_partners_state'] = list(current.union(set(matches)))
                st.rerun()

        # Widget Multiselect (Piloté par la session)
        if 'selected_partners_state' not in st.session_state: st.session_state['selected_partners_state'] = []
        
        selected_partners = st.multiselect(
            "Magasins sélectionnés :", 
            options=all_partners,
            default=st.session_state['selected_partners_state'],
            key="partners_widget",
            on_change=lambda: st.session_state.update({'selected_partners_state': st.session_state.partners_widget})
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected_partners:
            # B. FILTRAGE INITIAL (Par Resto)
            df_step1 = df[df[col_resto].isin(selected_partners)].copy()
            
            # C. FILTRES AVANCÉS (STABILISÉS)
            st.markdown("---")
            with st.expander("🌪️ Filtres Avancés (Statut, Ville...)", expanded=True):
                f1, f2 = st.columns(2)
                
                # Identification colonnes
                c_status = next((c for c in df.columns if c.lower() == 'status'), None)
                c_city = next((c for c in df.columns if 'city' in c.lower()), None)
                
                # 1. Filtre Statut
                if c_status:
                    # IMPORTANT : On prend les statuts uniques de la sélection "Step 1" pour les options
                    # Mais on ne filtre que si l'utilisateur change la sélection
                    all_statuses = sorted(df_step1[c_status].astype(str).unique().tolist())
                    sel_stats = f1.multiselect("Statut", all_statuses, default=all_statuses, key="ms_status")
                    
                    # Application du filtre
                    if sel_stats:
                        df_step1 = df_step1[df_step1[c_status].isin(sel_stats)]
                
                # 2. Filtre Ville
                if c_city:
                    all_cities = sorted(df_step1[c_city].astype(str).unique().tolist())
                    sel_cities = f2.multiselect("Ville", all_cities, key="ms_city") # Pas de default pour ne pas encombrer
                    
                    if sel_cities:
                        df_step1 = df_step1[df_step1[c_city].isin(sel_cities)]

            # D. MAPPING (6 Colonnes)
            st.markdown("---")
            st.subheader("🔗 Validation Colonnes")
            
            cols = df.columns.tolist()
            # Auto-detection
            idx_d = next((i for i, c in enumerate(cols) if 'day' in c.lower() or 'date' in c.lower()), 0)
            idx_i = next((i for i, c in enumerate(cols) if 'id' in c.lower() and 'order' in c.lower()), 0)
            idx_r = next((i for i, c in enumerate(cols) if 'restaurant name' in c.lower()), 0)
            idx_s = next((i for i, c in enumerate(cols) if 'status' in c.lower()), 0)
            idx_c = next((i for i, c in enumerate(cols) if 'commission' in c.lower()), 0)
            idx_f = next((i for i, c in enumerate(cols) if 'total' in c.lower() or 'item' in c.lower()), 0)

            c1, c2, c3 = st.columns(3)
            src_day = c1.selectbox("1. order day", cols, index=idx_d, key="sel_day")
            src_id = c2.selectbox("2. order id", cols, index=idx_i, key="sel_id")
            src_res = c3.selectbox("3. restaurant name", cols, index=idx_r, key="sel_res")
            
            c4, c5, c6 = st.columns(3)
            src_stat = c4.selectbox("4. status", cols, index=idx_s, key="sel_stat")
            src_comm = c5.selectbox("5. commission", cols, index=idx_c, key="sel_comm")
            src_food = c6.selectbox("6. Total Food", cols, index=idx_f, key="sel_food")

            # Création DataFrame Final
            df_final = pd.DataFrame()
            df_final['order day'] = df_step1[src_day]
            df_final['order id'] = df_step1[src_id]
            df_final['restaurant name'] = df_step1[src_res]
            df_final['status'] = df_step1[src_stat]
            df_final['restaurant commission'] = df_step1[src_comm]
            df_final['Total Food'] = df_step1[src_food]

            # E. KPI & EXPORT
            st.markdown("### 📊 Résumé")
            # Nettoyage pour calcul
            def clean_nums(s): return pd.to_numeric(s.astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            tot_food = clean_nums(df_final['Total Food']).sum()
            tot_comm = clean_nums(df_final['restaurant commission']).sum()

            k1, k2, k3 = st.columns(3)
            k1.metric("Commandes", len(df_final))
            k2.metric("Total Food", f"{tot_food:,.2f}")
            k3.metric("Total Comm.", f"{tot_comm:,.2f}")

            st.dataframe(df_final.head(50), use_container_width=True, height=250)
            
            csv = df_final.to_csv(index=False).encode('utf-8')
            
            # Nom fichier
            if len(selected_partners) == 1: fname = f"Detail_{selected_partners[0].replace(' ','_')}.csv"
            elif search_txt: fname = f"Detail_Groupe_{search_txt}.csv"
            else: fname = "Detail_Commandes.csv"

            st.download_button(
                "📥 Télécharger CSV (6 Colonnes)", 
                csv, fname, "text/csv", 
                type="primary", 
                use_container_width=True
            )

        else:
            st.info("👈 Sélectionnez des magasins pour voir les données.")
            
    else:
        st.error("Colonne 'restaurant name' introuvable.")

else:
    # Message d'accueil si pas de fichier en session
    st.info("👋 Veuillez uploader un fichier pour commencer.")
