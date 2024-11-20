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
    
    def create_rag_chain(self, split_docs): #responsible for creating the numerical representation of the provided documents.
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
    
    def get_rag_chain(self, collection_name): #this is similar to a librarian who knows how to find the relevant parts from the chroma embedding
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
    
    def generate_questions(self, collection_name, question_count, complexity): ##since we're using RAG the prompt we're passing to the LLM is more specific and focused because it includes the relevant context retrieved from the embeddings.
        rag_chain = self.get_rag_chain(collection_name)
        prompt = get_question_generation_prompt(question_count, complexity)
        response = rag_chain.invoke({"query": prompt})
        
        # Process and return the questions
        questions = [q.strip() for q in response['result'].split('\n') if q.strip() and not q.startswith("Here are")]
        return questions
    
    def validate_answer(self, collection_name, question, answer):
        rag_chain = self.get_rag_chain(collection_name)
        prompt = get_answer_validation_prompt(question, answer)
        validation_response = rag_chain.invoke({"query": prompt})
        print(f"Prompt: {prompt}")
        print(f"Result: {validation_response['result']}")
        return validation_response['result'].strip()