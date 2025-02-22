import streamlit as st ; 
import time 
from dotenv import load_dotenv
from utils.llm import init_database
from utils.llm import get_response
from langchain_core.messages import AIMessage, HumanMessage

def login(username, password):
    # Remplacez ceci par la vérification réelle des identifiants
    if username == "admin" and password == "aze123":
        return True
    return False
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="login-header">
            <div class="login-logo">🤖</div>
            <h1>Database Assistant</h1>
            <p>Connectez-vous pour accéder à votre assistant IA de bases de données</p>
        </div>
        ''', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            
            col1, col2 = st.columns(2)
            with col1:
                st.form_submit_button("Annuler", use_container_width=True)
            with col2:
                submitted = st.form_submit_button("Se connecter", use_container_width=True)
                
            if submitted:
                with st.spinner("Authentification en cours..."):
                    time.sleep(0.5)  # Simuler un délai de connexion
                    if login(username, password):
                        st.session_state.logged_in = True
                        st.success("Connexion réussie !")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects. Veuillez réessayer.")
        
        st.markdown('<div class="footer-credit">© 2025 BARRY - Tous droits réservés</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_main_page():
    load_dotenv()

    # Sidebar amélioré
    with st.sidebar:
        st.markdown('<h3 class="sidebar-header">🔧 Paramètres de connexion</h3>', unsafe_allow_html=True)
        
        # Status de connexion
        if st.session_state.connection_status == "connected":
            st.markdown('<div class="connection-status status-connected">✅ Connecté</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="connection-status status-disconnected">❌ Non connecté</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Configuration de la base de données
        with st.expander("📊 Configuration de la base de données", expanded=True):
            db_type = st.selectbox(
                "Type de base de données",
                ["MySQL", "PostgreSQL", "SQL Server"],
                index=0,
                key="db_type",
                help="Sélectionnez le type de base de données à laquelle vous souhaitez vous connecter"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Hôte", value="localhost", key="Host")
            with col2:
                port = st.text_input("Port", value="3306", key="Port")
            
            user = st.text_input("Nom d'utilisateur", value="root", key="User")
            password = st.text_input("Mot de passe", type="password", value="admin", key="Password")
            database = st.text_input("Base de données", value="artist", key="Database")
        
        # Configuration du modèle LLM
        with st.expander("🧠 Configuration du modèle IA", expanded=True):
            llm_type = st.selectbox(
                "Type de modèle",
                ["OpenAI", "Groq"],
                index=0,
                key="llm_type",
                help="Sélectionnez le fournisseur de modèle d'IA à utiliser"
            )
            
            model_options = {
                "OpenAI": ["gpt-4-0125-preview", "gpt-4-turbo", "gpt-3.5-turbo"],
                "Groq": ["llama2-70b-4096", "mixtral-8x7b-32768"]
            }
            
            model = st.selectbox(
                "Modèle",
                model_options[llm_type],
                index=0,
                key="model",
                help="Sélectionnez le modèle spécifique à utiliser"
            )
            
            api_key = st.text_input(
                "Clé API",
                type="password",
                key="api_key",
                help="Entrez votre clé API pour le service sélectionné"
            )
        
        # Bouton de connexion
        connect_col1, connect_col2 = st.columns([3, 1])
        with connect_col1:
            connect_button = st.button(
                "Se connecter à la BD",
                key="connect_button",
                help="Établir la connexion à la base de données",
                use_container_width=True
            )
        with connect_col2:
            test_button = st.button(
                "Test",
                key="test_button",
                help="Tester la connexion",
                use_container_width=True
            )
            
        if connect_button:
            with st.spinner("Connexion à la base de données..."):
                try:
                    db = init_database(
                        db_type,
                        user,
                        password,
                        host,
                        port,
                        database
                    )
                    if db is not None:
                        st.session_state.db = db
                        st.session_state.connection_status = "connected"
                        st.success("✅ Connexion à la base de données réussie !")
                    else:
                        st.error("❌ Échec de connexion à la base de données.")
                except Exception as e:
                    st.error(f"❌ Échec de connexion : {str(e)}")
        
        st.markdown("---")
        
        # Options du compte
        with st.expander("👤 Options du compte", expanded=False):
            st.text(f"Utilisateur: admin")
            st.text(f"Rôle: Administrateur")
            
            if st.button("📤 Se déconnecter", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

    # Zone principale
    st.markdown('<h1><span style="color:#2E7DFF"></span> Database Assistant</h1>', unsafe_allow_html=True)
    
    # Onglets principaux
    tab1, tab3 = st.tabs(["💬 Assistant SQL", "ℹ️ Aide"])
    
    with tab1:
        # Section chat
        st.markdown('<h3>Posez vos questions sur la base de données</h3>', unsafe_allow_html=True)
        
        # Zone de chat avec style amélioré
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if isinstance(message, AIMessage):
                    st.markdown(f'<div class="ai-message"><strong>🤖 Assistant:</strong><br>{message.content}</div>', unsafe_allow_html=True)
                elif isinstance(message, HumanMessage):
                    st.markdown(f'<div class="human-message"><strong>👤 Vous:</strong><br>{message.content}</div>', unsafe_allow_html=True)
        
        # Zone de saisie améliorée
        user_query = st.chat_input("Posez votre question sur la base de données...", disabled=st.session_state.connection_status != "connected")
        
        if user_query is not None and user_query.strip() != "":
            st.session_state.chat_history.append(HumanMessage(content=user_query))
            
            with st.spinner("Génération de la réponse..."):
                if "db" in st.session_state:
                    if "api_key" in st.session_state and "llm_type" in st.session_state:
                        response = get_response(
                            user_query, 
                            st.session_state.db, 
                            st.session_state.chat_history, 
                            st.session_state.llm_type, 
                            st.session_state.api_key, 
                            st.session_state.model if "model" in st.session_state and st.session_state.model.strip() != "" else None
                        )
                    else:
                        response = "⚠️ Veuillez configurer les paramètres du modèle IA d'abord."
                else:
                    response = "⚠️ Veuillez vous connecter à une base de données d'abord."
                    
            st.session_state.chat_history.append(AIMessage(content=response))
            st.rerun()
        
        # Message d'aide contextuel
        if st.session_state.connection_status != "connected":
            st.info("👆 Connectez-vous d'abord à votre base de données via le panneau latéral pour commencer à poser des questions.")
    
    with tab3:
        st.markdown('<h3>Comment utiliser l\'assistant</h3>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="form-container">
            <h4>🔍 Exemples de questions</h4>
            <ul>
                <li>Quels sont les 5 artistes les plus populaires?</li>
                <li>Montrez-moi le nombre total de ventes par région</li>
                <li>Quelle est la moyenne des prix des produits par catégorie?</li>
                <li>Listez les clients qui ont passé plus de 3 commandes</li>
            </ul>
        </div>
        
        <div class="form-container">
            <h4>🛠 Guide d'utilisation</h4>
            <ol>
                <li><strong>Connexion à la base de données</strong> - Configurez la connexion dans le panneau latéral</li>
                <li><strong>Configuration du modèle IA</strong> - Sélectionnez un fournisseur et un modèle</li>
                <li><strong>Posez vos questions</strong> - Utilisez un langage naturel pour interroger votre base de données</li>
            </ol>
        </div>
        
        <div class="form-container">
            <h4>📞 Support</h4>
            <p>Si vous rencontrez des problèmes ou avez des questions, contactez le support technique:</p>
            <ul>
                <li>Email: s.barry@mundiapolis.ma</li>
                <li>Téléphone: +212777730540</li>
                <li>Horaires: Du lundi au vendredi, 9h00 - 18h00</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Feedback form
        with st.expander("📝 Donnez votre avis sur l'assistant", expanded=False):
            with st.form("feedback_form"):
                st.write("Aidez-nous à améliorer l'assistant en partageant votre expérience")
                rating = st.slider("Note globale", 1, 5, 5)
                feedback_text = st.text_area("Commentaires (optionnel)")
                submit_feedback = st.form_submit_button("Envoyer")
                
                if submit_feedback:
                    st.success("Merci pour votre retour! Nous l'avons bien reçu.")


