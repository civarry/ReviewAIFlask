import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask Config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_fallback_secret_key')
    
    # Directory Configuration
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