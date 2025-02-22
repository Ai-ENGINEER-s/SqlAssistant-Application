import streamlit as st
import urllib.parse
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import sqlalchemy.exc
import time

# Configuration de la page et des styles globaux
st.set_page_config(
    page_title="DIGITAR Database Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS améliorés
# Fonction pour charger le CSS depuis un fichier externe
def load_css(file_path):
    with open(file_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Charger le fichier CSS
load_css("styles.css")

# Fonction pour initialiser la base de données en fonction du type
def init_database(db_type: str, user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    try:
        if db_type == "MySQL":
            db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
        elif db_type == "PostgreSQL":
            db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        elif db_type == "SQL Server":
            driver = 'ODBC Driver 17 for SQL Server'
            if user and password:
                driver = '{ODBC Driver 17 for SQL Server}'
                params = urllib.parse.quote_plus(f"DRIVER={driver};SERVER={host};DATABASE={database};UID={user};PWD={password}")
                db_uri = f"mssql+pyodbc:///?odbc_connect={params}"
            else:
                db_uri = f"mssql+pyodbc://{host}/{database}?trusted_connection=yes&driver={driver}"
        else:
            raise ValueError("Unsupported database type")
        
        return SQLDatabase.from_uri(db_uri)
    except Exception as e:
        st.error(f"❌ Échec de connexion à la base de données: {str(e)}")
        return None

def get_llm_chain(db, llm_type, api_key, model=None):
    default_model = "gpt-4-0125-preview"
  
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.

    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}

    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.

    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT `ArtistId`, COUNT(*) as track_count FROM `Track` GROUP BY `ArtistId` ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT `Name` FROM `Artist` LIMIT 10;

    Your turn:

    Question: {question}
    SQL Query:
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    try:
        if llm_type == "OpenAI":
            llm = ChatOpenAI(api_key=api_key, model=model or default_model) 
        elif llm_type == "Groq":
            llm = ChatGroq(api_key=api_key)
        else:
            raise ValueError("Unsupported LLM type")

        def get_schema(_):
            return db.get_table_info()

        return (
            RunnablePassthrough.assign(schema=get_schema)
            | prompt
            | llm
            | StrOutputParser()
        )
    except Exception as e:
        st.error(f"❌ Échec d'initialisation du modèle LLM: {str(e)}")
        return None

def get_response(user_query: str, db: SQLDatabase, chat_history: list, llm_type: str, api_key: str, model: str = None):
    sql_chain = get_llm_chain(db, llm_type, api_key, model)
    if sql_chain is None:
        return "Échec d'initialisation du modèle LLM. Veuillez vérifier vos paramètres."

    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    try:
        if llm_type == "OpenAI":
            llm = ChatOpenAI(api_key=api_key)
        elif llm_type == "Groq":
            llm = ChatGroq(api_key=api_key)
        else:
            raise ValueError("Unsupported LLM type")

        chain = (
            RunnablePassthrough.assign(query=sql_chain).assign(
                schema=lambda _: db.get_table_info(),
                response=lambda vars: db.run(vars["query"]),
            )
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke({
            "question": user_query,
            "chat_history": chat_history,
        })
    except sqlalchemy.exc.ProgrammingError as pe:
        return f"Erreur SQL: {str(pe)}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {str(e)}"

# Initialisation des variables de session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Bonjour ! Je suis votre assistant SQL. Posez-moi des questions sur votre base de données."),
    ]

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"

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
        
        st.markdown('<div class="footer-credit">© 2025 DIGITAR - Tous droits réservés</div>', unsafe_allow_html=True)
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
    st.markdown('<h1><span style="color:#2E7DFF">DIGITAR</span> Database Assistant</h1>', unsafe_allow_html=True)
    
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
                <li>Email: support@digitar.tech</li>
                <li>Téléphone: +33 (0)1 23 45 67 89</li>
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

# Logique principale de l'application
if st.session_state.logged_in:
    show_main_page()
else:
    show_login_page()