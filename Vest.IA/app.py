from flask import Flask
from banco_dados.create_db import criar_banco
from routes import configure_routes

app = Flask(__name__)

criar_banco()
configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
