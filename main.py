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
        st.error(f"Failed to connect to database: {str(e)}")
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
        st.error(f"Failed to initialize LLM chain: {str(e)}")
        return None

def get_response(user_query: str, db: SQLDatabase, chat_history: list, llm_type: str, api_key: str, model: str = None):
    sql_chain = get_llm_chain(db, llm_type, api_key, model)
    if sql_chain is None:
        return "Failed to initialize LLM chain. Check your LLM settings."

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
        return f"SQL error: {str(pe)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Initialisation des variables de session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."),
    ]

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login(username, password):
    # Remplacez ceci par la vérification réelle des identifiants
    if username == "admin" and password == "aze123":
        return True
    return False

def show_login_page():
    st.set_page_config(page_title="Login - Chat with Database", page_icon=":lock:", layout="centered")
    st.title("Login to Chat with Your Database")

    st.markdown("""
        <style>
        .login-container {
            # background-color: #f4f4f9;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            margin: 0 auto;
        }
        .login-button {
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
        }
        .footer-text {
            margin-top: 1rem;
            font-size: 0.875rem;
            color: #888;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login", key="login_button", help="Click to log in", use_container_width=True)

    if login_button:
        if login(username, password):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Incorrect credentials. Please try again.")

    st.markdown('<div class="footer-text">Developed by DIGITAR</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_main_page():
    load_dotenv()

    st.set_page_config(page_title="Chat with Database", page_icon=":speech_balloon:", layout="centered")

    st.markdown("""
        <style>
        .main {
            color: #ffffff;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("Chat with Your Database")

    with st.sidebar:
        st.subheader("Settings", divider=True)
        st.write("Connect to the database and start chatting.")
        
        db_type = st.selectbox("Database Type", ["MySQL", "PostgreSQL", "SQL Server"], key="db_type")
        host = st.text_input("Host", value="localhost", key="Host")
        port = st.text_input("Port", value="3306", key="Port")
        user = st.text_input("UserName", value="root", key="User")
        password = st.text_input("Password", type="password", value="admin", key="Password")
        database = st.text_input("Database", value="artist", key="Database")
        
        st.subheader("LLM Configuration")
        llm_type = st.selectbox("LLM Type", ["OpenAI", "Groq"], key="llm_type")
        model = st.text_input("Model (optional)", value="", key="model", help="Leave empty to use the default model")
        api_key = st.text_input("API Key", type="password", key="api_key")

        if st.button("Connect"):
            with st.spinner("Connecting to database..."):
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
                        st.success("Connected to database!")
                    else:
                        st.error("Failed to connect to the database.")
                except Exception as e:
                    st.error(f"Failed to connect to database: {str(e)}")

    st.subheader("Chat with the Database")
    st.write("Ask your database anything and get the response in natural language.")

    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.markdown(message.content)

    user_query = st.chat_input("Type a message...")
    if user_query is not None and user_query.strip() != "":
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        
        with st.chat_message("Human"):
            st.markdown(user_query)
            
        with st.chat_message("AI"):
            if "db" in st.session_state:
                if "api_key" in st.session_state and "llm_type" in st.session_state:
                    response = get_response(
                        user_query, 
                        st.session_state.db, 
                        st.session_state.chat_history, 
                        st.session_state.llm_type, 
                        st.session_state.api_key, 
                        st.session_state.model if st.session_state.model.strip() != "" else None
                    )
                else:
                    response = "Please configure the LLM settings first."
            else:
                response = "Please connect to a database first."
            st.markdown(response)
            
        st.session_state.chat_history.append(AIMessage(content=response))

    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.experimental_rerun()

if st.session_state.logged_in:
    show_main_page()
else:
    show_login_page()
