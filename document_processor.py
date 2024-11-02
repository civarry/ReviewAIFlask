import os
import uuid
import pandas as pd
from docx import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, save_dir, chunk_size, chunk_overlap):
        self.save_dir = save_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        os.makedirs(self.save_dir, exist_ok=True)

    def extract_text_from_file(self, uploaded_file):
        """Extract text from various file types."""
        filename = uploaded_file.filename
        if filename.endswith('.txt'):
            return uploaded_file.read().decode('utf-8')
        elif filename.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            return ' '.join(df.astype(str).agg(' '.join, axis=1).tolist())
        elif filename.endswith('.docx'):
            doc = Document(uploaded_file)
            return ' '.join([para.text for para in doc.paragraphs])
        return None

    def save_text_to_file(self, text, filename):
        """Save extracted text to a file."""
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(self.save_dir, unique_filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return file_path

    def load_documents(self):
        """Load documents from the save directory."""
        loader = DirectoryLoader(
            self.save_dir, 
            glob="**/*.txt", 
            loader_cls=TextLoader, 
            show_progress=True
        )
        return loader.load()

    def split_documents(self, documents):
        """Split documents into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return text_splitter.split_documents(documents)

    def cleanup_documents(self):
        """Remove files in the SAVE_DIR after processing."""
        for filename in os.listdir(self.save_dir):
            file_path = os.path.join(self.save_dir, filename)
            os.remove(file_path)

    def process_file(self, uploaded_file):
        """Process a file from upload to splitting."""
        text = self.extract_text_from_file(uploaded_file)
        if text:
            self.save_text_to_file(text, uploaded_file.filename)
            documents = self.load_documents()
            split_docs = self.split_documents(documents)
            self.cleanup_documents()
            return split_docs
        return None