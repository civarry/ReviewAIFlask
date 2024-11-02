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
        """Create RAG chain with embeddings."""
        embedding_model = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name
        )

        vector_store = Chroma(
            collection_name="document_embeddings",
            embedding_function=embedding_model,
            persist_directory=self.embeddings_dir
        )

        vector_store.reset_collection()
        vector_store.add_documents(split_docs)

        retriever = vector_store.as_retriever()
        return RetrievalQA.from_chain_type(
            llm=self.groq_chat,
            chain_type="stuff",
            retriever=retriever
        )

    def generate_questions(self, rag_chain, question_count, complexity):
        """Generate questions using the RAG chain."""
        user_query = f"""You are an advanced question generation model tasked with creating {question_count} unique questions based exclusively on the provided documents. Each question should reflect the specified complexity level of {complexity}.\n
        Your output must consist of questions only, with no additional information or commentary.\n
        ***Complexity Level:*** Ensure each question aligns with the specified complexity level ({complexity}).\n
        ***Uniqueness:*** Each question must be distinct, ensuring no overlap in content or phrasing among the questions.\n
        ***Question Format:*** Generate only questions, focusing on open-ended formats that encourage deeper thinking and exploration of the text.\n
        ***Strict Adherence:*** All questions must strictly derive from the content of the documents provided, with no external information or assumptions included."""

        response = rag_chain.invoke({"query": user_query})
        questions = [q.strip() for q in response['result'].split('\n') 
                    if q.strip() and not q.startswith("Here are")]
        return questions

    def validate_answer(self, rag_chain, question, answer):
        """Validate an answer using the RAG chain."""
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