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
