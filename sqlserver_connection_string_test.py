
import streamlit as st
import pyodbc

# Interface utilisateur pour les informations de connexion
st.title('Configuration de la connexion SQL Server')
server = st.text_input('Nom du serveur SQL Server (ex: localhost\\SQLEXPRESS)', value='localhost\\SQLEXPRESS')
database = st.text_input('Nom de la base de données')
username = st.text_input('Nom d\'utilisateur SQL Server (optionnel)')
password = st.text_input('Mot de passe SQL Server (optionnel)', type='password')

# Fonction pour se connecter à la base de données
def get_db_connection(server, database, username=None, password=None):
    if not server or not database:
        st.warning('Veuillez entrer le nom du serveur et le nom de la base de données.')
        return None

    driver = '{ODBC Driver 17 for SQL Server}'
    if username and password:
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    else:
        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'

    try:
        st.info(f"Tentative de connexion à {server}/{database}...")
        conn = pyodbc.connect(connection_string)
        st.success(f"Connexion réussie à {server}/{database}")
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[1]
        st.error(f"Échec de la connexion : {sqlstate}")
        return None

# Fonction pour exécuter une requête SQL
def execute_query(query, conn):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except pyodbc.Error as ex:
        sqlstate = ex.args[1]
        st.error(f"Erreur SQL : {sqlstate}")
        return []

# Interface utilisateur Streamlit
st.title('Application Streamlit avec SQL Server')

# Test de connexion
if st.button('Tester la connexion'):
    conn = get_db_connection(server, database, username, password)
    if conn:
        conn.close()

# Afficher les données de la table produits
if st.button('Afficher les produits'):
    conn = get_db_connection(server, database, username, password)
    if conn:
        query = "SELECT * FROM produits"
        results = execute_query(query, conn)
        if results:
            for row in results:
                st.write(row)
        else:
            st.warning('Aucun résultat trouvé.')
        conn.close()

# Ajouter un nouveau produit
st.subheader('Ajouter un nouveau produit')
new_name = st.text_input('Nom du produit')
new_category = st.number_input('ID de la catégorie', min_value=1)
new_supplier = st.number_input('ID du fournisseur', min_value=1)
new_price = st.number_input('Prix', min_value=0.0)

if st.button('Ajouter le produit'):
    conn = get_db_connection(server, database, username, password)
    if conn:
        cursor = conn.cursor()
        insert_query = f"INSERT INTO produits (nom, categorie_id, fournisseur_id, prix) VALUES ('{new_name}', {new_category}, {new_supplier}, {new_price})"
        try:
            cursor.execute(insert_query)
            conn.commit()
            st.success('Produit ajouté avec succès')
        except pyodbc.Error as ex:
            sqlstate = ex.args[1]
            st.error(f"Erreur lors de l'ajout du produit : {sqlstate}")
        finally:
            conn.close()

# Lancer l'application Streamlit
if __name__ == '__main__':
    st.write('Bienvenue sur l\'application Streamlit avec SQL Server')











#main application : 


# import urllib.parse
# from dotenv import load_dotenv
# from langchain_core.messages import AIMessage, HumanMessage
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain_community.utilities import SQLDatabase
# from langchain_core.output_parsers import StrOutputParser
# from langchain_openai import ChatOpenAI
# from langchain_groq import ChatGroq
# import streamlit as st
# import sqlalchemy.exc

# from sqlalchemy import create_engine
# import urllib.parse

# from sqlalchemy import create_engine
# # Fonction pour initialiser la base de données en fonction du type
# def init_database(db_type: str, user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
#     try:
#         if db_type == "MySQL":
#             db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
#         elif db_type == "PostgreSQL":
#             db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
#         elif db_type == "SQL Server":
#             driver =  'ODBC Driver 17 for SQL Server'
#             if user and password:
#                 driver = '{ODBC Driver 17 for SQL Server}'
#                 params = urllib.parse.quote_plus(f"DRIVER={driver};SERVER={host};DATABASE={database};UID={user};PWD={password}")
#                 db_uri = f"mssql+pyodbc:///?odbc_connect={params}"
#             else:
#                 db_uri = f"mssql+pyodbc://{host}/{database}?trusted_connection=yes&driver={driver}"
#             return SQLDatabase.from_uri(db_uri)
#         else:
#             raise ValueError("Unsupported database type")
        
#         return SQLDatabase.from_uri(db_uri)
#     except Exception as e:
#         st.error(f"Failed to connect to database: {str(e)}")
#         return None

# def get_llm_chain(db, llm_type, api_key, model=None):
#     default_model = "gpt-4-0125-preview"
  
#     template = """
#     You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
#     Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.

#     <SCHEMA>{schema}</SCHEMA>

#     Conversation History: {chat_history}

#     Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.

#     For example:
#     Question: which 3 artists have the most tracks?
#     SQL Query: SELECT `ArtistId`, COUNT(*) as track_count FROM `Track` GROUP BY `ArtistId` ORDER BY track_count DESC LIMIT 3;
#     Question: Name 10 artists
#     SQL Query: SELECT `Name` FROM `Artist` LIMIT 10;

#     Your turn:

#     Question: {question}
#     SQL Query:
#     """

#     prompt = ChatPromptTemplate.from_template(template)
    
