from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
import requests
import json
from datetime import datetime

from app import app, client, get_google_provider_cfg, get_user_services
from models import User

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
    return render_template('index.html', show_progress_bar=False, current_year=datetime.now().year)

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html', show_progress_bar=False, current_year=datetime.now().year)

@app.route('/upload_file', methods=['GET', 'POST'])
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
            try:
                doc_processor, rag_service = get_user_services(current_user.id)
                split_docs = doc_processor.process_file(uploaded_file)
                
                if split_docs:
                    collection_name = rag_service.create_rag_chain(split_docs)
                    session[f'collection_name_{current_user.id}'] = collection_name
                    session['current_step'] = 1
                    return redirect(url_for('generate_questions'))
                else:
                    app.logger.error("Document processing returned None")
                    flash('Error processing document: No content could be extracted')
                    return redirect(request.url)
                
            except Exception as e:
                app.logger.error(f"Error processing document: {str(e)}")
                flash(f'Error processing document: {str(e)}')
                return redirect(request.url)
        
        flash('Unsupported file type')
        return redirect(request.url)
    
    return render_template('upload.html', 
                         current_step=session.get('current_step', 0),
                         user=current_user,
                         show_progress_bar=True)

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
        complexity = request.form.get('complexity', 'Easy')
        
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
                         user=current_user,
                         show_progress_bar=True)

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
                         zip=zip,
                         show_progress_bar=True)

@app.context_processor
def utility_processor():
    """Add current_step to all templates by default"""
    return dict(
        current_step=session.get('current_step', 0),
    )