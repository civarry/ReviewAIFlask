from flask import Flask, session
from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient
import requests
import pathlib
import os
from config import Config
from document_processor import DocumentProcessor
from rag_service import RAGService

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config.from_object(Config)

# OAuth 2.0 client setup
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User session management
@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        return None
    # Get user data from session
    user_data = session.get('user_data')
    if user_data:
        from models import User
        return User(user_id, user_data['email'], user_data['name'])
    return None

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

def get_user_storage_path(user_id):
    """Create and return user-specific storage paths"""
    base_path = pathlib.Path(app.config['BASE_STORAGE_DIR'])
    user_path = base_path / str(user_id)
    user_path.mkdir(parents=True, exist_ok=True)
    
    # Create user-specific directories
    save_dir = user_path / 'documents'
    save_dir.mkdir(exist_ok=True)
    embeddings_dir = user_path / 'embeddings'
    embeddings_dir.mkdir(exist_ok=True)
    
    return str(save_dir), str(embeddings_dir)

def get_user_services(user_id):
    """Get or create user-specific document processor and RAG service"""
    save_dir, embeddings_dir = get_user_storage_path(user_id)
    
    doc_processor = DocumentProcessor(
        save_dir=save_dir,
        chunk_size=app.config['CHUNK_SIZE'],
        chunk_overlap=app.config['CHUNK_OVERLAP']
    )

    rag_service = RAGService(
        groq_api_key=app.config['GROQ_API_KEY'],
        model_name=app.config['MODEL_NAME'],
        embedding_model_name=app.config['EMBEDDING_MODEL_NAME'],
        embeddings_dir=embeddings_dir
    )
    
    return doc_processor, rag_service

# Import routes at the bottom to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)