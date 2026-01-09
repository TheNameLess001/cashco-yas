import streamlit as st
import os

# --- CONFIGURATION GLOBALE ---
YASSIR_PURPLE = "#6f42c1"
st.set_page_config(
    page_title="Yassir Partner Tool",
    page_icon="🟣",
    layout="wide"
)

# --- STYLE CSS GLOBAL (S'applique à toutes les pages) ---
st.markdown(f"""
    <style>
    /* Couleurs Yassir */
    .stApp {{ background-color: #F8F9FA; }}
    h1, h2, h3 {{ color: {YASSIR_PURPLE} !important; font-family: 'Arial', sans-serif; }}
    
    /* Boutons */
    .stButton>button {{
        background-color: {YASSIR_PURPLE}; color: white; border-radius: 8px; border: none;
        padding: 10px 24px; transition: 0.3s;
    }}
    .stButton>button:hover {{ background-color: #5a32a3; color: white; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: white; border-right: 2px solid {YASSIR_PURPLE}; }}
    
    /* Signature Footer */
    .footer {{
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #555; text-align: center;
        padding: 15px; border-top: 2px solid {YASSIR_PURPLE};
        font-family: 'Courier New', monospace; font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

# --- CONTENU ACCUEIL ---
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.title("🟣")

with col2:
    st.title("Portail Facturation Partenaires")
    st.markdown("### Solution automatisée de gestion des commissions")

st.markdown("---")

# Carte de bienvenue
st.info("""
**Bienvenue sur l'outil de gestion Yassir.**
Cette plateforme vous permet de transformer les données brutes des opérations en factures partenaires conformes.

👈 **Utilisez le menu à gauche pour naviguer :**
1. **🛠️ Préparation Données** : Nettoyez et filtrez les exports bruts (Admin Earnings).
2. **📄 Génération Factures** : Créez les PDF officiels (Facture & Détail) pour chaque partenaire.
""")

st.markdown("### 🚀 Workflow Recommandé")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### Étape 1")
    st.caption("Importez le fichier `admin-earnings-export.csv` dans l'onglet **Préparation**.")
with c2:
    st.markdown("#### Étape 2")
    st.caption("Sélectionnez un partenaire et téléchargez son fichier nettoyé `Detail_Commandes.csv`.")
with c3:
    st.markdown("#### Étape 3")
    st.caption("Allez dans **Génération Factures**, importez le fichier nettoyé et éditez les PDF.")

# --- SIGNATURE ---
st.markdown("""
<div class="footer">
    Designed & Developed by <span style="color:#6f42c1;">Saif Eddine Bounoir</span> 🚀
</div>
""", unsafe_allow_html=True)
