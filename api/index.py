from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sys
import os

# Adicionar o diretório raiz ao PATH para encontrar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import init_db, add_user, verify_user, get_user_id, save_message, get_messages

app = Flask(__name__)
app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app.secret_key = 'sua_chave_secreta_aqui'

# Rota específica para arquivos estáticos
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Inicializar o banco de dados
init_db()

@app.route('/')
def home():
    if 'username' in session:
        user_id = get_user_id(session['username'])
        messages = get_messages()
        return render_template('chat.html', username=session['username'], 
                             user_id=user_id, messages=messages)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, wait_time = verify_user(username, password)
        
        if wait_time > 0:
            flash(f'Conta temporariamente bloqueada. Tente novamente em {wait_time} segundos.', 'error')
        elif success:
            session['username'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não coincidem!', 'error')
        else:
            if add_user(username, email, password):
                flash('Conta criada com sucesso!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Usuário ou email já existem!', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    content = request.form.get('content')
    if content:
        user_id = get_user_id(session['username'])
        save_message(user_id, session['username'], content)
    
    return redirect(url_for('home'))

# Adicionar handler WSGI para Vercel
app.wsgi_app = app.wsgi_app
