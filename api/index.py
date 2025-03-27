from flask import Flask, render_template, request, redirect, url_for, flash, session
import sys
import os

# Adicionar o diretório raiz ao PATH para encontrar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import init_db, add_user, verify_user, get_user_id, save_message, get_messages

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Inicializar o banco de dados
init_db()

# ...existing code from app.py...
