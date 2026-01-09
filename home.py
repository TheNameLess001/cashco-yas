import streamlit as st
import os

# --- CONFIGURATION ---
YASSIR_PURPLE = "#6f42c1"
LOGO_PATH = "logo.png"

st.set_page_config(page_title="Yassir Partner Tool", page_icon="🟣", layout="wide")

# --- LOGO MENU (Haut Gauche) ---
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, width=180) # Logo en haut du menu
    st.sidebar.markdown("---")

# --- CSS GLOBAL ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; font-family: 'Arial', sans-serif; }}
    .stButton>button {{
        background-color: {YASSIR_PURPLE}; color: white; border-radius: 8px; border: none;
        padding: 10px 24px; transition: 0.3s;
    }}
    .stButton>button:hover {{ background-color: #5a32a3; color: white; }}
    [data-testid="stSidebar"] {{ background-color: white; border-right: 2px solid {YASSIR_PURPLE}; }}
    .footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #555; text-align: center;
        padding: 15px; border-top: 2px solid {YASSIR_PURPLE};
        font-family: 'Courier New', monospace; font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

# --- CONTENU ACCUEIL ---
st.title("🟣 Portail Facturation Partenaires")
st.markdown("### Solution automatisée de gestion des commissions")

st.info("""
**Bienvenue sur l'outil de gestion Yassir.**
Cette plateforme vous permet de transformer les données brutes des opérations en factures partenaires conformes.

👈 **Utilisez le menu à gauche pour naviguer.**
""")

st.markdown("### 🚀 Workflow")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### 1. Préparation")
    st.caption("Nettoyez l'export brut Admin Earnings.")
with c2:
    st.markdown("#### 2. Sélection")
    st.caption("Choisissez les restaurants et la période.")
with c3:
    st.markdown("#### 3. Facturation")
    st.caption("Générez les PDF officiels.")

# --- SIGNATURE ---
st.markdown("""
<div class="footer">
    Designed & Developed by <span style="color:#6f42c1;">Saif Eddine Bounoir</span> 🚀
</div>
""", unsafe_allow_html=True)
