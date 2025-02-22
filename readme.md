
```markdown
#  Database Assistant 🤖

**Database Assistant** est une application web interactive qui vous permet d'interagir avec vos bases de données SQL en utilisant des modèles de langage naturel (LLM). Posez des questions en langage naturel, et l'assistant génère et exécute les requêtes SQL correspondantes pour vous fournir des réponses claires et précises.

---

## Fonctionnalités principales 🚀

- **Connexion à plusieurs types de bases de données** : MySQL, PostgreSQL, SQL Server.
- **Génération de requêtes SQL** : L'assistant génère des requêtes SQL en fonction de vos questions en langage naturel.
- **Historique de conversation** : Conservez un historique des questions et réponses pour une meilleure continuité.
- **Support de plusieurs modèles LLM** : Intégration avec OpenAI (GPT-4, GPT-3.5) et Groq (Llama2, Mixtral).
- **Interface utilisateur intuitive** : Une interface Streamlit moderne et réactive pour une expérience utilisateur optimale.
- **Sécurité** : Authentification requise pour accéder à l'application.

---

## Comment utiliser l'application 🛠️

### 1. Connexion à l'application
- Accédez à la page de connexion.
- Entrez les identifiants suivants :
  - **Nom d'utilisateur** : `admin`
  - **Mot de passe** : `aze123`

### 2. Configuration de la base de données
- Dans le panneau latéral, configurez les paramètres de connexion à votre base de données :
  - Type de base de données (MySQL, PostgreSQL, SQL Server).
  - Hôte, port, nom d'utilisateur, mot de passe et nom de la base de données.
- Cliquez sur **"Se connecter à la BD"** pour établir la connexion.

### 3. Configuration du modèle IA
- Sélectionnez le fournisseur de modèle (OpenAI ou Groq).
- Choisissez le modèle spécifique (par exemple, GPT-4, Llama2).
- Entrez votre clé API pour le service sélectionné.

### 4. Posez vos questions
- Dans l'onglet **"💬 Assistant SQL"**, posez vos questions en langage naturel.
- L'assistant générera et exécutera la requête SQL correspondante, puis affichera les résultats.

### 5. Exemples de questions
- "Quels sont les 5 artistes les plus populaires ?"
- "Montrez-moi le nombre total de ventes par région."
- "Quelle est la moyenne des prix des produits par catégorie ?"
- "Listez les clients qui ont passé plus de 3 commandes."

---

## Prérequis 📋

- **Python 3.8 ou supérieur**
- **Streamlit** : `pip install streamlit`
- **LangChain** : `pip install langchain`
- **SQLAlchemy** : `pip install sqlalchemy`
- **dotenv** : `pip install python-dotenv`
- **Autres dépendances** : `pip install langchain-openai langchain-groq mysql-connector-python psycopg2 pyodbc`

---

## Installation et exécution 🚀

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-utilisateur/digitar-database-assistant.git
   cd digitar-database-assistant
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Lancez l'application :
   ```bash
   streamlit run app.py
   ```

4. Accédez à l'application dans votre navigateur à l'adresse :
   ```
   http://localhost:8501
   ```

---


## Auteur 👤

- **BARRY SANOUSSA**
- [BARRY](https://sanoussabarry.com/)
```

