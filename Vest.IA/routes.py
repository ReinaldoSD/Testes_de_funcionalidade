
from flask import jsonify, request, render_template
from banco_dados.database import conectar, cadastrar_roupa, editar_roupa, excluir_roupa
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
from google import genai
from google.genai import types
import PIL.Image

API_KEY=os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

def configure_routes(app):

    @app.route('/')
    def home():
        return render_template("index.html")

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

    
    @app.route('/cadastrar_via_imagem', methods=['POST'])
    


    def cadastrar_via_imagem():
        if 'imagem' not in request.files:
            return jsonify({"erro": "Nenhuma imagem enviada na requisição"}), 400
            
        file = request.files['imagem']
        if file.filename == '':
            return jsonify({"erro": "Nenhum arquivo selecionado"}), 400

        if file:
            try:
                
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                img_to_analyze = PIL.Image.open(filepath)

                prompt = """
                Atue como um especialista em moda. Analise esta peça de roupa e retorne um objeto JSON estrito com as seguintes chaves e valores:
                - "nome": um nome descritivo juntando o tipo e a cor (ex: camisa_preta, saia_lilas, casaco_branco).
                - "tipo": a categoria da peça (ex: camisa, calca, saia, casaco).
                - "cor": a cor ou cores predominantes (ex: bege, lilas, verde, preto).
                - "ocasiao": a melhor ocasião de uso (escolha entre: casual, profissional, flexivel, festa).
                - "clima_ideal": o clima mais adequado (escolha entre: frio, quente, meia-estacao).
                """
                
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=[prompt, img_to_analyze],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
                
                
                dados_roupa = json.loads(response.text)

                
                caminho_banco = f"static/uploads/{filename}"
                cadastrar_roupa(
                    nome=dados_roupa.get('nome', 'Indefinido'),
                    tipo=dados_roupa.get('tipo', 'Indefinido'),
                    cor=dados_roupa.get('cor', 'Indefinida'),
                    ocasiao=dados_roupa.get('ocasiao', 'Indefinida'),
                    clima_ideal=dados_roupa.get('clima_ideal', 'Indefinido'),
                    imagem=caminho_banco
                )

                return jsonify({
                    "mensagem": "Roupa analisada pela IA e cadastrada com sucesso!",
                    "dados_extraidos": dados_roupa,
                    "caminho_imagem": caminho_banco
                }), 201

            except json.JSONDecodeError:
                return jsonify({"erro": "Falha ao processar o JSON retornado pela API.", "resposta_bruta": response.text}), 500
            except Exception as e:
                return jsonify({"erro": f"Erro interno ao processar a imagem: {str(e)}"}), 500