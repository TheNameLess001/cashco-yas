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

# --- 2. GESTION DE LA SESSION (PERSISTANCE) ---
if 'global_df' not in st.session_state:
    st.session_state['global_df'] = None
if 'file_signature' not in st.session_state:
    st.session_state['file_signature'] = None
if 'selected_partners' not in st.session_state:
    st.session_state['selected_partners'] = []

# --- 3. CHARGEMENT STABLE ---
def process_file_upload(uploaded_file):
    if uploaded_file is None: return

    file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if st.session_state['file_signature'] != file_sig:
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
            df.columns = df.columns.str.strip()
            
            st.session_state['global_df'] = df
            st.session_state['file_signature'] = file_sig
            st.session_state['selected_partners'] = [] 
            
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

# --- 6. LOGIQUE PRINCIPALE ---
if st.session_state['global_df'] is not None:
    df = st.session_state['global_df']
    
    col_resto = next((c for c in df.columns if 'restaurant name' in c.lower()), None)
    
    if col_resto:
        all_partners = sorted(df[col_resto].dropna().unique().tolist())
        
        # --- A. SÉLECTION ---
        st.markdown(f'<div class="search-box">', unsafe_allow_html=True)
        st.subheader("🔍 Sélection des Magasins")
        
        c_search, c_add, c_reset = st.columns([3, 1, 1])
        search_txt = c_search.text_input("Recherche rapide (ex: KFC)", key="sb_search")
        matches = [p for p in all_partners if search_txt.lower() in p.lower()] if search_txt else []
        
        with c_add:
            st.write("") 
            st.write("") 
            if search_txt and st.button(f"➕ Ajouter ({len(matches)})", key="btn_add"):
                current = set(st.session_state['selected_partners'])
                st.session_state['selected_partners'] = list(current.union(set(matches)))
                st.rerun()
            elif not search_txt:
                 st.button("➕ Ajouter", disabled=True, key="btn_add_dis")

        with c_reset:
            st.write("")
            st.write("")
            if st.button("🗑️ Vider", key="btn_clear"):
                st.session_state['selected_partners'] = []
                st.rerun()

        sel_partners = st.multiselect(
            "Liste active :",
            options=all_partners,
            key="selected_partners" 
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- B. FILTRAGE ---
        if sel_partners:
            df_step1 = df[df[col_resto].isin(sel_partners)].copy()
            
            st.markdown("---")
            with st.expander("🌪️ Filtres Avancés (Statut, Ville...)", expanded=True):
                f1, f2, f3 = st.columns(3)
                
                c_stat = next((c for c in df.columns if c.lower() == 'status'), None)
                c_city = next((c for c in df.columns if 'city' in c.lower()), None)
                c_pay = next((c for c in df.columns if 'payment' in c.lower()), None)
                
                if c_stat:
                    opts_stat = sorted(df_step1[c_stat].astype(str).unique().tolist())
                    sel_stat = f1.multiselect("Statut", opts_stat, default=opts_stat, key="f_stat")
                    if sel_stat: df_step1 = df_step1[df_step1[c_stat].isin(sel_stat)]
                
                if c_city:
                    opts_city = sorted(df_step1[c_city].astype(str).unique().tolist())
                    sel_city = f2.multiselect("Ville", opts_city, key="f_city")
                    if sel_city: df_step1 = df_step1[df_step1[c_city].isin(sel_city)]

                if c_pay:
                    opts_pay = sorted(df_step1[c_pay].astype(str).unique().tolist())
                    sel_pay = f3.multiselect("Paiement", opts_pay, key="f_pay")
                    if sel_pay: df_step1 = df_step1[df_step1[c_pay].isin(sel_pay)]

            # --- C. MAPPING (5 COLONNES) ---
            st.markdown("---")
            st.subheader("🔗 Validation Colonnes")
            st.caption("La colonne 'Commission' a été retirée (calcul automatique à l'étape suivante).")
            
            cols = df.columns.tolist()
            
            # Auto-Detection
            idx_d = next((i for i, c in enumerate(cols) if 'day' in c.lower() or 'date' in c.lower()), 0)
            idx_i = next((i for i, c in enumerate(cols) if 'id' in c.lower() and 'order' in c.lower()), 0)
            idx_r = next((i for i, c in enumerate(cols) if 'restaurant name' in c.lower()), 0)
            idx_s = next((i for i, c in enumerate(cols) if 'status' in c.lower()), 0)
            
            # Priorité à 'item total' pour Total Food
            idx_f = next((i for i, c in enumerate(cols) if 'item total' in c.lower()), 0)
            if idx_f == 0: idx_f = next((i for i, c in enumerate(cols) if 'total' in c.lower()), 0)

            # Ligne 1 : Infos Commande
            m1, m2, m3 = st.columns(3)
            src_day = m1.selectbox("1. order day", cols, index=idx_d, key="sel_day")
            src_id = m2.selectbox("2. order id", cols, index=idx_i, key="sel_id")
            src_res = m3.selectbox("3. restaurant name", cols, index=idx_r, key="sel_res")
            
            # Ligne 2 : Statut & Montant
            m4, m5 = st.columns(2)
            src_stat = m4.selectbox("4. status", cols, index=idx_s, key="sel_stat")
            src_food = m5.selectbox("5. Total Food (Source: item total)", cols, index=idx_f, key="sel_food")

            # Construction DataFrame Final (5 Colonnes)
            df_final = pd.DataFrame()
            df_final['order day'] = df_step1[src_day]
            df_final['order id'] = df_step1[src_id]
            df_final['restaurant name'] = df_step1[src_res]
            df_final['status'] = df_step1[src_stat]
            df_final['Total Food'] = df_step1[src_food]

            # D. KPI & EXPORT
            st.markdown("### 📊 Résumé")
            
            def clean_money(s): return pd.to_numeric(s.astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            tot_food = clean_money(df_final['Total Food']).sum()

            k1, k2 = st.columns(2)
            k1.metric("Commandes Filtrées", len(df_final))
            k2.metric("Total Food (Est.)", f"{tot_food:,.2f} MAD")

            st.dataframe(df_final.head(50), use_container_width=True, height=250)
            
            csv = df_final.to_csv(index=False).encode('utf-8')
            
            if len(sel_partners) == 1: fname = f"Detail_{sel_partners[0].strip().replace(' ','_')}.csv"
            elif search_txt: fname = f"Detail_Groupe_{search_txt}.csv"
            else: fname = "Detail_Commandes_Yassir.csv"

            st.download_button(
                "📥 Télécharger CSV (Prêt pour Facturation)", 
                csv, fname, "text/csv", 
                type="primary", use_container_width=True
            )
            
        else:
            st.info("👈 Veuillez sélectionner au moins un magasin.")
            
    else:
        st.error("Colonne 'restaurant name' introuvable.")

else:
    st.info("👋 Veuillez uploader un fichier pour commencer.")
