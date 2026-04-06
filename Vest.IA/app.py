from flask import Flask, jsonify
from banco_dados.database import cadastrar_roupa, editar_roupa, excluir_roupa
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir if 'banco_dados' not in current_dir else os.path.dirname(current_dir)

DB_FOLDER = os.path.join(project_root, 'banco_dados')
DB_PATH = os.path.join(DB_FOLDER, 'vest.ia.db')

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return "Servidor rodando"

# listar roupas
@app.route('/listar')
def listar():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM roupas")
    dados = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(dados)

# cadastrar roupa
@app.route('/cadastrar')
def cadastrar():
    cadastrar_roupa("Camisa preta", "Camisa", "Preta", "Casual", "Meia-estação")
    return "Roupa cadastrada!"

# usar roupa
@app.route('/usar/<int:roupa_id>')
def usar(roupa_id):
    conn = conectar()
    cursor = conn.cursor()

    # atualiza uso
    cursor.execute("""
    UPDATE roupas
    SET vezes_usada = vezes_usada + 1
    WHERE id = ?
    """, (roupa_id,))

    # registra histórico
    cursor.execute("""
    INSERT INTO historico (roupa_id, data_uso)
    VALUES (?, ?)
    """, (roupa_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    return f"Roupa {roupa_id} usada!"

# ver histórico
@app.route('/historico')
def historico():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM historico")
    dados = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(dados)

# editar
@app.route('/editar/<int:roupa_id>')
def editar(roupa_id):
    editar_roupa(roupa_id, "Nova camisa", "Camisa", "Azul", "Casual", "Quente")
    return f"Roupa {roupa_id} atualizada!"

@app.route('/excluir/<int:roupa_id>')
def excluir(roupa_id):
    excluir_roupa(roupa_id)
    return f"Roupa {roupa_id} excluída com sucesso!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
