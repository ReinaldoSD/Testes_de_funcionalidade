from flask import Flask
from banco_dados.create_db import criar_banco
from routes import configure_routes
import os

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagens_roupas')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

criar_banco()
configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
