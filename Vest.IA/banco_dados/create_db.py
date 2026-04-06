import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
DB_FOLDER = os.path.join(project_root, 'banco_dados')
DB_PATH = os.path.join(DB_FOLDER, 'vest.ia.db')

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def criar_banco():
    conn = get_db_connection()
    cursor = conn.cursor()

    # tabela roupas (agora com clima_ideal)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roupas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        tipo TEXT,
        cor TEXT,
        ocasiao TEXT,
        clima_ideal TEXT,
        imagem TEXT,
        vezes_usada INTEGER DEFAULT 0
    )
    ''')

    # tabela histórico
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roupa_id INTEGER,
        data_uso TEXT,
        FOREIGN KEY (roupa_id) REFERENCES roupas(id)
    )
    ''')

    conn.commit()
    conn.close()

    print("Banco criado com sucesso!")

# execute
if __name__ == "__main__":
    criar_banco()
