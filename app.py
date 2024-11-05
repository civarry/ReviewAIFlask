from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from oauthlib.oauth2 import WebApplicationClient
import requests
from config import Config
from document_processor import DocumentProcessor
from rag_service import RAGService
import os
import json
from datetime import datetime
import pathlib

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# User model
class User(UserMixin):
    def __init__(self, user_id, email, name):
        self.id = user_id
        self.email = email
        self.name = name

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

# Initialize services for each user
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

# Auth routes
@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )
    
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Get user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
        
        # Create user object and log them in
        user = User(unique_id, users_email, users_name)
        login_user(user)
        session['user_data'] = {
            'email': users_email,
            'name': users_name
        }
        
        return redirect(url_for("upload_file"))
    
    return "User email not verified by Google.", 400

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("upload_file"))

@app.route('/', methods=['GET', 'POST'])
@login_required
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
            doc_processor, rag_service = get_user_services(current_user.id)
            split_docs = doc_processor.process_file(uploaded_file)
            
            if split_docs:
                # Store only the collection name in session
                collection_name = rag_service.create_rag_chain(split_docs)
                session[f'collection_name_{current_user.id}'] = collection_name
                session['current_step'] = 1
                return redirect(url_for('generate_questions'))
            
            flash('Error processing document')
            return redirect(request.url)
        
        flash('Unsupported file type')
        return redirect(request.url)
    
    return render_template('upload.html', 
                         current_step=session.get('current_step', 0),
                         user=current_user)

@app.route('/generate_questions', methods=['GET', 'POST'])
@login_required
def generate_questions():
    collection_name = session.get(f'collection_name_{current_user.id}')
    if not collection_name:
        flash('Please upload a document first')
        return redirect(url_for('upload_file'))
    
    session['current_step'] = 1
    
    if request.method == 'POST':
        question_count = int(request.form.get('question_count', 5))
        complexity = request.form.get('complexity', 'Medium')
        
        _, rag_service = get_user_services(current_user.id)
        questions = rag_service.generate_questions(
            collection_name,
            question_count,
            complexity
        )
        
        session['current_step'] = 2
        return render_template('questions.html',
                             questions=questions,
                             current_step=session['current_step'],
                             user=current_user)
    
    return render_template('generate_questions.html',
                         current_step=session['current_step'],
                         user=current_user)

@app.route('/submit_answers', methods=['POST'])
@login_required
def submit_answers():
    collection_name = session.get(f'collection_name_{current_user.id}')
    if not collection_name:
        flash('Please upload a document first')
        return redirect(url_for('upload_file'))
    
    session['current_step'] = 3
    
    questions = request.form.getlist('questions')
    answers = request.form.getlist('answers')
    
    _, rag_service = get_user_services(current_user.id)
    validations = []
    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        validation_text = rag_service.validate_answer(
            collection_name,
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
                         user=current_user,
                         zip=zip)

@app.context_processor
def utility_processor():
    """Add current_step and user to all templates by default"""
    return dict(
        current_step=session.get('current_step', 0),
        user=getattr(current_user, 'name', None)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)