import os
import base64
import sqlite3
import random
from datetime import datetime

from flask import (
    jsonify, request, render_template,
    redirect, session, url_for, flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from banco_dados.database import (
    conectar, cadastrar_roupa, editar_roupa, excluir_roupa,
    cadastrar_usuario, verificar_usuario, email_existe,
    buscar_historico_usuario,
)
from utils.auth_utils   import login_obrigatorio
from utils.email_utils  import enviar_email_codigo
from utils.clima_utils  import obter_clima_local
from utils.imagem_utils import salvar_imagem_base64, salvar_foto_perfil
from modulos.ia_classificador import classificar_imagem
from modulos.ia_sugestoes     import (
    detectar_intencao, montar_look,
    gerar_look_por_clima, gerar_texto_look,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# ══════════════════════════════════════════════════════════════
def configure_routes(app):

    app.config['UPLOAD_PERFIL'] = os.path.join(BASE_DIR, 'static', 'uploads', 'perfil')

    # ── PÁGINAS ───────────────────────────────────────────────

    @app.route('/', methods=['GET'])
    @app.route('/login', methods=['GET'])
    def login_page():
        if 'usuario_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    @app.route('/register', methods=['GET'])
    @app.route('/registrar', methods=['GET'])
    def register_page():
        if 'usuario_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('register.html')

    @app.route('/recuperar_senha')
    def recuperar_senha_page():
        return render_template('esquecisenha.html')

    @app.route('/dashboard')
    @login_obrigatorio
    def dashboard():
        usuario_id = session['usuario_id']
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM roupas WHERE usuario_id = ?", (usuario_id,))
        total_roupas = cursor.fetchone()['total']
        cursor.execute(
            "SELECT * FROM roupas WHERE usuario_id = ? ORDER BY vezes_usada ASC LIMIT 5",
            (usuario_id,),
        )
        menos_usadas = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', total_roupas=total_roupas, menos_usadas=menos_usadas)

    @app.route('/cadastrar')
    @login_obrigatorio
    def cadastrar_page():
        return render_template('cadastrar_roupa.html')

    @app.route('/sugestoes')
    @login_obrigatorio
    def sugestoes_page():
        return render_template('sugestoes.html')

    @app.route('/minhas_roupas')
    @login_obrigatorio
    def roupas_page():
        return render_template('minhas_roupas.html')

    @app.route('/historico_page')
    @login_obrigatorio
    def historico_page():
        return render_template('historico.html')

    # ── AUTENTICAÇÃO ──────────────────────────────────────────

    @app.route('/login', methods=['POST'])
    def login():
        dados = request.get_json()
        if not dados:
            return jsonify({"ok": False, "mensagem": "Dados inválidos."}), 400
        email = dados.get('email', '').strip()
        senha = dados.get('senha', '').strip()
        usuario = verificar_usuario(email, senha)
        if usuario:
            session['usuario_id']   = usuario['id']
            session['usuario_nome'] = usuario['nome']
            return jsonify({"ok": True, "redirect": url_for('dashboard')})
        return jsonify({"ok": False, "mensagem": "E-mail ou senha incorretos."})

    @app.route('/registrar', methods=['POST'])
    def registrar():
        dados = request.get_json()
        nome  = dados.get('nome')
        email = dados.get('email')
        senha = dados.get('senha')
        if not nome or not email or not senha:
            return jsonify({"ok": False, "mensagem": "Preencha todos os campos!"}), 400
        if email_existe(email):
            return jsonify({"ok": False, "mensagem": "Este e-mail já está cadastrado. Faça login."})
        codigo = str(random.randint(100000, 999999))
        session.update(temp_nome=nome, temp_email=email, temp_senha=senha, temp_codigo=codigo)
        if enviar_email_codigo(email, codigo):
            return jsonify({"ok": True, "mensagem": "Código enviado!"})
        return jsonify({"ok": False, "mensagem": "Erro ao enviar e-mail."}), 500

    @app.route('/validar_cadastro', methods=['POST'])
    def validar_cadastro():
        try:
            dados          = request.get_json()
            codigo_digitado = str(dados.get('codigo', '')).strip()
            codigo_salvo   = str(session.get('temp_codigo', '')).strip()
            if codigo_digitado != codigo_salvo:
                return jsonify({"ok": False, "mensagem": "Código inválido."})
            nome  = session.get('temp_nome')
            email = session.get('temp_email')
            senha = session.get('temp_senha')
            if not cadastrar_usuario(nome, email, senha):
                return jsonify({"ok": False, "mensagem": "Esse e-mail já está em uso."})
            conn   = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()
            if not user:
                return jsonify({"ok": False, "mensagem": "Erro interno ao logar após criar conta."})
            session['usuario_id']   = user['id']
            session['usuario_nome'] = nome
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "mensagem": f"Erro do servidor: {e}"})

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Você saiu da sua conta com sucesso.', 'sucesso')
        return redirect(url_for('login_page'))

    # ── RECUPERAÇÃO DE SENHA ──────────────────────────────────

    @app.route('/enviar_codigo', methods=['POST'])
    def enviar_codigo_rota():
        dados = request.get_json()
        email = dados.get('email', '').strip()
        conn  = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        conn.close()
        if not usuario:
            return jsonify({"ok": False, "mensagem": "Este e-mail não está cadastrado."})
        codigo = str(random.randint(100000, 999999))
        session['reset_codigo'] = codigo
        session['reset_email']  = email
        if enviar_email_codigo(email, codigo):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "mensagem": "Erro ao enviar o e-mail. Tente novamente."})

    @app.route('/validar_codigo', methods=['POST'])
    def validar_codigo_esqueci():
        dados          = request.get_json()
        codigo_digitado = str(dados.get('codigo', '')).strip()
        codigo_salvo   = str(session.get('reset_codigo', '')).strip()
        if not codigo_salvo or codigo_salvo == 'None':
            return jsonify({"ok": False, "mensagem": "Sessão expirada. Volte e recomece o processo."})
        if codigo_digitado == codigo_salvo:
            return jsonify({"ok": True})
        return jsonify({"ok": False, "mensagem": "Código inválido! Tente novamente."})

    @app.route('/redefinir_senha', methods=['POST'])
    def redefinir_senha():
        dados      = request.get_json()
        nova_senha = dados.get('senha', '').strip()
        email      = session.get('reset_email')
        if not email:
            return jsonify({"ok": False, "mensagem": "Sessão expirada. Volte ao início."})
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE email = ?",
            (generate_password_hash(nova_senha), email),
        )
        conn.commit()
        conn.close()
        session.pop('reset_codigo', None)
        session.pop('reset_email', None)
        return jsonify({"ok": True})

    # ── GUARDA-ROUPA ──────────────────────────────────────────

    @app.route('/cadastrar_via_imagem', methods=['POST'])
    @login_obrigatorio
    def cadastrar_via_imagem():
        files          = request.files.getlist('imagem')
        img_bytes_list = [f.read() for f in files]
        # fotos base64 para retornar ao front para preview
        fotos_b64 = [
            f"data:{files[i].content_type};base64,{base64.b64encode(b).decode()}"
            for i, b in enumerate(img_bytes_list)
        ]
        resultado = classificar_imagem(img_bytes_list)
        return jsonify({"dados": resultado, "fotos_base64": fotos_b64})

    @app.route('/salvar_final', methods=['POST'])
    @login_obrigatorio
    def salvar_final():
        usuario_id = session.get('usuario_id')
        dados      = request.get_json()
        nome       = dados.get('nome')
        tipo       = dados.get('tipo', 'Outros').strip()
        cor        = dados.get('cor')
        ocasiao    = dados.get('ocasiao')
        clima      = dados.get('clima')
        fotos_b64  = dados.get('fotos_base64', [])

        pasta_tipo    = "".join(c for c in tipo if c.isalnum() or c in (' ', '_', '-')).strip()
        diretorio_tipo = os.path.join(BASE_DIR, 'static', 'uploads', pasta_tipo)

        caminhos_salvos = []
        for fb64 in fotos_b64:
            nome_arquivo = salvar_imagem_base64(fb64, diretorio_tipo)
            caminhos_salvos.append(f"/static/uploads/{pasta_tipo}/{nome_arquivo}")

        cadastrar_roupa(usuario_id, nome, tipo, cor, ocasiao, clima, caminhos_salvos)
        return jsonify({"ok": True, "mensagem": "Roupa guardada com sucesso!"})

    @app.route('/listar', methods=['GET'])
    @login_obrigatorio
    def listar_roupas():
        usuario_id = session.get('usuario_id')
        conn       = conectar()
        conn.row_factory = sqlite3.Row
        cursor     = conn.cursor()
        cursor.execute("SELECT * FROM roupas WHERE usuario_id = ?", (usuario_id,))
        lista_final = []
        for r in cursor.fetchall():
            roupa_dict = dict(r)
            cursor.execute("SELECT caminho FROM fotos_roupas WHERE roupa_id = ?", (r['id'],))
            roupa_dict['fotos'] = [f['caminho'] for f in cursor.fetchall()]
            lista_final.append(roupa_dict)
        conn.close()
        return jsonify(lista_final)

    @app.route('/sugerir_combinacoes/<int:roupa_id>')
    @login_obrigatorio
    def sugerir_combinacoes(roupa_id):
        usuario_id = session['usuario_id']
        conn       = conectar()
        cursor     = conn.cursor()
        cursor.execute("SELECT * FROM roupas WHERE id = ? AND usuario_id = ?", (roupa_id, usuario_id))
        roupa_base = cursor.fetchone()
        if not roupa_base:
            conn.close()
            return jsonify({"erro": "Peça não encontrada"}), 404
        roupa_base  = dict(roupa_base)
        tipo_base   = roupa_base['tipo']
        ocasiao_base = roupa_base['ocasiao']
        clima_base  = roupa_base['clima']
        superiores  = ["Camisa", "Camiseta", "Blusa", "Casaco"]
        inferiores  = ["Calça", "Bermuda", "Saia"]
        tipos_compativeis = []
        if tipo_base in superiores:
            tipos_compativeis = inferiores + ["Calçado"]
        elif tipo_base in inferiores:
            tipos_compativeis = superiores + ["Calçado"]
        elif tipo_base == "Vestido":
            tipos_compativeis = ["Calçado", "Casaco"]
        elif tipo_base == "Calçado":
            tipos_compativeis = superiores + inferiores + ["Vestido"]
        cursor.execute("SELECT * FROM roupas WHERE usuario_id = ? AND id != ?", (usuario_id, roupa_id))
        todas_roupas = [dict(row) for row in cursor.fetchall()]
        sugestoes = []
        for r in todas_roupas:
            if r['tipo'] in tipos_compativeis and r['ocasiao'] == ocasiao_base and r['clima'] == clima_base:
                cursor.execute("SELECT caminho FROM fotos_roupas WHERE roupa_id = ? LIMIT 1", (r['id'],))
                foto_row  = cursor.fetchone()
                r['foto'] = foto_row['caminho'] if foto_row else None
                sugestoes.append(r)
        conn.close()
        return jsonify({"peca_selecionada": roupa_base, "combinacoes_sugeridas": sugestoes})

    @app.route('/usar/<int:id>')
    @login_obrigatorio
    def usar(id):
        usuario_id = session.get('usuario_id')
        conn       = conectar()
        cursor     = conn.cursor()
        cursor.execute("SELECT id FROM roupas WHERE id = ? AND usuario_id = ?", (id, usuario_id))
        if cursor.fetchone():
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO historico (roupa_id, data_uso) VALUES (?, ?)", (id, data_atual))
            cursor.execute("UPDATE roupas SET vezes_usada = vezes_usada + 1 WHERE id = ?", (id,))
            conn.commit()
            conn.close()
            return jsonify({"ok": True})
        conn.close()
        return jsonify({"ok": False, "mensagem": "Operação não permitida."}), 403

    @app.route('/excluir/<int:id>')
    @login_obrigatorio
    def excluir(id):
        usuario_id = session.get('usuario_id')
        nome_excluido = excluir_roupa(id, usuario_id)
        if nome_excluido:
            return jsonify({"ok": True, "mensagem": f"Roupa '{nome_excluido}' excluída."})
        return jsonify({"ok": False, "mensagem": "Erro ou permissão negada."}), 403

    @app.route('/editar/<int:id>', methods=['POST'])
    @login_obrigatorio
    def editar(id):
        usuario_id = session.get('usuario_id')
        dados = request.get_json()
        try:
            editar_roupa(
                id, usuario_id,
                dados.get('nome'), dados.get('tipo'),
                dados.get('cor'),  dados.get('ocasiao'), dados.get('clima'),
            )
            return jsonify({"ok": True, "mensagem": "Roupa atualizada com sucesso!"})
        except Exception as e:
            return jsonify({"ok": False, "mensagem": f"Erro ao editar: {e}"}), 500

    @app.route('/historico')
    @login_obrigatorio
    def historico():
        dados = buscar_historico_usuario(session.get('usuario_id'))
        return jsonify(dados)

    # ── PERFIL ────────────────────────────────────────────────

    @app.route('/perfil')
    @login_obrigatorio
    def perfil():
        usuario_id = session['usuario_id']
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email, foto_url FROM usuarios WHERE id = ?", (usuario_id,))
        user_data = cursor.fetchone()
        conn.close()
        if not user_data:
            return redirect(url_for('login_page'))
        foto = user_data[2] or "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
        return render_template('perfil.html', usuario={
            "nome": user_data[0], "email": user_data[1], "foto_url": foto,
        })

    @app.route('/perfil/alterar_senha', methods=['POST'])
    @login_obrigatorio
    def alterar_senha():
        usuario_id     = session['usuario_id']
        senha_atual    = request.form.get('senha_atual')
        nova_senha     = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        if nova_senha != confirmar_senha:
            flash('As novas senhas não coincidem.', 'error')
            return redirect(url_for('perfil'))
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE id = ?", (usuario_id,))
        senha_banco = cursor.fetchone()[0]
        # Nota: lógica original mantida (ver limitações na documentação)
        if check_password_hash(senha_banco, senha_atual) == False:
            conn.close()
            flash('Sua senha atual está incorreta.', 'error')
            return redirect(url_for('perfil'))
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (generate_password_hash(nova_senha), usuario_id),
        )
        conn.commit()
        conn.close()
        flash('Sua senha foi alterada com sucesso!', 'success')
        return redirect(url_for('perfil'))

    @app.route('/perfil/atualizar_foto', methods=['POST'])
    @login_obrigatorio
    def atualizar_foto():
        usuario_id = session['usuario_id']
        if 'foto_perfil' not in request.files:
            flash('Nenhum arquivo selecionado.', 'error')
            return redirect(url_for('perfil'))
        foto = request.files['foto_perfil']
        if not foto.filename:
            flash('Nenhum arquivo selecionado.', 'error')
            return redirect(url_for('perfil'))
        ext = foto.filename.rsplit('.', 1)[-1].lower() if '.' in foto.filename else ''
        if ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            flash('Formato não suportado. Use PNG, JPG, GIF ou WEBP.', 'error')
            return redirect(url_for('perfil'))
        pasta_perfil = os.path.join(BASE_DIR, 'static', 'uploads', 'perfil')
        nome_arquivo = salvar_foto_perfil(foto.stream, pasta_perfil)
        if not nome_arquivo:
            flash('Erro ao processar a imagem.', 'error')
            return redirect(url_for('perfil'))
        url_foto = f"/static/uploads/perfil/{nome_arquivo}"
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET foto_url = ? WHERE id = ?", (url_foto, usuario_id))
        conn.commit()
        conn.close()
        flash('Foto de perfil atualizada com sucesso! 📸', 'success')
        return redirect(url_for('perfil'))

    # ── ALTERAÇÃO DE DADOS SEGURA ─────────────────────────────

    @app.route('/perfil/alterar_dados')
    @login_obrigatorio
    def alterar_dados_page():
        usuario_id = session['usuario_id']
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email FROM usuarios WHERE id = ?", (usuario_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        return render_template('alterar_dados.html', usuario={"nome": user_data['nome'], "email": user_data['email']})

    @app.route('/api/confirmar_senha_perfil', methods=['POST'])
    @login_obrigatorio
    def api_confirmar_senha_perfil():
        dados = request.get_json()
        email_digitado = dados.get('email', '').strip()
        senha = dados.get('senha', '')
        usuario_id = session['usuario_id']

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
        resultado = cursor.fetchone()
        conn.close()

        email_atual = resultado['email']

        # 1. Verifica se o e-mail digitado é o mesmo da conta logada
        if email_digitado.lower() != email_atual.lower():
            return jsonify({"ok": False, "mensagem": "E-mail incorreto. Digite o e-mail da sua conta."})

        # 2. Verifica se a senha está correta no banco de dados
        if verificar_usuario(email_atual, senha):
            return jsonify({"ok": True})
            
        return jsonify({"ok": False, "mensagem": "Senha incorreta."})

    @app.route('/api/solicitar_alteracao_dados', methods=['POST'])
    @login_obrigatorio
    def api_solicitar_alteracao_dados():
        dados = request.get_json()
        novo_nome = dados.get('nome', '').strip()
        novo_email = dados.get('email', '').strip()
        usuario_id = session['usuario_id']

        if not novo_nome or not novo_email:
            return jsonify({"ok": False, "mensagem": "Preencha todos os campos."})

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
        email_atual = cursor.fetchone()['email']
        conn.close()

        # Cenário 1: Apenas o nome mudou. Atualiza direto no banco.
        if novo_email.lower() == email_atual.lower():
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET nome = ? WHERE id = ?", (novo_nome, usuario_id))
            conn.commit()
            conn.close()
            session['usuario_nome'] = novo_nome  # Atualiza a sessão
            return jsonify({"ok": True, "acao": "nome_atualizado"})

        # Cenário 2: O e-mail mudou. Verifica se já existe e dispara código.
        if email_existe(novo_email):
            return jsonify({"ok": False, "mensagem": "Este e-mail já está sendo usado por outra conta."})

        import random
        codigo = str(random.randint(100000, 999999))
        session['temp_novo_nome'] = novo_nome
        session['temp_novo_email'] = novo_email
        session['codigo_alteracao_dados'] = codigo

        if enviar_email_codigo(novo_email, codigo):
            return jsonify({"ok": True, "acao": "exigir_codigo", "mensagem": "Código enviado para o novo e-mail!"})
        
        return jsonify({"ok": False, "mensagem": "Erro ao tentar enviar o código para o novo e-mail."})

    @app.route('/api/validar_alteracao_dados', methods=['POST'])
    @login_obrigatorio
    def api_validar_alteracao_dados():
        dados = request.get_json()
        codigo_digitado = str(dados.get('codigo', '')).strip()
        codigo_salvo = str(session.get('codigo_alteracao_dados', '')).strip()

        if not codigo_salvo or codigo_digitado != codigo_salvo:
            return jsonify({"ok": False, "mensagem": "Código inválido."})

        novo_nome = session.get('temp_novo_nome')
        novo_email = session.get('temp_novo_email')
        usuario_id = session['usuario_id']

        # Efetiva a alteração no banco
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET nome = ?, email = ? WHERE id = ?", (novo_nome, novo_email, usuario_id))
        conn.commit()
        conn.close()

        # Limpa o processo e atualiza a sessão local
        session.pop('codigo_alteracao_dados', None)
        session.pop('temp_novo_nome', None)
        session.pop('temp_novo_email', None)
        session['usuario_nome'] = novo_nome

        return jsonify({"ok": True, "mensagem": "Dados atualizados com sucesso!"})

    # ── APIs DE SUGESTÃO ──────────────────────────────────────

    @app.route('/api/sugestoes_combinacoes')
    @login_obrigatorio
    def api_sugestoes_combinacoes():
        usuario_id = session['usuario_id']
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.nome, r.tipo, r.cor, r.clima_ideal, r.ocasiao, f.caminho as foto
            FROM roupas r
            LEFT JOIN (
                SELECT roupa_id, MIN(caminho) as caminho FROM fotos_roupas GROUP BY roupa_id
            ) f ON r.id = f.roupa_id
            WHERE r.usuario_id = ?
        """, (usuario_id,))
        roupas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        clima_atual, temperatura = obter_clima_local()

        return jsonify({
            "clima_atual":   clima_atual,
            "temperatura":   temperatura,
            "fallback_ativo": clima_atual is None,
            "looks": {
                "calor":        gerar_look_por_clima(roupas, "Calor"),
                "frio":         gerar_look_por_clima(roupas, "Frio"),
                "meia_estacao": gerar_look_por_clima(roupas, "Meia"),
            },
        })

    @app.route('/api/busca_personalizada', methods=['POST'])
    @login_obrigatorio
    def api_busca_personalizada():
        usuario_id = session['usuario_id']
        dados      = request.get_json()
        descricao  = (dados.get('descricao') or '').strip().lower()
        if not descricao:
            return jsonify({'pecas': [], 'mensagem': 'Descreva o que você precisa.'})

        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.nome, r.tipo, r.cor, r.ocasiao, r.clima_ideal, f.caminho as foto
            FROM roupas r
            LEFT JOIN (
                SELECT roupa_id, MIN(caminho) as caminho FROM fotos_roupas GROUP BY roupa_id
            ) f ON r.id = f.roupa_id
            WHERE r.usuario_id = ?
        """, (usuario_id,))
        roupas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        intencao = detectar_intencao(descricao)
        from modulos.ia_sugestoes import _score_peca
        scored   = sorted(roupas, key=lambda r: _score_peca(r, intencao), reverse=True)
        filtrado = [r for r in scored if _score_peca(r, intencao) > 0]

        if filtrado:
            return jsonify({'pecas': filtrado[:6], 'mensagem': f'Looks selecionados para: "{descricao}"'})
        return jsonify({
            'pecas': roupas[:6],
            'mensagem': 'Não encontrei correspondência exata, mas aqui estão sugestões do seu guarda-roupa:',
        })

    @app.route('/api/stylist_look', methods=['POST'])
    @login_obrigatorio
    def api_stylist_look():
        usuario_id  = session['usuario_id']
        dados       = request.get_json()
        mensagem    = (dados.get('mensagem') or '').strip()
        clima_api   = dados.get('clima_atual')
        excluir_ids = set(dados.get('excluir_ids', []) + dados.get('look_atual', []))

        if not mensagem:
            return jsonify({'resposta_ia': 'Me conta o que você precisa! 😊', 'look': None})

        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.nome, r.tipo, r.cor, r.ocasiao, r.clima_ideal, r.vezes_usada,
                   f.caminho as foto
            FROM roupas r
            LEFT JOIN (
                SELECT roupa_id, MIN(caminho) as caminho FROM fotos_roupas GROUP BY roupa_id
            ) f ON r.id = f.roupa_id
            WHERE r.usuario_id = ?
        """, (usuario_id,))
        roupas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not roupas:
            return jsonify({
                'resposta_ia': (
                    'Você ainda não tem roupas cadastradas! '
                    'Vá em <strong>Cadastrar Roupa</strong> e adicione suas peças primeiro. 👕'
                ),
                'look': None,
            })

        intencao   = detectar_intencao(mensagem, clima_api)
        look_pecas = montar_look(roupas, intencao, excluir_ids)

        if not look_pecas:
            return jsonify({
                'resposta_ia': (
                    'Não encontrei peças que combinem. '
                    'Tente descrever de outra forma ou adicione mais roupas! 😊'
                ),
                'look': None,
            })

        texto = gerar_texto_look(look_pecas, intencao, clima_api)

        return jsonify({
            'resposta_ia': texto['resposta_ia'],
            'look': {
                'titulo':    texto['titulo'],
                'pecas':     look_pecas,
                'clima':     texto['clima'],
                'ocasiao':   texto['ocasiao'],
                'descricao': texto['descricao'],
            },
        })
