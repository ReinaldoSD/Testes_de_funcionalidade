from flask import jsonify, request, render_template
from banco_dados.database import conectar, cadastrar_roupa, editar_roupa, excluir_roupa
from datetime import datetime
from werkzeug.utils import secure_filename
import os, json, uuid, io, base64, PIL.Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
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
        roupas = {row['id']: dict(row) for row in cursor.fetchall()}
        for r in roupas.values():
            r['fotos'] = []

        cursor.execute("SELECT roupa_id, caminho FROM fotos_roupas")
        for row in cursor.fetchall():
            if row['roupa_id'] in roupas:
                roupas[row['roupa_id']]['fotos'].append(row['caminho'])
                
        conn.close()
        return jsonify(list(roupas.values()))

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
        cursor.execute("""
            SELECT h.data_uso, r.nome 
            FROM historico h
            JOIN roupas r ON h.roupa_id = r.id
            ORDER BY h.id DESC
        """)
        dados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(dados)

    @app.route('/excluir/<int:roupa_id>')
    def excluir(roupa_id):
        nome_da_peca = excluir_roupa(roupa_id)
        
        return f"A peça '{nome_da_peca}' foi excluída com sucesso!"

    @app.route('/cadastrar_via_imagem', methods=['POST'])
    def cadastrar_via_imagem():
        files = request.files.getlist('imagem')
        if not files or files[0].filename == '':
            return jsonify({"erro": "Nenhuma imagem enviada"}), 400

        imagens_ia = [
    """Analise esta imagem de uma peça de roupa e retorne um JSON estritamente com as chaves: 
    "nome", "tipo" (ex: Camiseta, Calça), "cor", "ocasiao" (ex: Casual, Formal) e "clima_ideal" (ex: Quente, Frio)."""
]
        fotos_base64 = []

        try:
            for file in files:
                img_bytes = file.read()
                imagens_ia.append(PIL.Image.open(io.BytesIO(img_bytes)))
                
                encoded = base64.b64encode(img_bytes).decode('utf-8')
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpeg'
                fotos_base64.append(f"data:image/{ext};base64,{encoded}")

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=imagens_ia,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            return jsonify({
                "dados": json.loads(response.text),
                "fotos_base64": fotos_base64
            }), 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"erro": str(e)}), 500

    @app.route('/salvar_final', methods=['POST'])
    def salvar_final():
        dados = request.json
        fotos_base64 = dados.get('fotos_base64', [])
        caminhos_finais = []

        upload_dir = os.path.join(app.root_path, 'static', 'uploads')

        for data_uri in fotos_base64:
            header, encoded = data_uri.split(",", 1)
            ext = header.split("/")[1].split(";")[0]
            nome_arquivo = f"{uuid.uuid4().hex}.{ext}"
            path_completo = os.path.join(upload_dir, nome_arquivo)
            
            with open(path_completo, "wb") as f:
                f.write(base64.b64decode(encoded))
            
            caminhos_finais.append(f"static/uploads/{nome_arquivo}")

        cadastrar_roupa(
            dados.get('nome'), 
            dados.get('tipo'), 
            dados.get('cor'), 
            dados.get('ocasiao'), 
            dados.get('clima'),
            caminhos_finais
        )
        return jsonify({"mensagem": "Roupa guardada com sucesso!"}), 200
