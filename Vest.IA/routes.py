from flask import jsonify, request, send_from_directory
from banco_dados.database import conectar, cadastrar_roupa, editar_roupa, excluir_roupa
from datetime import datetime
import os
from werkzeug.utils import secure_filename

def configure_routes(app):
    UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/listar')
    def listar():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roupas")
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(dados)

    @app.route('/upload', methods=['POST'])
    def upload_imagem():
        if 'imagem' not in request.files:
            return jsonify({"erro": "Nenhum arquivo foi enviado"}), 400
        
        arquivo = request.files['imagem']
        
        if arquivo.filename == '':
            return jsonify({"erro": "Nenhum arquivo selecionado"}), 400
        
        if arquivo and allowed_file(arquivo.filename):
            nome_seguro = secure_filename(arquivo.filename)
            nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_seguro}"
            caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
            arquivo.save(caminho_completo)
            
            caminho_relativo = f"imagens_roupas/{nome_arquivo}"
            return jsonify({
                "mensagem": "Imagem enviada com sucesso",
                "caminho_imagem": caminho_relativo
            }), 200
        else:
            return jsonify({"erro": "Tipo de arquivo não permitido. Envie apenas imagens (png, jpg, jpeg, gif)"}), 400

    @app.route('/imagens_roupas/<nome_arquivo>')
    def ver_imagem(nome_arquivo):
        return send_from_directory(UPLOAD_FOLDER, nome_arquivo)

    @app.route('/cadastrar', methods=['POST'])
    def cadastrar():
        dados = request.get_json()
        nome = dados.get('nome')
        tipo = dados.get('tipo')
        cor = dados.get('cor')
        ocasiao = dados.get('ocasiao')
        clima_ideal = dados.get('clima_ideal')
        caminho_imagem = dados.get('imagem')

        if not all([nome, tipo, cor, ocasiao, clima_ideal]):
            return jsonify({"erro": "Preencha todos os campos obrigatórios"}), 400

        cadastrar_roupa(nome, tipo, cor, ocasiao, clima_ideal, caminho_imagem)
        return jsonify({"mensagem": "Roupa cadastrada com sucesso"}), 201

    @app.route('/usar/<int:roupa_id>')
    def usar(roupa_id):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roupas WHERE id = ?", (roupa_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({"erro": "Roupa não encontrada"}), 404

        cursor.execute("UPDATE roupas SET vezes_usada = vezes_usada + 1 WHERE id = ?", (roupa_id,))
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO historico (roupa_id, data_uso) VALUES (?, ?)", (roupa_id, data_atual))
        conn.commit()
        conn.close()
        return jsonify({"mensagem": f"Roupa {roupa_id} usada em {data_atual}!"}), 200

    @app.route('/historico')
    def historico():
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historico")
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(dados)

    @app.route('/editar/<int:roupa_id>', methods=['PUT'])
    def editar(roupa_id):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roupas WHERE id = ?", (roupa_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({"erro": "Roupa não encontrada"}), 404
        conn.close()

        dados = request.get_json()
        nome = dados.get('nome')
        tipo = dados.get('tipo')
        cor = dados.get('cor')
        ocasiao = dados.get('ocasiao')
        clima_ideal = dados.get('clima_ideal')
        caminho_imagem = dados.get('imagem')

        if not all([nome, tipo, cor, ocasiao, clima_ideal]):
            return jsonify({"erro": "Preencha todos os campos obrigatórios"}), 400

        editar_roupa(roupa_id, nome, tipo, cor, ocasiao, clima_ideal, caminho_imagem)
        return jsonify({"mensagem": f"Roupa {roupa_id} atualizada com sucesso!"}), 200

    @app.route('/excluir/<int:roupa_id>')
    def excluir(roupa_id):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roupas WHERE id = ?", (roupa_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({"erro": "Roupa não encontrada"}), 404
        
        excluir_roupa(roupa_id)
        conn.close()
        return jsonify({"mensagem": f"Roupa {roupa_id} excluída com sucesso!"}), 200