#     try:
#         if llm_type == "OpenAI":
#             llm = ChatOpenAI(api_key=api_key, model=model or default_model) 
#         elif llm_type == "Groq":
#             llm = ChatGroq(api_key=api_key)
#         else:
#             raise ValueError("Unsupported LLM type")

#         def get_schema(_):
#             return db.get_table_info()

#         return (
#             RunnablePassthrough.assign(schema=get_schema)
#             | prompt
#             | llm
#             | StrOutputParser()
#         )
#     except Exception as e:
#         st.error(f"Failed to initialize LLM chain: {str(e)}")
#         return None

# def get_response(user_query: str, db: SQLDatabase, chat_history: list, llm_type: str, api_key: str, model: str = None):
#     sql_chain = get_llm_chain(db, llm_type, api_key, model)
#     if sql_chain is None:
#         return "Failed to initialize LLM chain. Check your LLM settings."

#     template = """
#     You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
#     Based on the table schema below, question, sql query, and sql response, write a natural language response.
#     <SCHEMA>{schema}</SCHEMA>

#     Conversation History: {chat_history}
#     SQL Query: <SQL>{query}</SQL>
#     User question: {question}
#     SQL Response: {response}
#     """

#     prompt = ChatPromptTemplate.from_template(template)
    
#     try:
#         if llm_type == "OpenAI":
#             llm = ChatOpenAI(api_key=api_key)
#         elif llm_type == "Groq":
#             llm = ChatGroq(api_key=api_key)
#         else:
#             raise ValueError("Unsupported LLM type")

#         chain = (
#             RunnablePassthrough.assign(query=sql_chain).assign(
#                 schema=lambda _: db.get_table_info(),
#                 response=lambda vars: db.run(vars["query"]),
#             )
#             | prompt
#             | llm
#             | StrOutputParser()
#         )

#         return chain.invoke({
#             "question": user_query,
#             "chat_history": chat_history,
#         })
#     except sqlalchemy.exc.ProgrammingError as pe:
#         return f"SQL error: {str(pe)}"
#     except Exception as e:
#         return f"An unexpected error occurred: {str(e)}"

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = [
#         AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
#     ]

# load_dotenv()

# st.set_page_config(page_title="Chat with Database", page_icon=":speech_balloon:", layout="centered")

# st.markdown("""
#     <style>
#     .main {
#         color: #ffffff;
#     }
#     .stButton button {
#         background-color: #4CAF50;
#         color: white;
#     }
#     .stTextInput input {
#         background-color: #1A2130;
#         color: #ffffff;
#     }
#     .stSelectbox select {
#         background-color: #1c1e22;
#         color: #ffffff;
#     }
#     .stTextArea textarea {
#         background-color: #1c1e22;
#         color: #ffffff;
#     }
#     .stMarkdown div {
#         color: #ffffff;
#     }
#     .sidebar .sidebar-content {
#         background-color:#686D76;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# st.title("Chat with Your Database")

# with st.sidebar:
#     st.subheader("Settings")
#     st.write("Connect to the database and start chatting.")
    
#     db_type = st.selectbox("Database Type", ["MySQL", "PostgreSQL", "SQL Server"], key="db_type")
#     st.text_input("Host", value="localhost", key="Host")
#     st.text_input("Port", value="3306", key="Port")
#     st.text_input("UserName", value="root", key="User")
#     st.text_input("Password", type="password", value="admin", key="Password")
#     st.text_input("Database", value="artist", key="Database")
    
#     st.subheader("LLM Configuration")
#     llm_type = st.selectbox("LLM Type", ["OpenAI", "Groq"], key="llm_type")
#     model = st.text_input("Model (optional)", value="", key="model", help="Leave empty to use the default model")
#     api_key = st.text_input("API Key", type="password", key="api_key")

#     if st.button("Connect"):
#         with st.spinner("Connecting to database..."):
#             try:
#                 db = init_database(
#                     st.session_state["db_type"],
#                     st.session_state["User"],
#                     st.session_state["Password"],
#                     st.session_state["Host"],
#                     st.session_state["Port"],
#                     st.session_state["Database"]
#                 )
#                 st.session_state.db = db
#                 st.success("Connected to database!")
#             except Exception as e:
#                 st.error(f"Failed to connect to database: {str(e)}")

# st.subheader("Chat with the Database")
# st.write("Ask your database anything and get the response in natural language.")

# for message in st.session_state.chat_history:
#     if isinstance(message, AIMessage):
#         with st.chat_message("AI"):
#             st.markdown(message.content)
#     elif isinstance(message, HumanMessage):
#         with st.chat_message("Human"):
#             st.markdown(message.content)

# user_query = st.chat_input("Type a message...")
# if user_query is not None and user_query.strip() != "":
#     st.session_state.chat_history.append(HumanMessage(content=user_query))
    
#     with st.chat_message("Human"):
#         st.markdown(user_query)
        
#     with st.chat_message("AI"):
#         if "db" in st.session_state:
#             if "api_key" in st.session_state and "llm_type" in st.session_state:
#                 response = get_response(
#                     user_query, 
#                     st.session_state.db, 
#                     st.session_state.chat_history, 
#                     st.session_state.llm_type, 
#                     st.session_state.api_key, 
#                     st.session_state.model if st.session_state.model.strip() != "" else None
#                 )
#             else:
#                 response = "Please configure the LLM settings first."
#         else:
#             response = "Please connect to a database first."
#         st.markdown(response)
        
#     st.session_state.chat_history.append(AIMessage(content=response))

