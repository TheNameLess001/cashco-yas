import streamlit as st
import os

# --- CONFIGURATION ---
YASSIR_PURPLE = "#6f42c1"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Yassir Partner Tool", page_icon="🟣", layout="wide")

# --- STYLE CSS GLOBAL (POPPINS & VIOLET) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}
    
    .stApp {{ background-color: #F8F9FA; }}
    
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; }}
    
    /* Boutons */
    .stButton>button {{
        background-color: {YASSIR_PURPLE}; color: white; border-radius: 12px; border: none;
        padding: 10px 24px; transition: 0.3s; font-weight: 600;
        box-shadow: 0 4px 10px rgba(111, 66, 193, 0.2);
    }}
    .stButton>button:hover {{ background-color: #5a32a3; color: white; transform: translateY(-2px); }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: white; border-right: 2px solid {YASSIR_PURPLE}; }}
    
    /* Footer */
    .footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #555; text-align: center;
        padding: 15px; border-top: 2px solid {YASSIR_PURPLE};
        font-family: 'Poppins', sans-serif; font-size: 12px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- LOGO MENU ---
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=160)
    st.sidebar.markdown("---")

# --- CONTENU ACCUEIL ---
c1, c2 = st.columns([1, 3])
with c2:
    st.title("Portail Facturation Partenaires")
    st.markdown("### 🚀 Solution automatisée de gestion des commissions")

st.markdown("---")

st.info("""
**Bienvenue sur l'outil de gestion Yassir.** Cette plateforme standardise le processus de facturation pour tous les partenaires.

👈 **Utilisez le menu à gauche pour naviguer.**
""")

# Workflow
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"#### 1. Préparation 🛠️")
    st.caption("Filtrage & Nettoyage des données brutes.")
with col2:
    st.markdown(f"#### 2. Génération 📄")
    st.caption("Création des Factures & Détails PDF.")
with col3:
    st.markdown(f"#### 3. Archivage 🗂️")
    st.caption("Téléchargement des pièces comptables.")

# --- SIGNATURE ---
st.markdown("""
<div class="footer">
    Designed & Developed by <span style="color:#6f42c1; font-weight:bold;">Saif Eddine Bounoir</span> 🚀
</div>
""", unsafe_allow_html=True)
