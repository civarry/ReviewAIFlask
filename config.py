import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask Config
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Directory Configuration
    BASE_STORAGE_DIR = "user_data"
    SAVE_DIR = 'documents'
    EMBEDDINGS_DIR = 'chroma_embeddings'
    
    # Model Configuration
    GROQ_API_KEY = os.getenv('groq_api_key')
    MODEL_NAME = 'llama-3.2-1b-preview'  # or 'mixtral-8x7b-32768l'
    
    # Document Processing Configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100
    
    # Embedding Model Configuration
    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Allowed File Extensions
    ALLOWED_EXTENSIONS = ('.txt', '.csv', '.docx')

    # Google OAuth 2.0 settings
    GOOGLE_CLIENT_ID = os.getenv('google_client_id')
    GOOGLE_CLIENT_SECRET = os.getenv('google_client_secret')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"