"""
streamlit_app.py - Interface utilisateur Streamlit pour le Chatbot CNAM Tunisie
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.llm.chain import get_chatbot
from src.retrieval.vectorstore import vectorstore_exists

# ── Configuration Page ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chatbot CNAM Tunisie",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── CSS Personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
    background: linear-gradient(135deg, #1e8449, #27ae60);
    color: white;
    padding: 1.5rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 1.5rem;
    }
    .main-header h1,
    .main-header p {
    text-shadow: 0 1px 2px rgba(0,0,0,0.25);
    }
    .stChatMessage { border-radius: 10px; }
    .source-badge {
        background: #eaf4fb;
        border-left: 3px solid #2980b9;
        padding: 0.5rem;
        border-radius: 0 5px 5px 0;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .warning-box {
        background: #fef9e7;
        border: 1px solid #f39c12;
        padding: 0.8rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏥 Assistant CNAM Tunisie</h1>
    <p>Caisse Nationale d'Assurance Maladie | الصندوق الوطني للتأمين على المرض</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Chemin vers le logo local
    logo_path = Path(__file__).parent/ "logo_cnam.jpg"

    if logo_path.exists():
        st.image(str(logo_path), use_column_width=True)
    else:
        st.markdown("## 🏥 CNAM Tunisie")

    st.markdown("---")
    st.markdown("### ⚙️ Options")

    use_web_search = st.toggle(
        "🌐 Recherche Web",
        value=True,
        help="Activer la recherche en ligne pour compléter les PDFs"
    )

    show_sources = st.toggle(
        "📎 Afficher les sources",
        value=True
    )

    st.markdown("---")
    st.markdown("### 📊 Statut du Système")

    if vectorstore_exists():
        st.success("✅ Base de données PDFs chargée")
    else:
        st.error("❌ Base PDFs non disponible")
        st.info("Lancez `python scripts/ingest_all.py`")

    st.markdown("---")
    st.markdown("### 📞 Contact CNAM")
    st.markdown("""
    - **Numéro vert** : 80 100 180  
    - **Site** : [cnam.nat.tn](https://www.cnam.nat.tn)  
    - **Email** : contact@cnam.nat.tn
    """)

    st.markdown("---")
    st.markdown("### 💡 Questions fréquentes")

    sample_questions = [
        "Comment se faire rembourser un médicament ?",
        "Quels sont les médecins conventionnés à Tunis ?",
        "Quel est le taux de remboursement d'une radio ?",
        "Comment choisir mon médecin de famille ?",
        "كيف يتم تسديد مصاريف الأدوية؟",
    ]

    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state["quick_question"] = q

# ── Historique des messages ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Bonjour ! Je suis votre assistant CNAM. 👋\n\n"
                "Je peux vous aider concernant :\n"
                "- 💊 Le remboursement des médicaments\n"
                "- 👨‍⚕️ Les médecins et cliniques conventionnés\n"
                "- 🏥 Les consultations et analyses médicales\n"
                "- 📋 Les procédures administratives CNAM\n\n"
                "Posez votre question en français ou en arabe !"
            ),
        }
    ]

# Afficher l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if show_sources and "sources" in msg:
            sources = msg["sources"]
            if sources["rag"] or sources["web"]:
                with st.expander("📎 Sources utilisées"):
                    if sources["rag"]:
                        st.markdown("**📄 Documents CNAM :**")
                        for s in sources["rag"]:
                            st.markdown(f"- {s}")
                    if sources["web"]:
                        st.markdown("**🌐 Sources web :**")
                        for s in sources["web"]:
                            st.markdown(f"- [{s['title']}]({s['url']})")

# ── Input utilisateur ─────────────────────────────────────────────────────────
# Gérer les questions rapides depuis le sidebar
default_input = st.session_state.pop("quick_question", "")

user_input = st.chat_input(
    "Posez votre question (français ou arabe)...",
) or default_input

if user_input:
    # Ajouter la question à l'historique
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Générer la réponse
    with st.chat_message("assistant"):
        with st.spinner("Recherche en cours dans les documents CNAM..."):
            try:
                chatbot = get_chatbot()
                result = chatbot.ask(user_input, use_web_search=use_web_search)
                answer = result["answer"]

                st.markdown(answer)

                # Afficher les sources
                if show_sources:
                    sources_rag = result.get("sources_rag", [])
                    sources_web = result.get("sources_web", [])
                    if sources_rag or sources_web:
                        with st.expander("📎 Sources utilisées"):
                            col1, col2 = st.columns(2)
                            with col1:
                                if sources_rag:
                                    st.markdown("**📄 Documents CNAM :**")
                                    for s in sources_rag:
                                        st.markdown(f"- `{s}`")
                                else:
                                    st.markdown("*Aucun document RAG*")
                            with col2:
                                if sources_web:
                                    st.markdown("**🌐 Sources web :**")
                                    for s in sources_web:
                                        st.markdown(f"- [{s['title'][:40]}...]({s['url']})")

                # Sauvegarder dans l'historique
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": {
                        "rag": result.get("sources_rag", []),
                        "web": result.get("sources_web", []),
                    },
                })

            except Exception as e:
                error_msg = (
                    f"⚠️ Erreur : {str(e)}\n\n"
                    "Vérifiez votre clé **GROQ_API_KEY** dans le fichier `.env`\n\n"
                    "Obtenez une clé gratuite sur : https://console.groq.com"
                )
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<small>⚠️ Cet assistant fournit des informations générales. "
    "Pour des situations spécifiques, contactez directement la CNAM au **80 100 180**.</small>",
    unsafe_allow_html=True,
)