from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from prompts import get_question_generation_prompt, get_answer_validation_prompt

class RAGService:
    def __init__(self, groq_api_key, model_name, embedding_model_name, embeddings_dir):
        self.groq_api_key = groq_api_key
        self.model_name = model_name
        self.embedding_model_name = embedding_model_name
        self.embeddings_dir = embeddings_dir
        self.groq_chat = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=self.model_name
        )
    
    def create_rag_chain(self, split_docs):
        """Create RAG chain with embeddings and return collection name."""
        embedding_model = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name
        )
        
        # Create a unique collection name for this upload
        collection_name = f"document_embeddings_{hash(str(split_docs))}"
        
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=self.embeddings_dir
        )
        
        vector_store.add_documents(split_docs)
        
        # Return only the collection name
        return collection_name
    
    def get_rag_chain(self, collection_name):
        """Recreate RAG chain from collection name."""
        embedding_model = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name
        )
        
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=self.embeddings_dir
        )
        
        retriever = vector_store.as_retriever()
        return RetrievalQA.from_chain_type(
            llm=self.groq_chat,
            chain_type="stuff",
            retriever=retriever
        )
    
    def generate_questions(self, collection_name, question_count, complexity):
        """Generate questions using the RAG chain."""
        rag_chain = self.get_rag_chain(collection_name)
        prompt = get_question_generation_prompt(question_count, complexity)
        response = rag_chain.invoke({"query": prompt})
        
        # Process and return the questions
        questions = [q.strip() for q in response['result'].split('\n') if q.strip() and not q.startswith("Here are")]
        return questions
    
    def validate_answer(self, collection_name, question, answer):
        """Validate an answer using the RAG chain."""
        rag_chain = self.get_rag_chain(collection_name)
        prompt = get_answer_validation_prompt(question, answer)
        validation_response = rag_chain.invoke({"query": prompt})
        return validation_response['result'].strip()