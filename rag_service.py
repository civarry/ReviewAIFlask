from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

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
        
        user_query = f"""You are an advanced question generation model tasked with creating {question_count} unique questions based exclusively on the provided documents. Each question should reflect the specified complexity level of {complexity}.
        
        Your output must consist of questions only, with no additional information or commentary.
        
        ***Complexity Level:*** Ensure each question aligns with the specified complexity level ({complexity}).
        ***Uniqueness:*** Each question must be distinct, ensuring no overlap in content or phrasing among the questions.
        ***Question Format:*** Generate only questions, focusing on open-ended formats that encourage deeper thinking and exploration of the text.
        ***Strict Adherence:*** All questions must strictly derive from the content of the documents provided, with no external information or assumptions included."""
        
        response = rag_chain.invoke({"query": user_query})
        questions = [q.strip() for q in response['result'].split('\n') if q.strip() and not q.startswith("Here are")]
        return questions
    
    def validate_answer(self, collection_name, question, answer):
        """Validate an answer using the RAG chain."""
        rag_chain = self.get_rag_chain(collection_name)
        
        validation_query = f"""
        Validation Task
        --------------
        Question: {question}
        Answer: {answer}
        
        Instructions for Validation:
        1. Compare answer against retrieved context from uploaded document
        2. Focus on factual accuracy and completeness
        3. Check if answer directly addresses the question
        4. Ignore any information not from the document context
        
        Required Output Format:
        Verdict: [One word: Correct or Incorrect]
        Feedback: [One clear sentence explaining the verdict, max 30 words]
        """
        
        validation_response = rag_chain.invoke({"query": validation_query})
        return validation_response['result'].strip()