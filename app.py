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
from utils.ui import show_login_page , show_main_page

# Configuration de la page et des styles globaux
st.set_page_config(
    page_title=" Database Assistant",
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




# Logique principale de l'application
if st.session_state.logged_in:
    show_main_page()
else:
    show_login_page()