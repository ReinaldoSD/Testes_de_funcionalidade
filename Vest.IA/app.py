import os
from flask import Flask
from banco_dados.create_db import criar_banco
from routes import configure_routes
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'chave_padrao_para_desenvolvimento')

_BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(_BASE_DIR, 'static', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config.update(
    UPLOAD_FOLDER      = UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024,
)

criar_banco()
configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)
