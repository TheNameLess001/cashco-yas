import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
YASSIR_PURPLE = "#6f42c1"
YASSIR_LIGHT = "#f3eafa"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Préparation Données", page_icon="🛠️", layout="wide")

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    section[data-testid="stSidebar"] {{ background-color: #FFFFFF !important; border-right: 2px solid {YASSIR_PURPLE}; }}
    .stButton>button {{ background-color: {YASSIR_PURPLE}; color: white; border-radius: 12px; border: none; }}
    .search-box {{ background-color: {YASSIR_LIGHT}; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid {YASSIR_PURPLE}; }}
    .rule-box {{ background-color: #e3f2fd; border-left: 5px solid #2196f3; padding: 10px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9em; }}
    </style>
""", unsafe_allow_html=True)

# --- LOGO ---
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=160)
    st.sidebar.markdown("---")

# --- SESSION ---
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

# --- MAIN ---
st.title("🛠️ Préparation & Filtrage")
uploaded_file = st.file_uploader("📂 Fichier Admin Earnings (CSV)", type=['csv'])
process_file_upload(uploaded_file)

if st.session_state['global_df'] is not None:
    df = st.session_state['global_df']
    col_resto = next((c for c in df.columns if 'restaurant name' in c.lower()), None)
    
    if col_resto:
        all_partners = sorted(df[col_resto].dropna().unique().tolist())
        
        # RECHERCHE MAGASIN
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

            # MAPPING
            st.markdown("---")
            st.subheader("🔗 Validation Colonnes & Règles")
            
            st.markdown("""
            <div class="rule-box">
                <b>Logique :</b> (Status est 'Delivered') <b>OU</b> (Colonne Returned est 'Returned').<br>
                <i>Note : On utilise OU (Union) pour additionner les deux groupes.</i>
            </div>
            """, unsafe_allow_html=True)

            cols = df.columns.tolist()
            id_d = next((i for i,c in enumerate(cols) if 'day' in c.lower() or 'date' in c.lower()), 0)
            id_i = next((i for i,c in enumerate(cols) if 'id' in c.lower() and 'order' in c.lower()), 0)
            id_r = next((i for i,c in enumerate(cols) if 'restaurant name' in c.lower()), 0)
            id_s = next((i for i,c in enumerate(cols) if 'status' in c.lower()), 0)
            id_f = next((i for i,c in enumerate(cols) if 'item total' in c.lower()), 0)
            if id_f == 0: id_f = next((i for i,c in enumerate(cols) if 'total' in c.lower()), 0)
            id_ret = next((i for i,c in enumerate(cols) if 'returned' in c.lower() or 'return' in c.lower()), 0)

            m1, m2, m3 = st.columns(3)
            s_d = m1.selectbox("1. Date", cols, index=id_d)
            s_i = m2.selectbox("2. ID", cols, index=id_i)
            s_r = m3.selectbox("3. Nom Resto", cols, index=id_r)
            
            m4, m5, m6 = st.columns(3)
            s_s = m4.selectbox("4. Statut (Status)", cols, index=id_s)
            s_f = m5.selectbox("5. Total Food", cols, index=id_f)
            s_ret = m6.selectbox("6. Colonne Returned", cols, index=id_ret)

            # --- LOGIQUE DE FILTRAGE ---
            # 1. Normalisation
            status_norm = df_step1[s_s].astype(str).str.strip().str.lower()
            returned_norm = df_step1[s_ret].astype(str).str.strip().str.lower()
            
            # 2. Application de la condition "OU" (|)
            # On veut : Tout ce qui est 'delivered' + Tout ce qui est 'returned' (peu importe le statut)
            condition = (status_norm == 'delivered') | (returned_norm == 'returned')
            
            df_final_filtered = df_step1[condition].copy()

            # EXPORT
            st.markdown("### 📥 Télécharger")
            
            nb_del = len(df_final_filtered[status_norm == 'delivered'])
            nb_ret = len(df_final_filtered[returned_norm == 'returned'])
            # Note : certains peuvent être les deux, donc la somme peut être > au total réel
            
            st.caption(f"📊 Analyse : {nb_del} 'Delivered' détectés | {nb_ret} 'Returned' détectés")
            
            df_fin = pd.DataFrame({
                'order day': df_final_filtered[s_d],
                'order id': df_final_filtered[s_i],
                'restaurant name': df_final_filtered[s_r],
                'status': df_final_filtered[s_s],
                'returned_check': df_final_filtered[s_ret],
                'Total Food': df_final_filtered[s_f]
            })
            
            csv = df_fin.to_csv(index=False).encode('utf-8')
            fn = "Detail_Commandes_Final.csv"
            if len(sel_partners) == 1: fn = f"Detail_{sel_partners[0].strip().replace(' ','_')}.csv"
            elif search_txt: fn = f"Detail_Groupe_{search_txt}.csv"

            st.download_button("Télécharger CSV", csv, fn, "text/csv", type="primary", use_container_width=True)

        else:
            st.info("Sélectionnez un magasin.")
    else:
        st.error("Colonne 'restaurant name' introuvable.")
else:
    st.info("Chargez un fichier.")
