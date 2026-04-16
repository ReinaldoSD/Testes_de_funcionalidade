from flask import jsonify
from banco_dados.database import conectar, cadastrar_roupa, editar_roupa, excluir_roupa
from datetime import datetime

def configure_routes(app):

    @app.route('/')
    def home():
        return "Servidor Vest.IA rodando!"

    @app.route('/listar')
    def listar():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roupas")
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(dados)

    @app.route('/cadastrar')
    def cadastrar():
        cadastrar_roupa("Camisa preta", "Camisa", "Preta", "Casual", "Meia-estação")
        return "Roupa cadastrada!"

    @app.route('/usar/<int:roupa_id>')
    def usar(roupa_id):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE roupas SET vezes_usada = vezes_usada + 1 WHERE id = ?", (roupa_id,))
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO historico (roupa_id, data_uso) VALUES (?, ?)", (roupa_id, data_atual))
        conn.commit()
        conn.close()
        return f"Roupa {roupa_id} usada em {data_atual}!"

    @app.route('/historico')
    def historico():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historico")
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(dados)

    @app.route('/editar/<int:roupa_id>')
    def editar(roupa_id):
        editar_roupa(roupa_id, "Nova camisa", "Camisa", "Azul", "Casual", "Quente")
        return f"Roupa {roupa_id} atualizada!"

    @app.route('/excluir/<int:roupa_id>')
    def excluir(roupa_id):
        excluir_roupa(roupa_id)
        return f"Roupa {roupa_id} excluída com sucesso!"
