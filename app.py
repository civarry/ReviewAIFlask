from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from document_processor import DocumentProcessor
from rag_service import RAGService
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize services
doc_processor = DocumentProcessor(
    save_dir=app.config['SAVE_DIR'],
    chunk_size=app.config['CHUNK_SIZE'],
    chunk_overlap=app.config['CHUNK_OVERLAP']
)

rag_service = RAGService(
    groq_api_key=app.config['GROQ_API_KEY'],
    model_name=app.config['MODEL_NAME'],
    embedding_model_name=app.config['EMBEDDING_MODEL_NAME'],
    embeddings_dir=app.config['EMBEDDINGS_DIR']
)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    session['current_step'] = 0
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if uploaded_file and uploaded_file.filename.lower().endswith(app.config['ALLOWED_EXTENSIONS']):
            split_docs = doc_processor.process_file(uploaded_file)
            
            if split_docs:
                rag_chain = rag_service.create_rag_chain(split_docs)
                app.config['RAG_CHAIN'] = rag_chain
                session['current_step'] = 1
                return redirect(url_for('generate_questions'))
            
            flash('Error processing document')
            return redirect(request.url)
        
        flash('Unsupported file type')
        return redirect(request.url)
    
    return render_template('upload.html', current_step=session.get('current_step', 0))

@app.route('/generate_questions', methods=['GET', 'POST'])
def generate_questions():
    if 'RAG_CHAIN' not in app.config:
        flash('Please upload a document first')
        return redirect(url_for('upload_file'))
    
    session['current_step'] = 1
    
    if request.method == 'POST':
        question_count = int(request.form.get('question_count', 5))
        complexity = request.form.get('complexity', 'Medium')
        
        questions = rag_service.generate_questions(
            app.config['RAG_CHAIN'],
            question_count,
            complexity
        )
        
        session['current_step'] = 2
        return render_template('questions.html',
                             questions=questions,
                             current_step=session['current_step'])
    
    return render_template('generate_questions.html',
                         current_step=session['current_step'])

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    if 'RAG_CHAIN' not in app.config:
        flash('Please upload a document first')
        return redirect(url_for('upload_file'))
    
    session['current_step'] = 3
    
    questions = request.form.getlist('questions')
    answers = request.form.getlist('answers')
    
    validations = []
    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        validation_text = rag_service.validate_answer(
            app.config['RAG_CHAIN'],
            question,
            answer
        )
        
        validations.append({
            'number': str(i),
            'question': question,
            'validation': validation_text
        })
    
    return render_template('results.html',
                         questions=questions,
                         answers=answers,
                         validations=validations,
                         current_step=session['current_step'],
                         zip=zip)

@app.context_processor
def utility_processor():
    """Add current_step to all templates by default"""
    return dict(current_step=session.get('current_step', 0))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get the port from the environment
    app.run(host='0.0.0.0', port=port, debug=False)