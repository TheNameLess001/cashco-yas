import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_LIGHT = "#f3eafa"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

# --- CSS STYLE ---
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
    
    div[data-testid="metric-container"] {{
        background-color: white; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOGO ---
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=160)
    st.sidebar.markdown("---")

# --- GESTION SESSION ---
if 'global_df' not in st.session_state: st.session_state['global_df'] = None
if 'file_signature' not in st.session_state: st.session_state['file_signature'] = None
if 'selected_partners' not in st.session_state: st.session_state['selected_partners'] = []

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
            st.error(f"Erreur : {e}")

# --- PAGE ---
st.title("🛠️ Préparation & Filtrage")
uploaded_file = st.file_uploader("📂 Fichier Admin Earnings (CSV)", type=['csv'])
process_file_upload(uploaded_file)

if st.session_state['global_df'] is not None:
    df = st.session_state['global_df']
    col_resto = next((c for c in df.columns if 'restaurant name' in c.lower()), None)
    
    if col_resto:
        all_partners = sorted(df[col_resto].dropna().unique().tolist())
        
        # ZONE RECHERCHE
        st.markdown(f'<div class="search-box">', unsafe_allow_html=True)
        st.subheader("🔍 Sélection des Magasins")
        c1, c2, c3 = st.columns([3, 1, 1])
        search_txt = c1.text_input("Recherche (ex: KFC)", key="sb_search")
        matches = [p for p in all_partners if search_txt.lower() in p.lower()] if search_txt else []
        
        with c2:
            st.write(""); st.write("")
            if search_txt and st.button(f"➕ Ajouter ({len(matches)})", key="add"):
                st.session_state['selected_partners'] = list(set(st.session_state['selected_partners']).union(set(matches)))
                st.rerun()
        with c3:
            st.write(""); st.write("")
            if st.button("🗑️ Vider", key="clr"):
                st.session_state['selected_partners'] = []
                st.rerun()

        sel_partners = st.multiselect("Liste active :", options=all_partners, key="selected_partners")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if sel_partners:
            df_step1 = df[df[col_resto].isin(sel_partners)].copy()
            
            # FILTRES
            st.markdown("---")
            with st.expander("🌪️ Filtres Avancés", expanded=True):
                f1, f2, f3 = st.columns(3)
                c_s = next((c for c in df.columns if c.lower() == 'status'), None)
                c_c = next((c for c in df.columns if 'city' in c.lower()), None)
                c_p = next((c for c in df.columns if 'payment' in c.lower()), None)
                
                if c_s: 
                    ops = sorted(df_step1[c_s].astype(str).unique().tolist())
                    sl = f1.multiselect("Statut", ops, default=ops, key="fs")
                    if sl: df_step1 = df_step1[df_step1[c_s].isin(sl)]
                if c_c:
                    opc = sorted(df_step1[c_c].astype(str).unique().tolist())
                    slc = f2.multiselect("Ville", opc, key="fc")
                    if slc: df_step1 = df_step1[df_step1[c_c].isin(slc)]
                if c_p:
                    opp = sorted(df_step1[c_p].astype(str).unique().tolist())
                    slp = f3.multiselect("Paiement", opp, key="fp")
                    if slp: df_step1 = df_step1[df_step1[c_p].isin(slp)]

            # MAPPING (CORRECTION: Item Total -> Total Food)
            st.markdown("---")
            st.subheader("🔗 Validation Colonnes")
            cols = df.columns.tolist()
            id_d = next((i for i,c in enumerate(cols) if 'day' in c.lower() or 'date' in c.lower()), 0)
            id_i = next((i for i,c in enumerate(cols) if 'id' in c.lower() and 'order' in c.lower()), 0)
            id_r = next((i for i,c in enumerate(cols) if 'restaurant name' in c.lower()), 0)
            id_s = next((i for i,c in enumerate(cols) if 'status' in c.lower()), 0)
            # Priorité Item Total
            id_f = next((i for i,c in enumerate(cols) if 'item total' in c.lower()), 0)
            if id_f == 0: id_f = next((i for i,c in enumerate(cols) if 'total' in c.lower()), 0)

            m1, m2, m3 = st.columns(3)
            s_d = m1.selectbox("1. Date", cols, index=id_d)
            s_i = m2.selectbox("2. ID", cols, index=id_i)
            s_r = m3.selectbox("3. Nom Resto", cols, index=id_r)
            m4, m5 = st.columns(2)
            s_s = m4.selectbox("4. Statut", cols, index=id_s)
            s_f = m5.selectbox("5. Total Food (Source: item total)", cols, index=id_f)

            df_fin = pd.DataFrame({
                'order day': df_step1[s_d], 'order id': df_step1[s_i],
                'restaurant name': df_step1[s_r], 'status': df_step1[s_s],
                'Total Food': df_step1[s_f]
            })

            # EXPORT
            st.markdown("### 📥 Télécharger")
            csv = df_fin.to_csv(index=False).encode('utf-8')
            fn = "Detail_Commandes.csv"
            if len(sel_partners) == 1: fn = f"Detail_{sel_partners[0].strip().replace(' ','_')}.csv"
            elif search_txt: fn = f"Detail_Groupe_{search_txt}.csv"

            st.download_button("Télécharger CSV (Prêt)", csv, fn, "text/csv", type="primary", use_container_width=True)
        else:
            st.info("Sélectionnez un magasin.")
    else:
        st.error("Colonne 'restaurant name' introuvable.")
else:
    st.info("Chargez un fichier.")
