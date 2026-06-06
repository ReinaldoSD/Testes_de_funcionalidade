from functools import wraps
from flask import session, redirect, url_for, flash


def login_obrigatorio(f):
    """
    Decorador que protege rotas autenticadas.
    Redireciona para /login se não houver sessão ativa.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'erro')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function
