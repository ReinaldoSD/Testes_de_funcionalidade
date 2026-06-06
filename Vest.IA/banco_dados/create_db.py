import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
DB_FOLDER = os.path.join(project_root, 'banco_dados')
DB_PATH = os.path.join(DB_FOLDER, 'vest.ia.db')

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de USUÁRIOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            foto_url TEXT,
            data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de Roupas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roupas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        tipo TEXT,
        cor TEXT,
        ocasiao TEXT,
        clima_ideal TEXT,
        vezes_usada INTEGER DEFAULT 0,
        data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    """)

    # Tabela de Fotos (Uma roupa pode ter várias fotos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fotos_roupas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roupa_id INTEGER NOT NULL,
        caminho TEXT NOT NULL,
        FOREIGN KEY (roupa_id) REFERENCES roupas (id)
    )
    """)

    # Tabela de Histórico de Uso
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roupa_id INTEGER NOT NULL,
        data_uso TEXT NOT NULL,
        FOREIGN KEY (roupa_id) REFERENCES roupas (id)
    )
    """)

    conn.commit()
    conn.close()
    print("Banco de dados e tabelas verificados/criados com sucesso!")

if __name__ == "__main__":
    criar_banco()
