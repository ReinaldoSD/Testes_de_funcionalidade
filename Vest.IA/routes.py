from flask import jsonify, request, render_template, redirect, session
from banco_dados.database import conectar, cadastrar_roupa, editar_roupa, excluir_roupa
from datetime import datetime
import os, json, uuid, io, base64, PIL.Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

import random
import smtplib
from email.mime.text import MIMEText

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

codigos_recuperacao = {}

def gerar_codigo():
    return str(random.randint(100000, 999999))

def enviar_email(email, codigo):

    msg = MIMEText(f"Seu código de recuperação Vest.IA: {codigo}")
    msg['Subject'] = "Recuperação de senha"
    msg['From'] = "SEUEMAIL@gmail.com"
    msg['To'] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("SEUEMAIL@gmail.com", "SENHA_DE_APP")
    server.send_message(msg)
    server.quit()

def configure_routes(app):

    @app.route('/')
    def home():
        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM roupas")
        total_roupas = cursor.fetchone()['total']

        cursor.execute("""
            SELECT * FROM roupas
            ORDER BY vezes_usada ASC
            LIMIT 5
        """)
        menos_usadas = cursor.fetchall()

        conn.close()

        return render_template(
            'dashboard.html',
            total_roupas=total_roupas,
            menos_usadas=menos_usadas
        )

    @app.route('/cadastrar')
    def cadastrar_page():
        return render_template('cadastrar_roupa.html')

    @app.route('/roupas')
    def roupas_page():
        return render_template('minhas_roupas.html')

    @app.route('/historico_page')
    def historico_page():
        return render_template('historico.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/recuperar_senha')
    def recuperar_senha():
        return render_template('esquecisenha.html')

    @app.route('/registrar', methods=['POST'])
    def registrar():

        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha)
                VALUES (?, ?, ?)
            """, (nome, email, senha))

            conn.commit()

        except:
            conn.close()
            return "E-mail já cadastrado."

        conn.close()

        return redirect('/')

    @app.route('/login', methods=['POST'])
    def login():

        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM usuarios
            WHERE email = ? AND senha = ?
        """, (email, senha))

        usuario = cursor.fetchone()

        conn.close()

        if usuario:

            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']

            return redirect('/dashboard')

        return "E-mail ou senha inválidos."

    @app.route('/listar')
    def listar():

        nome = request.args.get('nome', '').lower()
        tipo = request.args.get('tipo', '')
        cor = request.args.get('cor', '')

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

        lista = list(roupas.values())

        if nome:
            lista = [r for r in lista if nome in r['nome'].lower()]

        if tipo:
            lista = [r for r in lista if r['tipo'] == tipo]

        if cor:
            lista = [r for r in lista if r['cor'] == cor]

        return jsonify(lista)

    @app.route('/usar/<int:roupa_id>')
    def usar(roupa_id):

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE roupas SET vezes_usada = vezes_usada + 1 WHERE id = ?",
            (roupa_id,)
        )

        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO historico (roupa_id, data_uso) VALUES (?, ?)",
            (roupa_id, data_atual)
        )

        conn.commit()
        conn.close()

        return "ok"

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
            "nome", "tipo", "cor", "ocasiao" e "clima_ideal"."""
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
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            return jsonify({
                "dados": json.loads(response.text),
                "fotos_base64": fotos_base64
            }), 200

        except Exception as e:
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


    @app.route('/enviar_codigo', methods=['POST'])
    def enviar_codigo():

        email = request.json['email']

        codigo = gerar_codigo()
        codigos_recuperacao[email] = codigo

        enviar_email(email, codigo)

        return jsonify({"ok": True})


    @app.route('/validar_codigo', methods=['POST'])
    def validar_codigo():

        email = request.json['email']
        codigo = request.json['codigo']

        if codigos_recuperacao.get(email) == codigo:
            session['email_reset'] = email
            return jsonify({"ok": True})

        return jsonify({"ok": False, "mensagem": "Código inválido"})


    @app.route('/redefinir_senha', methods=['POST'])
    def redefinir_senha():

        email = session.get('email_reset')

        if not email:
            return jsonify({"ok": False, "mensagem": "Não autorizado"})

        nova_senha = request.json['senha']

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE usuarios
            SET senha = ?
            WHERE email = ?
        """, (nova_senha, email))

        conn.commit()
        conn.close()

        codigos_recuperacao.pop(email, None)
        session.pop('email_reset', None)

        return jsonify({"ok": True, "mensagem": "Senha atualizada!"})