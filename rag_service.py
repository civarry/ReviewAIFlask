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
        
        # Define specific instructions based on complexity level
        complexity_instructions = {
            "Easy": "Generate questions that are straightforward and easily understandable, focusing on key concepts.",
            "Medium": "Create questions that are understandable but include a subtle twist or require connecting concepts.",
            "Hard": "Formulate questions that challenge the user to think critically or make inferences based on the document."
        }
        
        # Retrieve the instructions for the specified complexity
        complexity_text = complexity_instructions.get(complexity, "Specify a valid complexity level.")

        user_query = f"""Generate {question_count} unique questions based strictly on the provided document.

        Required: Analyze the provided document to identify key concepts, terminology, and logical flow.

        {complexity_text}

        Instructions:
        1. **Unique Questions**: Each question should cover different content or phrasing.
        2. **Open-ended**: Formulate questions that require critical thinking or inference.
        3. **Document-Based**: Rely solely on the document's content—no external assumptions.

        Output only the questions, with no commentary or additional information."""
        
        rag_chain = self.get_rag_chain(collection_name)
        response = rag_chain.invoke({"query": user_query})
        
        # Process and return the questions
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